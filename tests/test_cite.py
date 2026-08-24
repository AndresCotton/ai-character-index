"""Regression tests for cite.py (engine/spec-cite/cite.py) -- goldens + units.

Golden masters (see dump_goldens.py for what each family pins and why):

- corpus: outline + show + resolve for every section of both pinned specs.
  Any behavioural change in section parsing, block segmentation, sentence
  splitting, or locator resolution turns up here, including in sections no
  published citation touches.
- find: `cite.py find` for a fixed query set -- match_normalize folding and
  cmd_find's sentence-span arithmetic, which the corpus commands never touch.

Unit tests pin the rules CITATION.md states explicitly -- the mechanical
normalizations, the sentence-split conventions, the locator grammar -- at the
function level, where a golden diff would only say "something changed"
without saying which rule broke. Plus one corpus-wide invariant: every
published quote in data/coverage.json must remain findable under
match_normalize folding, the property `find` and the term sweep depend on.
"""

import difflib
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dump_goldens as dump  # noqa: E402
import cite  # noqa: E402  (importable: dump_goldens put engine/spec-cite on sys.path)

ROOT = dump.ROOT
DIFF_LINES = 60


class GoldenSnapshotTest(unittest.TestCase):
    def assert_golden(self, golden_name, current, family):
        golden = (dump.GOLDEN / golden_name).read_text(encoding="utf-8")
        if current == golden:
            return
        diff = "\n".join(
            list(
                difflib.unified_diff(
                    golden.splitlines(),
                    current.splitlines(),
                    f"golden/{golden_name}",
                    "current",
                    lineterm="",
                )
            )[:DIFF_LINES]
        )
        self.fail(
            f"cite.py {family} snapshot changed. If the change is "
            "intentional, regenerate with `python3 tests/dump_goldens.py "
            f"--write {family}` and review the diff.\n{diff}"
        )

    def test_corpus_snapshot_is_unchanged(self):
        """The corpus dumps are pinned by digest, not by committed text.

        They were ~800 KB of checked-in output whose only job was to make a
        failure readable. The dump is byte-deterministic from the pinned spec
        copies -- `dump_goldens.py --write corpus` reproduces them exactly --
        so the readable diff is still one command away, and the repository no
        longer carries the text to get it. cite-find.txt stays committed as
        text: it is small, and its diffs are the interpretable ones.
        """
        digests = json.loads(
            (dump.GOLDEN / "corpus-sha256.json").read_text(encoding="utf-8")
        )["goldens"]
        for spec in dump.SPECS:
            with self.subTest(spec=spec):
                name = f"cite-corpus-{spec}.txt"
                self.assertIn(name, digests, f"{name} missing from corpus-sha256.json")
                current = dump.dump_spec(spec)
                actual = hashlib.sha256(current.encode("utf-8")).hexdigest()
                if actual == digests[name]["sha256"]:
                    continue
                self.fail(
                    f"cite.py corpus snapshot changed for {spec}.\n"
                    f"  expected sha256 {digests[name]['sha256']}\n"
                    f"  actual   sha256 {actual}\n"
                    f"  expected {digests[name]['bytes']} bytes, "
                    f"got {len(current.encode('utf-8'))}\n"
                    "To see WHAT changed: the dump is deterministic from the\n"
                    "pinned spec copies, so the old output is reproducible from\n"
                    "the old code. Regenerate on each side and diff them:\n"
                    "  python3 tests/dump_goldens.py --write corpus\n"
                    "  cp tests/golden/cite-corpus-*.txt /tmp/new/\n"
                    "  git stash && python3 tests/dump_goldens.py --write corpus\n"
                    "  diff -u tests/golden/cite-corpus-constitution.txt "
                    "/tmp/new/cite-corpus-constitution.txt; git stash pop\n"
                    "If the change is intentional, update the digest in "
                    "tests/golden/corpus-sha256.json (dump_goldens.py --write "
                    "corpus rewrites it)."
                )

    def test_find_snapshot_is_unchanged(self):
        self.assert_golden("cite-find.txt", dump.dump_find(), "find")


class NormalizeTest(unittest.TestCase):
    def test_footnote_markers_dropped(self):
        self.assertEqual(cite.normalize("Claude[^12] behaves."), "Claude behaves.")

    def test_xref_link_keeps_anchor(self):
        self.assertEqual(cite.normalize("see [?](#the-anchor) here"), "see #the-anchor here")

    def test_markdown_link_keeps_text(self):
        self.assertEqual(cite.normalize("see [the spec](https://x.y) here"), "see the spec here")

    def test_leading_list_marker_dropped(self):
        self.assertEqual(cite.normalize("- item text"), "item text")
        self.assertEqual(cite.normalize("3. item text"), "item text")

    def test_whitespace_collapsed(self):
        self.assertEqual(cite.normalize("a\n  b\t c"), "a b c")


class MatchNormalizeTest(unittest.TestCase):
    def test_curly_quotes_fold_to_straight(self):
        self.assertEqual(cite.match_normalize("‘a’ “b”"), "'a' \"b\"")

    def test_dashes_and_ellipsis_fold(self):
        # em/en dashes and ellipsis fold, then dash runs collapse to one.
        self.assertEqual(cite.match_normalize("a—b c–d e…"), "a-b c-d e...")

    def test_ascii_dash_runs_collapse(self):
        self.assertEqual(cite.match_normalize("a -- b --- c"), "a - b - c")

    def test_folding_makes_typographic_and_ascii_equal(self):
        self.assertEqual(
            cite.match_normalize("Claude’s “values” — stated"),
            cite.match_normalize("Claude's \"values\" -- stated"),
        )


class SplitSentencesTest(unittest.TestCase):
    def test_plain_split(self):
        self.assertEqual(
            cite.split_sentences("One is here. Two is here."),
            ["One is here.", "Two is here."],
        )

    def test_abbreviation_does_not_split(self):
        self.assertEqual(
            cite.split_sentences("Cases like e.g. this one stay whole."),
            ["Cases like e.g. this one stay whole."],
        )

    def test_lowercase_continuation_does_not_split(self):
        self.assertEqual(
            cite.split_sentences("It stops. then resumes."),
            ["It stops. then resumes."],
        )

    def test_closing_quote_stays_with_sentence(self):
        self.assertEqual(
            cite.split_sentences('He said "stop." Then left.'),
            ['He said "stop."', "Then left."],
        )

    def test_split_before_digit(self):
        self.assertEqual(
            cite.split_sentences("See above. 3 cases follow."),
            ["See above.", "3 cases follow."],
        )

    def test_terminal_punctuation_variants(self):
        self.assertEqual(
            cite.split_sentences("Really? Yes! Fine."),
            ["Really?", "Yes!", "Fine."],
        )


class ParseLocatorTest(unittest.TestCase):
    def test_full_locator(self):
        self.assertEqual(
            cite.parse_locator("model-spec@2025-09-17 > #the-anchor > ¶3 s2"),
            ("model-spec", "2025-09-17", "#the-anchor", (3, 2, 3, 2)),
        )

    def test_version_defaults_to_none(self):
        spec, version, ref, span = cite.parse_locator("constitution > Overview")
        self.assertEqual((spec, version, ref, span), ("constitution", None, "Overview", None))

    def test_ascii_p_equals_pilcrow(self):
        self.assertEqual(
            cite.parse_locator("constitution > A > p2")[3],
            cite.parse_locator("constitution > A > ¶2")[3],
        )

    def test_sentence_range_same_block(self):
        self.assertEqual(
            cite.parse_locator("constitution > A > ¶2 s1-3")[3], (2, 1, 2, 3)
        )

    def test_cross_block_range(self):
        self.assertEqual(
            cite.parse_locator("constitution > A > ¶2 s3-¶4 s1")[3], (2, 3, 4, 1)
        )

    def test_block_only_span(self):
        self.assertEqual(
            cite.parse_locator("constitution > A > ¶5")[3], (5, None, 5, None)
        )

    def test_nested_section_ref_rejoined(self):
        self.assertEqual(
            cite.parse_locator("constitution > A > B > ¶1")[2], "A > B"
        )


class PublishedQuotesFindableTest(unittest.TestCase):
    """Invariant `find` and the term sweep rely on: folding never loses a
    published quote. Each locator is checked against the spec version it
    pins (parse_locator + load_spec(spec, version), cached per
    (spec, version)), so a spec-mirror update cannot false-fail the test.
    Runs in-process (no subprocess per citation) so the whole corpus stays
    cheap."""

    def test_every_published_quote_survives_folding(self):
        coverage = json.loads((ROOT / "data" / "coverage.json").read_text(encoding="utf-8"))
        specs = {}
        misses = []
        for behaviour in coverage["coverage"]:
            for citation in behaviour.get("citations", []):
                spec, version, _, _ = cite.parse_locator(citation["locator"])
                key = (spec, version)
                if key not in specs:
                    _, _, lines = cite.load_spec(spec, version)
                    specs[key] = cite.match_normalize("\n".join(lines))
                needle = cite.match_normalize(citation["quote"])
                if needle not in specs[key]:
                    misses.append(citation["locator"])
        self.assertEqual(misses, [], f"quotes no longer findable after folding: {misses}")


if __name__ == "__main__":
    unittest.main()
