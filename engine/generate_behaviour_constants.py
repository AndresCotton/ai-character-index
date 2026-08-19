#!/usr/bin/env python3
"""Regenerate the derived behaviour constants from data/behaviours.json.

data/behaviours.json is the behaviour-identity registry (Decision 1, 2026-08-18):
one entry per behaviour across all sets, keyed by slug. This script rewrites the
four derived constants that must stay in lockstep with it:

  1. GROUPS               site/spec-reader/app.js
                          All index-set entries, listed under their group in
                          numeric_id order. Group order = order of first
                          appearance by numeric_id.
  2. BEHAVIOURS           engine/build-spec-reader-data.py
                          The index-set entries whose numeric_id has a record in
                          data/coverage.json (today ids 1-3) -- exactly the set
                          the builder can render. A coverage record with no
                          registry definition is an error; a definition with no
                          coverage record is stored but not published.
  3. key order + titles   engine/panel/behaviours.json
                          Panel-harness keys stay curated here (judge prompts),
                          but their order follows PANEL_BEHAVIOURS below and any
                          entry's `title` field is rewritten from the mapped
                          registry name. The panel<->registry mapping is owned
                          here (it is panel-pipeline metadata, deliberately not
                          in the registry schema); it mirrors the SLUGS dict in
                          engine/panel/build_site_data.py.
  4. display.behaviours   engine/panel/panel-config.json
                          Renders PANEL_DISPLAY_SLUGS below -- the reader-test
                          slugs shown in site/llm-panel-review. Membership lives
                          here because the registry schema deliberately carries
                          no panel-display flag; every slug is validated against
                          the registry, so a renamed slug fails loudly instead
                          of going silently stale.

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

# Panel-harness keys in the committed engine/panel/behaviours.json order, mapped
# to their registry slug. None = panel-only key with no registry entry (the two
# rubric-calibration behaviours live in the harness, not in any behaviour set).
PANEL_BEHAVIOURS = (
    ("no-sycophancy", "no-sycophancy"),
    ("undermine-oversight", None),
    ("helpfulness", "helpfulness"),
    ("harmlessness-to-user", "harmlessness-to-the-user"),
    ("third-party-harm", "harm-avoidance-to-third-parties"),
    ("proportionate-risk", "proportionate-risk-mitigation"),
    ("tradeoffs", "how-to-approach-tradeoffs"),
    ("over-under-caution", "avoiding-over-and-under-caution"),
    ("objectivity", "objectivity-on-contested-questions"),
    ("user-autonomy", "user-autonomy"),
    ("general-welfare", "animal-welfare-impacts"),
)

# Reader-test slugs shown in site/llm-panel-review (rendered into
# panel-config.json display.behaviours). The two general-guidelines slugs join
# when the full rollout data lands (panel-config.json _activation_note).
PANEL_DISPLAY_SLUGS = (
    "helpfulness",
    "harm-avoidance-to-third-parties",
    "avoiding-over-and-under-caution",
)

# Definitions render as implicit string concatenations, greedy-wrapped so each
# quoted part is at most this many characters including its trailing space.
# Chosen so the committed constant reproduces as nearly as possible: behaviour
# 2's definition is exactly 67 chars and stays on one line, behaviour 3's wrap
# reproduces exactly, and behaviour 1's second word moves up one line.
DEFINITION_WIDTH = 67


def load_registry(root: Path) -> dict:
    registry = json.loads((root / "data" / "behaviours.json").read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        sys.exit("data/behaviours.json: top level must be an object keyed by slug")
    seen = {}
    for slug, entry in registry.items():
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            sys.exit(f"data/behaviours.json: {slug!r} is not a kebab-case slug")
        for field in ("name", "set", "numeric_id"):
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

def js_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + '"'


def render_groups_js(registry: dict) -> str:
    """The `const GROUPS = [...];` block for site/spec-reader/app.js."""
    entries = index_entries(registry)
    groups = []  # (name, [(numeric_id, name), ...]) in first-appearance order
    for slug, entry in entries:
        group = entry["group"]
        if not group:
            sys.exit(
                f"registry: index behaviour {slug} has no group -- every index "
                f"behaviour must appear under a GROUPS category"
            )
        if not groups or groups[-1][0] != group:
            groups.append((group, []))
        groups[-1][1].append((entry["numeric_id"], entry["name"]))
    # first-appearance order by numeric_id means groups are already ordered; a
    # group that reappeared later would split the sidebar, so forbid it
    names = [name for name, _ in groups]
    if len(names) != len(set(names)):
        sys.exit("registry: index groups are not contiguous in numeric_id order")
    lines = ["const GROUPS = ["]
    for name, behaviours in groups:
        lines.append("  {")
        lines.append(f"    name: {js_string(name)},")
        lines.append("    behaviours: [")
        for numeric_id, behaviour_name in behaviours:
            lines.append(f"      [{numeric_id}, {js_string(behaviour_name)}],")
        lines.append("    ],")
        lines.append("  },")
    lines.append("];")
    return "\n".join(lines)


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


def render_display_array() -> str:
    """The display.behaviours array literal for engine/panel/panel-config.json."""
    lines = ["["]
    for index, slug in enumerate(PANEL_DISPLAY_SLUGS):
        comma = "," if index < len(PANEL_DISPLAY_SLUGS) - 1 else ""
        lines.append(f'      "{slug}"{comma}')
    lines.append("    ]")
    return "\n".join(lines)


def render_panel_behaviours(root: Path, registry: dict) -> str:
    """engine/panel/behaviours.json with key order pinned and titles refreshed
    from the registry; every other byte of the curated entries is preserved."""
    path = root / "engine" / "panel" / "behaviours.json"
    committed = json.loads(path.read_text(encoding="utf-8"))
    expected_keys = [panel_key for panel_key, _ in PANEL_BEHAVIOURS]
    if list(committed) != expected_keys:
        sys.exit(
            "engine/panel/behaviours.json keys diverge from PANEL_BEHAVIOURS in "
            f"generate_behaviour_constants.py:\n  file:     {list(committed)}\n"
            f"  expected: {expected_keys}\nReconcile the mapping deliberately, then re-run."
        )
    for panel_key, slug in PANEL_BEHAVIOURS:
        if slug is None:
            continue
        if slug not in registry:
            sys.exit(f"PANEL_BEHAVIOURS maps {panel_key!r} to unknown registry slug {slug!r}")
        entry = committed[panel_key]
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

    for slug in PANEL_DISPLAY_SLUGS:
        entry = registry.get(slug)
        if entry is None or entry["set"] != "reader-test":
            sys.exit(f"PANEL_DISPLAY_SLUGS lists {slug!r}, which the registry does not carry as a reader-test behaviour")

    app_js = (root / "site" / "spec-reader" / "app.js").read_text(encoding="utf-8")
    new_app_js = _splice(app_js, "const GROUPS = [", "\n];\n", render_groups_js(registry) + "\n")

    builder = (root / "engine" / "build-spec-reader-data.py").read_text(encoding="utf-8")
    new_builder = _splice(builder, "BEHAVIOURS = [", "\n]\n", render_behaviours_py(registry, coverage_ids(root)) + "\n")

    config = (root / "engine" / "panel" / "panel-config.json").read_text(encoding="utf-8")
    display_start = config.index('"display": {')
    array_start = config.index('"behaviours": [', display_start)
    open_bracket = config.index("[", array_start)
    close_bracket = config.index("]", open_bracket)
    new_config = config[:open_bracket] + render_display_array() + config[close_bracket + 1:]
    json.loads(new_config)  # the splice must leave valid JSON behind

    new_panel = render_panel_behaviours(root, registry)

    return {
        "site/spec-reader/app.js": new_app_js,
        "engine/build-spec-reader-data.py": new_builder,
        "engine/panel/panel-config.json": new_config,
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
        print("OK: GROUPS, BEHAVIOURS, and the panel slug lists match data/behaviours.json")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
