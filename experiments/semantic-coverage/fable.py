#!/usr/bin/env python3
"""Fable per-chunk relevance scoring (an LLM judge) -- a comparison column to the
embeddings. A Fable subagent reads each batch file and scores every chunk 0.00-1.00 for
relevance to the behaviour, writing an <batch>-out.json ({locator: score}). We then merge
into scores-<behaviour>-fable.json, which the demo picks up as its own column.

  python3 fable.py prep [batchsize]   # -> fable_work/<behaviour>-b<NN>.json chunk batches
  python3 fable.py merge              # fable_work/*-out.json -> scores-<behaviour>-fable.json

Persisted separately from the embedding scores (its own files + the fable_work/ raw batches).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score  # reuse corpus() (paragraph, TOC-filtered) + behaviours.json
WORK = HERE / "fable_work"


def prep(bs):
    WORK.mkdir(exist_ok=True)
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    units = score.corpus()  # [(locator, text)] both specs, paragraph granularity
    for name, b in behaviours.items():
        chunks = [{"loc": loc, "text": text} for loc, text in units]
        nb = 0
        for k in range(0, len(chunks), bs):
            nb += 1
            (WORK / f"{name}-b{nb:02d}.json").write_text(json.dumps(
                {"behaviour": name, "label": b["label"], "query": b["query"],
                 "chunks": chunks[k:k + bs]}, indent=2))
        print(f"{name}: {len(chunks)} chunks -> {nb} batch files (size {bs})")


def merge():
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    units = dict(score.corpus())  # locator -> text
    for name, b in behaviours.items():
        scores = {}
        for f in sorted(WORK.glob(f"{name}-b*-out.json")):
            scores.update(json.loads(f.read_text()))
        results = [{"locator": loc, "score": round(float(scores[loc]), 4), "snippet": units[loc][:220]}
                   for loc in units if loc in scores]
        results.sort(key=lambda r: -r["score"])
        missing = [loc for loc in units if loc not in scores]
        (HERE / f"scores-{name}-fable.json").write_text(json.dumps(
            {"behaviour": name, "label": b["label"], "query": b["query"],
             "source": "Fable 5 per-chunk relevance judgement (0-1 scale), paragraph granularity",
             "provider": "fable", "model": "fable-5", "n_blocks": len(results),
             "results": results}, indent=2))
        tag = "complete" if not missing else f"MISSING {len(missing)}"
        print(f"{name}: merged {len(results)}/{len(units)} -> scores-{name}-fable.json -- {tag}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prep":
        prep(int(sys.argv[2]) if len(sys.argv) > 2 else 150)
    elif cmd == "merge":
        merge()
    else:
        sys.exit("usage: fable.py prep [batchsize] | merge")
