import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "sp_prior", "hypothesis": "fox + one stablegla component", "family": "decay-attention"}


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        half_lives = torch.logspace(math.log10(8.0), math.log10(256.0), heads)
        rate = math.log(2.0) / half_lives
        self.base_log_decay = nn.Parameter(torch.log(torch.expm1(rate)))
        self.decay_delta = nn.Linear(d, heads, bias=False)
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(x).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        base = -F.softplus(self.base_log_decay).view(1, self.h, 1)
        adapt = 0.5 * torch.tanh(self.decay_delta(x)).transpose(1, 2)
        loga = base * torch.exp(adapt)
        c = loga.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)
        content = F.softplus((q @ k.transpose(-1, -2)) / math.sqrt(self.dh))
        logits = content.clamp_min(1e-8).log() + bias
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = torch.softmax(logits, dim=-1) @ v
        return self.o(out.transpose(1, 2).reshape(B, T, D))
