"""Forgetting Transformer (FoX) baseline, per arXiv 2503.02130.

Softmax attention whose logits carry a data-dependent cumulative log-forget
bias: logits_ij = q_i.k_j/sqrt(dh) + sum_{t=j+1..i} log sigmoid(w_f x_t + b).
No positional encoding (the forget gate supplies recency), no static decay
prior, no write gate, standard scaled dot-product content term. Faithful
prior-art control for StableGLA attribution.
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "fox-baseline", "hypothesis": "published FoX class suffices",
        "family": "decay-attention"}


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 4.0)  # start near no-forgetting
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        logf = F.logsigmoid(self.fgate(x)).transpose(1, 2)      # (B,h,T)
        c = logf.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)                # c_i - c_j
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh) + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = torch.softmax(logits, dim=-1) @ v
        return self.o(out.transpose(1, 2).reshape(B, T, D))
