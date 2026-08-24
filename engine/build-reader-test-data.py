#!/usr/bin/env python3
"""Build the behaviour set for the reader test bench (site/spec-reader-test/).

The bench shares its spec text with the published reader and carries only its own
behaviours, so this writes just the behaviour payload -- not a second copy of the specs.

Source: data/reader-test-coverage.json, which holds the behaviour definitions under test
plus one coverage record per behaviour x lab, in the same record shape as data/coverage.json
(so a record can be lifted from a sweep unchanged). Absent that file, the bench is empty and
both specs render in full with nothing highlighted.
"""

from __future__ import annotations

import json
from pathlib import Path

from coverage_payload import coverage_payload


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "reader-test-coverage.json"
OUTPUT = ROOT / "site" / "spec-reader-test" / "data" / "behaviours.json"

LAB_IDS = ["anthropic", "openai"]

EMPTY_NOTE = (
    "Behaviour set under test on the reader-test bench. Empty until the reviewer's "
    "behaviours are published. Spec text comes from ../../spec-reader/data/documents.json."
)


def main() -> None:
    if not SOURCE.exists():
        payload = {"generatedFrom": [], "note": EMPTY_NOTE, "behaviours": []}
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        print(f"Wrote {OUTPUT.relative_to(ROOT)} (no behaviours under test)")
        return

    source = json.loads(SOURCE.read_text())
    records = source["coverage"]

    unknown_lab_ids = sorted(
        {record["lab_id"] for record in records} - set(LAB_IDS)
    )
    if unknown_lab_ids:
        # A record whose lab is not in this builder's list fails loudly,
        # naming the lab_id(s) -- silently dropping it would be data loss
        # for whoever forks the reader.
        raise SystemExit(
            f"coverage record(s) with lab_id(s) {unknown_lab_ids} not in this "
            f"builder's lab list {LAB_IDS}"
        )

    behaviours = []
    for behaviour in source["behaviours"]:
        per_lab = {}
        for lab_id in LAB_IDS:
            matches = [
                record
                for record in records
                if record["behaviour_id"] == behaviour["id"] and record["lab_id"] == lab_id
            ]
            if len(matches) != 1:
                # A spec with no coverage is a record whose citations are empty, never a
                # missing record: the reader reports absence as a finding, and can only do
                # that if the verdict was actually made.
                raise SystemExit(
                    f"behaviour {behaviour['id']} ({behaviour['slug']}): expected exactly one "
                    f"{lab_id} coverage record, found {len(matches)}"
                )
            per_lab[lab_id] = coverage_payload(matches[0], lab_id, behaviour["slug"])
        behaviours.append(
            {
                "id": behaviour["id"],
                "slug": behaviour["slug"],
                "name": behaviour["name"],
                "definition": behaviour["definition"],
                "category": behaviour["category"],
                "coverage": per_lab,
            }
        )

    payload = {
        "generatedFrom": [str(SOURCE.relative_to(ROOT))],
        "behaviours": behaviours,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(behaviours)} behaviours under test)")


if __name__ == "__main__":
    main()
