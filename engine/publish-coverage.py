#!/usr/bin/env python3
"""Publish a behaviour's stage-4 spec coverage into data/coverage.json.

Usage:
    publish-coverage.py research/sweeps/NN-<slug> [--check]

Parses the behaviour's stage-4 artifact (4-spec-coverage.md), re-verifies every
stored quote byte-for-byte against engine/spec-cite/cite.py, and replaces that
behaviour's records in data/coverage.json. With --check, verifies and diffs
against the currently published records without writing.

The artifact is a parsing contract (behaviour 2 is the template):
  - header bullet:  - **Behaviour:** <id>, <name> (...)
  - header bullet:  - **Sweep date:** YYYY-MM-DD
  - per-spec sections "## Claude constitution ..." and "## OpenAI Model Spec ...",
    each listing excerpts as:
        - **Locator:** `<locator>`
          **Quote:** <one line, resolver output>
          **Role:** <one line>
          **Flags:** -- | adjacent ... | example_block ...
  - a "## Verdict and depth" table with one row per spec:
        | Claude constitution (...) | <verdict> | <0-4> | <rationale> |
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data" / "coverage.json"
CITE = ROOT / "engine" / "spec-cite" / "cite.py"

CITATION_FORMAT = (
    "specs/CITATION.md; quotes are exact output of engine/spec-cite/cite.py resolve; "
    "example blocks store the caption line, cite the whole block"
)

LABS = [
    ("anthropic", "## Claude constitution"),
    ("openai", "## OpenAI Model Spec"),
]

ENTRY_RE = re.compile(
    r"- \*\*Locator:\*\* `(?P<locator>[^`]+)`\n"
    r"  \*\*Quote:\*\* (?P<quote>.+)\n"
    r"  \*\*Role:\*\* (?P<role>.+)\n"
    r"  \*\*Flags:\*\* (?P<flags>.+)"
)


def section(text: str, start: str, enders: list[str]) -> str:
    body = text.split(start, 1)[1]
    cut = len(body)
    for ender in enders:
        position = body.find(ender)
        if 0 <= position < cut:
            cut = position
    return body[:cut]


def parse_citations(part: str) -> list[dict]:
    citations = []
    for match in ENTRY_RE.finditer(part):
        flags = match.group("flags")
        citation = {
            "locator": match.group("locator").replace(" > ", " › "),
            "quote": match.group("quote").strip(),
            "role": match.group("role").strip().rstrip("."),
        }
        if "adjacent" in flags:
            citation["adjacent"] = True
        if "example_block" in flags:
            citation["example_block"] = True
        citations.append(citation)
    return citations


def parse_verdict_table(text: str) -> dict[str, dict]:
    table = section(text, "## Verdict and depth", ["\n## "])
    rows = {}
    for line in table.splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 4 or cells[0].startswith(("Spec", "---")):
            continue
        lab = "anthropic" if cells[0].startswith("Claude constitution") else (
            "openai" if cells[0].startswith("OpenAI Model Spec") else None
        )
        if not lab:
            continue
        rationale = cells[3].replace("`", "")
        rationale = re.sub(r"\bNote: (\w)", lambda m: m.group(1).upper(), rationale)
        rows[lab] = {
            "verdict": cells[1],
            "depth_0_4": int(cells[2]),
            "depth_note": rationale,
        }
    if set(rows) != {"anthropic", "openai"}:
        sys.exit("could not parse both rows of the verdict table")
    return rows


def verify_citations(citations: list[dict]) -> None:
    failures = 0
    for citation in citations:
        locator = citation["locator"].replace(" › ", " > ")
        resolved = subprocess.run(
            [sys.executable, str(CITE), "resolve", locator],
            capture_output=True, text=True,
        ).stdout.rstrip("\n")
        expected = (
            resolved.splitlines()[0] if citation.get("example_block") else resolved
        )
        if expected != citation["quote"]:
            failures += 1
            print(f"MISMATCH  {citation['locator']}")
            print(f"  stored:   {citation['quote'][:90]}")
            print(f"  resolved: {expected[:90]}")
    if failures:
        sys.exit(f"{failures} quote mismatches against cite.py; aborting")
    print(f"{len(citations)} locators re-verified against cite.py, 0 mismatches")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("behaviour_dir", type=Path)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()

    artifact = (arguments.behaviour_dir / "4-spec-coverage.md").read_text()

    header = re.search(r"\*\*Behaviour:\*\* (\d+), ([^(\n]+?)(?: \(|\n)", artifact)
    sweep_date = re.search(r"\*\*Sweep date:\*\* (\d{4}-\d{2}-\d{2})", artifact)
    if not header or not sweep_date:
        sys.exit("could not parse the behaviour header or sweep date")
    behaviour_id = int(header.group(1))
    behaviour_name = header.group(2).strip()

    verdicts = parse_verdict_table(artifact)
    enders = ["\n## Considered and not kept", "\n## Verdict and depth"]
    records = []
    all_citations = []
    for lab_id, heading in LABS:
        citations = parse_citations(
            section(artifact, heading, [h for _, h in LABS if h != heading] + enders)
        )
        if not citations:
            sys.exit(f"no citations parsed for {lab_id}")
        all_citations.extend(citations)
        version = citations[0]["locator"].split(" › ")[0].split("@")[1]
        records.append(
            {
                "behaviour_id": behaviour_id,
                "behaviour_name": behaviour_name,
                "lab_id": lab_id,
                **verdicts[lab_id],
                "citations": citations,
                "verified_against_version": version,
                "verified_date": sweep_date.group(1),
                "citation_format": CITATION_FORMAT,
            }
        )

    verify_citations(all_citations)

    data = json.loads(COVERAGE.read_text())
    existing = [r for r in data["coverage"] if r["behaviour_id"] == behaviour_id]

    if arguments.check:
        if existing == records:
            print(f"CHECK OK: behaviour {behaviour_id} published records match the artifact")
        elif not existing:
            print(f"CHECK: behaviour {behaviour_id} not yet published; would add "
                  f"{len(records)} records ({len(all_citations)} citations)")
        else:
            sys.exit(f"CHECK FAILED: behaviour {behaviour_id} published records "
                     "differ from the artifact")
        return

    data["coverage"] = [
        r for r in data["coverage"] if r["behaviour_id"] != behaviour_id
    ] + records
    data["coverage"].sort(key=lambda r: (r["behaviour_id"], r["lab_id"]))
    COVERAGE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {COVERAGE.relative_to(ROOT)}: behaviour {behaviour_id} "
          f"({behaviour_name}), {len(all_citations)} citations")


if __name__ == "__main__":
    main()
