#!/usr/bin/env python3
"""Recall check: do the top-scored blocks recover the human-curated passages?

Ground truth = the verbatim block-quotes in research/sweeps/01-no-sycophancy.md
(the "Spec coverage -- verbatim excerpts" section, a human-curated citation set).
Each quote is matched to its scored block by TEXT (normalized substring), so it is
robust to locator-format differences, then we report that block's rank in the
scores-no-sycophancy-<provider>.json ranking.

    python3 recall.py [provider]     # provider: openai (default) | deepinfra

This does NOT tune anything to the labels -- it just reports where the cited
passages land, and recall@N across a few N. Interpret, don't fit.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score  # reuse corpus() -> (locator, text), same locators as the scores files

SWEEP = HERE.parent.parent / "research" / "sweeps" / "01-no-sycophancy.md"


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def cited_passages():
    """Contiguous runs of '>' block-quote lines in the coverage section = one passage
    each. The 'Adjacent' items use inline '-' quotes (no '>'), so they're naturally
    excluded -- this returns the CORE curated citations only."""
    lines = SWEEP.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## Spec coverage"))
    end = next(i for i, l in enumerate(lines) if l.startswith("## Curated evals"))
    passages, cur = [], []
    for l in lines[start:end]:
        s = l.strip()
        if s.startswith(">"):
            cur.append(s.lstrip("> ").strip())
        elif cur:
            passages.append(" ".join(cur))
            cur = []
    if cur:
        passages.append(" ".join(cur))
    return passages


def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else "openai"
    sf = HERE / f"scores-no-sycophancy-{provider}.json"
    if not sf.exists():
        sys.exit(f"missing {sf.name} -- run: python3 score.py no-sycophancy {provider}")
    scores = json.loads(sf.read_text())
    ranked = scores["results"]  # already sorted desc
    rank = {r["locator"]: i + 1 for i, r in enumerate(ranked)}
    sval = {r["locator"]: r["score"] for r in ranked}
    total = len(ranked)

    nblocks = [(loc, norm(text)) for loc, text in score.corpus()]
    passages = cited_passages()

    print(f"\nRecall check -- no-sycophancy [{provider}: {scores['model']}]")
    print(f"{len(passages)} curated passages vs {total} scored blocks\n")

    ranks = []
    for p in passages:
        k = norm(p)
        needle = k[20:90] if len(k) > 90 else k
        hit = next((loc for loc, nt in nblocks if needle and needle in nt), None)
        if hit is None:
            print(f"  NO MATCH  {p[:66]}...")
            continue
        r = rank[hit]
        ranks.append(r)
        pct = 100.0 * r / total
        print(f"  rank {r:>4}/{total} (top {pct:4.1f}%)  score {sval[hit]:.3f}  {hit}")

    print(f"\n  matched {len(ranks)}/{len(passages)} passages")
    if ranks:
        print("\n  recall@N (share of curated passages within the top-N scored blocks):")
        for n in (5, 10, 15, 20, 30, 50, 100):
            hits = sum(1 for r in ranks if r <= n)
            print(f"    top {n:>3}:  {hits}/{len(ranks)}  ({100.0*hits/len(ranks):4.0f}%)")
        med = sorted(ranks)[len(ranks) // 2]
        print(f"\n  median rank of a curated passage: {med}/{total}  (worst: {max(ranks)})")


if __name__ == "__main__":
    main()
