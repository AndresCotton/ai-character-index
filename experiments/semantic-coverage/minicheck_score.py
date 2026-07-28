#!/usr/bin/env python3
"""MiniCheck grounding/entailment scoring -- a third, LOCAL, free scoring column.

For each spec chunk (as the grounding *document*) and each atomic facet-claim of the
behaviour, MiniCheck returns P(claim is supported by the chunk). We aggregate max over
facets: a chunk "covers" the behaviour if it substantiates any facet. This is a different
signal from cosine (similarity) and the LLM judge (holistic relevance) -- it's entailment.

Run with the minicheck venv (has torch/transformers; does NOT need openai):
    .venv-mc/bin/python minicheck_score.py <behaviour> [chunk]     chunk: paragraph|sentence

Writes scores-<behaviour>-MiniCheck-deberta[-sentence].json -> a column in the demo.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score  # units_meta + puts cite on sys.path; imports openai only inside main(), so safe here
import cite

MODEL = "deberta-v3-large"
TAG = "MiniCheck-deberta"


def claims_for(query):
    """Atomic facet-claims = the behaviour query split into sentences (MiniCheck wants
    sentence-level claims)."""
    return [s.strip() for s in cite.split_sentences(query) if s.strip()]


def main():
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    name = sys.argv[1] if len(sys.argv) > 1 else None
    chunk = sys.argv[2] if len(sys.argv) > 2 else "paragraph"
    if name not in behaviours:
        sys.exit(f"usage: minicheck_score.py <behaviour> [chunk]   ({', '.join(behaviours)})")
    if chunk not in ("paragraph", "sentence"):
        sys.exit("chunk must be 'paragraph' or 'sentence'")
    b = behaviours[name]
    claims = claims_for(b["query"])
    units = score.units_meta(chunk)

    from minicheck.minicheck import MiniCheck
    scorer = MiniCheck(model_name=MODEL, cache_dir=str(HERE / "ckpts"))

    # one (doc, claim) pair per (chunk, facet); aggregate max per chunk
    docs, clist, locs = [], [], []
    for loc, _, _, text in units:
        for c in claims:
            docs.append(text)
            clist.append(c)
            locs.append(loc)
    print(f"scoring {len(units)} chunks x {len(claims)} claims = {len(docs)} pairs ...", file=sys.stderr)
    _, probs, _, _ = scorer.score(docs=docs, claims=clist)

    agg = {}
    for loc, p in zip(locs, probs):
        agg[loc] = max(agg.get(loc, 0.0), float(p))
    results = [{"locator": loc, "score": round(agg[loc], 4), "snippet": text[:220]}
               for loc, _, _, text in units]
    results.sort(key=lambda r: -r["score"])

    stem = f"{name}-{TAG}" + ("" if chunk == "paragraph" else f"-{chunk}")
    (HERE / f"scores-{stem}.json").write_text(json.dumps(
        {"behaviour": name, "label": b["label"], "query": b["query"],
         "source": f"MiniCheck {MODEL}: max over facet-claims of P(claim supported by chunk)",
         "provider": "minicheck", "model": TAG, "chunk": chunk,
         "claims": claims, "n_blocks": len(results), "results": results}, indent=2))
    print(f"\n{name} [{TAG}, {chunk}] -- {len(results)} scored, {len(claims)} claims -> scores-{stem}.json")
    for r in results[:8]:
        print(f"  {r['score']:.3f}  {r['locator'].split(' > ', 1)[1][:55]}")


if __name__ == "__main__":
    main()
