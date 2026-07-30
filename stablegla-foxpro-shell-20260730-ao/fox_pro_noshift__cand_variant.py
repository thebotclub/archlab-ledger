import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "fox_pro_noshift", "hypothesis": "Pro minus KV-shift floors -> the shift is the conv-equivalent ingredient",
        "family": "foxpro-shell"}


def _tokshift(u, alpha):
    # u: (B,T,D); alpha: (B,T,1) in (0,1). alpha*u_{t-1} + (1-alpha)*u_t, u_{-1}=0.
    prev = F.pad(u, (0, 0, 1, 0))[:, :-1, :]
    return alpha * prev + (1 - alpha) * u


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 4.0)
        self.qnorm = nn.RMSNorm(self.dh)
        self.knorm = nn.RMSNorm(self.dh)
        self.onorm = nn.RMSNorm(self.dh)
        self.ogate = nn.Linear(d, d, bias=False)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        q, kt, vt = self.qkv(x).chunk(3, -1)
        k, v = kt, vt
        q = self.qnorm(q.view(B, T, self.h, self.dh).transpose(1, 2))
        k = self.knorm(k.view(B, T, self.h, self.dh).transpose(1, 2))
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        logf = F.logsigmoid(self.fgate(x)).transpose(1, 2)
        c = logf.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh) + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = self.onorm(torch.softmax(logits, dim=-1) @ v)
        out = out.transpose(1, 2).reshape(B, T, D)
        return self.o(torch.sigmoid(self.ogate(x)) * out)
