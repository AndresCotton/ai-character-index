#!/usr/bin/env python3
"""Publish a behaviour's stage-4 spec coverage into data/coverage.json.

Usage:
    publish-coverage.py research/sweeps/NN-<slug> [--check]

Reads the behaviour's stage-4 artifact, re-verifies every stored quote
byte-for-byte against engine/spec-cite/cite.py, and replaces that behaviour's
records in data/coverage.json. With --check, verifies and diffs against the
currently published records without writing.

Two artifact forms; the sidecar wins when both exist:

1. Structured sidecar `4-spec-coverage.json` -- validated against
   data/schema/spec-coverage-sidecar.schema.json (through validate_data.py's
   jsonschema/stdlib backends) plus cross-checks a single-file schema cannot
   express: records agree with the top-level behaviour identity and with the
   NN-<slug> directory name, exactly one record per lab, the declared
   citation_format is the project's convention, each declared
   verified_against_version equals the version pinned by the record's first
   locator, and a reconstructed sidecar names its source and date. Records
   are published verbatim (citation key order included), so a sidecar derived
   from data/coverage.json round-trips byte-for-byte.
2. Markdown `4-spec-coverage.md` -- the original layout contract, parsed by
   regex; the fallback when no sidecar exists (behaviour 2 is the template):
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

Both artifact paths gate their records against data/schema/coverage.schema.json
before quote verification: whichever artifact produced the records, they must
match the real coverage schema before anything is written or checked, and a
failing record aborts the publish. The sidecar schema's coverageRecord $def
mirrors this shape for authoring convenience, but this coverage-schema gate is
the load-bearing check on what enters data/coverage.json, so the mirror cannot
silently drift out of sync and let a bad record through. The cite.py gate is
the same on both paths: every quote goes through `cite.py resolve`
verification before anything is written or checked.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))   # engine/ -> validate_data
import validate_data  # noqa: E402

COVERAGE = ROOT / "data" / "coverage.json"
CITE = ROOT / "engine" / "spec-cite" / "cite.py"
SIDECAR_SCHEMA = ROOT / "data" / "schema" / "spec-coverage-sidecar.schema.json"
COVERAGE_SCHEMA = ROOT / "data" / "schema" / "coverage.schema.json"

SUPPORTED_SIDECAR_VERSION = 1

MARKDOWN_NAME = "4-spec-coverage.md"
SIDECAR_NAME = "4-spec-coverage.json"

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
    parts = text.split(start, 1)
    if len(parts) < 2:
        sys.exit(f"publish-coverage: artifact is missing the section starting "
                 f"{start!r} -- expected the stage-4 layout")
    body = parts[1]
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


def _locator_spec_part(locator: str) -> str:
    """The spec@version prefix of a locator, tolerant of the separator
    variants CITATION.md allows (" > " and ">"; the artifacts use " › ")."""
    return re.split(r"\s*(?:\u203a|>)\s*", locator, maxsplit=1)[0]


def parse_markdown(artifact_path: Path) -> tuple[int, list[dict]]:
    """The regex path: unchanged contract for 4-spec-coverage.md artifacts."""
    artifact = artifact_path.read_text()

    header = re.search(r"\*\*Behaviour:\*\* (\d+), ([^(\n]+?)(?: \(|\n)", artifact)
    sweep_date = re.search(r"\*\*Sweep date:\*\* (\d{4}-\d{2}-\d{2})", artifact)
    if not header or not sweep_date:
        sys.exit("could not parse the behaviour header or sweep date")
    behaviour_id = int(header.group(1))
    behaviour_name = header.group(2).strip()

    verdicts = parse_verdict_table(artifact)
    enders = ["\n## Considered and not kept", "\n## Verdict and depth"]
    records = []
    for lab_id, heading in LABS:
        citations = parse_citations(
            section(artifact, heading, [h for _, h in LABS if h != heading] + enders)
        )
        if not citations:
            sys.exit(f"no citations parsed for {lab_id}")
        try:
            version = _locator_spec_part(citations[0]["locator"]).split("@")[1]
        except IndexError:
            sys.exit(
                f"{artifact_path.name}: {lab_id} first locator does not "
                "start with spec@version"
            )
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
    return behaviour_id, records


def parse_sidecar(sidecar_path: Path, sweep_dir: Path) -> tuple[int, list[dict]]:
    """The structured path: schema-validate 4-spec-coverage.json, then apply
    the cross-checks a single-file schema cannot express. Returns its records
    verbatim (citation key order included) for byte-stable publication."""
    try:
        sidecar = json.loads(sidecar_path.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"{sidecar_path.name}: invalid JSON: {exc}")

    schema = json.loads(SIDECAR_SCHEMA.read_text())
    errors = validate_data.validate_instance(sidecar, schema)
    if errors:
        print(f"{sidecar_path.name}: failed schema validation:")
        for error in errors:
            print(f"  {error}")
        sys.exit(f"{sidecar_path.name}: {len(errors)} schema error(s)")

    # The schema declares the field; only this check rejects a future value.
    sidecar_version = sidecar["sidecar_version"]
    if sidecar_version != SUPPORTED_SIDECAR_VERSION:
        sys.exit(
            f"{sidecar_path.name}: sidecar_version {sidecar_version} is not "
            f"supported (this publisher understands sidecar_version "
            f"{SUPPORTED_SIDECAR_VERSION} only)"
        )

    provenance = sidecar["provenance"]
    if provenance["reconstructed"]:
        missing = [
            key for key in ("reconstructedFrom", "reconstructedDate")
            if key not in provenance
        ]
        if missing:
            sys.exit(
                f"{sidecar_path.name}: a reconstructed sidecar must carry "
                + " and ".join(missing)
            )

    behaviour_id = sidecar["behaviour_id"]
    behaviour_name = sidecar["behaviour_name"]

    directory_number, _, directory_slug = sweep_dir.name.partition("-")
    if not directory_number.isdigit() or int(directory_number) != behaviour_id:
        sys.exit(
            f"{sidecar_path.name}: behaviour_id {behaviour_id} does not match "
            f"its directory {sweep_dir.name!r}"
        )
    if sidecar["slug"] != directory_slug:
        sys.exit(
            f"{sidecar_path.name}: slug {sidecar['slug']!r} does not match "
            f"its directory {sweep_dir.name!r}"
        )

    records = sidecar["records"]
    by_lab = {}
    for index, record in enumerate(records):
        if (
            record["behaviour_id"] != behaviour_id
            or record["behaviour_name"] != behaviour_name
        ):
            sys.exit(
                f"{sidecar_path.name}: records[{index}] disagrees with the "
                "top-level behaviour identity"
            )
        if record["citation_format"] != CITATION_FORMAT:
            sys.exit(
                f"{sidecar_path.name}: records[{index}] citation_format is not "
                "the project's citation convention (see CITATION_FORMAT)"
            )
        try:
            version = _locator_spec_part(record["citations"][0]["locator"]).split("@")[1]
        except IndexError:
            sys.exit(
                f"{sidecar_path.name}: records[{index}] first locator does not "
                "start with spec@version"
            )
        if version != record["verified_against_version"]:
            sys.exit(
                f"{sidecar_path.name}: records[{index}] verified_against_version "
                f"{record['verified_against_version']!r} does not match the "
                f"version pinned by its first locator ({version!r})"
            )
        lab_id = record["lab_id"]
        if lab_id in by_lab:
            sys.exit(f"{sidecar_path.name}: duplicate record for lab {lab_id!r}")
        by_lab[lab_id] = record

    expected_labs = {lab_id for lab_id, _ in LABS}
    if set(by_lab) != expected_labs:
        sys.exit(
            f"{sidecar_path.name}: expected exactly one record per lab "
            f"{sorted(expected_labs)}, got {sorted(by_lab)}"
        )
    return behaviour_id, records


def validate_coverage_records(records: list[dict], source: str) -> None:
    """Schema-gate records about to enter data/coverage.json, whichever
    artifact path produced them. Both the structured sidecar path and the
    regex markdown path run their records through
    data/schema/coverage.schema.json here, before quote verification and
    before anything is written or checked. The sidecar schema's
    coverageRecord $def mirrors this shape for authoring convenience, but
    this validation against the real coverage schema is the load-bearing gate
    on what enters data/coverage.json -- it holds even if the mirror drifts
    out of sync. Fails loudly on any violation."""
    schema = json.loads(COVERAGE_SCHEMA.read_text())
    errors = validate_data.validate_instance({"coverage": records}, schema)
    if errors:
        print(f"{source}: records fail data/schema/coverage.schema.json:")
        for error in errors:
            print(f"  {error}")
        sys.exit(
            f"{source}: {len(errors)} coverage-schema error(s); nothing written"
        )


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

    sidecar_path = arguments.behaviour_dir / SIDECAR_NAME
    markdown_path = arguments.behaviour_dir / MARKDOWN_NAME
    if sidecar_path.exists():
        behaviour_id, records = parse_sidecar(sidecar_path, arguments.behaviour_dir)
        print(f"using structured sidecar {sidecar_path.name}")
        artifact_name = sidecar_path.name
    elif markdown_path.exists():
        behaviour_id, records = parse_markdown(markdown_path)
        artifact_name = markdown_path.name
    else:
        sys.exit(
            f"no stage-4 artifact in {arguments.behaviour_dir}: expected "
            f"{SIDECAR_NAME} or {MARKDOWN_NAME}"
        )

    # Both paths gate their records against the real coverage schema before
    # quote verification, so nothing enters data/coverage.json without
    # matching data/schema/coverage.schema.json whichever artifact produced it.
    validate_coverage_records(records, artifact_name)

    all_citations = [
        citation for record in records for citation in record["citations"]
    ]
    behaviour_name = records[0]["behaviour_name"]

    verify_citations(all_citations)

    data = json.loads(COVERAGE.read_text())
    existing = [r for r in data["coverage"] if r["behaviour_id"] == behaviour_id]

    def record_key(record):
        return (record.get("behaviour_id"), record.get("lab_id"))

    if arguments.check:
        if sorted(existing, key=record_key) == sorted(records, key=record_key):
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
    try:
        coverage_label = COVERAGE.relative_to(ROOT)
    except ValueError:  # COVERAGE rebound outside the repo (tests)
        coverage_label = COVERAGE
    print(f"Wrote {coverage_label}: behaviour {behaviour_id} "
          f"({behaviour_name}), {len(all_citations)} citations")


if __name__ == "__main__":
    main()
