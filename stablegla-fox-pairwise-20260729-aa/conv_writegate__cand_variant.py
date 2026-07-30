import math
import torch
import torch.nn as nn
import torch.nn.functional as F

META = {"name": "conv_writegate", "hypothesis": "fox + one stablegla component", "family": "decay-attention"}


class Mixer(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.conv = nn.Conv1d(d, d, 4, groups=d, bias=False)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.fgate = nn.Linear(d, heads, bias=True)
        nn.init.constant_(self.fgate.bias, 4.0)
        self.write_gate = nn.Linear(d, heads, bias=False)
        self.write_bias = nn.Parameter(torch.full((heads,), 2.0))
        self.o = nn.Linear(d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        xc = self.conv(F.pad(x.transpose(1, 2), (3, 0))).transpose(1, 2)
        q, k, v = self.qkv(xc).chunk(3, -1)
        q = q.view(B, T, self.h, self.dh).transpose(1, 2)
        k = k.view(B, T, self.h, self.dh).transpose(1, 2)
        v = v.view(B, T, self.h, self.dh).transpose(1, 2)
        logf = F.logsigmoid(self.fgate(xc)).transpose(1, 2)
        c = logf.cumsum(-1)
        bias = c.unsqueeze(-1) - c.unsqueeze(-2)
        logwrite = F.logsigmoid(self.write_gate(xc) + self.write_bias).transpose(1, 2)
        logits = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh) + bias + logwrite.unsqueeze(-2)
        mask = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        logits = logits.masked_fill(~mask, float("-inf"))
        out = torch.softmax(logits, dim=-1) @ v
        return self.o(out.transpose(1, 2).reshape(B, T, D))
