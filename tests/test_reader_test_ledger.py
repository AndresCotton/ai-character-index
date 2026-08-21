"""Gate test: the reader-test bench ledger matches its sweep artifacts.

data/reader-test-coverage.json was hand-transcribed from the stage-4 sweeps
in behaviours-for-adria/; engine/generate-reader-test-ledger.py closes the
loop. --check compares every coverage row against its artifact -- verdict,
depth, the depth rationale, and every citation's locator, quote, role, and
core/adjacent flag -- and fails on any divergence the script's DISCLOSED
list does not pin by name. Regeneration is byte-identity pinned: a no-op
rewrite reproduces the committed ledger exactly.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "engine" / "generate-reader-test-ledger.py"


class ReaderTestLedgerMatchesArtifactsTest(unittest.TestCase):

    def test_check_passes_on_committed_tree(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CHECK OK", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
