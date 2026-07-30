"""FoX sensitivity arm: gate-bias init=2.0, rope=norope.

Same published-FoX formulation as campaign y's baseline (arXiv 2503.02130):
softmax attention with a data-dependent cumulative log-forget bias, no
static decay prior, no write gate, standard sqrt(d)-scaled content term.
This arm only varies the forget-gate bias init and whether RoPE is applied
to q/k before the content dot product (published FoX has no positional
encoding; RoPE is an addition being tested here, not part of the original).
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "fox-sensitivity-b2.0-ropenorope",
        "hypothesis": "gate-bias init or added RoPE rescues FoX transitions",
        "family": "decay-attention"}


def _rope(x):
    B, h, T, dh = x.shape
    half = dh // 2
    inv_freq = 1.0 / (10000 ** (torch.arange(0, half, device=x.device).float() / half))
    t = torch.arange(T, device=x.device).float()
    freqs = torch.einsum("t,d->td", t, inv_freq)
    cos, sin = freqs.cos(), freqs.sin()
    x1, x2 = x[..., :half], x[..., half:]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1).to(x.dtype)


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 2.0)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        pass  # no RoPE (published FoX)
        logf = F.logsigmoid(self.fgate(x)).transpose(1, 2)      # (B,h,T)
        c = logf.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)                # c_i - c_j
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh) + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = torch.softmax(logits, dim=-1) @ v
        return self.o(out.transpose(1, 2).reshape(B, T, D))
