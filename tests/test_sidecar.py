"""Gate tests for the structured stage-4 sidecar (4-spec-coverage.json).

Pins the sidecar path of engine/publish-coverage.py:

- every committed sidecar validates against
  data/schema/spec-coverage-sidecar.schema.json (both validator backends)
  and carries complete reconstruction provenance when marked reconstructed;
- a sidecar with a corrupted quote still fails --check at the cite.py
  re-resolution gate (the sidecar changes the parsing contract, never the
  quote-verification invariant);
- schema violations fail loudly at publish time;
- sidecar_version must be 1 -- the schema declares the field, but only the
  publisher rejects a future value;
- the reconstruction honesty rule is enforced: a sidecar marked
  reconstructed must name its source and date;
- every cross-check parse_sidecar() runs after schema validation has a
  mutation guard (slug vs directory name, record identity vs top-level,
  citation_format vs the project constant, verified_against_version vs the
  first locator, duplicate lab records, and sidecar-beats-markdown
  precedence), each on a scratch copy of the committed behaviour-1 sweep.

Locators/quotes in the negative fixtures are borrowed from
data/coverage.json (known-good: they resolve against the pinned mirrors),
so the only thing that can fail is the corruption under test.
"""

import importlib.util
import json
import contextlib
import io
import shutil
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

    def test_future_sidecar_version_fails(self):
        # sidecar_version 2 is schema-valid (integer, minimum 1), so only
        # the publisher's explicit version check can reject it.
        def mutate(sidecar):
            sidecar["sidecar_version"] = 2
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("sidecar_version", combined)
        self.assertIn("not supported", combined)

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

    def test_reconstructed_sidecar_without_date_fails(self):
        # Both legs of the honesty rule: source alone is not enough.
        def mutate(sidecar):
            sidecar["provenance"] = {
                "reconstructed": True,
                "reconstructedFrom": "data/coverage.json @ test",
            }
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reconstructedDate", result.stdout + result.stderr)

    def test_reconstructed_sidecar_without_note_fails(self):
        # All three legs: source + date without a note is still not honest.
        def mutate(sidecar):
            sidecar["provenance"] = {
                "reconstructed": True,
                "reconstructedFrom": "data/coverage.json @ test",
                "reconstructedDate": "2026-08-18",
            }
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("note", result.stdout + result.stderr)

    def test_missing_lab_record_fails(self):
        def mutate(sidecar):
            sidecar["records"] = sidecar["records"][:1]
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("one record per lab", result.stdout + result.stderr)


class SidecarCrossCheckTest(unittest.TestCase):
    """Mutation guards for the cross-checks parse_sidecar() runs after
    schema validation, on scratch copies of the committed behaviour-1
    sweep (the committed artifact is never mutated). Every mutation is
    schema-valid, so only the cross-check under test can reject it, and
    every cross-check trips before cite.py runs, so these stay fast.
    """

    SOURCE = "01-no-sycophancy"

    def run_scratch_check(self, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = Path(tmp) / self.SOURCE
            shutil.copytree(SWEEPS / self.SOURCE, sweep_dir)
            sidecar_path = sweep_dir / "4-spec-coverage.json"
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            mutate(sidecar)
            sidecar_path.write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return subprocess.run(
                [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )

    def test_slug_mismatching_directory_fails(self):
        def mutate(sidecar):
            sidecar["slug"] = "sycophancy"   # dir is 01-no-sycophancy
        result = self.run_scratch_check(mutate)
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("slug", combined)
        self.assertIn("does not match its directory", combined)

    def test_record_identity_mismatch_fails(self):
        for field, value in (("behaviour_id", 2), ("behaviour_name", "Elsewhere")):
            with self.subTest(field=field):
                def mutate(sidecar, field=field, value=value):
                    sidecar["records"][0][field] = value
                result = self.run_scratch_check(mutate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    "disagrees with the top-level behaviour identity",
                    result.stdout + result.stderr,
                )

    def test_citation_format_mismatch_fails(self):
        def mutate(sidecar):
            sidecar["records"][0]["citation_format"] = "some other convention"
        result = self.run_scratch_check(mutate)
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("citation_format", combined)
        self.assertIn("project's citation convention", combined)

    def test_verified_against_version_mismatch_fails(self):
        def mutate(sidecar):
            sidecar["records"][0]["verified_against_version"] = "1999-01-01"
        result = self.run_scratch_check(mutate)
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("verified_against_version", combined)
        self.assertIn("does not match the version pinned by its first locator",
                      combined)

    def test_duplicate_lab_record_fails(self):
        def mutate(sidecar):
            sidecar["records"].append(dict(sidecar["records"][0]))
        result = self.run_scratch_check(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate record for lab", result.stdout + result.stderr)

    def test_unknown_lab_record_fails(self):
        # The other direction of the one-record-per-lab check: a record whose
        # lab_id is schema-valid (the schema only requires a non-empty string)
        # but is not one of the expected labs for the behaviour. The coverage
        # schema also allows any lab_id string, so only this cross-check can
        # reject it -- pinning it from the "unexpected lab" side.
        def mutate(sidecar):
            sidecar["records"][1]["lab_id"] = "deepmind"
        result = self.run_scratch_check(mutate)
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("one record per lab", combined)
        self.assertIn("deepmind", combined)

    def test_sidecar_wins_when_markdown_also_present(self):
        """Precedence: with both artifacts present the publisher must take
        the sidecar. The scratch copy's markdown is deliberately
        unparseable, so a green check is only reachable through the sidecar
        path -- the markdown path would abort parsing it."""
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = Path(tmp) / self.SOURCE
            shutil.copytree(SWEEPS / self.SOURCE, sweep_dir)
            (sweep_dir / "4-spec-coverage.md").write_text(
                "not a stage-4 artifact\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(
            result.returncode, 0,
            "sidecar must win over an unparseable markdown sibling:\n"
            + result.stdout + result.stderr,
        )
        self.assertIn("using structured sidecar", result.stdout)
        self.assertIn("CHECK OK", result.stdout)


class SidecarCoverageSchemaGateTest(unittest.TestCase):
    """The sidecar path's records are gated by the REAL
    data/schema/coverage.schema.json before quote verification -- not merely
    by the sidecar schema's mirrored coverageRecord $def. Those two $defs are
    hand-maintained copies of one another, so the load-bearing claim is that a
    record can pass the sidecar schema yet still be rejected by the coverage
    schema if the two ever drift apart. This simulates exactly that drift: a
    coverage schema that requires a field the sidecar mirror does not must
    reject records that are valid against the sidecar schema -- proving it is
    the coverage gate, not the mirror, that protects data/coverage.json.
    """

    @staticmethod
    def _load_publish():
        spec = importlib.util.spec_from_file_location("publish_coverage", PUBLISH)
        publish = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publish)
        return publish

    def test_sidecar_schema_valid_but_coverage_schema_invalid_fails(self):
        publish = self._load_publish()

        sidecar = make_fixture_sidecar()
        sidecar_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        # Premise: the fixture is valid against its OWN schema, so the sidecar
        # gate passes and only the coverage gate can reject what follows.
        self.assertEqual(
            validate_data.validate_instance(sidecar, sidecar_schema), []
        )

        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = Path(tmp) / FIXTURE_DIR_NAME
            sweep_dir.mkdir()
            sidecar_path = sweep_dir / "4-spec-coverage.json"
            sidecar_path.write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            # Passes the sidecar schema and every cross-check; returns the
            # records verbatim, exactly as main() receives them.
            _, records = publish.parse_sidecar(sidecar_path, sweep_dir)

            # Drift: coverage.schema.json gains a requirement the sidecar
            # mirror lacks. The records carry no such field.
            coverage_schema = json.loads(
                (ROOT / "data" / "schema" / "coverage.schema.json")
                .read_text(encoding="utf-8")
            )
            record_def = coverage_schema["$defs"]["coverageRecord"]
            record_def["required"].append("drift_canary")
            record_def["properties"]["drift_canary"] = {
                "type": "string", "minLength": 1,
            }

            # Schema-level pin: the drifted schema rejects the records on BOTH
            # validator backends, so the gate holds with or without jsonschema.
            for force_stdlib in (False, True):
                with self.subTest(force_stdlib=force_stdlib):
                    self.assertTrue(
                        validate_data.validate_instance(
                            {"coverage": records}, coverage_schema,
                            force_stdlib=force_stdlib,
                        ),
                        f"drifted coverage schema must reject the sidecar "
                        f"records (force_stdlib={force_stdlib})",
                    )

            # Wired-gate pin: validate_coverage_records -- the call main() now
            # makes on the sidecar path -- reads COVERAGE_SCHEMA, so point it
            # at the drifted schema and it must abort the publish.
            stricter = Path(tmp) / "coverage.drift.json"
            stricter.write_text(
                json.dumps(coverage_schema, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            publish.COVERAGE_SCHEMA = stricter
            with self.assertRaises(SystemExit) as ctx:
                publish.validate_coverage_records(records, sidecar_path.name)
        self.assertIn("coverage-schema error", str(ctx.exception))



class LocatorSeparatorTest(unittest.TestCase):
    """Version extraction tolerates the separator variants CITATION.md
    allows (artifacts use " \u203a "; ">" and " > " must work too)."""

    def test_ascii_separator_sidecar_checks_green(self):
        def mutate(sidecar):
            for record in sidecar["records"]:
                for citation in record["citations"]:
                    citation["locator"] = citation["locator"].replace(" \u203a ", " > ")
        result = run_check(make_fixture_sidecar(mutate=mutate))
        self.assertEqual(
            result.returncode, 0,
            "ascii-separator locators must parse:\n" + result.stdout + result.stderr,
        )
        self.assertNotIn("does not start with spec@version",
                         result.stdout + result.stderr)


class WritePathRoundTripTest(unittest.TestCase):
    """The load-bearing byte-stability claim, exercised through the
    publisher's real write path: republishing a committed sidecar into a
    scratch coverage.json reproduces the committed file byte-for-byte."""

    def test_republish_behaviour_2_is_byte_identical(self):
        spec = importlib.util.spec_from_file_location("publish_under_test", PUBLISH)
        pub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pub)
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp) / "coverage.json"
            shutil.copy(COVERAGE, scratch)
            pub.COVERAGE = scratch
            saved = sys.argv
            sys.argv = ["publish-coverage.py", str(SWEEPS / "02-calibration")]
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    pub.main()
            finally:
                sys.argv = saved
            self.assertIn("Wrote", buf.getvalue())
            self.assertEqual(
                scratch.read_bytes(), COVERAGE.read_bytes(),
                "republish must reproduce data/coverage.json byte-for-byte",
            )


if __name__ == "__main__":
    unittest.main()
