import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "attnconv", "hypothesis": "conv + bounded selective decay is the minimal pair",
        "family": "minimal-decay-attention"}


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        xc = self.conv(F.pad(x.transpose(1, 2), (3, 0))).transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh)
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = torch.softmax(logits, dim=-1) @ v
        return self.o(out.transpose(1, 2).reshape(B, T, D))
