"""Gate tests for the band keep-set payload (behaviours-v5-reader.json).

The keep-set is the committed v5 panel run pre-filtered to the panel's band
boundary: site/spec-reader/data/behaviours-v5-reader.json, built by
engine/panel/build_site_data.py with --threshold=4 --solid-threshold=6 from
runlog-v5.jsonl (the two overrides are the 3-judge band boundary:
relatedCut = j+1 = 4, coreCut = 2j = 6). The reader renders nothing below that
cut, so the keep-set is exactly what it can show: engine/verify-reader-test.mjs
uses it as the passage-count oracle, and ?data=behaviours-v5-reader loads it.

Three nets here:

1. Structural invariants on the committed payload -- the citation count (363,
   not the unfiltered 3,630 and not the retired adria ledger's 294), every
   passage over the score cut with the votes guard, adjacent == (score < 6),
   and no role fraction above its denominator.
2. Every stored quote re-resolves byte-for-byte through cite.py -- the same
   net data/coverage.json gets in tests/test_coverage_json.py.
3. A golden rebuild: the builder with the same overrides reproduces the
   committed payload byte-for-byte -- it emits the same render-form role
   fractions site/spec-reader/app.js applies at render. A silent change
   in either cut shows up as a diff here.

Band LABELS (adjacent vs the band the panel view renders) need the real
tierBand arithmetic; engine/panel/test_reader_v5_labels.js extracts tierBand
from app.js and checks every passage against it, driven from here.

Run:  python3 -m unittest tests.test_reader_v5_payload
"""

import contextlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "site" / "spec-reader" / "data" / "behaviours-v5-reader.json"
BUILDER = ROOT / "engine" / "panel" / "build_site_data.py"
LABELS_HARNESS = ROOT / "engine" / "panel" / "test_reader_v5_labels.js"

EXPECTED_CITATIONS = 363
EXPECTED_BEHAVIOURS = 10

# Under #68's per-passage cuts these three ragged 2-judge passages score 4/6,
# which is core on their own scale (coreCut = 2j = 4) but labelled adjacent by
# the flat solid cut of 6. Accepted and enumerated rather than tolerated; any
# other exception must fail.
# Mirrored verbatim in engine/panel/test_reader_v5_labels.js (which asserts
# them); kept here so the accepted set is visible beside the payload tests.
# The payload's locators use the ">" separator.
KNOWN_LABEL_EXCEPTIONS = {
    "constitution@2026-01-20 > Being helpful > What constitutes genuine helpfulness > \u00b69",
    "constitution@2026-01-20 > Overview > Claude\u2019s core values > \u00b67",
    "model-spec@2025-12-18 > #overview > \u00b66",
}

from tests.test_coverage_json import resolve_in_process  # noqa: E402


def load_payload():
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def all_passages(payload):
    for behaviour in payload["behaviours"]:
        for lab, cell in behaviour["coverage"].items():
            for passage in cell.get("passages", []):
                yield behaviour, lab, passage


class StructuralInvariantsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.payload = load_payload()

    def test_citation_and_behaviour_counts(self):
        self.assertEqual(len(self.payload["behaviours"]), EXPECTED_BEHAVIOURS)
        citations = list(all_passages(self.payload))
        # 363, not 3,630 (unfiltered) and not 294 (the retired adria bench):
        # the two wrong values mean the filter was skipped or the wrong source
        # was transcribed.
        self.assertEqual(len(citations), EXPECTED_CITATIONS)

    def test_every_passage_is_over_the_cut_with_the_votes_guard(self):
        for behaviour, lab, passage in all_passages(self.payload):
            votes = len(passage["verdicts"])
            with self.subTest(locator=passage["locator"]):
                self.assertGreaterEqual(passage["score"], 4)
                self.assertGreaterEqual(votes, 2)

    def test_adjacent_matches_the_solid_cut(self):
        for behaviour, lab, passage in all_passages(self.payload):
            with self.subTest(locator=passage["locator"]):
                self.assertEqual(passage["adjacent"], passage["score"] < 6)

    def test_no_role_fraction_above_its_denominator(self):
        for behaviour, lab, passage in all_passages(self.payload):
            match = re.search(r"\(score (\d+)/(\d+)\)", passage["role"])
            with self.subTest(locator=passage["locator"]):
                self.assertIsNotNone(
                    match, f"no score fraction in role: {passage['role'][:60]}")
                self.assertLessEqual(
                    int(match.group(1)), int(match.group(2)),
                    f"impossible fraction {match.group(0)}",
                )


class QuoteResolutionTest(unittest.TestCase):
    """Every stored quote re-resolves byte-for-byte (in-process, one spec load
    per spec, as in tests/test_coverage_json.py)."""

    def test_every_quote_re_resolves(self):
        payload = load_payload()
        specs_cache = {}
        for behaviour, lab, passage in all_passages(payload):
            locator = passage["locator"]
            with self.subTest(locator=locator):
                try:
                    resolved = resolve_in_process(specs_cache, locator)
                except SystemExit as e:
                    self.fail(f"locator failed to resolve: {e}")
                # Mirror the builder's citation_quote: a fenced example block
                # stores the caption before the fence; otherwise strip the
                # bold markers mid-word bold would break anchor matching.
                if "~~~" in resolved:
                    expected = resolved.split("~~~")[0].strip().replace("**", "")
                    self.assertTrue(passage.get("exampleBlock"),
                                    f"{locator}: fence without exampleBlock flag")
                else:
                    expected = resolved.replace("**", "")
                    self.assertFalse(passage.get("exampleBlock"),
                                     f"{locator}: exampleBlock without fence")
                self.assertEqual(
                    passage["quote"], expected,
                    f"{behaviour['slug']} ({lab}): stored quote does not match "
                    "resolver output",
                )


class GoldenRebuildTest(unittest.TestCase):
    """The builder with the same overrides reproduces the committed payload
    byte-for-byte, once role fractions carry the cell's true maximum (the rule
    app.js applies at render). A silent change in either cut surfaces here."""

    def test_rebuild_reproduces_the_committed_payload(self):
        sp = importlib.util.spec_from_file_location("builder_under_test", BUILDER)
        bs = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(bs)
        scratch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        (scratch / "site" / "spec-reader" / "data").mkdir(parents=True)
        bs.DATA_DIR = scratch / "site" / "spec-reader" / "data"
        saved = sys.argv
        sys.argv = ["build_site_data.py", "--threshold=4", "--solid-threshold=6",
                    "--run-date=2026-08-17", "--out=behaviours-v5-reader.json"]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                bs.main()
        finally:
            sys.argv = saved
        rebuilt = (scratch / "site" / "spec-reader" / "data" /
                   "behaviours-v5-reader.json").read_bytes()
        # a real byte comparison: the builder emits the render-form role
        # fractions itself, so no test-side transformation is needed
        self.assertEqual(
            rebuilt, PAYLOAD.read_bytes(),
            "rebuilt bench payload diverges from the committed file",
        )


class BandLabelsHarnessTest(unittest.TestCase):
    """Drives engine/panel/test_reader_v5_labels.js: tierBand extracted from
    app.js, checked against every committed passage."""

    def test_labels_match_the_panel_band(self):
        result = subprocess.run(
            ["node", str(LABELS_HARNESS)], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
