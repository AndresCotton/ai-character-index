"""Gate test: every published behaviour's records match its stage-4 artifact.

Runs `engine/publish-coverage.py <sweep-dir> --check` for every
research/sweeps/*/ directory holding a stage-4 artifact
(`4-spec-coverage.md` or its structured sidecar `4-spec-coverage.json`).
The publish script re-resolves every stored quote byte-for-byte against
cite.py and diffs the parsed records against data/coverage.json, so this
single test covers quote fidelity, the artifact parsing contract, and the
published data in one shot.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "engine" / "publish-coverage.py"
COVERAGE = ROOT / "data" / "coverage.json"
COVERAGE_SCHEMA = ROOT / "data" / "schema" / "coverage.schema.json"
SWEEPS = ROOT / "research" / "sweeps"

sys.path.insert(0, str(ROOT / "engine"))
import validate_data  # noqa: E402


class PublishCheckGateTest(unittest.TestCase):
    def test_published_behaviours_match_their_artifacts(self):
        sweep_dirs = sorted({
            artifact.parent
            for pattern in ("*/4-spec-coverage.md", "*/4-spec-coverage.json")
            for artifact in ROOT.glob(f"research/sweeps/{pattern}")
        })
        self.assertTrue(sweep_dirs, "no stage-4 artifacts found")
        for sweep_dir in sweep_dirs:
            with self.subTest(behaviour=sweep_dir.name):
                result = subprocess.run(
                    [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                    capture_output=True, text=True, encoding="utf-8",
                )
                self.assertEqual(
                    result.returncode, 0, result.stdout + result.stderr
                )
                self.assertIn("CHECK OK", result.stdout)


class CorruptedQuoteNegativeTest(unittest.TestCase):
    """Mutation guard for the gate above: the positive test stays green even
    if publish-coverage.py's mismatch detection is gutted (e.g. verify
    always reports success). Build a throwaway sweep dir whose artifact
    carries one deliberately corrupted quote and assert --check exits
    non-zero on it, so detection itself is pinned.

    Locators/quotes are borrowed from data/coverage.json (known-good: they
    resolve against the pinned mirrors), so the ONLY thing that can fail is
    the corruption we introduced -- a parse error, a version miss, or a
    schema violation would be a fixture bug, not a gate finding (the
    verdicts below are schema-valid enum values on purpose: the markdown
    path's coverage-schema gate runs before cite.py).
    """

    @staticmethod
    def pick_single_line_quote(lab_id):
        data = json.loads(COVERAGE.read_text(encoding="utf-8"))
        for record in data["coverage"]:
            if record["lab_id"] != lab_id:
                continue
            for citation in record["citations"]:
                if "\n" not in citation["quote"] and not citation.get("example_block"):
                    return citation
        raise AssertionError(f"no single-line {lab_id} quote in coverage.json")

    def test_corrupted_quote_fails_check(self):
        anthropic = self.pick_single_line_quote("anthropic")
        openai = self.pick_single_line_quote("openai")
        corrupted = anthropic["quote"] + " [corrupted]"
        # behaviour 99 is unpublished, so --check cannot pass via the
        # records-match branch; only the quote verification runs here.
        artifact = f"""# Behaviour 99: negative fixture

- **Behaviour:** 99, negative fixture
- **Sweep date:** 2026-01-01
- **Citation format:** fixture for the corrupted-quote negative test

## Claude constitution

- **Locator:** `{anthropic['locator'].replace(' › ', ' > ')}`
  **Quote:** {corrupted}
  **Role:** negative fixture
  **Flags:** --

## OpenAI Model Spec

- **Locator:** `{openai['locator'].replace(' › ', ' > ')}`
  **Quote:** {openai['quote']}
  **Role:** negative fixture
  **Flags:** --

## Verdict and depth

| Spec | Verdict | Depth | Note |
| --- | --- | --- | --- |
| Claude constitution | partial | 1 | negative fixture |
| OpenAI Model Spec | partial | 1 | negative fixture |
"""
        with tempfile.TemporaryDirectory() as sweep_dir:
            target = Path(sweep_dir) / "4-spec-coverage.md"
            target.write_text(artifact, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PUBLISH), sweep_dir, "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertNotEqual(
            result.returncode, 0,
            "corrupted quote must fail the publish gate:\n"
            + result.stdout + result.stderr,
        )
        # Pin WHERE it failed: the mismatch detector, not a fixture parse
        # error or a locator/version problem.
        self.assertIn("MISMATCH", result.stdout)


class MarkdownSchemaParityTest(unittest.TestCase):
    """The regex path gets the sidecar path's schema gate: parse_markdown()
    records are validated against data/schema/coverage.schema.json before
    the publisher writes or checks anything. Mutates a scratch copy of a
    committed markdown sweep -- never the artifact itself. The verdict cell
    is free text in the layout contract, so parsing happily accepts a word
    outside the schema's enum; only this gate can catch it.
    """

    SOURCE = "02-calibration"

    def _mutated_scratch_sweep(self, tmp: str) -> Path:
        sweep_dir = Path(tmp) / self.SOURCE
        shutil.copytree(SWEEPS / self.SOURCE, sweep_dir)
        # This test targets the markdown parse path; 02-calibration now
        # ships a sidecar, which would otherwise win and mask the mutation.
        (sweep_dir / "4-spec-coverage.json").unlink(missing_ok=True)
        artifact = sweep_dir / "4-spec-coverage.md"
        text = artifact.read_text(encoding="utf-8")
        head, sep, tail = text.partition("## Verdict and depth")
        self.assertTrue(sep, "fixture source lost its verdict table")
        mutated = tail.replace("| covered |", "| fully covered |", 1)
        self.assertNotEqual(mutated, tail, "no verdict cell was mutated")
        artifact.write_text(head + sep + mutated, encoding="utf-8")
        return sweep_dir

    def test_schema_invalid_markdown_records_fail_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = self._mutated_scratch_sweep(tmp)
            result = subprocess.run(
                [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertNotEqual(
            result.returncode, 0,
            "schema-invalid markdown records must fail the publish gate:\n"
            + result.stdout + result.stderr,
        )
        # Pin WHERE it failed: the coverage-schema gate, before cite.py.
        combined = result.stdout + result.stderr
        self.assertIn("coverage.schema.json", combined)
        self.assertIn("fully covered", combined)

    def test_mutated_records_fail_both_validator_backends(self):
        """Unit-level pin: the records parse_markdown() derives from the
        mutated artifact fail validate_data.validate_instance on BOTH
        backends, so the gate holds whether or not jsonschema is installed.
        """
        spec = importlib.util.spec_from_file_location("publish_coverage", PUBLISH)
        publish = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publish)
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = self._mutated_scratch_sweep(tmp)
            _, records = publish.parse_markdown(sweep_dir / "4-spec-coverage.md")
        schema = json.loads(COVERAGE_SCHEMA.read_text(encoding="utf-8"))
        for force_stdlib in (False, True):
            with self.subTest(force_stdlib=force_stdlib):
                errors = validate_data.validate_instance(
                    {"coverage": records}, schema, force_stdlib=force_stdlib
                )
                self.assertTrue(
                    errors,
                    f"mutated records must fail the coverage schema "
                    f"(force_stdlib={force_stdlib})",
                )


class MarkdownVersionExtractionTest(unittest.TestCase):
    """Symmetric failure behavior with the sidecar path: a markdown record's
    first locator that does not start with spec@version must abort cleanly
    (SystemExit) rather than raise an IndexError traceback. The sidecar path
    wraps the identical extraction in try/except IndexError; the regex path
    must fail the same way.
    """

    # The anthropic locator carries no @version; parse_markdown processes
    # anthropic first, so version extraction aborts before OpenAI is read.
    ARTIFACT = """# Behaviour 98: version fixture

- **Behaviour:** 98, version fixture
- **Sweep date:** 2026-01-01

## Claude constitution

- **Locator:** `constitution > Being helpful > ¶2 s1`
  **Quote:** fixture quote
  **Role:** fixture
  **Flags:** --

## OpenAI Model Spec

- **Locator:** `model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1`
  **Quote:** fixture quote
  **Role:** fixture
  **Flags:** --

## Verdict and depth

| Spec | Verdict | Depth | Note |
| --- | --- | --- | --- |
| Claude constitution | partial | 1 | fixture |
| OpenAI Model Spec | partial | 1 | fixture |
"""

    def test_markdown_locator_without_version_fails_cleanly(self):
        spec = importlib.util.spec_from_file_location("publish_coverage", PUBLISH)
        publish = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publish)
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "4-spec-coverage.md"
            artifact.write_text(self.ARTIFACT, encoding="utf-8")
            # An uncaught IndexError would propagate as IndexError, not
            # SystemExit -- so passing here pins the clean failure.
            with self.assertRaises(SystemExit) as ctx:
                publish.parse_markdown(artifact)
        self.assertIn("spec@version", str(ctx.exception))



class CheckOrderAndLayoutFailuresTest(unittest.TestCase):
    """--check compares records order-insensitively, and layout breakage
    fails cleanly (SystemExit with a message, never a traceback)."""

    def test_lab_order_swapped_sidecar_still_checks_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = Path(tmp) / "01-no-sycophancy"
            shutil.copytree(SWEEPS / "01-no-sycophancy", sweep_dir)
            sidecar_path = sweep_dir / "4-spec-coverage.json"
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar["records"] = list(reversed(sidecar["records"]))
            sidecar_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 0,
                         "lab order must not break --check:\n" + result.stdout + result.stderr)
        self.assertIn("CHECK OK", result.stdout)

    def test_missing_verdict_section_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = Path(tmp) / "02-calibration"
            shutil.copytree(SWEEPS / "02-calibration", sweep_dir)
            (sweep_dir / "4-spec-coverage.json").unlink(missing_ok=True)
            artifact = sweep_dir / "4-spec-coverage.md"
            text = artifact.read_text(encoding="utf-8")
            artifact.write_text(text.split("## Verdict and depth", 1)[0], encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("missing the section", combined)
        self.assertNotIn("Traceback", combined)

    def test_malformed_depth_cell_fails_cleanly(self):
        """A non-numeric depth cell is a layout breakage, not a crash: the
        publisher must exit cleanly with a message naming the artifact and
        the behaviour, never a raw ValueError traceback."""
        with tempfile.TemporaryDirectory() as tmp:
            sweep_dir = Path(tmp) / "02-calibration"
            shutil.copytree(SWEEPS / "02-calibration", sweep_dir)
            # Target the markdown parse path; the sidecar would otherwise
            # win and mask the mutation.
            (sweep_dir / "4-spec-coverage.json").unlink(missing_ok=True)
            artifact = sweep_dir / "4-spec-coverage.md"
            text = artifact.read_text(encoding="utf-8")
            head, sep, tail = text.partition("## Verdict and depth")
            self.assertTrue(sep, "fixture source lost its verdict table")
            mutated = tail.replace("| 3 |", "| three |", 1)
            self.assertNotEqual(mutated, tail, "no depth cell was mutated")
            artifact.write_text(head + sep + mutated, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PUBLISH), str(sweep_dir), "--check"],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("layout error", combined)
        self.assertIn("three", combined)
        self.assertIn("4-spec-coverage.md", combined)
        self.assertIn("behaviour 2", combined)
        self.assertNotIn("Traceback", combined)


if __name__ == "__main__":
    unittest.main()
