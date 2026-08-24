#!/usr/bin/env python3
"""The two reader builders must reproduce the committed site payloads byte-for-byte.

The site payloads are committed static output (there is no build step in the
deploy), so "the committed payload is exactly what the current builders emit"
is a data-integrity claim worth pinning. This test executes both builders with
a redirected OUTPUT path (the working tree is never touched) and byte-diffs
the result against the committed file.
"""

import importlib.util
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBuildersReproduceCommittedPayloads(unittest.TestCase):
    def _assert_reproduces(self, builder_path, module_name, committed):
        if not committed.exists():
            self.skipTest(f"{committed} not present")
        committed_bytes = committed.read_bytes()
        mod = _load_module(module_name, builder_path)
        # Redirect OUTPUT into an in-repo scratch dir (the builders print
        # OUTPUT.relative_to(ROOT), so the target must stay under ROOT).
        scratch = ROOT / ".builder-repro-scratch"
        scratch.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        mod.OUTPUT = scratch / committed.name
        mod.main()
        self.assertEqual(
            mod.OUTPUT.read_bytes(),
            committed_bytes,
            f"{builder_path.name} output differs from committed "
            f"{committed.relative_to(ROOT)}",
        )

    def test_spec_reader_payload_reproduces(self):
        self._assert_reproduces(
            ROOT / "engine" / "build-spec-reader-data.py",
            "build_spec_reader_data",
            ROOT / "site" / "spec-reader" / "data" / "documents.json",
        )

    def test_reader_test_payload_reproduces(self):
        self._assert_reproduces(
            ROOT / "engine" / "build-reader-test-data.py",
            "build_reader_test_data",
            ROOT / "site" / "spec-reader-test" / "data" / "behaviours.json",
        )


if __name__ == "__main__":
    unittest.main()
