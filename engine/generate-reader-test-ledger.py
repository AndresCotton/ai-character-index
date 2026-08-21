#!/usr/bin/env python3
"""Regenerate data/reader-test-coverage.json from the sweep artifacts it was
transcribed from, or check the committed ledger against them.

The reader-test bench ledger (10 behaviours x 2 labs, 294 citations) was
hand-transcribed from the stage-4 spec-coverage sweeps in
behaviours-for-adria/. This script closes that loop: it parses each
artifact's per-lab excerpt blocks (locator / quote / role, Core and Adjacent
sections) and its "Verdict and depth" table, and either rewrites the ledger's
coverage rows from them (default) or exits 1 naming every divergence
(--check). A clean --check means the published ledger still agrees with the
sweep artifacts field for field -- locator, quote, role, core/adjacent flag,
verdict, depth, and the depth rationale.

Editorial fields the reconstruction cannot derive stay untouched:
`verified_date` (a transcription date) and each citation's `example_block`
flag (a reading of the quote, not marked in the artifacts). Both carry
through unchanged; --check does not validate them.

Two normalizations keep the check on substance, not typography:
  - locator separators: artifacts write " > " between segments; the ledger
    renders " > " or " \u203a " (its own rows 9/10 disagree with each other).
  - markdown backticks: reviewer prose in the artifacts wraps spec tags like
    `#assume_objective_pov` in backticks; the ledger transcribed them bare.
    Roles and rationales compare with backticks stripped on both sides
    (quotes compare exactly -- they are verbatim spec text).

DISCLOSED pins the one known judgment divergence between the ledger and its
source artifact (named, with its reason). The check fails on any NEW
divergence, and also fails if a disclosed one disappears without being
removed from DISCLOSED -- disclosures are not a place to park fixes.

A row-level disclosure (locator None) only shelters divergences that are
themselves punctuation-only (equal once trailing punctuation/whitespace is
stripped) -- it cannot be used to wave through a substantive rewrite of a
field it claims is "lightly edited". Anything else at that field, at any
locator, fails loudly and by name, disclosed or not.

--check also verifies the ledger has exactly one coverage row per
(behaviour, lab) pair implied by ledger["behaviours"] x the labs the
artifacts define -- a silently dropped row is a failure, and the failure
names every missing pair.

Usage:
    python3 engine/generate-reader-test-ledger.py            # rewrite in place
    python3 engine/generate-reader-test-ledger.py --check    # exit 1 on drift
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "reader-test-coverage.json"
BATCH = ROOT / "behaviours-for-adria"

# The artifact sections that carry each lab's excerpts, keyed by lab id.
SPEC_SECTIONS = {"Claude constitution": "anthropic", "OpenAI Model Spec": "openai"}
VERDICT_ROW = re.compile(
    r"^\|\s*(.+?)\s*\((\d{4}-\d{2}-\d{2})\)\s*\|\s*(\S+)\s*\|\s*(\d)\s*\|\s*(.+)\s*\|$")

# Disclosed divergences between the ledger and its artifacts, pinned here.
# Two forms: (slug, lab, normalized locator, field) discloses one cell;
# (slug, lab, None, field) discloses that field for the whole row. See the
# module docstring.
DISCLOSED = {
    ("harmlessness-to-the-user", "openai",
     "model-spec@2025-12-18 > #do_not_lie > ¶5", "adjacent"):
        "the artifact files the passage under Core; the ledger and the "
        "rendered bench carry it as Related -- a transcription judgment "
        "under review (log item 9, 2026-08-21)",
    ("animal-welfare-impacts", "anthropic", None, "role"):
        "roles lightly edited during transcription (punctuation cleanup); "
        "locators and quotes compare exact",
    ("animal-welfare-impacts", "openai", None, "role"):
        "roles lightly edited during transcription (punctuation cleanup); "
        "locators and quotes compare exact",
}


def is_disclosed(slug: str, lab: str, locator, field: str, a=None, b=None) -> bool:
    """Is this (row or cell) divergence covered by DISCLOSED?

    A cell-level entry ((slug, lab, locator, field)) covers whatever it
    names, no further questions asked -- it is pinned to one exact locator.
    A row-level entry ((slug, lab, None, field)) covers a field across the
    whole row, but only where the actual divergence is punctuation-only;
    `a`/`b` are the two compared values, and a genuinely different `a`/`b`
    is refused even though the row is nominally disclosed.
    """
    if (slug, lab, locator, field) in DISCLOSED:
        return True
    if (slug, lab, None, field) in DISCLOSED:
        return a is not None and b is not None and punct_stripped(a) == punct_stripped(b)
    return False


def norm_locator(locator: str) -> str:
    return locator.replace(" \u203a ", " > ")


def norm_prose(text: str) -> str:
    return (text or "").replace("`", "").strip()


def punct_stripped(text: str) -> str:
    """Trailing punctuation/whitespace stripped, for judging "punctuation
    cleanup" divergences. Apply to already norm_prose'd text."""
    return re.sub(r"[.,;:!?'\"]+$", "", text or "").rstrip()


def parse_artifact(path: Path) -> dict:
    """Per-lab excerpts (in document order) + the verdict table."""
    text = path.read_text(encoding="utf-8")
    out = {
        lab: {"citations": [], "verdict": None, "depth": None, "rationale": None}
        for lab in SPEC_SECTIONS.values()
    }
    lab = None
    adjacent = False
    in_verdict_table = False
    for line in text.splitlines():
        m = re.match(r"^## (.+?) \(", line)
        if m:
            lab = SPEC_SECTIONS.get(m.group(1))
            adjacent = False
            in_verdict_table = False
            continue
        if line.startswith("## Verdict and depth"):
            in_verdict_table = True
            continue
        if line.startswith("### "):
            adjacent = line.startswith("### Adjacent")
            continue
        if in_verdict_table:
            vm = VERDICT_ROW.match(line)
            if vm:
                row_lab = SPEC_SECTIONS.get(vm.group(1))
                if row_lab:
                    out[row_lab]["verdict"] = vm.group(3)
                    out[row_lab]["depth"] = int(vm.group(4))
                    out[row_lab]["rationale"] = vm.group(5)
            continue
        if lab is None:
            continue
        if line.startswith("- **Locator:** `"):
            out[lab]["citations"].append({
                "locator": line.split("`")[1],
                "quote": None,
                "role": None,
                "adjacent": adjacent,
            })
        elif line.startswith("  **Quote:** ") and out[lab]["citations"]:
            out[lab]["citations"][-1]["quote"] = line[len("  **Quote:** "):]
        elif line.startswith("  **Role:** ") and out[lab]["citations"]:
            out[lab]["citations"][-1]["role"] = line[len("  **Role:** "):]
    return out


DIR_NUMBER_PREFIX = re.compile(r"^\d+-")


def artifact_for(slug: str) -> Path:
    """The sweep artifact a ledger behaviour was transcribed from.

    Matches a directory whose name, with its leading "NN-" sweep-order
    prefix stripped, equals the slug exactly -- not a substring match, so a
    future slug that happens to be a substring of another can't silently
    bind to the wrong artifact.
    """
    matches = []
    for base in (BATCH, BATCH / "general-guidelines"):
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if entry.is_dir() and DIR_NUMBER_PREFIX.sub("", entry.name) == slug:
                matches.append(entry / "4-spec-coverage.md")
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"no sweep artifact under behaviours-for-adria/ for behaviour {slug!r}")
    sys.exit(f"ambiguous sweep artifact for behaviour {slug!r}: "
              f"{len(matches)} directories match: {[str(m.parent) for m in matches]}")


def missing_coverage(ledger: dict) -> list[tuple[str, str]]:
    """(behaviour slug, lab) pairs ledger["coverage"] is missing a row for,
    against the full cross of ledger["behaviours"] x the labs the sweep
    artifacts define. Sorted for stable, name-everything failure output."""
    labs = sorted(set(SPEC_SECTIONS.values()))
    expected = {(b["slug"], lab) for b in ledger["behaviours"] for lab in labs}
    behaviours = {b["id"]: b for b in ledger["behaviours"]}
    present = {(behaviours[row["behaviour_id"]]["slug"], row["lab_id"])
               for row in ledger["coverage"]}
    return sorted(expected - present)


def diff_ledger(ledger: dict) -> tuple[list, list]:
    """(undisclosed problems, disclosed divergences still present)."""
    problems, disclosed_present = [], []
    behaviours = {b["id"]: b for b in ledger["behaviours"]}

    for slug, lab in missing_coverage(ledger):
        problems.append(
            f"{slug}/{lab}: no coverage row in ledger for this behaviour/lab "
            f"pair (dropped, or never written)")

    def note(slug, lab, locator, field, message, a=None, b=None):
        loc = norm_locator(locator) if locator else None
        if is_disclosed(slug, lab, loc, field, a, b):
            disclosed_present.append((slug, lab, loc, field))
        else:
            problems.append(f"{slug}/{lab}: {message}")

    for row in ledger["coverage"]:
        slug = behaviours[row["behaviour_id"]]["slug"]
        lab = row["lab_id"]
        parsed = parse_artifact(artifact_for(slug))[lab]

        if parsed["verdict"] is None:
            problems.append(f"{slug}/{lab}: artifact has no Verdict and depth table")
            continue
        if parsed["verdict"] != row["verdict"]:
            note(slug, lab, None, "verdict",
                 f"verdict {row['verdict']!r} in ledger, {parsed['verdict']!r} in artifact")
        if parsed["depth"] != row["depth_0_4"]:
            note(slug, lab, None, "depth",
                 f"depth {row['depth_0_4']} in ledger, {parsed['depth']} in artifact")
        if norm_prose(parsed["rationale"]) != norm_prose(row["depth_note"]):
            note(slug, lab, None, "depth_note",
                 "depth_note diverges from the artifact rationale")

        art_locs = [norm_locator(c["locator"]) for c in parsed["citations"]]
        ledger_locs = [norm_locator(c["locator"]) for c in row["citations"]]
        if art_locs != ledger_locs:
            missing = [l for l in ledger_locs if l not in art_locs]
            extra = [l for l in art_locs if l not in ledger_locs]
            problems.append(
                f"{slug}/{lab}: citation set diverges -- ledger has "
                f"{len(ledger_locs)}, artifact {len(art_locs)}"
                + (f"; missing from artifact: {missing[:2]}" if missing else "")
                + (f"; extra in artifact: {extra[:2]}" if extra else ""))
            continue

        art_by_loc = {norm_locator(c["locator"]): c for c in parsed["citations"]}
        for cit in row["citations"]:
            loc = norm_locator(cit["locator"])
            block = art_by_loc[loc]
            if (block["quote"] or "").strip() != (cit["quote"] or "").strip():
                note(slug, lab, loc, "quote", f"quote diverges at {cit['locator']!r}")
            role_art, role_ledger = norm_prose(block["role"]), norm_prose(cit["role"])
            if role_art != role_ledger:
                note(slug, lab, loc, "role", f"role diverges at {cit['locator']!r}",
                     role_art, role_ledger)
            if bool(block["adjacent"]) != bool(cit.get("adjacent", False)):
                note(slug, lab, loc, "adjacent",
                     f"core/adjacent flag diverges at {cit['locator']!r} "
                     f"(artifact: {'Adjacent' if block['adjacent'] else 'Core'}, "
                     f"ledger: {'Related' if cit.get('adjacent') else 'Core'})")

    for key in DISCLOSED:
        slug, lab, loc, field = key
        if loc is None:
            present = any(s == slug and l == lab for s, l, _, _ in disclosed_present)
        else:
            present = key in disclosed_present
        if not present:
            problems.append(
                f"disclosed divergence no longer present -- remove it from "
                f"DISCLOSED in generate-reader-test-ledger.py: {key}")
    return problems, disclosed_present


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    problems, disclosed = diff_ledger(ledger)

    if check:
        if problems:
            print(f"reader-test-coverage.json diverges from its sweep artifacts "
                  f"({len(problems)} problem(s)):")
            for p in problems:
                print(f"  - {p}")
            print("Regenerate: python3 engine/generate-reader-test-ledger.py")
            return 1
        n_cits = sum(len(r["citations"]) for r in ledger["coverage"])
        print(f"CHECK OK: reader-test-coverage.json matches its "
              f"{len(ledger['coverage'])} sweep-artifact rows (verdicts, depths, "
              f"rationales, {n_cits} citations)"
              + (f"; {len(disclosed)} disclosed divergence(s) pinned" if disclosed else ""))
        return 0

    # Write mode: rebuild the coverage rows from the artifacts. --check is
    # the gate; this is the recovery path after an artifact changes. Values
    # come from the artifact, but where ledger and artifact agree up to
    # formatting (backticks in reviewer prose) the ledger's form is kept so a
    # no-op regeneration is byte-identical. Disclosed cells keep their ledger
    # values; editorial fields (example_block, verified_date) carry through.
    behaviours = {b["id"]: b for b in ledger["behaviours"]}
    for row in ledger["coverage"]:
        slug = behaviours[row["behaviour_id"]]["slug"]
        lab = row["lab_id"]
        parsed = parse_artifact(artifact_for(slug))[lab]
        row["verdict"] = parsed["verdict"]
        row["depth_0_4"] = parsed["depth"]
        if norm_prose(parsed["rationale"]) != norm_prose(row["depth_note"]):
            row["depth_note"] = parsed["rationale"]
        if len(parsed["citations"]) != len(row["citations"]):
            sys.exit(f"{slug}/{lab}: citation count diverges; reconcile first")
        for cit, block in zip(row["citations"], parsed["citations"]):
            if norm_locator(cit["locator"]) != norm_locator(block["locator"]):
                sys.exit(
                    f"{slug}/{lab}: citation order diverges at {cit['locator']!r}; "
                    "reconcile before regenerating")
            loc = norm_locator(cit["locator"])
            cit["quote"] = block["quote"]
            role_art, role_ledger = norm_prose(block["role"]), norm_prose(cit["role"])
            if role_art != role_ledger \
                    and not is_disclosed(slug, lab, loc, "role", role_art, role_ledger):
                cit["role"] = block["role"]
            if not is_disclosed(slug, lab, loc, "adjacent"):
                cit["adjacent"] = block["adjacent"]
    LEDGER.write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"reader-test-coverage.json regenerated from behaviours-for-adria/ "
          f"({len(ledger['coverage'])} rows; {len(disclosed)} disclosed divergence(s) preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
