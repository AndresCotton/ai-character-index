#!/usr/bin/env python3
"""The two reader builders must reproduce the committed site payloads byte-for-byte.

The site payloads are committed static output (there is no build step in the
deploy), so "the committed payload is exactly what the current builders emit"
is a data-integrity claim worth pinning. This test executes both builders with
a redirected OUTPUT path (the working tree is never touched) and byte-diffs
the result against the committed file.
"""

import importlib.util
import os
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "engine" / "spec-cite"))
import cite  # noqa: E402


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBuildersReproduceCommittedPayloads(unittest.TestCase):
    def setUp(self):
        # The builders run in-process, so pin the user-spec manifest at a path that
        # cannot exist and reset cite's registry: a developer's ambient
        # SPEC_CITE_USER_SPECS (or specs/user/specs.json) must never leak a user spec
        # into a byte-identity rebuild. Mirrors the isolation in
        # tests/test_custom_spec_decoupling.py and engine/panel/test_panel.py's
        # hermetic_env().
        self._saved_manifest = os.environ.get(cite.MANIFEST_ENV_VAR)
        os.environ[cite.MANIFEST_ENV_VAR] = "/nonexistent/specs.json"
        cite.load_user_manifest()

    def tearDown(self):
        if self._saved_manifest is None:
            os.environ.pop(cite.MANIFEST_ENV_VAR, None)
        else:
            os.environ[cite.MANIFEST_ENV_VAR] = self._saved_manifest
        cite.load_user_manifest()

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
        # Run with a clean argv too: build-spec-reader-data.main() reads sys.argv
        # when called bare, so ambient unittest flags must not reach the builder.
        saved_argv = sys.argv
        sys.argv = [str(builder_path)]
        try:
            mod.main()
        finally:
            sys.argv = saved_argv
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

if __name__ == "__main__":
    unittest.main()
