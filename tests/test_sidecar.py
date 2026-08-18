"""Gate tests for the structured stage-4 sidecar (4-spec-coverage.json).

Pins the sidecar path of engine/publish-coverage.py:

- every committed sidecar validates against
  data/schema/spec-coverage-sidecar.schema.json (both validator backends)
  and carries complete reconstruction provenance when marked reconstructed;
- a sidecar with a corrupted quote still fails --check at the cite.py
  re-resolution gate (the sidecar changes the parsing contract, never the
  quote-verification invariant);
- schema violations fail loudly at publish time;
- the reconstruction honesty rule is enforced: a sidecar marked
  reconstructed must name its source and date.

Locators/quotes in the negative fixtures are borrowed from
data/coverage.json (known-good: they resolve against the pinned mirrors),
so the only thing that can fail is the corruption under test.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "engine" / "publish-coverage.py"
COVERAGE = ROOT / "data" / "coverage.json"
SCHEMA = ROOT / "data" / "schema" / "spec-coverage-sidecar.schema.json"
SWEEPS = ROOT / "research" / "sweeps"

sys.path.insert(0, str(ROOT / "engine"))
import validate_data  # noqa: E402

# Behaviour 99 is unpublished, so --check can never pass via the
# records-match branch; only parsing + quote verification run on fixtures.
FIXTURE_DIR_NAME = "99-negative-fixture"


def pick_single_line_quote(lab_id):
    data = json.loads(COVERAGE.read_text(encoding="utf-8"))
    for record in data["coverage"]:
        if record["lab_id"] != lab_id:
            continue
        for citation in record["citations"]:
            if "\n" not in citation["quote"] and not citation.get("example_block"):
                return citation
    raise AssertionError(f"no single-line {lab_id} quote in coverage.json")


def make_fixture_record(lab_id, citation):
    return {
        "behaviour_id": 99,
        "behaviour_name": "negative fixture",
        "lab_id": lab_id,
        "verdict": "covered",
        "depth_0_4": 1,
        "depth_note": "negative fixture",
        "citations": [dict(citation)],
        # The version pinned by the record's first locator; the publisher
        # cross-checks this equality, so derive it rather than hardcode it.
        "verified_against_version": citation["locator"].split(" › ")[0].split("@")[1],
        "verified_date": "2026-01-01",
        "citation_format": json.loads(COVERAGE.read_text(encoding="utf-8"))[
            "coverage"][0]["citation_format"],
    }


def make_fixture_sidecar(corrupt=False, mutate=None):
    anthropic = dict(pick_single_line_quote("anthropic"))
    openai = dict(pick_single_line_quote("openai"))
    if corrupt:
        anthropic["quote"] += " [corrupted]"
    sidecar = {
        "sidecar_version": 1,
        "behaviour_id": 99,
        "behaviour_name": "negative fixture",
        "slug": "negative-fixture",
        "records": [
            make_fixture_record("anthropic", anthropic),
            make_fixture_record("openai", openai),
        ],
        "provenance": {"reconstructed": False},
    }
    if mutate:
        mutate(sidecar)
    return sidecar


def run_check(sidecar, dir_name=FIXTURE_DIR_NAME):
    with tempfile.TemporaryDirectory() as tmp:
        sweep_dir = Path(tmp) / dir_name
        sweep_dir.mkdir()
        (sweep_dir / "4-spec-coverage.json").write_text(
            json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return subprocess.run(
            [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
            capture_output=True, text=True, encoding="utf-8",
        )


class CommittedSidecarTest(unittest.TestCase):
    """Committed sidecars are schema-valid on both backends, and any
    reconstruction carries the full provenance the honesty bar requires."""

    def test_committed_sidecars_validate(self):
        sidecars = sorted(SWEEPS.glob("*/4-spec-coverage.json"))
        self.assertTrue(sidecars, "no sidecars committed")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        for path in sidecars:
            with self.subTest(sidecar=str(path.relative_to(ROOT))):
                instance = json.loads(path.read_text(encoding="utf-8"))
                for force_stdlib in (False, True):
                    self.assertEqual(
                        validate_data.validate_instance(
                            instance, schema, force_stdlib=force_stdlib
                        ),
                        [],
                    )
                provenance = instance["provenance"]
                if provenance["reconstructed"]:
                    self.assertIn("reconstructedFrom", provenance)
                    self.assertIn("reconstructedDate", provenance)
                # Mirror the publisher's directory cross-checks statically.
                number, _, slug = path.parent.name.partition("-")
                self.assertEqual(int(number), instance["behaviour_id"])
                self.assertEqual(slug, instance["slug"])

    def test_sidecar_schema_is_valid_draft_2020_12(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        jsonschema.Draft202012Validator.check_schema(
            json.loads(SCHEMA.read_text(encoding="utf-8"))
        )


class SidecarNegativeTest(unittest.TestCase):
    """Mutation guards for the sidecar path of publish-coverage.py."""

    def test_corrupted_quote_fails_check(self):
        result = run_check(make_fixture_sidecar(corrupt=True))
        self.assertNotEqual(
            result.returncode, 0,
            "corrupted quote must fail the publish gate:\n"
            + result.stdout + result.stderr,
        )
        # Pin WHERE it failed: the cite.py mismatch detector, not a schema
        # or fixture problem.
        self.assertIn("MISMATCH", result.stdout)

    def test_unknown_key_fails_schema_validation(self):
        def mutate(sidecar):
            sidecar["severity"] = "high"
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("failed schema validation", combined)
        self.assertIn("severity", combined)

    def test_reconstructed_sidecar_without_source_fails(self):
        # The honesty rule: reconstructed means naming the source and date.
        def mutate(sidecar):
            sidecar["provenance"] = {"reconstructed": True}
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reconstructedFrom", result.stdout + result.stderr)

    def test_missing_lab_record_fails(self):
        def mutate(sidecar):
            sidecar["records"] = sidecar["records"][:1]
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("one record per lab", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
