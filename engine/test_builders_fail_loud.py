#!/usr/bin/env python3
"""Fail-loud tests for the two reader payload builders.

A builder that cannot build must name the offending data (behaviour, document,
lab) in a SystemExit -- never a bare traceback, never a silent drop. Every
mutation runs on a scratch copy in a temp dir; committed data and committed
site payloads are never touched.

Run:  python3 engine/test_builders_fail_loud.py
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSpecReaderBuilderFailsLoud(unittest.TestCase):
    """build-spec-reader-data.py: exactly one record per (behaviour, document)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="build-spec-reader-fail-loud-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        (self.tmp / "data").mkdir()
        shutil.copy(ROOT / "data" / "coverage.json", self.tmp / "data" / "coverage.json")
        self.mod = load("build-spec-reader-data")
        # Redirect the data read + output; DOCUMENTS' spec paths were bound to
        # the real repo at module load and stay valid.
        self.mod.ROOT = self.tmp
        self.mod.OUTPUT = self.tmp / "documents.json"

    def rewrite_coverage(self, mutate):
        path = self.tmp / "data" / "coverage.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_committed_data_still_builds_byte_identical(self):
        # The hardening must not change builder output for valid data.
        self.mod.main()
        committed = (ROOT / "site" / "spec-reader" / "data" / "documents.json").read_bytes()
        self.assertEqual(self.mod.OUTPUT.read_bytes(), committed)

    def test_missing_record_exits_naming_behaviour_and_document(self):
        def mutate(d):
            d["coverage"] = [
                record for record in d["coverage"]
                if not (record["behaviour_id"] == 2 and record["lab_id"] == "openai")
            ]
        self.rewrite_coverage(mutate)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.main()
        message = str(ctx.exception.code)
        self.assertIn("calibration", message)
        self.assertIn("openai", message)
        self.assertIn("found 0", message)

    def test_duplicate_record_exits_naming_behaviour_and_document(self):
        def mutate(d):
            original = next(
                record for record in d["coverage"]
                if record["behaviour_id"] == 1 and record["lab_id"] == "anthropic"
            )
            d["coverage"].append(dict(original))
        self.rewrite_coverage(mutate)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.main()
        message = str(ctx.exception.code)
        self.assertIn("no-sycophancy", message)
        self.assertIn("anthropic", message)
        self.assertIn("found 2", message)


class TestBenchBuilderFailsLoud(unittest.TestCase):
    """build-reader-test-data.py: an unknown lab_id is a loud failure, not a silent drop."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="build-reader-test-fail-loud-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Mirror the data/ layout so SOURCE.relative_to(ROOT) still works.
        (self.tmp / "data").mkdir()
        shutil.copy(
            ROOT / "data" / "reader-test-coverage.json",
            self.tmp / "data" / "reader-test-coverage.json",
        )
        self.mod = load("build-reader-test-data")
        self.mod.ROOT = self.tmp
        self.mod.SOURCE = self.tmp / "data" / "reader-test-coverage.json"
        self.mod.OUTPUT = self.tmp / "behaviours.json"

    def rewrite_source(self, mutate):
        path = self.mod.SOURCE
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_committed_data_still_builds_byte_identical(self):
        # The hardening must not change builder output for valid data.
        self.mod.main()
        committed = (ROOT / "site" / "spec-reader-test" / "data" / "behaviours.json").read_bytes()
        self.assertEqual(self.mod.OUTPUT.read_bytes(), committed)

    def test_unknown_lab_id_exits_naming_the_offender(self):
        # A SystemExit carrying a string code makes the interpreter print the
        # message to stderr and exit with status 1 (non-zero).
        def mutate(d):
            d["coverage"][0]["lab_id"] = "deepmind"
        self.rewrite_source(mutate)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.main()
        message = str(ctx.exception.code)
        self.assertIn("deepmind", message)
        self.assertNotIsInstance(ctx.exception.code, int)  # message, not silent exit(0)

    def test_absent_source_file_still_builds_empty_bench(self):
        # The documented "file absent -> empty bench" path is unchanged.
        self.mod.SOURCE = self.tmp / "does-not-exist.json"
        self.mod.main()
        payload = json.loads(self.mod.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(payload["behaviours"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
