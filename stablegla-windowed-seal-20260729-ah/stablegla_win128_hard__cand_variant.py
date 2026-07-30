"""Stable normalized multi-timescale GLA.

A retrieval-focused linear memory with three stabilizers:
1) log-spaced static half-life priors prevent all heads from collapsing onto one
   fragile learned decay regime;
2) a small bounded input-dependent residual adapts decay without erasing the
   prior; and
3) positive row-normalized kernel weights make every read a convex combination,
   preventing seed-dependent output-scale explosions.
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {
    "name": "stablegla",
    "hypothesis": (
        "Anchored multi-timescale decay plus positive normalized retrieval "
        "preserves GLA's strong associative recall while reducing seed-sensitive "
        "collapse caused by unconstrained decay and signed unnormalized reads."
    ),
    "family": "stable-linear-memory",
}


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        # Raw log-spaced half-life prior: model-level init does not overwrite Parameters.
        half_lives = torch.logspace(math.log10(8.0), math.log10(256.0), heads)
        rate = math.log(2.0) / half_lives
        self.base_log_decay = nn.Parameter(torch.log(torch.expm1(rate)))
        # Zero-initialized adaptive residual; bounded to +-0.5 log-rate units.
        self.decay_delta = nn.Linear(d, heads, bias=False)
        self.write_gate = nn.Linear(d, heads, bias=False)
        self.write_bias = nn.Parameter(torch.full((heads,), 2.0))
        self.qnorm = nn.RMSNorm(self.dh)
        self.knorm = nn.RMSNorm(self.dh)
        self.onorm = nn.RMSNorm(self.dh)
        self.o = nn.Linear(d, d, bias=False)

    def initial_half_lives(self):
        rate = F.softplus(self.base_log_decay)
        return math.log(2.0) / rate

    def _parts(self, x):
        B, T, D = x.shape
        xc = self.conv(F.pad(x.transpose(1, 2), (3, 0))).transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = self.qnorm(q.view(B, T, self.h, self.dh).transpose(1, 2))
        k = self.knorm(k.view(B, T, self.h, self.dh).transpose(1, 2))
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        base = -F.softplus(self.base_log_decay).view(1, self.h, 1)
        adapt = 0.5 * torch.tanh(self.decay_delta(xc)).transpose(1, 2)
        # Adapt multiplicatively around the stationary negative log-decay prior.
        loga = base * torch.exp(adapt)
        l = loga.cumsum(-1)
        sim = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh)
        # Positive feature kernel; clamp exponent before normalization.
        content = F.softplus(sim)
        decay = l.unsqueeze(-1) - l.unsqueeze(-2)
        logwrite = F.logsigmoid(self.write_gate(xc) + self.write_bias).transpose(1, 2)
        logits = content.clamp_min(1e-8).log() + decay + logwrite.unsqueeze(-2)
        idx = torch.arange(T, device=x.device); mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril() & ((idx.unsqueeze(-1) - idx) < 128)
        logits = logits.masked_fill(~mask, float('-inf'))
        weights = torch.softmax(logits, dim=-1)
        return weights, v

    def debug_weights(self, x):
        return self._parts(x)[0]

    def forward(self, x):
        B, T, D = x.shape
        weights, v = self._parts(x)
        out = self.onorm(weights @ v)
        return self.o(out.transpose(1, 2).reshape(B, T, D))
