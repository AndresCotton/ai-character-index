#!/usr/bin/env python3
"""Does scoring K3 at SENTENCE granularity give the same signal as at PARAGRAPH?

Uses the (partial, credit-limited) per-sentence K3 scores. Coverage is per-section, so a
paragraph is either fully sentence-covered or not covered at all -- clean for comparison.
For each fully-covered paragraph we aggregate its sentence scores (max = "relevant if any
sentence is") and compare to that paragraph's own paragraph-level K3 score.

  python3 granularity.py     # no API calls, no spend
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rankavg(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0
        i = j + 1
    return r


def pear(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((x - mb) ** 2 for x in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def spearman(a, b):
    return pear(rankavg(a), rankavg(b))


def f1(pred, ref):
    tp = sum(1 for i in range(len(pred)) if pred[i] and ref[i])
    fp = sum(1 for i in range(len(pred)) if pred[i] and not ref[i])
    fn = sum(1 for i in range(len(pred)) if not pred[i] and ref[i])
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0


def main():
    for beh in ("no-sycophancy", "undermine-oversight"):
        para = {r["locator"]: r["score"] for r in json.loads(
            (HERE / f"scores-{beh}-Kimi-K3.json").read_text())["results"]}
        sf = HERE / f"partial-Kimi-K3-sentence-{beh}.json"
        if not sf.exists():
            print(f"{beh}: no sentence file"); continue
        sent = {r["locator"]: r["score"] for r in json.loads(sf.read_text())["results"]}
        by_para = {}
        for sloc, s in sent.items():
            p = sloc.rsplit(" > s", 1)[0]
            by_para.setdefault(p, []).append(s)
        # paragraphs that have sentence scores AND a paragraph score
        locs = [p for p in by_para if p in para]
        pv = [para[p] for p in locs]
        agg_max = [max(by_para[p]) for p in locs]
        agg_mean = [sum(by_para[p]) / len(by_para[p]) for p in locs]
        relp = [x >= 0.5 for x in pv]
        rels = [x >= 0.5 for x in agg_max]
        print(f"\n{beh}  ({len(locs)} covered paragraphs; {sum(relp)} paragraph-relevant, {sum(rels)} sentence-relevant)")
        print(f"  sentence(max)  vs paragraph:  spearman {spearman(agg_max, pv):.3f}  pearson {pear(agg_max, pv):.3f}")
        print(f"  sentence(mean) vs paragraph:  spearman {spearman(agg_mean, pv):.3f}")
        print(f"  agree on 'relevant' (>=0.5):  F1 {f1(rels, relp):.3f}")


if __name__ == "__main__":
    main()
