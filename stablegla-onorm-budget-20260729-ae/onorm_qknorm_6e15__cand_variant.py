import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "onorm_qknorm_6e15", "hypothesis": "conv + bounded selective decay is the minimal pair",
        "family": "minimal-decay-attention"}


class Mixer(nn.Module):
    BOUND = 0.5

    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        rate = math.log(2.0) / 45.25
        self.base_log_decay = nn.Parameter(torch.full((heads,), math.log(math.expm1(rate))))
        self.decay_delta = nn.Linear(d, heads, bias=False)
        self.onorm = nn.RMSNorm(self.dh)
        self.qnorm = nn.RMSNorm(self.dh)
        self.knorm = nn.RMSNorm(self.dh)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        xc = self.conv(F.pad(x.transpose(1, 2), (3, 0))).transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = self.qnorm(q.view(B, T, self.h, self.dh).transpose(1, 2))
        k = self.knorm(k.view(B, T, self.h, self.dh).transpose(1, 2))
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        base = -F.softplus(self.base_log_decay).view(1, self.h, 1)
        adapt = self.BOUND * torch.tanh(self.decay_delta(xc)).transpose(1, 2)
        loga = base * torch.exp(adapt)
        c = loga.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh) + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = self.onorm(torch.softmax(logits, dim=-1) @ v)
        return self.o(out.transpose(1, 2).reshape(B, T, D))
