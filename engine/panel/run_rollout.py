#!/usr/bin/env python3
"""Produce the full panel dataset: every rollout behaviour x both specs x the frontier panel.

DRY-RUN BY DEFAULT: prints the exact call plan, what resume will skip, and a cost
estimate. Nothing is sent to any API unless --go is passed.

  python3 run_rollout.py [--go] [--runlog=path] [--behaviours=key,key]

Judging is whole-document mode (whole_doc.py), resume-safe: rerunning after a crash
or provider failure only executes missing cells. Known provider quirks and their
fallbacks (from the first three behaviours):
  - Fable content-filtered on one harm-dense cell -> substitute tag `opus`
    (builder prefers fable when both exist).
  - K3 can exhaust its output budget reasoning (finish_reason: length) -> substitute
    tag `kimi-k2` (builder prefers kimi when both exist).
Run a failing cell's substitute with:  python3 whole_doc.py <behaviour> <spec> <sub-tag>
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "panel-config.json").read_text())

ROLLOUT = ["helpfulness", "harmlessness-to-user", "third-party-harm", "proportionate-risk",
           "tradeoffs", "over-under-caution", "objectivity", "user-autonomy", "general-welfare"]
PANEL = ["sol", "fable", "kimi"]
# measured on the first three behaviours (whole-doc mode)
EST = {"sol": 0.55, "fable": 1.60, "kimi": 1.20}   # $ per (behaviour, both specs)


def main():
    go = "--go" in sys.argv
    runlog = HERE / "runlog.jsonl"
    behaviours = ROLLOUT
    for a in sys.argv[1:]:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
        elif a.startswith("--behaviours="):
            behaviours = a.split("=", 1)[1].split(",")
    sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
    h = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(h)
    h.RUNLOG = runlog
    done = h.done_keys("v3w") if runlog.exists() else set()
    first_loc = {s: h.passages(s)[0][0] for s in CONFIG["specs"]}

    plan, skipped = [], []
    for beh in behaviours:
        for spec in CONFIG["specs"]:
            for tag in PANEL:
                cell = (beh, spec, tag)
                if (beh, spec, tag, first_loc[spec]) in done:
                    skipped.append(cell)
                else:
                    plan.append(cell)
    est = sum(EST[t] / len(CONFIG["specs"]) for _, _, t in plan)
    print(f"plan: {len(plan)} calls ({len(skipped)} cells resumed), estimated ${est:.0f}-{est*1.5:.0f}")
    for beh, spec, tag in plan:
        print(f"  whole_doc.py {beh} {spec} {tag}")
    if not go:
        print("\nDRY RUN -- nothing was sent. Re-run with --go to execute.")
        return
    for beh, spec, tag in plan:
        r = subprocess.run([sys.executable, str(HERE / "whole_doc.py"), beh, spec, tag],
                           cwd=HERE)
        if r.returncode != 0:
            print(f"FAILED (continuing): {beh} {spec} {tag} -- see fallbacks in the docstring")
    print("rollout pass complete -- check for PARSE FAILURE lines above, run substitutes "
          "for any failed cell, then: python3 build_site_data.py --runlog=... --rubric=v3w --panel=frontier")


if __name__ == "__main__":
    main()
