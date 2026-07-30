import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "fox_softplus", "hypothesis": "fox + one stablegla component", "family": "decay-attention"}


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 4.0)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        logf = F.logsigmoid(self.fgate(x)).transpose(1, 2)
        c = logf.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)
        content = F.softplus((q @ k.transpose(-1, -2)) / math.sqrt(self.dh))
        logits = content.clamp_min(1e-8).log() + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = torch.softmax(logits, dim=-1) @ v
        return self.o(out.transpose(1, 2).reshape(B, T, D))
