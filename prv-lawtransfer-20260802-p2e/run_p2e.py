#!/usr/bin/env python3
"""p2d: pre-registered transfer test. Instrument frozen from p2c's run_p2c.py.

The ONLY changes from p2c are evaluation draws and arm plumbing, per
campaign.json's instrument.changes_from_p2c_are_evaluation_draws_only:
  - eval RNG seed 3379290924 (fresh salt, sealed in the campaign dir)
  - filler pool from corpus offset 600000 (disjoint from p2c's 300000..560000)
  - per-stratum random base offset for probe placement (spacing kept)
  - --force-window (arm 3) alongside p2c's --disable-window (arm 4)
Scoring, anchoring, G1 method, BOS handling, and OOM robustness are
byte-equivalent to p2c. No fitting of any kind happens here.
"""
import argparse, json, os, random, sys, time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

OUT_DIR = os.path.expanduser("~/archlab-p2e")
CORPUS = os.path.expanduser("~/archlab-s05/data/train.bin")
EVAL_SEED = 1235501797
FILLER_OFFSET = 900000

KEYS = ["hexagon", "walnut", "compass", "lantern", "meadow", "quartz", "harbour",
        "thistle", "cobalt", "juniper", "marble", "falcon", "cinder", "orchid",
        "granite", "willow", "amber", "pelican", "saffron", "tundra"]
VALUES = ["47", "83", "19", "62", "35", "78", "94", "21", "56", "13",
          "68", "42", "97", "25", "71", "38", "84", "16", "59", "03"]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def strata_for(window, max_context, n_in=10, n_out=14, guard=48):
    lo_hi = window - guard
    hi_lo, hi_hi = window + guard, max_context - 400
    if lo_hi <= 64 or hi_hi <= hi_lo:
        return []
    ratio = (lo_hi / 64.0) ** (1.0 / (n_in - 1))
    inside = {int(round(64 * ratio ** i)) for i in range(n_in)}
    step = (hi_hi - hi_lo) / (n_out - 1)
    outside = {int(round(hi_lo + step * i)) for i in range(n_out)}
    return sorted(inside | outside)


def build_prompt(tok, filler, distance, key, value, insert_needle=True):
    """Distance is measured to the VALUE token (p2c FIX 1, frozen)."""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--window", type=int, required=True)
    ap.add_argument("--max-context", type=int, default=4096)
    ap.add_argument("--reps", type=int, default=48)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--disable-window", action="store_true",
                    help="arm 4: force config.sliding_window=None on a windowed model")
    ap.add_argument("--force-window", type=int, default=None,
                    help="arm 3: force config.sliding_window to an UNSEEN value")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    device = f"cuda:{args.gpu}"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.float16, attn_implementation="eager")
    if args.disable_window:
        log(f"COUNTERFACTUAL: forcing sliding_window None (was {model.config.sliding_window})")
        model.config.sliding_window = None
        for layer in getattr(model, "model", model).layers:
            if hasattr(getattr(layer, "self_attn", None), "sliding_window"):
                layer.self_attn.sliding_window = None
    if args.force_window is not None:
        log(f"UNSEEN BOUNDARY: forcing sliding_window {args.force_window} "
            f"(was {model.config.sliding_window})")
        model.config.sliding_window = args.force_window
        for layer in getattr(model, "model", model).layers:
            if hasattr(getattr(layer, "self_attn", None), "sliding_window"):
                layer.self_attn.sliding_window = args.force_window
    model = model.to(device).eval()
    log(f"{args.model} on {device}; config.sliding_window={model.config.sliding_window}")

    # G1, frozen from p2c: windowed models use the SLIDING mask builder.
    enforcement = {}
    try:
        from transformers.masking_utils import (create_causal_mask,
                                                create_sliding_window_causal_mask)
        # G1 probe must be long enough to see the ACTUAL boundary, which is
        # force_window when set, not args.window (args.window only controls
        # strata_for()). p2e decouples the two (--window 4096 --force-window
        # 5500) to keep strata comparable to p2d arm4; a probe sized off
        # args.window alone would be shorter than the real boundary and
        # falsely report full visibility. Caught pre-completion, 2026-08-02.
        n = max(args.window, args.force_window or 0) + 128
        emb = torch.zeros(1, n, model.config.hidden_size, device=device, dtype=torch.float16)
        builder = (create_causal_mask if model.config.sliding_window is None
                   else create_sliding_window_causal_mask)
        m = builder(config=model.config, inputs_embeds=emb,
                    attention_mask=torch.ones(1, n, dtype=torch.long, device=device),
                    past_key_values=None, position_ids=None)
        if m is None:
            enforcement = {"builder": builder.__name__, "result": "None returned"}
        else:
            row = m[0, 0, n - 1]
            vis = (row > -1e3).nonzero().flatten()
            enforcement = {"builder": builder.__name__,
                           "n_visible": int(vis.numel()),
                           "max_attendable_distance": int((n - 1) - vis.min().item())}
        log(f"G1 (correct builder): {enforcement}")
    except Exception as exc:  # record the REAL reason, never overwrite it
        enforcement = {"error": f"{type(exc).__name__}: {exc}"}
        log(f"G1 failed: {enforcement}")

    import numpy as np
    corpus = np.memmap(CORPUS, dtype=np.uint16, mode="r")
    llama = AutoTokenizer.from_pretrained("NousResearch/Llama-2-7b-hf")
    filler = tok(llama.decode(corpus[FILLER_OFFSET:FILLER_OFFSET + 260000].tolist()),
                 add_special_tokens=False).input_ids
    log(f"filler pool: {len(filler)} tokens (corpus offset {FILLER_OFFSET})")

    strata = strata_for(args.window, args.max_context)
    log(f"strata: {strata}")
    rng = random.Random(EVAL_SEED)
    probes, by_d, by_d_loose, ctrl = [], {}, {}, {}
    truncated_at = None

    for d in strata:
        strict_ok = loose_ok = n = 0
        cs = cn = 0
        stratum_probes = []
        # fresh draws: random base offset per stratum, spacing guarantee kept
        span = max(1, len(filler) - d - 1000)
        base = rng.randrange(span)
        for r in range(args.reps):
            key, value = rng.choice(KEYS), rng.choice(VALUES)
            off = (base + r * (d + 400)) % span
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
        "campaign": "prv-lawtransfer-20260802-p2e",
        "model": args.model, "tag": args.tag,
        "window_used": args.window,
        "config_sliding_window": model.config.sliding_window,
        "counterfactual_window_disabled": bool(args.disable_window),
        "forced_window": args.force_window,
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
        "eval_rng_seed": EVAL_SEED, "filler_offset": FILLER_OFFSET,
        "probes": probes,
        "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, open(f"{OUT_DIR}/p2e_{args.tag}.json", "w"), indent=1)
    log(f"wrote {OUT_DIR}/p2e_{args.tag}.json")


if __name__ == "__main__":
    sys.exit(main())
