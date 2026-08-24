#!/usr/bin/env python3
"""Regenerate the golden snapshots in tests/golden/.

    python3 tests/dump_goldens.py --write            # all goldens
    python3 tests/dump_goldens.py --write corpus     # just the cite.py corpus
    python3 tests/dump_goldens.py --write find       # just the find queries

Two golden families:

corpus -- cite.py outline + show + resolve for every section of both pinned
specs. Sections are enumerated by importing cite.py (so the dump always
covers every section the parser sees), but every captured line is genuine
CLI output from a subprocess call, so the snapshot pins what a user of the
tool actually gets.

find -- cite.py find for a fixed query set. `find` is the one command the
corpus snapshot cannot pin: its output depends on match_normalize folding
(curly quotes, dashes, ellipses) and on the sentence-span arithmetic in
cmd_find, neither of which outline/show/resolve exercise.

When to regenerate (and when not to): see tests/README.md.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITE = ROOT / "engine" / "spec-cite" / "cite.py"
GOLDEN = Path(__file__).resolve().parent / "golden"

sys.path.insert(0, str(CITE.parent))
import cite  # noqa: E402

SPECS = ("constitution", "model-spec")

# (spec, query) pairs for the find golden. Queries use straight ASCII
# quotes/dashes on purpose: a hit proves the folding maps them onto the
# specs' typographic characters.
FIND_QUERIES = [
    # straight apostrophe must fold onto the constitution's curly ones
    ("constitution", "Claude's three types of principals"),
    # "--" must fold onto an em-dash in the spec text
    ("constitution", "a calculated bet on our part--if powerful AI is coming"),
    # straight double quotes must fold onto curly ones
    ("constitution", 'viewing lower priorities as "tie-breakers"'),
    # a needle crossing a sentence boundary: must report an s<lo>-<hi> range
    # and join both sentences in the excerpt (the cmd_find span arithmetic)
    ("constitution", "bear on a given interaction. In practice, the vast majority"),
    # a multi-hit single-sentence query across specs
    ("model-spec", "chain of command"),
    # a known miss: pins the not-found exit path and message
    ("constitution", "this-is-not-in-the-spec-at-all"),
]


def cli(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        [sys.executable, str(CITE), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        if check:
            sys.exit(f"cite.py {' '.join(args)} failed:\n{result.stderr}")
        body = result.stdout.rstrip("\n")
        body = (body + "\n" if body else "") + result.stderr.rstrip("\n")
        return body + f"\n[exit {result.returncode}]"
    return result.stdout.rstrip("\n")


def section_ref(spec: str, section: "cite.Section") -> str:
    if spec == "model-spec" and section.anchor:
        return f"#{section.anchor}"
    return section.path_str


def dump_spec(spec: str) -> str:
    version, sections, lines = cite.load_spec(spec, None)
    pinned = f"{spec}@{version}"
    out = [f"$ cite.py outline {pinned}", cli("outline", pinned)]
    for section in sections:
        ref = section_ref(spec, section)
        locator = f"{pinned} > {ref}"
        out.append(f'$ cite.py show "{locator}"')
        out.append(cli("show", locator))
        if cite.section_blocks(section, lines):  # empty sections have no span
            out.append(f'$ cite.py resolve "{locator}"')
            out.append(cli("resolve", locator))
    return "\n\n".join(out) + "\n"


def dump_find() -> str:
    out = []
    for spec, query in FIND_QUERIES:
        out.append(f'$ cite.py find {spec} "{query}"')
        out.append(cli("find", spec, query, check=False))
    return "\n\n".join(out) + "\n"


def main() -> None:
    args = sys.argv[1:]
    only = next((a for a in args if a != "--write"), None)
    if "--write" not in args or only not in (None, "corpus", "find"):
        sys.exit("usage: dump_goldens.py --write [corpus|find]"
                 "   (regenerates tests/golden/)")
    GOLDEN.mkdir(parents=True, exist_ok=True)
    if only in (None, "corpus"):
        # The corpus text is NOT committed (it was ~800 KB whose only job was to
        # make a failure readable). It is written here for local diffing and is
        # gitignored; what the suite checks is the digest manifest beside it.
        digest_path = GOLDEN / "corpus-sha256.json"
        manifest = json.loads(digest_path.read_text(encoding="utf-8"))
        for spec in SPECS:
            target = GOLDEN / f"cite-corpus-{spec}.txt"
            body = dump_spec(spec)
            target.write_text(body, encoding="utf-8")
            raw = body.encode("utf-8")
            manifest["goldens"][target.name] = {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "lines": body.count("\n"),
            }
            print(f"wrote {target.relative_to(ROOT)} (gitignored; for diffing)")
        digest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {digest_path.relative_to(ROOT)}")
    if only in (None, "find"):
        target = GOLDEN / "cite-find.txt"
        target.write_text(dump_find(), encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
