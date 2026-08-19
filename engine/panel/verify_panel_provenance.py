#!/usr/bin/env python3
"""Verify that the shipped site/llm-panel-review/data/behaviours.json is
reproducible from the committed canonical runlog (engine/panel/runlog-v3.jsonl).

Standard being checked: "a fresh clone can verify and reproduce every published
panel number."

The check
  1. reads the committed runlog (fails loudly if it is missing, unreadable, or
     has no rows for the rubric);
  2. rebuilds the payload with build_site_data.py into a scratch directory
     (nothing inside the repo tree is written);
  3. deep-compares rebuilt vs shipped on every field except the documented
     allowance below, printing exact JSON-path deltas on mismatch;
  4. cross-validates the payload's provenance text against facts derived from
     the runlog and panel-config.json (rubric, panel seats, model ids, judges);
  5. splices the shipped runDate into the rebuilt document, re-serializes with
     the builder's exact serializer, and byte-compares against the shipped file
     -- proving the allowance is the ONLY byte-level difference.

DOCUMENTED ALLOWANCE -- provenance.runDate
  build_site_data.py stamps provenance.runDate with `date.today()` at build
  time; the runlog row schema carries no timestamp field, so the original
  build date cannot be re-derived from the log -- a rebuild can only ever emit
  the day it runs, never the historical build date. The shipped value is
  corroborated outside the log: runlog-v3.md records the evidence (the source
  file's mtime 2026-07-29, and the 2026-07-30 integration run named in
  test_panel.py), and verify() tripwires it against DOCUMENTED_RUN_DATE.
  Every other byte must match; step 5 proves that.

Usage
  python3 engine/panel/verify_panel_provenance.py
  python3 engine/panel/verify_panel_provenance.py --payload=other.json --runlog=other.jsonl

Exit codes: 0 = verified; 1 = verification mismatch; 2 = missing/unreadable input.
No network, no keys.
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_RUNLOG = HERE / "runlog-v3.jsonl"
DEFAULT_PAYLOAD = ROOT / "site" / "llm-panel-review" / "data" / "behaviours.json"
DEFAULT_RUBRIC = "v3w"
DEFAULT_PANEL = "frontier"
# JSON paths the builder cannot reproduce deterministically; see module docstring.
ALLOWED_FIELDS = [("provenance", "runDate")]
# The allowance is anchored to the human-reviewed provenance record:
# runlog-v3.md documents the shipped build date. Drift means the payload
# was rebuilt after the note was written.
DOCUMENTED_RUN_DATE = "2026-07-30"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def serialize(doc):
    """build_site_data.py's exact serializer (json.dumps, indent=1, ensure_ascii=False)."""
    return json.dumps(doc, indent=1, ensure_ascii=False)


def runlog_facts(runlog, rubric):
    """Facts derived from the log alone: row counts, models, behaviours, specs
    for rows matching `rubric` (the rows build_site_data.py consumes)."""
    facts = {"rows_total": 0, "rows_rubric": 0, "parsed_false": 0,
             "models": collections.Counter(), "behaviours": collections.Counter(),
             "specs": collections.Counter()}
    with runlog.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            facts["rows_total"] += 1
            if d.get("rubric", "v1") != rubric:
                continue
            facts["rows_rubric"] += 1
            if not d.get("parsed", True):
                facts["parsed_false"] += 1
                continue
            facts["models"][d["model"]] += 1
            facts["behaviours"][d["behaviour"]] += 1
            facts["specs"][d["spec"]] += 1
    return facts


def rebuild(runlog, rubric, panel, scratch_root):
    """Run build_site_data.main() with its ROOT rebound to scratch_root and the
    scratch `--runlog`; returns the rebuilt payload path. Reads from the repo
    (panel-config.json, spec texts; data/reader-test-coverage.json is byte-copied
    into scratch because main() resolves it through ROOT); writes only to scratch."""
    (scratch_root / "data").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "data" / "reader-test-coverage.json",
                    scratch_root / "data" / "reader-test-coverage.json")
    (scratch_root / "site" / "llm-panel-review" / "data").mkdir(parents=True, exist_ok=True)
    bs = _load("build_site_data_under_test", HERE / "build_site_data.py")
    bs.ROOT = scratch_root
    # DATA_DIR is derived from ROOT at module load; rebind it too.
    bs.DATA_DIR = scratch_root / "site" / "llm-panel-review" / "data"
    saved_argv = sys.argv
    # --out= pins the rebuild to the canonical filename: without it the
    # builder emits a timestamped run file (and touches the manifest).
    sys.argv = ["build_site_data.py", f"--runlog={runlog}",
                f"--rubric={rubric}", f"--panel={panel}",
                "--out=behaviours.json"]
    try:
        bs.main()
    finally:
        sys.argv = saved_argv
    return scratch_root / "site" / "llm-panel-review" / "data" / "behaviours.json"


def _remove_allowed(doc):
    """Deep copy minus the documented ALLOWED_FIELDS."""
    out = copy.deepcopy(doc)
    for path in ALLOWED_FIELDS:
        node = out
        for key in path[:-1]:
            if not isinstance(node, dict) or key not in node:
                node = None
                break
            node = node[key]
        if isinstance(node, dict):
            node.pop(path[-1], None)
    return out


def diff_json(a, b, path="$"):
    """Exact JSON-path deltas between two parsed documents."""
    out = []
    if type(a) is not type(b):
        out.append(f"{path}: shipped {a!r} ({type(a).__name__}) != rebuilt {b!r} ({type(b).__name__})")
    elif isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a:
                out.append(f"{path}.{key}: absent from shipped; rebuilt {b[key]!r}")
            elif key not in b:
                out.append(f"{path}.{key}: shipped {a[key]!r}; absent from rebuilt")
            else:
                out.extend(diff_json(a[key], b[key], f"{path}.{key}"))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: list length shipped={len(a)} rebuilt={len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff_json(x, y, f"{path}[{i}]"))
    elif a != b:
        out.append(f"{path}: shipped {a!r} != rebuilt {b!r}")
    return out


def check_provenance(shipped_doc, rubric, panel, facts, config):
    """Cross-check the payload's provenance text against log-derived and
    config-derived facts. Returns a list of error strings (empty = consistent)."""
    errs = []
    prov = shipped_doc.get("provenance", {})

    expected_from = [f"engine/panel/build_site_data.py ({rubric})"]
    if shipped_doc.get("generatedFrom") != expected_from:
        errs.append(f"generatedFrom {shipped_doc.get('generatedFrom')!r} != {expected_from!r}")

    if prov.get("rubric") != rubric:
        errs.append(f"provenance.rubric {prov.get('rubric')!r} != checked rubric {rubric!r}")
    if prov.get("panel_config") != panel:
        errs.append(f"provenance.panel_config {prov.get('panel_config')!r} != checked panel {panel!r}")

    # panel seats, derived from panel-config.json exactly as the builder emits them:
    # "<tag> (<model id>)" for the primary seats when the panel defines them,
    # raw tags otherwise (mirrors build_site_data.py's two branches).
    models_cfg = config.get("models", {})
    panels_cfg = config.get("panels", {})
    if f"{panel}_primary" in panels_cfg:
        expected_panel = sorted(f"{tag} ({models_cfg[tag]['id']})"
                                for tag in panels_cfg[f"{panel}_primary"] if tag in models_cfg)
    else:
        expected_panel = sorted(panels_cfg.get(panel, []))
    if sorted(prov.get("panel", [])) != expected_panel:
        errs.append(f"provenance.panel {sorted(prov.get('panel', []))!r} != config-derived {expected_panel!r}")

    # judges: must equal the seats actually present in the payload's verdicts,
    # must be members of the configured panel, and must appear in the log.
    seats = sorted({m for b in shipped_doc.get("behaviours", [])
                    for cov in b.get("coverage", {}).values()
                    for p in cov.get("passages", []) for m in p.get("verdicts", {})})
    if prov.get("judges_seen_in_data") != seats:
        errs.append(f"provenance.judges_seen_in_data {prov.get('judges_seen_in_data')!r} != "
                    f"seats derived from the payload's verdicts {seats!r}")
    panel_members = set(panels_cfg.get(panel, []))
    extra = set(seats) - panel_members
    if extra:
        errs.append(f"judges not in configured panel {panel!r}: {sorted(extra)!r}")
    unexplained = set(seats) - set(facts["models"])
    if unexplained:
        errs.append(f"judges absent from the runlog's {rubric} rows: {sorted(unexplained)!r}")

    # runDate: the documented allowance -- well-formed and not in the future;
    # equality with the rebuild is NOT required (the rebuild stamps today).
    rd = prov.get("runDate", "")
    try:
        if date.fromisoformat(rd) > date.today():
            errs.append(f"provenance.runDate {rd!r} is in the future")
    except (TypeError, ValueError):
        errs.append(f"provenance.runDate {rd!r} is not an ISO date")
    return errs


def compare(shipped_raw, rebuilt_raw, rubric, panel, facts, config):
    """Full comparison. Returns (exit_code, report_lines)."""
    lines = []
    try:
        shipped_doc = json.loads(shipped_raw)
    except json.JSONDecodeError as e:
        return 1, [f"FAIL: shipped payload is not valid JSON: {e}"]
    try:
        rebuilt_doc = json.loads(rebuilt_raw)
    except json.JSONDecodeError as e:
        return 1, [f"FAIL: rebuilt payload is not valid JSON (builder drift?): {e}"]

    deltas = diff_json(_remove_allowed(shipped_doc), _remove_allowed(rebuilt_doc))
    prov_errs = check_provenance(shipped_doc, rubric, panel, facts, config)

    splice = copy.deepcopy(rebuilt_doc)
    if isinstance(splice.get("provenance"), dict):
        splice["provenance"]["runDate"] = shipped_doc.get("provenance", {}).get("runDate")
    splice_ok = serialize(splice).encode("utf-8") == shipped_raw

    shipped_rd = shipped_doc.get("provenance", {}).get("runDate")
    rebuilt_rd = rebuilt_doc.get("provenance", {}).get("runDate")

    if not deltas and not prov_errs and splice_ok:
        lines.append("PASS: shipped payload reproduces from the committed runlog")
        lines.append("  deep-compare: identical on all fields except the documented allowance provenance.runDate")
        lines.append(f"  allowance: shipped runDate={shipped_rd!r}; rebuild stamps {rebuilt_rd!r} "
                     "(builder uses date.today(); the log schema carries no timestamps)")
        lines.append("  byte-compare: byte-identical after splicing the shipped runDate into the rebuild")
        return 0, lines

    lines.append("FAIL: rebuilt payload does not match the shipped payload")
    for d in deltas[:25]:
        lines.append(f"  delta: {d}")
    if len(deltas) > 25:
        lines.append(f"  ... and {len(deltas) - 25} more deltas")
    for e in prov_errs:
        lines.append(f"  provenance: {e}")
    if not splice_ok and not deltas and not prov_errs:
        lines.append("  serialization mismatch: payloads deep-equal modulo the allowance but bytes differ "
                     "-- check serializer/version drift in build_site_data.py")
    return 1, lines


def verify(runlog=DEFAULT_RUNLOG, payload=DEFAULT_PAYLOAD, rubric=DEFAULT_RUBRIC,
           panel=DEFAULT_PANEL, keep_scratch=False, verbose=True):
    """Orchestrate the check. Returns the exit code (0/1/2)."""
    say = (lambda *a: print(*a)) if verbose else (lambda *a: None)

    if not payload.exists():
        say(f"FAIL: shipped payload not found: {payload}")
        return 2
    if not runlog.exists():
        say(f"FAIL: canonical runlog not found: {runlog}")
        say("      the committed log that produced the shipped payload must exist; "
            "see engine/panel/runlog-v3.md")
        return 2
    try:
        shipped_raw = payload.read_bytes()
    except OSError as e:
        say(f"FAIL: cannot read shipped payload: {e}")
        return 2
    try:
        shipped_doc = json.loads(shipped_raw)
        shipped_rundate = shipped_doc.get("provenance", {}).get("runDate")
    except (json.JSONDecodeError, AttributeError):
        shipped_rundate = None
    if shipped_rundate != DOCUMENTED_RUN_DATE:
        say(f"FAIL: shipped payload runDate {shipped_rundate!r} differs from the "
            f"documented build date {DOCUMENTED_RUN_DATE!r} (engine/panel/runlog-v3.md) "
            "-- the payload was rebuilt after the provenance note was written")
        return 1
    try:
        facts = runlog_facts(runlog, rubric)
    except (OSError, json.JSONDecodeError) as e:
        say(f"FAIL: cannot read/parse runlog {runlog}: {e}")
        return 2
    if facts["rows_rubric"] == 0:
        say(f"FAIL: runlog has no rubric={rubric!r} rows ({facts['rows_total']} rows total) "
            "-- wrong log for this payload")
        return 1

    config_path = HERE / "panel-config.json"
    try:
        config = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        say(f"FAIL: cannot read/parse panel config {config_path}: {e}")
        return 2
    sha = hashlib.sha256(runlog.read_bytes()).hexdigest()
    say(f"runlog: {runlog} ({facts['rows_rubric']}/{facts['rows_total']} rows rubric={rubric}, "
        f"judges {sorted(facts['models'])}; sha256 {sha[:16]}...)")

    if keep_scratch:
        scratch_root = Path(tempfile.mkdtemp(prefix="panel-provenance-"))
        cleanup = None
    else:
        tmp = tempfile.TemporaryDirectory(prefix="panel-provenance-")
        scratch_root = Path(tmp.name)
        cleanup = tmp.cleanup
    try:
        rebuilt_path = rebuild(runlog, rubric, panel, scratch_root)
        rebuilt_raw = rebuilt_path.read_bytes()
    except BaseException as e:   # a builder crash is a verification failure, not a traceback;
        # BaseException, not Exception: a sys.exit() inside the builder raises
        # SystemExit, which an `except Exception` would re-raise unreported
        if isinstance(e, KeyboardInterrupt):
            raise              # Ctrl-C is not a verification failure -- let it propagate
        say(f"FAIL: rebuild from the committed runlog crashed: {type(e).__name__}: {e}")
        return 1
    finally:
        if cleanup:
            cleanup()

    rc, lines = compare(shipped_raw, rebuilt_raw, rubric, panel, facts, config)
    for line in lines:
        say(line)
    if keep_scratch:
        say(f"  scratch rebuild kept at: {scratch_root}")
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Verify the shipped llm-panel-review payload reproduces from the committed runlog.")
    ap.add_argument("--runlog", type=Path, default=DEFAULT_RUNLOG,
                    help=f"canonical runlog (default {DEFAULT_RUNLOG})")
    ap.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD,
                    help=f"shipped payload to verify (default {DEFAULT_PAYLOAD})")
    ap.add_argument("--rubric", default=DEFAULT_RUBRIC)
    ap.add_argument("--panel", default=DEFAULT_PANEL)
    ap.add_argument("--keep-scratch", action="store_true",
                    help="keep the scratch rebuild directory and print its path")
    a = ap.parse_args(argv)
    return verify(a.runlog, a.payload, a.rubric, a.panel, keep_scratch=a.keep_scratch)


if __name__ == "__main__":
    sys.exit(main())
