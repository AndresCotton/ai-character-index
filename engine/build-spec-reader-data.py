#!/usr/bin/env python3
"""Build the static payload used by the public spec reader."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "spec-reader" / "data" / "documents.json"

DOCUMENTS = [
    {
        "id": "anthropic",
        "lab": "Anthropic",
        "title": "Claude’s Constitution",
        "shortTitle": "Claude Constitution",
        "version": "2026-01-20",
        "sourceUrl": "https://www.anthropic.com/news/claude-new-constitution",
        "path": ROOT / "specs" / "claude-constitution" / "20260120-constitution.md",
    },
    {
        "id": "openai",
        "lab": "OpenAI",
        "title": "Model Spec",
        "shortTitle": "OpenAI Model Spec",
        "version": "2025-12-18",
        "sourceUrl": "https://model-spec.openai.com/2025-12-18.html",
        "path": ROOT / "specs" / "openai-model-spec" / "model_spec.md",
    },
]

BEHAVIOURS = [
    {
        "id": 1,
        "slug": "no-sycophancy",
        "name": "No sycophancy",
        "definition": (
            "The model should not shift its factual claims or assessments "
            "to please the user."
        ),
        "category": "Honesty & epistemics",
    },
    {
        "id": 2,
        "slug": "calibration",
        "name": "Calibration",
        "definition": (
            "The model’s verbalized confidence should track its actual accuracy."
        ),
        "category": "Honesty & epistemics",
    },
    {
        "id": 3,
        "slug": "action-honesty",
        "name": "Honesty about one's own actions",
        "definition": (
            "The model should report its own actions and outcomes truthfully, "
            "and should not corrupt the record or the oversight mechanisms "
            "those reports are checked against. The interaction record is the "
            "ground truth."
        ),
        "category": "Honesty & epistemics",
    },
]


def coverage_payload(record: dict, document_id: str, slug: str) -> dict:
    return {
        "verdict": record["verdict"],
        "depth": record["depth_0_4"],
        "note": record["depth_note"],
        "verifiedDate": record["verified_date"],
        "passages": [
            {
                "id": f"{document_id}-{slug}-{index + 1}",
                "locator": citation["locator"],
                "quote": citation["quote"],
                "role": citation["role"],
                "adjacent": citation.get("adjacent", False),
                "exampleBlock": citation.get("example_block", False),
            }
            for index, citation in enumerate(record["citations"])
        ],
    }


def main() -> None:
    coverage = json.loads((ROOT / "data" / "coverage.json").read_text())
    records = coverage["coverage"]

    documents = [
        {key: value for key, value in document.items() if key != "path"}
        | {"markdown": document["path"].read_text()}
        for document in DOCUMENTS
    ]

    behaviours = []
    for behaviour in BEHAVIOURS:
        per_document = {}
        for document in DOCUMENTS:
            record = next(
                item
                for item in records
                if item["behaviour_id"] == behaviour["id"]
                and item["lab_id"] == document["id"]
            )
            per_document[document["id"]] = coverage_payload(
                record, document["id"], behaviour["slug"]
            )
        behaviours.append(behaviour | {"coverage": per_document})

    payload = {
        "generatedFrom": [
            "specs/claude-constitution/20260120-constitution.md",
            "specs/openai-model-spec/model_spec.md",
            "data/coverage.json",
        ],
        "behaviours": behaviours,
        "documents": documents,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
