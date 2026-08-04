"""S0.5 architectures: nanoGPT-class, 120M-param-class, real-corpus scale.

Same design contract as the toy-scale harness (~/archlab-runs/stablegla-
interior-calibration-20260726-k/p80x384/models.py): all arms share embedding
(tied with the output head), block layout, and SwiGLU MLP; they differ only
in the token-mixing operator, so parameter counts match to <2%.

New at this scale: a chunked causal-attention-with-additive-bias helper
(`chunked_causal`) used by fox/stablegla, and gla's own analogous inline
chunk loop, so a forward+backward at seq_len=2048 doesn't retain a full
(B,H,T,T) tensor for autograd. Each chunk's body is wrapped in
torch.utils.checkpoint (recomputed during backward instead of retained),
so peak activation memory is bounded by O(chunk*T), not O(T*T), regardless
of how many chunks there are -- a plain smaller `chunk` value WITHOUT
checkpointing would still retain every chunk's (B,H,chunk,Tk) tensor
simultaneously for backward, summing back up to O(T*T). chunk=None => one
chunk of size T (exact, unchunked formula; no memory saving, since
checkpointing a single T-sized chunk doesn't shrink it -- fine for the
toy-scale harness's small T, wrong default for this scale's T=2048 training).

Layer codes: A=softmax attention (RoPE), G=GLA, F=FoX (arXiv 2503.02130
baseline), S=StableGLA (multi-timescale stable normalized GLA, campaign
m/q/t claim).
"""
import hashlib
import math
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.checkpoint as ckpt

ARCHS = {
    "transformer": "A" * 12,
    "gla":         "G" * 12,
    "fox":         "F" * 12,
    "stablegla":   "S" * 12,
}


class RMSNorm(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.w = nn.Parameter(torch.ones(d))

    def forward(self, x):
        return self.w * x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + 1e-6)


def build_rope(head_dim, max_len, base=10000.0):
    inv = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
    t = torch.arange(max_len).float()
    freqs = torch.outer(t, inv)
    return torch.cos(freqs), torch.sin(freqs)


def apply_rope(x, cos, sin):
    T = x.shape[2]
    c, s = cos[:T].to(x.dtype), sin[:T].to(x.dtype)
    x1, x2 = x[..., ::2], x[..., 1::2]
    out = torch.empty_like(x)
    out[..., ::2] = x1 * c - x2 * s
    out[..., 1::2] = x1 * s + x2 * c
    return out


# Trailing attention window (tokens): 0/unset => unrestricted causal attention.
# d1 COPY (Lab 3 dose-onset campaign): env var renamed S05_WINDOW -> D1_WINDOW so a
# stale S05_WINDOW in the environment can never silently set this campaign's window,
# and the window is ALSO applied to the plain softmax Attention class (the s05
# original only applied it inside chunked_causal, used by FoX/StableGLA).
# Read once at import -- callers must assert models.WINDOW == expected (p1d lesson).
WINDOW = int(os.environ.get("D1_WINDOW", "0") or 0)


def _causal_chunk_body(qi, kj, vj, row_idx, col_idx, content_fn, bias_fn):
    sim = qi @ kj.transpose(-1, -2)
    logits = content_fn(sim) + bias_fn(row_idx, col_idx)
    mask = col_idx.unsqueeze(0) <= row_idx.unsqueeze(-1)
    if WINDOW > 0:
        # keep only source positions j with 0 <= i - j < WINDOW
        mask = mask & ((row_idx.unsqueeze(-1) - col_idx.unsqueeze(0)) < WINDOW)
    logits = logits.masked_fill(~mask, float("-inf"))
    w = torch.softmax(logits, dim=-1)
    return w @ vj


def chunked_causal(q, k, v, content_fn, bias_fn, chunk=None):
    """Causal softmax attention with an arbitrary additive log-bias, computed
    in causal query-chunks, each gradient-checkpointed so peak activation
    memory is bounded to O(chunk*T) instead of O(T*T) -- see module docstring.
    chunk=None => one chunk of size T (exact, unchunked formula).

    q,k,v: (B,H,T,Dh). content_fn(sim) -> log-space content term, sim is
    q_chunk @ k^T (already NOT scaled). bias_fn(row_idx, col_idx) -> additive
    (B,H,C,Tk) log-bias for absolute query positions `row_idx` (len C) against
    key positions `col_idx` (len Tk); handles decay/write-gate terms.
    """
    B, H, T, Dh = q.shape
    step = T if chunk is None else chunk
    outs = []
    for start in range(0, T, step):
        end = min(start + step, T)
        qi = q[:, :, start:end]
        kj, vj = k[:, :, :end], v[:, :, :end]
        row_idx = torch.arange(start, end, device=q.device)
        col_idx = torch.arange(0, end, device=q.device)
        out_chunk = ckpt.checkpoint(
            _causal_chunk_body, qi, kj, vj, row_idx, col_idx, content_fn,
            bias_fn, use_reentrant=False)
        outs.append(out_chunk)
    return torch.cat(outs, dim=2)


class Attention(nn.Module):
    """Standard causal multi-head softmax attention with RoPE. Uses
    F.scaled_dot_product_attention, which dispatches to flash-attention
    kernels on CUDA when available -- no separate chunking needed."""
    def __init__(self, d, heads, max_len):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        cos, sin = build_rope(self.dh, max_len)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)
        # d1: sliding-window causal mask (True = attend). Position i may attend
        # position j iff j <= i and i - j < WINDOW. WINDOW=0 => plain causal.
        if WINDOW > 0:
            idx = torch.arange(max_len)
            m = (idx.unsqueeze(-1) >= idx.unsqueeze(0)) & \
                ((idx.unsqueeze(-1) - idx.unsqueeze(0)) < WINDOW)
            self.register_buffer("win_mask", m, persistent=False)
        else:
            self.win_mask = None

    def forward(self, x, chunk=None):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        q, k = apply_rope(q, self.cos, self.sin), apply_rope(k, self.cos, self.sin)
        if self.win_mask is not None:
            o = F.scaled_dot_product_attention(
                q, k, v, attn_mask=self.win_mask[:T, :T])
        else:
            o = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.o(o.transpose(1, 2).reshape(B, T, D))


def _gla_chunk_body(qi, ki, vi, bi, state):
    """One chunk of the O(T) chunkwise-parallel recurrent form of causal
    linear attention with a per-(batch,head,position) SCALAR log-decay
    (see GLA docstring). bi is the LOCAL cumulative log-decay within this
    chunk (relative to just-before-chunk-start, i.e. bi[...,0]==loga of the
    chunk's first token) -- kept local/bounded so exp(bi) never involves the
    full-sequence decay magnitude, unlike a naive global-cumsum formulation.
    state (B,H,Dh,Dh) is the carried-in running state, expressed relative to
    just-before-this-chunk. Returns (out_chunk, updated_state)."""
    c = qi.shape[2]
    idx = torch.arange(c, device=qi.device)
    causal = idx.unsqueeze(0) <= idx.unsqueeze(-1)
    decay = bi.unsqueeze(-1) - bi.unsqueeze(-2)
    w = torch.where(causal, decay, torch.tensor(-1e9, device=qi.device)).exp()
    sim = qi @ ki.transpose(-1, -2)
    intra = (sim * w) @ vi
    inter = torch.exp(bi).unsqueeze(-1) * (qi @ state)
    out_chunk = intra + inter
    b_last = bi[..., -1:]
    k_scaled = ki * torch.exp(b_last.unsqueeze(-1) - bi.unsqueeze(-1))
    new_state = torch.exp(b_last).unsqueeze(-1) * state + k_scaled.transpose(-1, -2) @ vi
    return out_chunk, new_state


def gla_recurrent(q, k, v, loga, chunk=None):
    """O(T) chunkwise-parallel form of GLA's causal linear attention:
    math-equivalent to o_i = sum_{j<=i} exp(l_i-l_j) (q_i.k_j) v_j,
    l=cumsum(loga), but NEVER materializes a (T,T) tensor -- only a
    (B,H,Dh,Dh) state is carried between chunks (Dh<<T), so both the memory
    AND the compute are O(T) rather than O(T^2). Each chunk is additionally
    checkpointed since the intra-chunk (B,H,chunk,chunk) term is still
    quadratic in `chunk` (bounded and small, unlike the old T-scale version).
    chunk=None => chunk=T (single chunk; degrades to the direct formula,
    used for exactness checks, not real training)."""
    B, H, T, Dh = q.shape
    step = T if chunk is None else chunk
    state = q.new_zeros(B, H, Dh, Dh)
    outs = []
    for start in range(0, T, step):
        end = min(start + step, T)
        bi = loga[:, :, start:end].cumsum(-1)
        out_chunk, state = ckpt.checkpoint(
            _gla_chunk_body, q[:, :, start:end], k[:, :, start:end],
            v[:, :, start:end], bi, state, use_reentrant=False)
        outs.append(out_chunk)
    return torch.cat(outs, dim=2)


class GLA(nn.Module):
    """Gated linear attention (attention-form; math-equivalent to the O(T)
    recurrence S_t = a_t S_{t-1} + k_t v_t^T, o_t = q_t S_t). No softmax
    normalization anywhere (this is linear, not softmax, attention) -- so
    unlike fox/stablegla this cannot route through chunked_causal's
    content_fn/bias_fn softmax abstraction. Uses gla_recurrent's genuine
    O(T) chunkwise-recurrent state form (see above), not an O(T^2)
    attention-shaped formula with checkpointed recompute."""
    def __init__(self, d, heads, max_len=None):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, padding=3, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.gate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.gate.bias, 4.0)
        self.onorm = RMSNorm(self.dh)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x, chunk=None):
        B, T, D = x.shape
        xc = self.conv(x.transpose(1, 2))[..., :T].transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2) / math.sqrt(self.dh)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        loga = F.logsigmoid(self.gate(xc)).transpose(1, 2)
        out = gla_recurrent(q, k, v, loga, chunk)
        o = self.onorm(out)
        return self.o(o.transpose(1, 2).reshape(B, T, D))


class FoX(nn.Module):
    """Forgetting Transformer baseline, arXiv 2503.02130: softmax attention
    with a data-dependent cumulative log-forget bias added to logits. No
    positional encoding, no static decay prior, no write gate, standard
    sqrt(d)-scaled content term. Ported verbatim from campaign y's
    cand_variant.py (fox_a), generalized with chunked_causal for seq=2048 eval."""
    def __init__(self, d, heads, max_len=None):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 4.0)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x, chunk=None):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        c = F.logsigmoid(self.fgate(x)).transpose(1, 2).cumsum(-1)  # (B,h,T)
        scale = 1.0 / math.sqrt(self.dh)

        def bias_fn(row_idx, col_idx):
            return c[:, :, row_idx].unsqueeze(-1) - c[:, :, col_idx].unsqueeze(-2)

        out = chunked_causal(q, k, v, lambda sim: sim * scale, bias_fn, chunk)
        return self.o(out.transpose(1, 2).reshape(B, T, D))


class StableGLA(nn.Module):
    """Multi-timescale stable normalized GLA (campaign m/q/t claim mixer).
    Ported verbatim from cand_stablegla.py (K reference), generalized with
    chunked_causal for seq=2048 eval."""
    def __init__(self, d, heads, max_len=None):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        half_lives = torch.logspace(math.log10(8.0), math.log10(256.0), heads)
        rate = math.log(2.0) / half_lives
        self.base_log_decay = nn.Parameter(torch.log(torch.expm1(rate)))
        self.decay_delta = nn.Linear(d, heads, bias=False)
        self.write_gate = nn.Linear(d, heads, bias=False)
        self.write_bias = nn.Parameter(torch.full((heads,), 2.0))
        self.qnorm = nn.RMSNorm(self.dh)
        self.knorm = nn.RMSNorm(self.dh)
        self.onorm = nn.RMSNorm(self.dh)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x, chunk=None):
        B, T, D = x.shape
        xc = self.conv(F.pad(x.transpose(1, 2), (3, 0))).transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = self.qnorm(q.view(B, T, self.h, self.dh).transpose(1, 2))
        k = self.knorm(k.view(B, T, self.h, self.dh).transpose(1, 2))
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        base = -F.softplus(self.base_log_decay).view(1, self.h, 1)
        adapt = 0.5 * torch.tanh(self.decay_delta(xc)).transpose(1, 2)
        loga = base * torch.exp(adapt)
        l = loga.cumsum(-1)
        logwrite = F.logsigmoid(self.write_gate(xc) + self.write_bias).transpose(1, 2)
        scale = 1.0 / math.sqrt(self.dh)

        def bias_fn(row_idx, col_idx):
            decay = l[:, :, row_idx].unsqueeze(-1) - l[:, :, col_idx].unsqueeze(-2)
            return decay + logwrite[:, :, col_idx].unsqueeze(-2)

        def content_fn(sim):
            return F.softplus(sim * scale).clamp_min(1e-8).log()

        out = chunked_causal(q, k, v, content_fn, bias_fn, chunk)
        out = self.onorm(out)
        return self.o(out.transpose(1, 2).reshape(B, T, D))

    def initial_half_lives(self):
        rate = F.softplus(self.base_log_decay)
        return math.log(2.0) / rate


class SwiGLU(nn.Module):
    def __init__(self, d, hidden):
        super().__init__()
        self.up = nn.Linear(d, 2 * hidden, bias=False)
        self.down = nn.Linear(hidden, d, bias=False)

    def forward(self, x):
        a, b = self.up(x).chunk(2, -1)
        return self.down(F.silu(a) * b)


_MIX_CLS = {"A": Attention, "G": GLA, "F": FoX, "S": StableGLA}


class Block(nn.Module):
    def __init__(self, kind, d, heads, hidden, max_len):
        super().__init__()
        self.n1, self.n2 = RMSNorm(d), RMSNorm(d)
        self.mix = _MIX_CLS[kind](d, heads, max_len)
        self.mlp = SwiGLU(d, hidden)

    def forward(self, x, chunk=None):
        x = x + self.mix(self.n1(x), chunk=chunk)
        return x + self.mlp(self.n2(x))


class Model(nn.Module):
    def __init__(self, arch, vocab, d=768, heads=12, hidden=2048, max_len=2048,
                 layout=None):
        super().__init__()
        self.layout = layout if layout is not None else ARCHS[arch]
        self.emb = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList(
            Block(kind, d, heads, hidden, max_len) for kind in self.layout)
        self.norm = RMSNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.head.weight = self.emb.weight  # weight tying, standard nanoGPT/GPT-2 practice
        self.apply(self._init)
        for b in self.blocks:                       # restore gate biases apply() zeroed
            if isinstance(b.mix, (GLA, FoX)):
                nn.init.constant_(b.mix.gate.bias if isinstance(b.mix, GLA)
                                   else b.mix.fgate.bias, 4.0)
            if isinstance(b.mix, StableGLA):
                nn.init.constant_(b.mix.write_bias, 2.0)

    @staticmethod
    def _init(m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.zeros_(m.bias)

    def reinitialize_named(self, init_seed):
        """Per-(seed, param-name) init streams, not RNG order -- see toy-scale
        models.py docstring. Makes shape-compatible shared tensors bit-
        identical across arches for a paired comparison."""
        for name, param in self.named_parameters():
            digest = hashlib.sha256(f"{init_seed}:{name}".encode()).digest()
            seed = int.from_bytes(digest[:8], "little") & 0x7FFFFFFFFFFFFFFF
            gen = torch.Generator(device=param.device).manual_seed(seed)
            with torch.no_grad():
                if name.endswith(("gate.bias", "fgate.bias")) and ".mix." in name:
                    param.fill_(4.0)
                elif name.endswith("write_bias"):
                    param.fill_(2.0)
                elif name.endswith(".bias"):
                    param.zero_()
                elif name.endswith(".weight") and param.ndim >= 2:
                    param.normal_(mean=0.0, std=0.02, generator=gen)
                elif name.endswith(".weight") and param.ndim == 1:
                    param.fill_(1.0)

    def forward(self, idx, chunk=None):
        x = self.emb(idx)
        for b in self.blocks:
            x = b(x, chunk=chunk)
        return self.head(self.norm(x))

    def param_count(self):
        return sum(p.numel() for p in self.parameters())
