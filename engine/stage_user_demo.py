#!/usr/bin/env python3
"""Stage a user-extended site for the feature harness (verify-panel-features.mjs).

Copies site/ into --out DIR/site, then exercises the SAME builder path a
clone/fork user would take, pointed at the copy:

  1. registers a synthetic user spec (`acme-spec`) via a user manifest and
     rebuilds `documents.json` with it folded in (build-spec-reader-data.py
     --user-manifest=...);
  2. registers a synthetic set:user behaviour (`acme-transparency`) in a
     registry copy, banks a tiny panel runlog against the user spec -- one
     related verdict + one core verdict, so the tier bands are both
     exercised -- and builds a timestamped payload + manifest via
     build_site_data.py (no --out), lifted into the copy.

The repo's own site data is restored exactly as found (the transient
timestamped file is removed, the prior manifest reinstated). Prints a JSON
summary the harness consumes:

  python3 engine/stage_user_demo.py --out /tmp/some/dir
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"
SITE = ROOT / "site"
PANEL_DATA = SITE / "llm-panel-review" / "data"

USER_SPEC = "acme-spec"
USER_BEHAVIOUR = "acme-transparency"
SPEC_MD = ("# Acme Transparency Spec\n\n"
           "The provider must disclose compute usage.\n\n"
           "## Reporting\n\nReports are published quarterly.\n")
RUN_DATE = "2026-08-19"   # pinned: keeps staged payloads deterministic


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="scratch dir; DIR/site is staged")
    args = ap.parse_args()
    out_site = Path(args.out).resolve() / "site"
    if out_site.exists():
        sys.exit(f"--out site already exists: {out_site}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Fixtures: user spec + manifest + registry copy + runlog.
        spec_md = tmp / "acme-spec.md"
        spec_md.write_text(SPEC_MD, encoding="utf-8")
        manifest = tmp / "specs.json"
        manifest.write_text(json.dumps({USER_SPEC: {"2026-01-01": {
            "path": str(spec_md), "default": True,
            "title": "Acme Transparency Spec",
            "sourceUrl": "https://acme.example.com/spec"}}}), encoding="utf-8")
        registry = json.loads((ROOT / "data" / "behaviours.json").read_text())
        registry[USER_BEHAVIOUR] = {
            "name": "Acme transparency", "set": "user", "numeric_id": 1,
            "group": None,
            "definition": "The provider must disclose compute usage to users.",
            "facets": []}
        reg_path = tmp / "registry.json"
        reg_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

        env = dict(os.environ, SPEC_CITE_USER_SPECS=str(manifest))
        cite = load_module("cite", ENGINE / "spec-cite" / "cite.py")
        os.environ[cite.MANIFEST_ENV_VAR] = str(manifest)   # in-process cite too
        cite.load_user_manifest()
        harness = load_module("h", ENGINE / "panel" / "harness.py")
        user_locs = [loc for loc, _s, _t in harness.passages(USER_SPEC)]
        if len(user_locs) < 2:
            sys.exit("user spec must expose at least two passages")
        bench_loc = next(iter(harness.passages("constitution")))[0]
        runlog = tmp / "runlog.jsonl"
        rows = [
            {"behaviour": USER_BEHAVIOUR, "spec": USER_SPEC, "model": "qwen-big",
             "locator": user_locs[0], "rubric": "v3w", "parsed": True, "verdict": 1},
            {"behaviour": USER_BEHAVIOUR, "spec": USER_SPEC, "model": "qwen-big",
             "locator": user_locs[1], "rubric": "v3w", "parsed": True, "verdict": 2},
            {"behaviour": "helpfulness", "spec": "constitution", "model": "qwen-big",
             "locator": bench_loc, "rubric": "v3w", "parsed": True, "verdict": 2},
        ]
        runlog.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

        # 1. Copy the site, then rebuild documents.json with the user spec in it.
        shutil.copytree(SITE, out_site)
        subprocess.run(
            [sys.executable, str(ENGINE / "build-spec-reader-data.py"),
             f"--user-manifest={manifest}",
             f"--out={out_site / 'spec-reader' / 'data' / 'documents.json'}"],
            check=True, cwd=ROOT, capture_output=True, text=True)

        # 2. Build the panel payload through the real timestamped path, lift it
        #    into the copy, and restore the repo's data dir exactly as found.
        prior_manifest = PANEL_DATA / "manifest.json"
        saved = prior_manifest.read_text() if prior_manifest.exists() else None
        try:
            subprocess.run(
                [sys.executable, str(ENGINE / "panel" / "build_site_data.py"),
                 f"--runlog={runlog}", f"--registry={reg_path}",
                 f"--behaviours=helpfulness,{USER_BEHAVIOUR}",
                 "--panel=itest", "--rubric=v3w", f"--run-date={RUN_DATE}"],
                check=True, cwd=ROOT, env=env, capture_output=True, text=True)
            emitted = json.loads(prior_manifest.read_text())
            name = emitted["latest"]
            src = PANEL_DATA / name
            shutil.copy2(src, out_site / "llm-panel-review" / "data" / name)
            src.unlink()
            entry = next(r for r in emitted["runs"] if r["filename"] == name)
            (out_site / "llm-panel-review" / "data" / "manifest.json").write_text(
                json.dumps({"latest": name, "runs": [entry]}, indent=2))
        finally:
            if saved is not None:
                prior_manifest.write_text(saved)
            elif prior_manifest.exists():
                prior_manifest.unlink()

        print(json.dumps({
            "site": str(out_site),
            "payload": name,
            "runDate": RUN_DATE,
            "stagedAt": datetime.now().isoformat(timespec="seconds"),
            "userSpec": USER_SPEC,
            "userBehaviour": USER_BEHAVIOUR,
            "panel": "itest",
        }, indent=2))


if __name__ == "__main__":
    main()
