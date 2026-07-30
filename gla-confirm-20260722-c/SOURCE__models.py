"""Architectures under test. All share embedding, block layout and SwiGLU MLP;
they differ only in the token-mixing operator, so parameter counts match to <2%.

Layer codes:
  A = full softmax attention (RoPE, causal)
  G = gated linear attention (GLA / DeltaNet-family proxy: data-dependent
      scalar-per-head decay, short depthwise conv, per-head output norm)

Registered architectures:
  transformer : A A A A          (baseline)
  gla         : G G G G          (pure linear-recurrent challenger)
  hybrid      : G G A G          (3:1 linear:full, Qwen3.5/Kimi-Linear-style ratio)
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

ARCHS = {
    "transformer": "AAAA",
    "gla":         "GGGG",
    "hybrid":      "GGAG",
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
    # x: (B, H, T, Dh)
    T = x.shape[2]
    c, s = cos[:T].to(x.dtype), sin[:T].to(x.dtype)
    x1, x2 = x[..., ::2], x[..., 1::2]
    out = torch.empty_like(x)
    out[..., ::2] = x1 * c - x2 * s
    out[..., 1::2] = x1 * s + x2 * c
    return out


class Attention(nn.Module):
    """Standard causal multi-head softmax attention with RoPE."""
    def __init__(self, d, heads, max_len):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        cos, sin = build_rope(self.dh, max_len)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        q, k = apply_rope(q, self.cos, self.sin), apply_rope(k, self.cos, self.sin)
        o = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.o(o.transpose(1, 2).reshape(B, T, D))


class GLA(nn.Module):
    """Gated linear attention, attention-form (math-equivalent to the O(T)
    recurrence S_t = a_t S_{t-1} + k_t v_t^T,  o_t = q_t S_t).

    a_t in (0,1): data-dependent scalar-per-head decay (sigmoid, bias init +4).
    Short causal depthwise conv (k=4) on the input, per-head RMS output norm --
    both standard in the GLA/DeltaNet family and load-bearing for recall tasks.
    No positional encoding: position comes from the recurrence, which is what
    gives this family its length-extrapolation behaviour.
    """
    def __init__(self, d, heads, max_len=None):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, padding=3, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.gate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.gate.bias, 4.0)
        self.onorm = RMSNorm(self.dh)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        xc = self.conv(x.transpose(1, 2))[..., :T].transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2) / math.sqrt(self.dh)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        loga = F.logsigmoid(self.gate(xc)).transpose(1, 2)          # (B,H,T)
        l = loga.cumsum(-1)                                          # log prod a_j
        # o_t = sum_{i<=t} exp(l_t - l_i) (q_t . k_i) v_i
        scores = q @ k.transpose(-1, -2)                             # (B,H,T,T)
        decay = l.unsqueeze(-1) - l.unsqueeze(-2)                    # l_t - l_i
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        w = torch.where(mask, decay, torch.tensor(-1e9, device=x.device)).exp()
        o = (scores * w) @ v                                         # (B,H,T,Dh)
        o = self.onorm(o)
        return self.o(o.transpose(1, 2).reshape(B, T, D))


class SwiGLU(nn.Module):
    def __init__(self, d, hidden):
        super().__init__()
        self.up = nn.Linear(d, 2 * hidden, bias=False)
        self.down = nn.Linear(hidden, d, bias=False)

    def forward(self, x):
        a, b = self.up(x).chunk(2, -1)
        return self.down(F.silu(a) * b)


class Block(nn.Module):
    def __init__(self, kind, d, heads, hidden, max_len, mixer_cls=None):
        super().__init__()
        self.n1, self.n2 = RMSNorm(d), RMSNorm(d)
        if kind == "A":
            self.mix = Attention(d, heads, max_len)
        elif kind == "G":
            self.mix = GLA(d, heads)
        elif kind == "C":                          # candidate slot
            self.mix = mixer_cls(d, heads)
        else:
            raise ValueError(kind)
        self.mlp = SwiGLU(d, hidden)

    def forward(self, x):
        x = x + self.mix(self.n1(x))
        return x + self.mlp(self.n2(x))


class Model(nn.Module):
    def __init__(self, arch, vocab, d=96, heads=4, hidden=256, max_len=512,
                 layout=None, mixer_cls=None):
        super().__init__()
        self.layout = layout if layout is not None else ARCHS[arch]
        self.emb = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList(
            Block(k, d, heads, hidden, max_len, mixer_cls)
            for k in self.layout)
        self.norm = RMSNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.apply(self._init)
        for b in self.blocks:                      # restore decay-gate bias
            if isinstance(b.mix, GLA):             # (apply() zeroed it)
                nn.init.constant_(b.mix.gate.bias, 4.0)

    @staticmethod
    def _init(m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.zeros_(m.bias)

    def forward(self, idx):
        x = self.emb(idx)
        for b in self.blocks:
            x = b(x)
        return self.head(self.norm(x))

    def param_count(self):
        return sum(p.numel() for p in self.parameters())
