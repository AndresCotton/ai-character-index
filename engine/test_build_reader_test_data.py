#!/usr/bin/env python3
"""Smoke test: engine/build-reader-test-data.py emits the bench payload shape.

Happy path runs the real builder with OUTPUT redirected into an in-repo
scratch dir (the builder prints OUTPUT.relative_to(ROOT), so the target must
stay under ROOT); the working tree is never touched. Failure path feeds the
builder a mutated scratch copy of the ledger and expects its descriptive
SystemExit. No network, no keys, sub-second.

Run:  python3 engine/test_build_reader_test_data.py
"""
import contextlib
import copy
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# The builder does `from coverage_payload import coverage_payload`; make sure
# engine/ is importable regardless of the invoking cwd.
sys.path.insert(0, str(HERE))


def load_builder():
    # Hyphenated filename: importlib, not a plain import.
    spec = importlib.util.spec_from_file_location(
        "build_reader_test_data", HERE / "build-reader-test-data.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBuildReaderTestData(unittest.TestCase):
    def setUp(self):
        self.source = json.loads(
            (ROOT / "data" / "reader-test-coverage.json").read_text(encoding="utf-8")
        )
        self.mod = load_builder()
        # Redirect OUTPUT into an in-repo scratch dir (the builder prints
        # OUTPUT.relative_to(ROOT), so the target must stay under ROOT).
        # .gitignore keeps .builder-repro-scratch/ out of the tree.
        scratch_root = ROOT / ".builder-repro-scratch"
        scratch_root.mkdir(exist_ok=True)
        self.scratch = Path(
            tempfile.mkdtemp(dir=scratch_root, prefix="build-reader-test-data-")
        )
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.mod.OUTPUT = self.scratch / "behaviours.json"

    def run_builder(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.mod.main()
        return buffer.getvalue()

    def test_happy_path_payload_shape(self):
        self.run_builder()
        payload = json.loads(self.mod.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(payload["generatedFrom"], ["data/reader-test-coverage.json"])

        behaviours = payload["behaviours"]
        self.assertIsInstance(behaviours, list)
        self.assertEqual(len(behaviours), len(self.source["behaviours"]))

        for behaviour, source_behaviour in zip(behaviours, self.source["behaviours"]):
            with self.subTest(slug=behaviour["slug"]):
                self.assertEqual(behaviour["id"], source_behaviour["id"])
                self.assertEqual(behaviour["slug"], source_behaviour["slug"])
                self.assertEqual(behaviour["name"], source_behaviour["name"])
                self.assertEqual(behaviour["definition"], source_behaviour["definition"])
                self.assertEqual(behaviour["category"], source_behaviour["category"])
                self.assertEqual(set(behaviour["coverage"]), set(self.mod.LAB_IDS))

                for lab_id, cov in behaviour["coverage"].items():
                    record = next(
                        r
                        for r in self.source["coverage"]
                        if r["behaviour_id"] == behaviour["id"] and r["lab_id"] == lab_id
                    )
                    self.assertEqual(
                        set(cov), {"verdict", "depth", "note", "verifiedDate", "passages"}
                    )
                    self.assertEqual(cov["verdict"], record["verdict"])
                    self.assertEqual(cov["depth"], record["depth_0_4"])
                    self.assertEqual(cov["note"], record["depth_note"])
                    self.assertEqual(cov["verifiedDate"], record["verified_date"])
                    # Passage ids are 1-indexed in citation order; the quote
                    # fields carry the source citation through unchanged.
                    self.assertEqual(len(cov["passages"]), len(record["citations"]))
                    for index, (passage, citation) in enumerate(
                        zip(cov["passages"], record["citations"]), start=1
                    ):
                        self.assertEqual(
                            passage["id"], f"{lab_id}-{behaviour['slug']}-{index}"
                        )
                        self.assertEqual(passage["locator"], citation["locator"])
                        self.assertEqual(passage["quote"], citation["quote"])
                        self.assertEqual(passage["role"], citation["role"])

    def test_duplicated_record_fails_with_descriptive_exit(self):
        # A duplicated (behaviour_id, lab_id) record must not be absorbed
        # silently: the builder exits with a message naming the behaviour
        # and the lab.
        mutated = copy.deepcopy(self.source)
        duplicated = copy.deepcopy(mutated["coverage"][0])
        mutated["coverage"].append(duplicated)
        source_copy = self.scratch / "reader-test-coverage.json"
        source_copy.write_text(json.dumps(mutated), encoding="utf-8")
        self.mod.SOURCE = source_copy

        with self.assertRaises(SystemExit) as caught:
            self.run_builder()
        message = str(caught.exception)
        self.assertIn("helpfulness", message)
        self.assertIn("anthropic", message)
        self.assertIn("found 2", message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
