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


def main() -> None:
    coverage = json.loads((ROOT / "data" / "coverage.json").read_text())
    records = coverage["coverage"]

    documents = []
    for document in DOCUMENTS:
        record = next(
            item
            for item in records
            if item["behaviour_id"] == 1 and item["lab_id"] == document["id"]
        )
        documents.append(
            {
                key: value
                for key, value in document.items()
                if key != "path"
            }
            | {
                "markdown": document["path"].read_text(),
                "coverage": {
                    "verdict": record["verdict"],
                    "depth": record["depth_0_4"],
                    "note": record["depth_note"],
                    "verifiedDate": record["verified_date"],
                    "passages": [
                        {
                            "id": f"{document['id']}-sycophancy-{index + 1}",
                            "locator": citation["locator"],
                            "quote": citation["quote"],
                            "role": citation["role"],
                            "adjacent": citation.get("adjacent", False),
                            "exampleBlock": citation.get("example_block", False),
                        }
                        for index, citation in enumerate(record["citations"])
                    ],
                },
            }
        )

    payload = {
        "generatedFrom": [
            "specs/claude-constitution/20260120-constitution.md",
            "specs/openai-model-spec/model_spec.md",
            "data/coverage.json",
        ],
        "behaviour": {
            "id": 1,
            "slug": "no-sycophancy",
            "name": "No sycophancy",
            "definition": (
                "The model should not shift its factual claims or assessments "
                "to please the user."
            ),
            "category": "Honesty & epistemics",
        },
        "documents": documents,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
