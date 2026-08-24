"""Gate test: the reader-test bench ledger matches its sweep artifacts.

data/reader-test-coverage.json was hand-transcribed from the stage-4 sweeps
in behaviours-for-adria/; engine/generate-reader-test-ledger.py closes the
loop. --check compares every coverage row against its artifact -- verdict,
depth, the depth rationale, and every citation's locator, quote, role, and
core/adjacent flag -- and fails on any divergence the script's DISCLOSED
list does not pin by name. Regeneration is byte-identity pinned: a no-op
rewrite reproduces the committed ledger exactly.

Below the happy-path gate, mutation tests corrupt a scratch copy of the
parsed ledger (never touching the file on disk) and assert diff_ledger()
both flags it and names the offending behaviour/lab cell -- covering the two
holes an adversarial review found (a row-level disclosure that sheltered an
arbitrary rewrite, and dropped rows nothing counted) plus one negative case
per compared field.
"""

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "engine" / "generate-reader-test-ledger.py"

spec = importlib.util.spec_from_file_location("reader_test_ledger_gen", GENERATOR)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def load_ledger() -> dict:
    return json.loads(gen.LEDGER.read_text(encoding="utf-8"))


def find_row(ledger: dict, slug: str, lab: str) -> dict:
    behaviours = {b["id"]: b for b in ledger["behaviours"]}
    for row in ledger["coverage"]:
        if behaviours[row["behaviour_id"]]["slug"] == slug and row["lab_id"] == lab:
            return row
    raise AssertionError(f"no row for {slug}/{lab}")


class ReaderTestLedgerMatchesArtifactsTest(unittest.TestCase):

    def test_check_passes_on_committed_tree(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CHECK OK", result.stdout)


class MutationTest(unittest.TestCase):
    """Each test corrupts one field on a scratch copy of the parsed ledger
    and asserts diff_ledger() reports exactly the kind of problem expected,
    naming the row it came from."""

    def setUp(self):
        self.ledger = load_ledger()

    def assert_flagged(self, ledger, slug, lab):
        problems, _ = gen.diff_ledger(ledger)
        self.assertTrue(problems, "corruption was not detected")
        self.assertTrue(
            any(p.startswith(f"{slug}/{lab}:") for p in problems),
            f"no problem named {slug}/{lab}; got: {problems}",
        )

    def test_verdict_corruption_fails_named(self):
        row = find_row(self.ledger, "helpfulness", "anthropic")
        row["verdict"] = "BOGUS"
        self.assert_flagged(self.ledger, "helpfulness", "anthropic")

    def test_depth_corruption_fails_named(self):
        row = find_row(self.ledger, "helpfulness", "openai")
        row["depth_0_4"] = (row["depth_0_4"] + 1) % 5
        self.assert_flagged(self.ledger, "helpfulness", "openai")

    def test_depth_note_corruption_fails_named(self):
        row = find_row(self.ledger, "user-autonomy", "anthropic")
        row["depth_note"] = "a rationale the artifact never wrote"
        self.assert_flagged(self.ledger, "user-autonomy", "anthropic")

    def test_locator_set_corruption_fails_named(self):
        row = find_row(self.ledger, "user-autonomy", "openai")
        row["citations"][0]["locator"] = "model-spec@2025-12-18 > #nonexistent > ¶1"
        self.assert_flagged(self.ledger, "user-autonomy", "openai")

    def test_quote_corruption_fails_named(self):
        row = find_row(self.ledger, "how-to-approach-tradeoffs", "anthropic")
        row["citations"][0]["quote"] = "words the spec never wrote, verbatim or otherwise"
        self.assert_flagged(self.ledger, "how-to-approach-tradeoffs", "anthropic")

    def test_role_corruption_at_undisclosed_row_fails_named(self):
        row = find_row(self.ledger, "how-to-approach-tradeoffs", "openai")
        row["citations"][0]["role"] = "an unrelated role, not present in the artifact"
        self.assert_flagged(self.ledger, "how-to-approach-tradeoffs", "openai")

    def test_adjacent_flag_corruption_fails_named(self):
        row = find_row(self.ledger, "user-autonomy", "anthropic")
        row["citations"][0]["adjacent"] = not bool(row["citations"][0].get("adjacent", False))
        self.assert_flagged(self.ledger, "user-autonomy", "anthropic")

    # -- Defect 1: a row-level DISCLOSED entry must not shelter a
    # substantive rewrite, only a genuinely punctuation-only one.

    def test_disclosed_row_shelters_punctuation_only_role_edit(self):
        # animal-welfare-impacts/anthropic really does have punctuation-only
        # role divergences against the artifact (trailing periods trimmed
        # during transcription) -- the committed ledger already carries
        # some. Confirm the row-level disclosure still passes those.
        problems, disclosed = gen.diff_ledger(self.ledger)
        self.assertFalse(problems, problems)
        self.assertTrue(
            any(s == "animal-welfare-impacts" and la == "anthropic" and f == "role"
                for s, la, _, f in disclosed),
            "expected the known punctuation-only role disclosures to be present",
        )

    def test_substantive_role_rewrite_under_disclosed_row_fails_named(self):
        row = find_row(self.ledger, "animal-welfare-impacts", "anthropic")
        row["citations"][0]["role"] = (
            "This role has been rewritten with unrelated content, "
            "not punctuation cleanup."
        )
        self.assert_flagged(self.ledger, "animal-welfare-impacts", "anthropic")

    def test_substantive_role_rewrite_second_disclosed_row_fails_named(self):
        row = find_row(self.ledger, "animal-welfare-impacts", "openai")
        row["citations"][0]["role"] = "also totally unrelated content"
        self.assert_flagged(self.ledger, "animal-welfare-impacts", "openai")

    # -- Defect 2: --check must verify it examined every expected row.

    def test_dropped_row_fails_and_names_every_missing_pair(self):
        ledger = copy.deepcopy(self.ledger)
        ledger["coverage"] = ledger["coverage"][:3]
        problems, _ = gen.diff_ledger(ledger)
        self.assertTrue(problems)
        missing = gen.missing_coverage(ledger)
        self.assertEqual(len(missing), 20 - 3)
        for slug, lab in missing:
            self.assertTrue(
                any(p.startswith(f"{slug}/{lab}:") for p in problems),
                f"missing pair {slug}/{lab} not named in problems",
            )

    def test_single_dropped_row_is_named(self):
        ledger = copy.deepcopy(self.ledger)
        dropped = ledger["coverage"].pop()
        behaviours = {b["id"]: b for b in ledger["behaviours"]}
        slug = behaviours[dropped["behaviour_id"]]["slug"]
        lab = dropped["lab_id"]
        problems, _ = gen.diff_ledger(ledger)
        self.assertTrue(any(p.startswith(f"{slug}/{lab}:") for p in problems))


class ArtifactForTest(unittest.TestCase):
    """Defect 4: artifact_for() must match the directory's slug segment
    exactly (numeric prefix stripped), not via substring search."""

    def test_unknown_slug_fails_loudly(self):
        with self.assertRaises(SystemExit):
            gen.artifact_for("not-a-real-behaviour-slug")

    def test_known_slugs_resolve_uniquely(self):
        ledger = load_ledger()
        for b in ledger["behaviours"]:
            path = gen.artifact_for(b["slug"])
            self.assertTrue(path.is_file(), f"{b['slug']} -> {path} does not exist")


if __name__ == "__main__":
    unittest.main(verbosity=2)
