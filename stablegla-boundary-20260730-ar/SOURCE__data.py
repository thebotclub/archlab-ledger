"""Fixed synthetic task suite. Everything is generated deterministically from
(split, task, salt) so the dataset is frozen by construction.

Tasks
-----
MQAR  (long-context recall proxy): [k1 v1 ... kN vN  SEP  q a q a ...]
      loss on answer positions only. IID eval at train length; a second eval
      at ~2.3x train length probes length generalisation.
STATE (reasoning proxy, state tracking): [d1 s1 d2 s2 ...] where
      s_i = P[(s_{i-1} + d_i) mod M]. Loss on state positions.
STATE-B (continual-learning phase): same task, different output permutation.

Hidden evaluation: eval batches are generated under HIDDEN_SALT, which the
training stream never sees; in the full program this salt lives with the
evaluation owner, not the submitters.
"""
import numpy as np

PAD, SEP = 0, 1
KEY0, NKEY = 10, 64        # keys  10..73
VAL0, NVAL = 74, 16        # values 74..89
DIG0 = 90                  # digits 90..99
ST0 = 100                  # state tokens 100..109
VOCAB = 110

SEQ_LEN = 48
MQAR_PAIRS, MQAR_QUERIES = 8, 8           # 8*2 + 1 + 8*2 = 33 tokens
LONG_LEN = 112
LONG_PAIRS, LONG_QUERIES = 32, 16         # 32*2 + 1 + 16*2 = 97 tokens
STATE_MOD = 5

TRAIN_SALT = 1234


def _hidden_salt():
    """Hidden-eval salt lives in a sealed file owned by the evaluation side.
    Candidate mixer code is statically scanned and may never reference this
    module's internals or the salt file."""
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "eval_salt.txt")
    with open(p) as f:
        return int(f.read().strip())


def configure(seq_len, mqar_pairs, mqar_queries, long_len, long_pairs,
              long_queries, nkey):
    """Re-scale the task suite (used by the GPU tier). Rebuilds vocab."""
    global SEQ_LEN, MQAR_PAIRS, MQAR_QUERIES, LONG_LEN, LONG_PAIRS
    global LONG_QUERIES, NKEY, VAL0, NVAL, DIG0, ST0, VOCAB
    SEQ_LEN, MQAR_PAIRS, MQAR_QUERIES = seq_len, mqar_pairs, mqar_queries
    LONG_LEN, LONG_PAIRS, LONG_QUERIES = long_len, long_pairs, long_queries
    NKEY = nkey
    VAL0 = KEY0 + NKEY
    NVAL = 16
    DIG0 = VAL0 + NVAL
    ST0 = DIG0 + 10
    VOCAB = ST0 + 10


def _rng(salt, *ids):
    return np.random.default_rng((salt, *ids))


def gen_mqar(rng, n, pairs, queries, seq_len):
    toks = np.zeros((n, seq_len), dtype=np.int64)
    mask = np.zeros((n, seq_len), dtype=bool)
    for i in range(n):
        keys = rng.choice(NKEY, size=pairs, replace=False) + KEY0
        vals = rng.integers(0, NVAL, size=pairs) + VAL0
        # FIXED-DISTANCE PANEL (campaign ar): query i references pair i,
        # so every retrieval distance equals 2*pairs exactly.
        qidx = np.arange(queries)
        seq = np.empty(pairs * 2, dtype=np.int64)
        seq[0::2], seq[1::2] = keys, vals
        out = [seq, [SEP]]
        for qi in qidx:
            out.append([keys[qi], vals[qi]])
        flat = np.concatenate([np.asarray(x, dtype=np.int64) for x in out])
        toks[i, :len(flat)] = flat
        apos = pairs * 2 + 1 + 1 + 2 * np.arange(queries)
        mask[i, apos] = True
    return toks, mask


def gen_state(rng, n, seq_len, perm=None):
    steps = (seq_len - 1) // 2
    perm = np.arange(STATE_MOD) if perm is None else perm
    toks = np.zeros((n, seq_len), dtype=np.int64)
    mask = np.zeros((n, seq_len), dtype=bool)
    d = rng.integers(0, 10, size=(n, steps))
    s = np.zeros(n, dtype=np.int64)
    for j in range(steps):
        s = (s + d[:, j]) % STATE_MOD
        toks[:, 2 * j] = DIG0 + d[:, j]
        toks[:, 2 * j + 1] = ST0 + perm[s]
        mask[:, 2 * j + 1] = True
    return toks, mask


def perm_b(salt=7):  # fixed derangement for the continual phase
    rng = _rng(salt, 0)
    while True:
        p = rng.permutation(STATE_MOD)
        if not np.any(p == np.arange(STATE_MOD)):
            return p


def train_batch(step, batch, seed, phase="A"):
    """60/40 MQAR/STATE mixture in phase A; STATE-B only in phase B."""
    rng = _rng(TRAIN_SALT, seed, step, 0 if phase == "A" else 1)
    if phase == "B":
        return gen_state(rng, batch, SEQ_LEN, perm=perm_b())
    n_m = int(batch * 0.7)
    tm, mm = gen_mqar(rng, n_m, MQAR_PAIRS, MQAR_QUERIES, SEQ_LEN)
    ts, ms = gen_state(rng, batch - n_m, SEQ_LEN)
    return np.concatenate([tm, ts]), np.concatenate([mm, ms])


def eval_sets(n=384):
    salt = _hidden_salt()
    r = lambda i: _rng(salt, i)
    return {
        "recall":      gen_mqar(r(1), n, MQAR_PAIRS, MQAR_QUERIES, SEQ_LEN),
        "recall_long": gen_mqar(r(2), n, LONG_PAIRS, LONG_QUERIES, LONG_LEN),
        "state":       gen_state(r(3), n, SEQ_LEN),
        "state_b":     gen_state(r(4), n, SEQ_LEN, perm=perm_b()),
    }
