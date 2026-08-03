#!/usr/bin/env python3
"""checkpoint-audit-20260803-audit1: released-checkpoint survey row.

NON-CLAIM survey. Reuses the p2c instrument verbatim where it matters:
  - value-anchored distances (p2c FIX 1)
  - strict digit-boundary scoring, loose recorded alongside (FIX 2)
  - matched-regime controls with retained generations (FIX 3)
  - BOS prepended (FIX 4)
  - spaced filler offsets (FIX 5)
  - G1 structural mask check via the installed transformers mask builders

Survey deltas vs p2c (precision deliberately reduced for throughput):
  - 16 reps per stratum (p2c used 48) -> wider CIs, noted in output
  - 14 strata: 8 log-spaced inside the nominal boundary, a 2-point bracket
    just outside it, 4 far strata out to max_context-400 (p2c used 24)
  - models with no effective window get the same strata placed at a NOMINAL
    boundary (default 4096) purely so rows are comparable; absence of a cliff
    there is the expected/registered outcome for those rows
  - G1 runs BOTH mask builders for hybrid models (e.g. gemma-2) and records
    per-layer attention types when the config declares them
"""
import argparse, json, os, random, sys, time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

OUT_DIR = os.path.expanduser("~/archlab2-runs/checkpoint-audit-20260803-audit1")
CORPUS = os.path.expanduser("~/archlab-s05/data/train.bin")
CAMPAIGN = "checkpoint-audit-20260803-audit1"

KEYS = ["hexagon", "walnut", "compass", "lantern", "meadow", "quartz", "harbour",
        "thistle", "cobalt", "juniper", "marble", "falcon", "cinder", "orchid",
        "granite", "willow", "amber", "pelican", "saffron", "tundra"]
VALUES = ["47", "83", "19", "62", "35", "78", "94", "21", "56", "13",
          "68", "42", "97", "25", "71", "38", "84", "16", "59", "03"]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def strata_survey(window, max_context, guard=48, n_in=8, n_far=4):
    """14 strata: 8 log-spaced inside, 2-point boundary bracket, 4 far."""
    lo_hi = window - guard
    ratio = (lo_hi / 64.0) ** (1.0 / (n_in - 1))
    inside = {int(round(64 * ratio ** i)) for i in range(n_in)}
    bracket = {window + guard, window + 4 * guard}
    far_lo, far_hi = window + 8 * guard, max_context - 400
    step = (far_hi - far_lo) / (n_far - 1)
    far = {int(round(far_lo + step * i)) for i in range(n_far)}
    return sorted(inside | bracket | far)


def build_prompt(tok, filler, distance, key, value, insert_needle=True):
    """Distance measured to the VALUE token (p2c FIX 1)."""
    head_ids = tok(f" The secret code for {key} is", add_special_tokens=False).input_ids
    tail_ids = tok(f" {value}. ", add_special_tokens=False).input_ids
    query_ids = tok(f" The secret code for {key} is", add_special_tokens=False).input_ids

    bos = [tok.bos_token_id] if tok.bos_token_id is not None else []
    prefix_len = 128
    suffix_len = distance - len(tail_ids) - len(query_ids) + 1
    if suffix_len < 0:
        return None, None
    prefix = filler[:prefix_len]
    suffix = filler[prefix_len:prefix_len + suffix_len]
    if len(suffix) < suffix_len:
        return None, None

    if insert_needle:
        ids = bos + list(prefix) + head_ids + tail_ids + list(suffix) + query_ids
        value_index = len(bos) + prefix_len + len(head_ids)
    else:
        filler_stub = list(filler[9000:9000 + len(head_ids) + len(tail_ids)])
        ids = bos + list(prefix) + filler_stub + list(suffix) + query_ids
        value_index = None
    qpos = len(ids) - 1
    return ids, (None if value_index is None else qpos - value_index)


def score(model, tok, ids, value, device):
    x = torch.tensor([ids], device=device)
    with torch.no_grad():
        out = model.generate(x, max_new_tokens=6, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    gen = tok.decode(out[0, len(ids):], skip_special_tokens=True).strip()
    strict = gen.startswith(value) and (len(gen) == len(value) or not gen[len(value)].isdigit())
    return strict, (value in gen[:12]), gen[:24]


def g1_structural(model, device):
    """Run mask builder(s); for hybrids run both and record layer types."""
    out = {}
    cfg = model.config
    out["declared_sliding_window"] = getattr(cfg, "sliding_window", None)
    out["declared_use_sliding_window"] = getattr(cfg, "use_sliding_window", None)
    lt = getattr(cfg, "layer_types", None)
    if lt:
        out["layer_types_counts"] = {t: lt.count(t) for t in set(lt)}
    try:
        from transformers.masking_utils import (create_causal_mask,
                                                create_sliding_window_causal_mask)
        w = out["declared_sliding_window"]
        n = (w + 128) if w else 4224
        emb = torch.zeros(1, n, cfg.hidden_size, device=device, dtype=torch.float16)
        builders = [create_causal_mask]
        if w and (out["declared_use_sliding_window"] is not False):
            builders.append(create_sliding_window_causal_mask)
        for builder in builders:
            m = builder(config=cfg, inputs_embeds=emb,
                        attention_mask=torch.ones(1, n, dtype=torch.long, device=device),
                        past_key_values=None, position_ids=None)
            if m is None:
                out[builder.__name__] = "None returned (mask-free fast path)"
            else:
                row = m[0, 0, n - 1]
                vis = (row > -1e3).nonzero().flatten()
                out[builder.__name__] = {
                    "n_visible": int(vis.numel()),
                    "max_attendable_distance": int((n - 1) - vis.min().item())}
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--nominal-window", type=int, required=True,
                    help="boundary the strata bracket; for windowless models this "
                         "is a comparability convention, not a claim")
    ap.add_argument("--max-context", type=int, default=8192)
    ap.add_argument("--reps", type=int, default=16)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--expectation", required=True,
                    help="pre-registered expectation, recorded verbatim in output")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    device = f"cuda:{args.gpu}"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.float16, attn_implementation="eager")
    model = model.to(device).eval()
    log(f"{args.model} on {device}; config.sliding_window="
        f"{getattr(model.config, 'sliding_window', None)}")

    enforcement = g1_structural(model, device)
    log(f"G1 structural: {enforcement}")

    import numpy as np
    corpus = np.memmap(CORPUS, dtype=np.uint16, mode="r")
    llama = AutoTokenizer.from_pretrained("NousResearch/Llama-2-7b-hf")
    filler = tok(llama.decode(corpus[300000:300000 + 260000].tolist()),
                 add_special_tokens=False).input_ids
    log(f"filler pool: {len(filler)} tokens")

    strata = strata_survey(args.nominal_window, args.max_context)
    log(f"strata ({len(strata)}): {strata}")
    rng = random.Random(20260803)
    probes, by_d, by_d_loose, ctrl = [], {}, {}, {}
    truncated_at = None
    t0 = time.time()

    for d in strata:
        strict_ok = loose_ok = n = 0
        cs = cn = 0
        stratum_probes = []
        for r in range(args.reps):
            key, value = rng.choice(KEYS), rng.choice(VALUES)
            off = (r * (d + 400)) % max(1, len(filler) - d - 1000)
            ids, rec = build_prompt(tok, filler[off:], d, key, value)
            if ids is None or len(ids) > args.max_context:
                continue
            try:
                s, l, gen = score(model, tok, ids, value, device)
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                try:
                    s, l, gen = score(model, tok, ids, value, device)
                except torch.cuda.OutOfMemoryError:
                    truncated_at = d
                    log(f"OOM twice at d={d} rep {r}; dropping partial stratum "
                        f"and finalizing with {len(by_d)} completed strata")
                    break
            strict_ok += int(s); loose_ok += int(l); n += 1
            stratum_probes.append({"target_distance": d, "distance_recorded": rec,
                                   "key": key, "value": value, "strict": bool(s),
                                   "loose": bool(l), "generated": gen})
            if r % 4 == 0:
                cids, _ = build_prompt(tok, filler[off:], d, key, value,
                                       insert_needle=False)
                if cids is not None and len(cids) <= args.max_context:
                    try:
                        cso, _, cgen = score(model, tok, cids, value, device)
                    except torch.cuda.OutOfMemoryError:
                        torch.cuda.empty_cache()
                        continue
                    cs += int(cso); cn += 1
                    stratum_probes.append({"target_distance": d, "control": True,
                                           "value": value, "strict": bool(cso),
                                           "generated": cgen})
        torch.cuda.empty_cache()
        if truncated_at is not None:
            break
        probes.extend(stratum_probes)
        if n:
            by_d[d] = strict_ok / n
            by_d_loose[d] = loose_ok / n
            ctrl[d] = (cs / cn) if cn else None
            log(f"  d={d:<6} strict {strict_ok}/{n}={strict_ok/n:.3f}  "
                f"loose {loose_ok/n:.3f}  control {cs}/{cn}")

    all_ctrl = [p for p in probes if p.get("control")]
    p_chance = (sum(p["strict"] for p in all_ctrl) / len(all_ctrl)) if all_ctrl else 0.0
    log(f"matched-regime chance (strict): {p_chance:.4f} over {len(all_ctrl)} controls")

    json.dump({
        "campaign": CAMPAIGN,
        "status": "NON-CLAIM survey; no sealed gates",
        "precision_note": ("16 reps/stratum (vs 48 in p2c): binomial 95% CI is "
                           "~+/-0.24 at p=0.5, ~+/-0.09 at p=0.94; adequate for "
                           "cliff/no-cliff verdicts, not for fine rate estimates"),
        "model": args.model, "tag": args.tag,
        "expectation_preregistered": args.expectation,
        "nominal_window_for_strata": args.nominal_window,
        "config_sliding_window": getattr(model.config, "sliding_window", None),
        "config_use_sliding_window": getattr(model.config, "use_sliding_window", None),
        "config_max_position_embeddings": getattr(model.config, "max_position_embeddings", None),
        "layers": getattr(model.config, "num_hidden_layers", None),
        "G1_enforcement": enforcement,
        "distance_anchored_to": "first value token",
        "recall_by_distance_strict": by_d,
        "recall_by_distance_loose": by_d_loose,
        "control_by_distance": ctrl,
        "p_chance_measured_matched_regime": p_chance,
        "n_controls": len(all_ctrl),
        "reps_per_stratum": args.reps, "strata": strata,
        "truncated_at_stratum": truncated_at,
        "runtime_seconds": round(time.time() - t0, 1),
        "probes": probes,
        "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, open(f"{OUT_DIR}/audit_{args.tag}.json", "w"), indent=1)
    log(f"wrote {OUT_DIR}/audit_{args.tag}.json")


if __name__ == "__main__":
    sys.exit(main())
