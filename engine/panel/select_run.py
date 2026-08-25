#!/usr/bin/env python3
"""Resolve/verify which payload site/spec-reader/ will load.

The page resolves its behaviour data in this order (see app.js there):
  1. ?data=<name>          URL-param pin                 (--pin here)
  2. data/manifest.json    "latest" timestamped run, maintained by build_site_data.py
  3. data/behaviours.json  the shipped fallback, always tracked

This CLI resolves the same chain against the same data directory, so a pin can be
verified before its URL is shared. A name resolves only when the file exists and
parses as JSON -- exactly how the page consumes it; anything else falls through to
the next source. Pinning is the inclusive OR of this CLI flag and the URL param:
both resolve the same way.

Usage:
  python3 select_run.py                    show the run ledger and what the page loads now
  python3 select_run.py --latest           resolve/verify the manifest's latest run
  python3 select_run.py --pin <name>       resolve/verify a specific run (a ?data= value,
                                           with or without its .json suffix)
  --data-dir=<dir>                         override the site data dir (tests)

Exit status: 0 when the requested source resolves, 1 otherwise.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_builder():
    spec = importlib.util.spec_from_file_location("build_site_data", HERE / "build_site_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    bsd = load_builder()
    argv = list(sys.argv[1:] if argv is None else argv)
    data_dir = bsd.DATA_DIR
    pin = None
    want_latest = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--pin="):
            pin = a.split("=", 1)[1]
        elif a == "--pin":
            i += 1
            if i >= len(argv):
                print("error: --pin needs a value", file=sys.stderr)
                return 1
            pin = argv[i]
        elif a == "--latest":
            want_latest = True
        elif a.startswith("--data-dir="):
            data_dir = Path(a.split("=", 1)[1])
        elif a == "--data-dir":
            i += 1
            if i >= len(argv):
                print("error: --data-dir needs a value", file=sys.stderr)
                return 1
            data_dir = Path(argv[i])
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            print(f"error: unknown argument {a!r}", file=sys.stderr)
            return 1
        i += 1

    manifest = bsd.read_manifest(data_dir / bsd.MANIFEST_NAME)
    resolved, source = bsd.resolve_data_name(data_dir, pin=pin, manifest=manifest)
    data_value = resolved[:-5] if resolved and resolved.endswith(".json") else resolved

    if pin is not None:
        if source == "pin":
            print(f"resolved {resolved} (source: pin)")
            print(f"?data={data_value}")
            return 0
        print(f"error: pin {pin!r} does not resolve in {data_dir} "
              "(absent, unparseable, or not a valid name)", file=sys.stderr)
        if resolved:
            print(f"note: the page would load {resolved} (source: {source}) instead",
                  file=sys.stderr)
        return 1

    if want_latest:
        if source == "latest":
            print(f"resolved {resolved} (source: latest)")
            print(f"?data={data_value}")
            return 0
        if not manifest.get("runs"):
            print(f"error: no manifest with runs at {data_dir / bsd.MANIFEST_NAME}",
                  file=sys.stderr)
        else:
            print(f"error: manifest latest {manifest.get('latest')!r} does not resolve "
                  f"in {data_dir}", file=sys.stderr)
        if resolved:
            print(f"note: the page would load {resolved} (source: {source}) instead",
                  file=sys.stderr)
        return 1

    # Default: report the chain as the page sees it, newest run first.
    try:
        shown_dir = data_dir.relative_to(bsd.ROOT)
    except ValueError:
        shown_dir = data_dir
    print(f"data dir: {shown_dir}")
    runs = manifest.get("runs", [])
    if runs:
        print(f"manifest: {len(runs)} run(s), latest {manifest.get('latest')}")
        for r in runs:
            print(f"  {r.get('timestamp', '?')}  {r.get('filename', '?')}  "
                  f"rubric={r.get('rubric', '?')}  panel={r.get('panel', '?')}")
    else:
        print("manifest: none (fresh clone -- no local runs)")
    if resolved:
        print(f"page loads: {resolved} (source: {source})")
        return 0
    print("page loads: nothing -- no pin, no manifest run, and no shipped fallback")
    return 1


if __name__ == "__main__":
    sys.exit(main())
