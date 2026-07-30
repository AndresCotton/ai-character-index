#!/usr/bin/env python3
"""Produce the full panel dataset: every rollout behaviour x both specs x the frontier panel.

DRY-RUN BY DEFAULT: prints the exact call plan, what resume will skip, and a cost
estimate. Nothing is sent to any API unless --go is passed.

  python3 run_rollout.py [--go] [--runlog=path] [--behaviours=key,key] [--panel=name]

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

# Every behaviours.json key except the two calibration behaviours (no-sycophancy,
# undermine-oversight), which were the rubric-development vehicles, not index rows.
ROLLOUT = ["helpfulness", "harmlessness-to-user", "third-party-harm", "proportionate-risk",
           "tradeoffs", "over-under-caution", "objectivity", "user-autonomy", "general-welfare"]
PANEL = CONFIG["panels"]["frontier_primary"]   # primaries only; substitutes run manually (Skill 4); --panel= overrides
# measured on the first three behaviours (whole-doc mode); the x1.5 band in the
# printout covers retries and long-output cells. Substitutes included so editing
# PANEL never KeyErrors the dry run.
EST = {"sol": 0.55, "fable": 1.60, "kimi": 1.20, "opus": 0.60, "kimi-k2": 0.35}  # $ per (behaviour, both specs)


def build_plan(behaviours, specs, panel, done, first_loc):
    """Pure: which cells to run vs which the runlog already covers."""
    plan, skipped = [], []
    for beh in behaviours:
        for spec in specs:
            for tag in panel:
                cell = (beh, spec, tag)
                if (beh, spec, tag, first_loc[spec]) in done:
                    skipped.append(cell)
                else:
                    plan.append(cell)
    return plan, skipped


def estimate(plan, n_specs):
    """Pure: dollar estimate for a plan; unpriced tags assume cheap."""
    return sum(EST.get(t, 0.10) / n_specs for _, _, t in plan)


def main():
    panel_name = "frontier"
    go = "--go" in sys.argv
    runlog = HERE / "runlog-v3.jsonl"   # the SAME file whole_doc.py appends to
    behaviours = ROLLOUT
    for a in sys.argv[1:]:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
        elif a.startswith("--behaviours="):
            behaviours = a.split("=", 1)[1].split(",")
        elif a.startswith("--panel="):
            panel_name = a.split("=", 1)[1]
            if (panel_name.startswith("_") or panel_name not in CONFIG["panels"]
                    or not isinstance(CONFIG["panels"][panel_name], list)):
                sys.exit(f"unknown panel {panel_name!r} -- panels: {[k for k in CONFIG['panels'] if not k.startswith('_')]}")
            globals()["PANEL"] = CONFIG["panels"][panel_name]
        elif a != "--go":
            sys.exit(f"unknown argument {a!r} -- valid: --go --runlog= --behaviours= --panel=")
    known = {k for k, v in json.loads((HERE / "behaviours.json").read_text()).items()
             if isinstance(v, dict)}
    bad = [b for b in behaviours if b not in known]
    if bad:
        sys.exit(f"unknown behaviours {bad} -- keys in behaviours.json: {sorted(known)}")
    sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
    h = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(h)
    h.RUNLOG = runlog
    done = h.done_keys(CONFIG["rubric"])
    first_loc = {s: h.passages(s)[0][0] for s in CONFIG["specs"]}

    plan, skipped = build_plan(behaviours, CONFIG["specs"], PANEL, done, first_loc)
    est = estimate(plan, len(CONFIG["specs"]))
    print(f"plan: {len(plan)} calls ({len(skipped)} cells resumed), estimated ${est:.0f}-{est*1.5:.0f}")
    for beh, spec, tag in plan:
        print(f"  whole_doc.py {beh} {spec} {tag}")
    if not go:
        print("\nDRY RUN -- nothing was sent. Re-run with --go to execute.")
        return
    fails = 0
    for beh, spec, tag in plan:
        r = subprocess.run([sys.executable, str(HERE / "whole_doc.py"), beh, spec, tag,
                            f"--runlog={runlog}"], cwd=HERE)
        if r.returncode != 0:
            fails += 1
            print(f"FAILED (continuing): {beh} {spec} {tag}")
            if fails >= 5:
                sys.exit("5 consecutive-run failures -- check keys/network before spending further")
        else:
            fails = 0
    # completeness check against the REAL runlog: catches parse failures (which exit 0),
    # crashes, and interrupts uniformly, and names the fix for each missing cell
    done = h.done_keys(CONFIG["rubric"])
    missing = [(b, sp, t) for b, sp, t in
               ((b, sp, t) for b in behaviours for sp in CONFIG["specs"] for t in PANEL)
               if (b, sp, t, first_loc[sp]) not in done]
    if missing:
        print(f"\nINCOMPLETE -- {len(missing)} cells still missing:")
        sub = {"fable": "opus", "kimi": "kimi-k2"}
        for b, sp, t in missing:
            alt = f"  (or substitute: whole_doc.py {b} {sp} {sub[t]})" if t in sub else ""
            print(f"  retry: whole_doc.py {b} {sp} {t} --runlog={runlog}{alt}")
    else:
        print(f"\nCOMPLETE -- every cell banked. Next: python3 build_site_data.py "
              f"--runlog={runlog} --rubric={CONFIG['rubric']} --panel={panel_name}")


if __name__ == "__main__":
    main()
