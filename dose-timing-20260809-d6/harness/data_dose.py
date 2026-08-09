"""Lab 3 d1 -- dose-mixing data layer (build task B1, the one new instrument).

Base stream: Lab 2's tokenized FineWeb-Edu corpus (READ-ONLY):
  /home/hani/archlab-s05/data/train.bin  (uint16 memmap, Llama-2 tokenizer,
  vocab 32000, sha pinned in the campaign manifest from corpus_meta.json).

Injection: pre-generated task-format rows (pools/needle_pool.npy,
pools/state_pool.npy, built by gen_pools.py, sha-pinned). Each pool row is a
full block_size token sequence; splicing a row replaces one corpus row of the
batch, so dose-as-fraction-of-rows == dose-as-fraction-of-tokens exactly.

Dose control: EXACT and deterministic. The number of injected rows in step s is
  k(s) = round(F(s+1)) - round(F(s))
where F is the closed-form cumulative expected injected-row count for the
(dose, schedule) pair -- a Bresenham accumulator. Over the whole run the total
injected rows equal round(dose * steps * batch) to within 1 row, at any dose
(the s05 layer's k = round(f * batch) per-step rounding collapses to 0 at
f=0.5%, batch 32 -- that is the defect this module exists to fix).

Schedules (all deliver the SAME total injected rows for the same dose):
  uniform : constant rate dose over all steps
  front   : rate dose*steps/c over the first c = round(0.2*steps) steps, else 0
  late    : rate dose*steps/c over the last  c steps, else 0

Determinism: corpus row draw is rng(data_seed*1_000_003 + step) -- byte-
identical to the s05/p1c convention. Pool row selection is
rng((pool_salt, data_seed, step)) -- disjoint stream, seed-paired across arms.

Achieved dose is COUNTED, not assumed: get_batch returns k and the trainer
accumulates injected_rows / total_rows into the run result.
"""
import os
import numpy as np

GENERATOR_VERSION = "d1-dose-gen-1.0.0"
DATA_DIR = "/home/hani/archlab-s05/data"          # Lab 2 corpus, read-only
POOL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pools")
VOCAB = 32000

_MM = {}


def corpus_memmap(split):
    if split not in _MM:
        _MM[split] = np.memmap(os.path.join(DATA_DIR, f"{split}.bin"),
                               dtype=np.uint16, mode="r")
    return _MM[split]


_POOLS = {}


def pool(name):
    if name not in _POOLS:
        _POOLS[name] = np.load(os.path.join(POOL_DIR, f"{name}_pool.npy"),
                               mmap_mode="r")
    return _POOLS[name]


def _sched_cum(dose, schedule, steps, batch):
    """Return F(s): cumulative expected injected rows after s steps (closed
    form, exact). c = round(0.2*steps) for the front/late/mid burst length."""
    total = dose * steps * batch
    c = max(1, int(round(0.2 * steps)))
    if schedule == "uniform":
        return lambda s: dose * batch * s
    if schedule == "front":
        return lambda s: total * min(s, c) / c
    if schedule == "late":
        start = steps - c
        return lambda s: total * min(max(0, s - start), c) / c
    # d6 (timing-schedule follow-up): "mid" delivers the same dose-sized burst
    # centred on the middle of training, ending at steps//2. ADDITIVE ONLY --
    # uniform/front/late are byte-identical to the d2..d5 instrument; "mid" is
    # a new schedule string the sealed d2..d5 lineage never used.
    if schedule == "mid":
        start = max(0, steps // 2 - c)
        return lambda s: total * min(max(0, s - start), c) / c
    raise ValueError(schedule)


def rows_for_step(dose, schedule, step, steps, batch):
    """Exact deterministic injected-row count for this step (Bresenham)."""
    if dose <= 0:
        return 0
    F = _sched_cum(dose, schedule, steps, batch)
    k = int(np.floor(F(step + 1) + 0.5)) - int(np.floor(F(step) + 0.5))
    return max(0, min(batch, k))


def get_batch(batch, block, data_seed, step, dose=0.0, schedule="uniform",
              steps=1, capability="none", pool_salt=0):
    """One training batch: corpus rows with the first k rows replaced by
    task-format pool rows. Returns (x, y, k)."""
    data = corpus_memmap("train")
    rng = np.random.default_rng(data_seed * 1_000_003 + step)
    ix = rng.integers(0, len(data) - block - 1, size=batch)
    x = np.stack([data[i:i + block].astype(np.int64) for i in ix])
    y = np.stack([data[i + 1:i + 1 + block].astype(np.int64) for i in ix])
    k = 0
    if dose > 0 and capability in ("recall", "state"):
        k = rows_for_step(dose, schedule, step, steps, batch)
        if k > 0:
            p = pool("needle" if capability == "recall" else "state")
            prng = np.random.default_rng((pool_salt, data_seed, step))
            sel = prng.integers(0, len(p), size=k)
            for j, s_ in enumerate(sel):
                row = np.asarray(p[s_]).astype(np.int64)
                x[j] = row[:block]
                y[j, :block - 1] = row[1:block]
                y[j, block - 1] = 0
    return x, y, k


def val_batch(batch, block, seed):
    data = corpus_memmap("val")
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(data) - block - 1, size=batch)
    x = np.stack([data[i:i + block].astype(np.int64) for i in ix])
    y = np.stack([data[i + 1:i + 1 + block].astype(np.int64) for i in ix])
    return x, y


def planned_total(dose, schedule, steps, batch):
    """Total injected rows the schedule will deliver (for manifest checks)."""
    return sum(rows_for_step(dose, schedule, s, steps, batch)
               for s in range(steps))
