"""Gate test: every published behaviour's records match its stage-4 artifact.

Runs `engine/publish-coverage.py <sweep-dir> --check` for every
research/sweeps/*/4-spec-coverage.md. The publish script re-resolves every
stored quote byte-for-byte against cite.py and diffs the parsed records
against data/coverage.json, so this single test covers quote fidelity, the
artifact parsing contract, and the published data in one shot.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "engine" / "publish-coverage.py"


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


if __name__ == "__main__":
    unittest.main()
