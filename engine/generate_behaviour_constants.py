#!/usr/bin/env python3
"""Regenerate the derived behaviour constants from data/behaviours.json.

data/behaviours.json is the behaviour-identity registry (Decision 1, 2026-08-18):
one entry per behaviour across all sets, keyed by slug. This script rewrites the
derived constants that must stay in lockstep with it:

  1. BEHAVIOURS           engine/build-spec-reader-data.py
                          The index-set entries whose numeric_id has a record in
                          data/coverage.json (today ids 1-3) -- exactly the set
                          the builder can render. A coverage record with no
                          registry definition is an error; a definition with no
                          coverage record is stored but not published.
  2. titles               engine/panel/behaviours.json
                          The judge prompts stay curated here; their keys are
                          registry slugs (the panel runlogs are keyed by the
                          same slugs) and every key must be one -- a judge
                          prompt for an unregistered behaviour fails the
                          generator. Committed key order is preserved, and any
                          entry's `title` field is rewritten from the registry
                          name.

display.behaviours in engine/panel/panel-config.json is curated configuration,
not generated: the builder validates every entry against the registry, so a
renamed or unknown slug fails loudly at build time.

Modes:
    python3 engine/generate_behaviour_constants.py            # rewrite in place
    python3 engine/generate_behaviour_constants.py --check    # exit 1 on drift

Only the constant blocks are rewritten; surrounding code is preserved
byte-for-byte. Run after any edit to data/behaviours.json; tests/
test_behaviour_registry.py is the drift gate that fails a commit which edited
a derived copy without updating the registry (and vice versa).
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETS = ("index", "reader-test", "user")

# Definitions render as implicit string concatenations, greedy-wrapped so each
# quoted part is at most this many characters including its trailing space.
# Chosen so the committed constant reproduces as nearly as possible: behaviour
# 2's definition is exactly 67 chars and stays on one line, behaviour 3's wrap
# reproduces exactly, and behaviour 1's second word moves up one line.
DEFINITION_WIDTH = 67


def load_registry(root: Path) -> dict:
    """Load data/behaviours.json, failing loud on any structural break.

    The required-field list is read from data/schema/behaviours.schema.json so
    the loader cannot drift from the schema: an entry missing any required
    field exits naming the slug and the field (before this, a missing field
    died as a bare KeyError in a renderer for index entries, or passed
    silently for reader-test entries). Duplicate keys are rejected at parse
    time -- JSON's default is silent last-wins, which would erase an entry in
    the identity source of truth.
    """
    schema = json.loads(
        (root / "data" / "schema" / "behaviours.schema.json").read_text(encoding="utf-8")
    )
    required_fields = schema["$defs"]["entry"]["required"]

    def reject_duplicate_keys(pairs):
        # object_pairs_hook for json.loads below, called for every JSON object
        # (innermost first). The top-level object maps slugs to entry objects,
        # so all its values are dicts; entry objects carry scalar values. That
        # tells the two messages apart.
        result = {}
        for key, value in pairs:
            if key in result:
                if isinstance(value, dict) and all(isinstance(v, dict) for v in result.values()):
                    sys.exit(
                        f"data/behaviours.json: duplicate top-level slug {key!r} -- JSON "
                        "silently keeps the last of duplicate keys, erasing the earlier entry"
                    )
                sys.exit(f"data/behaviours.json: duplicate key {key!r} inside one entry")
            result[key] = value
        return result

    registry = json.loads(
        (root / "data" / "behaviours.json").read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )
    if not isinstance(registry, dict):
        sys.exit("data/behaviours.json: top level must be an object keyed by slug")
    seen = {}
    for slug, entry in registry.items():
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            sys.exit(f"data/behaviours.json: {slug!r} is not a kebab-case slug")
        if not isinstance(entry, dict):
            sys.exit(f"data/behaviours.json: {slug}: entry must be an object")
        for field in required_fields:
            if field not in entry:
                sys.exit(f"data/behaviours.json: {slug}: entry is missing required field {field!r}")
        behaviour_set = entry.get("set")
        if behaviour_set not in SETS:
            sys.exit(f"data/behaviours.json: {slug}: unknown set {behaviour_set!r}")
        numeric_id = entry.get("numeric_id")
        if not isinstance(numeric_id, int) or isinstance(numeric_id, bool) or numeric_id < 1:
            sys.exit(f"data/behaviours.json: {slug}: numeric_id must be an integer >= 1")
        key = (behaviour_set, numeric_id)
        if key in seen:
            sys.exit(
                f"data/behaviours.json: {behaviour_set} id {numeric_id} appears twice "
                f"({seen[key]!r} and {slug!r}) -- ids are per-set join keys and must stay unique"
            )
        seen[key] = slug
    return registry


def index_entries(registry: dict) -> list:
    return sorted(
        ((slug, entry) for slug, entry in registry.items() if entry["set"] == "index"),
        key=lambda item: item[1]["numeric_id"],
    )


def coverage_ids(root: Path) -> set:
    coverage = json.loads((root / "data" / "coverage.json").read_text(encoding="utf-8"))
    return {record["behaviour_id"] for record in coverage.get("coverage", [])}


# ---------------------------------------------------------------------------
# Renderers (pure: registry -> constant text)
# ---------------------------------------------------------------------------

def py_string_parts(definition: str) -> list:
    """Greedy word-wrap into quoted parts of at most DEFINITION_WIDTH chars,
    trailing space included (the earlier part keeps the space at a split). The
    last word needs no trailing space, so a definition whose final word lands
    exactly on the width stays on one line. A definition that fits in one part
    still renders parenthesized (the committed constant's style)."""
    words = definition.split(" ")
    parts, current = [], ""
    for position, word in enumerate(words):
        is_last = position == len(words) - 1
        needed = len(current) + len(word) + (0 if is_last else 1)
        if current and needed > DEFINITION_WIDTH:
            parts.append(current)
            current = word + " "
        else:
            current += word + " "
    parts.append(current.rstrip(" "))
    escaped = [part.replace("\\", "\\\\").replace('"', '\\"') for part in parts]
    return [f'"{part}"' for part in escaped]


def render_behaviours_py(registry: dict, covered: set) -> str:
    """The `BEHAVIOURS = [...]` block for engine/build-spec-reader-data.py."""
    entries = index_entries(registry)
    by_id = {entry["numeric_id"]: (slug, entry) for slug, entry in entries}
    missing = sorted(covered - set(by_id))
    if missing:
        sys.exit(f"coverage.json carries behaviour_id(s) {missing} the registry does not define")
    undefined = sorted(numeric_id for numeric_id in covered if not by_id[numeric_id][1]["definition"])
    if undefined:
        sys.exit(
            f"coverage.json carries behaviour_id(s) {undefined} whose registry "
            f"definition is empty -- add the definition before publishing"
        )
    lines = ["BEHAVIOURS = ["]
    for numeric_id in sorted(covered):
        slug, entry = by_id[numeric_id]
        name_part = py_string_parts(entry["name"])
        group_part = py_string_parts(entry["group"])
        if len(name_part) != 1 or len(group_part) != 1:
            sys.exit(f"registry: {slug}: name or group is too long to render on one line")
        lines.append("    {")
        lines.append(f'        "id": {numeric_id},')
        lines.append(f'        "slug": "{slug}",')
        lines.append(f'        "name": {name_part[0]},')
        lines.append('        "definition": (')
        for part in py_string_parts(entry["definition"]):
            lines.append(f"            {part}")
        lines.append("        ),")
        lines.append(f'        "category": {group_part[0]},')
        lines.append("    },")
    lines.append("]")
    return "\n".join(lines)


def render_panel_behaviours(root: Path, registry: dict) -> str:
    """engine/panel/behaviours.json with `title` fields refreshed from the
    registry; keys are registry slugs (every key must be one -- a judge
    prompt for an unregistered behaviour fails here), committed key order is
    preserved, and every other byte of the curated entries is untouched."""
    path = root / "engine" / "panel" / "behaviours.json"
    committed = json.loads(path.read_text(encoding="utf-8"))
    unknown = [slug for slug in committed if slug not in registry]
    if unknown:
        sys.exit(
            f"engine/panel/behaviours.json carries key(s) {unknown} that are "
            "not registry slugs (data/behaviours.json) -- every judge prompt "
            "must belong to a registered behaviour"
        )
    for slug, entry in committed.items():
        if "title" in entry:
            entry["title"] = registry[slug]["name"]
    return json.dumps(committed, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Splicing (constant-block replacement only; surrounding bytes untouched)
# ---------------------------------------------------------------------------

def _splice(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start) + len(end_marker)
    return text[:start] + replacement + text[end:]


def regenerate(root: Path) -> dict:
    """Returns {repo-relative path: new full text} for every derived file."""
    registry = load_registry(root)

    builder = (root / "engine" / "build-spec-reader-data.py").read_text(encoding="utf-8")
    new_builder = _splice(builder, "BEHAVIOURS = [", "\n]\n", render_behaviours_py(registry, coverage_ids(root)) + "\n")

    new_panel = render_panel_behaviours(root, registry)

    return {
        "engine/build-spec-reader-data.py": new_builder,
        "engine/panel/behaviours.json": new_panel,  # written without trailing newline
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="exit 1 with a diff if any derived constant has drifted from the registry")
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="repository root to operate on (default: this repo)")
    args = parser.parse_args(argv)

    outputs = regenerate(args.root)
    drifted = False
    for relative, new_text in outputs.items():
        path = args.root / relative
        old_bytes = path.read_bytes()
        new_bytes = new_text.encode("utf-8")
        if old_bytes == new_bytes:
            if not args.check:
                print(f"unchanged  {relative}")
            continue
        drifted = True
        if args.check:
            old_lines = old_bytes.decode("utf-8").splitlines(keepends=True)
            new_lines = new_bytes.decode("utf-8").splitlines(keepends=True)
            sys.stdout.writelines(difflib.unified_diff(old_lines, new_lines,
                                                       f"committed {relative}", f"registry-derived {relative}"))
        else:
            path.write_bytes(new_bytes)
            print(f"regenerated {relative}")
    if args.check:
        if drifted:
            print("\nFAIL: derived constants drifted from data/behaviours.json -- "
                  "run `python3 engine/generate_behaviour_constants.py` and commit the result",
                  file=sys.stderr)
            return 1
        print("OK: BEHAVIOURS and the panel judge-prompt titles match data/behaviours.json")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
