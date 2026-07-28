#!/usr/bin/env python3
"""Equivalence test: does scoring a whole DOCUMENT in one prompt match scoring it
section-by-section, at sentence granularity? Reports the delta in QUALITY (agreement +
coverage), COST (tokens), and TIME. Gate before any sentence-level K3 run.

  python3 equivalence.py <behaviour> <spec>     spec: constitution | model-spec
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score
import judge

MODEL = "moonshotai/Kimi-K3"
PROVIDER = "together"
MAXTOK = 16384  # headroom so a whole-doc call isn't artificially truncated


def rankavg(x):
    idx = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[idx[j + 1]] == x[idx[i]]:
            j += 1
        for k in range(i, j + 1):
            r[idx[k]] = (i + j) / 2.0
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((x - mb) ** 2 for x in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def spearman(a, b):
    return pearson(rankavg(a), rankavg(b))


def run(client, query, groups):
    """One API call per group. Returns (scores, prompt_toks, completion_toks, seconds)."""
    scores, pin, pout, t0 = {}, 0, 0, time.time()
    for g in groups:
        obj, usage = judge.judge_batch(client, MODEL, query, g, max_tokens=MAXTOK)
        for i, (loc, _) in enumerate(g):
            v = obj.get(str(i + 1))
            if v is not None:
                scores[loc] = max(0.0, min(1.0, float(v)))
        pin += usage.prompt_tokens
        pout += usage.completion_tokens
    return scores, pin, pout, time.time() - t0


def cost(pin, pout):
    return pin * 3 / 1e6 + pout * 15 / 1e6  # Kimi-K3 list: $3/M in, $15/M out


def main():
    beh, spec = sys.argv[1], sys.argv[2]
    chunk = sys.argv[3] if len(sys.argv) > 3 else "paragraph"
    query = json.loads((HERE / "behaviours.json").read_text())[beh]["query"]
    meta = [u for u in score.units_meta(chunk) if u[1] == spec]  # (loc, spec, section, text)
    sections, cur = [], None
    for loc, sp, sec, txt in meta:
        if sec != cur:
            sections.append([]); cur = sec
        sections[-1].append((loc, txt))
    whole = [[(loc, txt) for loc, sp, sec, txt in meta]]
    n = len(meta)

    base, keyname = judge.PROVIDERS[PROVIDER]
    from openai import OpenAI
    client = OpenAI(api_key=judge.env(keyname), base_url=base)

    print(f"\n{beh} / {spec} [{chunk}]: {n} {chunk}s, {len(sections)} sections\n")
    print("per-section (one call per section) ...", file=sys.stderr)
    ps, pin_s, pout_s, t_s = run(client, query, sections)
    print("whole-document (one call) ...", file=sys.stderr)
    pw, pin_w, pout_w, t_w = run(client, query, whole)

    common = [l for l, _, _, _ in meta if l in ps and l in pw]
    a = [ps[l] for l in common]
    b = [pw[l] for l in common]
    mad = sum(abs(x - y) for x, y in zip(a, b)) / len(common) if common else float("nan")
    mx = max((abs(x - y) for x, y in zip(a, b)), default=float("nan"))
    big = sum(1 for x, y in zip(a, b) if abs(x - y) > 0.2)

    print("QUALITY")
    print(f"  coverage:     per-section {len(ps)}/{n}   whole-doc {len(pw)}/{n}   (both scored: {len(common)})")
    print(f"  agreement:    spearman {spearman(a, b):.3f}   mean|Δ| {mad:.3f}   max|Δ| {mx:.3f}   |Δ|>0.2: {big}/{len(common)}")
    print("COST")
    print(f"  per-section:  {pin_s} in / {pout_s} out  = ${cost(pin_s, pout_s):.3f}")
    print(f"  whole-doc:    {pin_w} in / {pout_w} out  = ${cost(pin_w, pout_w):.3f}")
    print("TIME")
    print(f"  per-section:  {t_s:.0f}s ({len(sections)} calls)")
    print(f"  whole-doc:    {t_w:.0f}s (1 call)")


if __name__ == "__main__":
    main()
