"""Gate test: every published behaviour's records match its stage-4 artifact.

Runs `engine/publish-coverage.py <sweep-dir> --check` for every
research/sweeps/*/4-spec-coverage.md. The publish script re-resolves every
stored quote byte-for-byte against cite.py and diffs the parsed records
against data/coverage.json, so this single test covers quote fidelity, the
artifact parsing contract, and the published data in one shot.
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


class PublishCheckGateTest(unittest.TestCase):
    def test_published_behaviours_match_their_artifacts(self):
        artifacts = sorted(ROOT.glob("research/sweeps/*/4-spec-coverage.md"))
        self.assertTrue(artifacts, "no stage-4 artifacts found")
        for artifact in artifacts:
            with self.subTest(behaviour=artifact.parent.name):
                result = subprocess.run(
                    [sys.executable, str(PUBLISH), str(artifact.parent), "--check"],
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
    the corruption we introduced -- a parse error or a version miss would
    be a fixture bug, not a gate finding.
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
| Claude constitution | fixture | 1 | negative fixture |
| OpenAI Model Spec | fixture | 1 | negative fixture |
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


if __name__ == "__main__":
    unittest.main()
