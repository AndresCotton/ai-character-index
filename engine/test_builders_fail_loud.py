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
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# The builders do `from coverage_payload import coverage_payload`; make sure
# engine/ is importable regardless of the invoking cwd.
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "spec-cite"))
import cite  # noqa: E402


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
        # Pin the user-spec manifest at a path that cannot exist and reset cite's
        # registry, so an ambient SPEC_CITE_USER_SPECS (or specs/user/specs.json)
        # can never leak a user spec into the byte-identity rebuild below. Mirrors
        # tests/test_custom_spec_decoupling.py's isolation.
        self._saved_manifest = os.environ.get(cite.MANIFEST_ENV_VAR)
        os.environ[cite.MANIFEST_ENV_VAR] = "/nonexistent/specs.json"
        cite.load_user_manifest()
        # Clean argv too: build-spec-reader-data.main() reads sys.argv when
        # called bare, so ambient unittest flags must not reach the builder.
        self._saved_argv = sys.argv
        sys.argv = [str(HERE / "build-spec-reader-data.py")]
        self.mod = load("build-spec-reader-data")
        # Redirect the data read + output; DOCUMENTS' spec paths were bound to
        # the real repo at module load and stay valid.
        self.mod.ROOT = self.tmp
        self.mod.OUTPUT = self.tmp / "documents.json"

    def tearDown(self):
        sys.argv = self._saved_argv
        if self._saved_manifest is None:
            os.environ.pop(cite.MANIFEST_ENV_VAR, None)
        else:
            os.environ[cite.MANIFEST_ENV_VAR] = self._saved_manifest
        cite.load_user_manifest()

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




if __name__ == "__main__":
    unittest.main(verbosity=2)
