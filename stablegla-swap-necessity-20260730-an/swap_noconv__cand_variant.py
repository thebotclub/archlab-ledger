import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "swap_noconv", "hypothesis": "unbounded FoX log-sigmoid gate suffices inside conv+qknorm+onorm",
        "family": "swap-necessity"}


class Mixer(nn.Module):
    BOUND = 0.5

    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 1.0)
        self.onorm = nn.RMSNorm(self.dh)
        self.qnorm = nn.RMSNorm(self.dh)
        self.knorm = nn.RMSNorm(self.dh)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        xc = x
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = self.qnorm(q.view(B, T, self.h, self.dh).transpose(1, 2))
        k = self.knorm(k.view(B, T, self.h, self.dh).transpose(1, 2))
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        loga = F.logsigmoid(self.fgate(xc)).transpose(1, 2)
        c = loga.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh) + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = self.onorm(torch.softmax(logits, dim=-1) @ v)
        return self.o(out.transpose(1, 2).reshape(B, T, D))
