#!/usr/bin/env python3
"""Compare panel-calibration variants cell by cell against the feedback targets.

  python3 compare.py <label>=<runlog>:<rubric> [<label>=<runlog>:<rubric> ...]

For every cell (behaviour x spec) present in any runlog: score distribution,
top passages, and the rank of each feedback-named target passage. Also writes
compare-latest.json next to this script for report generation.
"""
import importlib.util, json, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent.parent / "engine" / "panel"
sp = importlib.util.spec_from_file_location("h", PANEL / "harness.py")
h = importlib.util.module_from_spec(sp); sp.loader.exec_module(h)

# Feedback-named core passages (Adria, 2026-08): locator -> short label
TARGETS = {
    ("proportionate-risk", "constitution"):
        [("constitution@2026-01-20 > Being broadly ethical > Avoiding harm > The costs and benefits of actions > ¶6",
          "probability-of-harm factor (named core)")],
    ("proportionate-risk", "model-spec"):
        [("model-spec@2025-12-18 > #control_side_effects > ¶1",
          "minimize side effects (named core)")],
    ("over-under-caution", "constitution"):
        [("constitution@2026-01-20 > Being helpful > Balancing helpfulness with other values > ¶23",
          "overcautious-or-overcompliant test (named core)")],
    ("tradeoffs", "constitution"):
        [("constitution@2026-01-20 > Overview > Claude’s core values > ¶6",
          "initial strongest expression (should lead)")],
}

TEXT = {}
ORDER = {}
for spec_name in ("constitution", "model-spec"):
    for i, (loc, sec, t) in enumerate(h.passages(spec_name)):
        TEXT[loc] = t
        ORDER[loc] = i


def load(runlog, rubric, judges=None):
    """{(behaviour, spec): {locator: {judge: verdict}}} for rows under `rubric`.
    `judges`: optional judge-tag set -- keeps panel composition constant across variants
    when a runlog holds extra seats (e.g. the kimi history plus the deepseek backfill)."""
    cells = defaultdict(lambda: defaultdict(dict))
    for line in Path(runlog).read_text().splitlines():
        d = json.loads(line)
        if d.get("rubric") != rubric or not d.get("parsed", True):
            continue
        if judges and d["model"] not in judges:
            continue
        cells[(d["behaviour"], d["spec"])][d["locator"]][d["model"]] = d["verdict"]
    return cells


def main():
    variants, judges, out = [], None, HERE / "compare-latest.json"
    for a in sys.argv[1:]:
        if a.startswith("--judges="):
            judges = set(a.split("=", 1)[1].split(","))
            continue
        if a.startswith("--out="):
            out = Path(a.split("=", 1)[1])
            continue
        label, rest = a.split("=", 1)
        runlog, rubric = rest.rsplit(":", 1)
        variants.append((label, runlog, rubric))
    variants = [(label, load(runlog, rubric, judges)) for label, runlog, rubric in variants]
    all_cells = sorted({c for _, v in variants for c in v})
    payload = {"variants": [l for l, _ in variants], "cells": {}}
    for cell in all_cells:
        beh, spec = cell
        print(f"\n{'='*100}\nCELL {beh} x {spec}")
        cellout = {}
        for label, data in variants:
            if cell not in data:
                continue
            votes = data[cell]
            scored = sorted(((sum(mv.values()), loc, mv) for loc, mv in votes.items()
                             if sum(mv.values()) > 0), key=lambda x: (-x[0], ORDER[x[1]]))
            dist = defaultdict(int)
            for s, _, _ in scored:
                dist[s] += 1
            judges = sorted({m for mv in votes.values() for m in mv})
            maxv = max([2] + [v for mv in votes.values() for v in mv.values()])
            print(f"\n[{label}] judges={judges}  positive={len(scored)}  "
                  f"dist={{{', '.join(f'{k}:{dist[k]}' for k in sorted(dist, reverse=True))}}}")
            top = []
            for rank, (s, loc, mv) in enumerate(scored[:15], 1):
                tags = "".join(f" {m}:{mv.get(m, '-')}" for m in judges)   # '-' = vote not landed yet
                snip = TEXT.get(loc, "")[:100].replace("\n", " ")
                mark = ""
                for tloc, tlabel in TARGETS.get(cell, []):
                    if loc == tloc:
                        mark = f"   <<< {tlabel}"
                print(f"  #{rank:2} score {s}/{maxv*len(judges)} {tags}  {loc.split(' > ', 1)[1]}{mark}\n"
                      f"      {snip}")
                top.append({"rank": rank, "score": s, "verdicts": mv, "locator": loc,
                            "snippet": snip, "target": bool(mark)})
            tinfo = []
            for tloc, tlabel in TARGETS.get(cell, []):
                rank = next((i + 1 for i, (s, loc, _) in enumerate(scored) if loc == tloc), None)
                sc = sum(votes.get(tloc, {}).values())
                print(f"  TARGET [{tlabel}]: rank={rank} score={sc} verdicts={votes.get(tloc, {})}")
                tinfo.append({"label": tlabel, "locator": tloc, "rank": rank, "score": sc,
                              "verdicts": votes.get(tloc, {})})
            cellout[label] = {"positive": len(scored), "dist": dict(dist), "top": top,
                              "targets": tinfo, "judges": judges, "maxv": maxv,
                              "scores": {loc: sum(mv.values()) for loc, mv in votes.items()}}
        payload["cells"][f"{beh}|{spec}"] = cellout
    out.write_text(json.dumps(payload, ensure_ascii=False))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
