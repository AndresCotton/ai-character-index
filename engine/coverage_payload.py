#!/usr/bin/env python3
"""Shared coverage-payload builder for the spec readers.

coverage_payload() converts one coverage record (the shape stored in
data/coverage.json) into the per-behaviour coverage object the readers
render. Imported by build-spec-reader-data.py, which passes the document id
(the lab namespace: "anthropic", "openai") as scope_id; the panel builder
shapes its own passages directly.
"""

from __future__ import annotations


def coverage_payload(record: dict, scope_id: str, slug: str) -> dict:
    """Build the reader-facing coverage dict for one (behaviour, spec) record.

    scope_id prefixes every passage id: the document id on the published
    reader, the lab id on the reader-test set.
    """
    return {
        "verdict": record["verdict"],
        "depth": record["depth_0_4"],
        "note": record["depth_note"],
        "verifiedDate": record["verified_date"],
        "passages": [
            {
                "id": f"{scope_id}-{slug}-{index + 1}",
                "locator": citation["locator"],
                "quote": citation["quote"],
                "role": citation["role"],
                "adjacent": citation.get("adjacent", False),
                "exampleBlock": citation.get("example_block", False),
            }
            for index, citation in enumerate(record["citations"])
        ],
    }
