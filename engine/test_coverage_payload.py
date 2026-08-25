#!/usr/bin/env python3
"""Unit tests for the shared reader payload builder (engine/coverage_payload.py).
No network, no keys, sub-second. Run:  python3 engine/test_coverage_payload.py
"""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cp = load("coverage_payload")

RECORD = {
    "behaviour_id": 1,
    "lab_id": "anthropic",
    "verdict": "covered",
    "depth_0_4": 3,
    "depth_note": "Direct, explicit coverage.",
    "verified_date": "2026-08-18",
    "citations": [
        {"locator": "S3", "quote": "quote one", "role": "core"},
        {
            "locator": "S7",
            "quote": "quote two",
            "role": "supporting",
            "adjacent": True,
            "example_block": True,
        },
    ],
}


class TestFieldMapping(unittest.TestCase):
    def test_record_fields_map_to_reader_keys(self):
        out = cp.coverage_payload(RECORD, "anthropic", "no-sycophancy")
        self.assertEqual(out["verdict"], "covered")
        self.assertEqual(out["depth"], 3)
        self.assertEqual(out["note"], "Direct, explicit coverage.")
        self.assertEqual(out["verifiedDate"], "2026-08-18")

    def test_key_order_is_stable(self):
        # The builders serialize with json.dumps, so key order is part of the
        # shipped bytes; lock it down to keep outputs byte-stable.
        out = cp.coverage_payload(RECORD, "anthropic", "no-sycophancy")
        self.assertEqual(list(out), ["verdict", "depth", "note", "verifiedDate", "passages"])
        self.assertEqual(
            list(out["passages"][0]),
            ["id", "locator", "quote", "role", "adjacent", "exampleBlock"],
        )

    def test_empty_citations_yield_empty_passages(self):
        out = cp.coverage_payload({**RECORD, "citations": []}, "openai", "no-sycophancy")
        self.assertEqual(out["passages"], [])


class TestScopeIdParameter(unittest.TestCase):
    """The one knob the original copies differed on: the passage-id prefix is
    whatever the caller passes as the second argument -- the document id (the
    lab namespace) for the reader payload."""

    def test_passage_ids_follow_scope_id(self):
        as_document = cp.coverage_payload(RECORD, "anthropic", "no-sycophancy")
        self.assertEqual(
            [p["id"] for p in as_document["passages"]],
            ["anthropic-no-sycophancy-1", "anthropic-no-sycophancy-2"],
        )
        as_lab = cp.coverage_payload(RECORD, "openai", "no-sycophancy")
        self.assertEqual(
            [p["id"] for p in as_lab["passages"]],
            ["openai-no-sycophancy-1", "openai-no-sycophancy-2"],
        )

    def test_passage_ids_are_1_indexed_in_citation_order(self):
        out = cp.coverage_payload(RECORD, "anthropic", "calibration")
        self.assertEqual(
            [p["id"] for p in out["passages"]],
            ["anthropic-calibration-1", "anthropic-calibration-2"],
        )


class TestCitationMapping(unittest.TestCase):
    def test_citation_fields_and_defaults(self):
        out = cp.coverage_payload(RECORD, "anthropic", "no-sycophancy")
        first, second = out["passages"]
        self.assertEqual(first["locator"], "S3")
        self.assertEqual(first["quote"], "quote one")
        self.assertEqual(first["role"], "core")
        # absent in the record -> defaults; assertIs pins boolean identity, so a
        # mutation to None (which would ship `null` instead of `false`) fails
        self.assertIs(first["adjacent"], False)
        self.assertIs(first["exampleBlock"], False)
        # present in the record -> carried through
        self.assertIs(second["adjacent"], True)
        self.assertIs(second["exampleBlock"], True)

    def test_payload_is_json_serializable(self):
        out = cp.coverage_payload(RECORD, "anthropic", "no-sycophancy")
        self.assertEqual(json.loads(json.dumps(out)), out)


if __name__ == "__main__":
    unittest.main()
