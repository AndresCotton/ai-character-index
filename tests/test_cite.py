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

import contextlib
import difflib
import io
import json
import os
import sys
import tempfile
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
        for spec in dump.SPECS:
            with self.subTest(spec=spec):
                self.assert_golden(
                    f"cite-corpus-{spec}.txt", dump.dump_spec(spec), "corpus"
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
    published quote. Runs in-process (no subprocess per citation) so the
    whole corpus stays cheap."""

    def test_every_published_quote_survives_folding(self):
        coverage = json.loads((ROOT / "data" / "coverage.json").read_text(encoding="utf-8"))
        specs = {}
        misses = []
        for behaviour in coverage["coverage"]:
            for citation in behaviour.get("citations", []):
                spec = citation["locator"].split("@")[0].strip()
                if spec not in specs:
                    _, sections, lines = cite.load_spec(spec, None)
                    specs[spec] = cite.match_normalize("\n".join(lines))
                needle = cite.match_normalize(citation["quote"])
                if needle not in specs[spec]:
                    misses.append(citation["locator"])
        self.assertEqual(misses, [], f"quotes no longer findable after folding: {misses}")


class SweepReproductionTest(unittest.TestCase):
    """The §7 done-criterion: `cite.py sweep <terms>` regenerates a behaviour's
    published term-sweep table byte-for-byte. Rather than snapshot the sweep into
    a golden (which would duplicate the counts), this diffs live sweep output
    against the table already embedded in the published artifact -- the single
    source of truth. It fails on either side moving: a sweep regression, or a
    spec-mirror change that leaves the published table stale (re-verify + re-sweep)."""

    def _sweep_table(self, terms_path):
        # table -> stdout, `parsed N terms` echo + warnings -> stderr; pin stdout.
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            cite.cmd_sweep([str(terms_path)])
        return out.getvalue().strip("\n")

    def _published_table(self, artifact_path):
        rows, capturing = [], False
        for line in artifact_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("| Term | constitution hits"):
                capturing = True
            if capturing:
                if not line.startswith("|"):
                    break
                rows.append(line)
        return "\n".join(rows)

    def test_published_tables_reproduce(self):
        terms_files = sorted((ROOT / "research" / "sweeps").glob("*/terms.txt"))
        self.assertTrue(terms_files, "no behaviour terms.txt found to reproduce")
        for terms in terms_files:
            with self.subTest(behaviour=terms.parent.name):
                published = self._published_table(terms.parent / "4-spec-coverage.md")
                self.assertTrue(published, f"no term-sweep table in {terms.parent.name}")
                self.assertEqual(self._sweep_table(terms), published)


class ParseTermsTest(unittest.TestCase):
    """parse_terms(path) -> (terms, warnings). Pins the comment/quote stripping
    and each malformed-line warning the sweep surfaces on stderr."""

    def _parse(self, text):
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            entries, warnings = cite.parse_terms(path)
            return [pat for _, pat in entries], warnings
        finally:
            os.unlink(path)

    def test_label_pattern_split(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("honest*  ::  honest\nlie (bounded) :: \\b(lie|lies)\\b\nplain\n")
            entries, warnings = cite.parse_terms(path)
            self.assertEqual(warnings, [])
            self.assertEqual(
                entries,
                [("honest*", "honest"), ("lie (bounded)", r"\b(lie|lies)\b"), ("plain", "plain")],
            )
        finally:
            os.unlink(path)

    def test_comments_and_blanks_skipped(self):
        terms, warnings = self._parse("# header\n\ncalibrat  # inline note\n\nconfiden\n")
        self.assertEqual(terms, ["calibrat", "confiden"])
        self.assertEqual(warnings, [])

    def test_hash_not_after_space_is_kept(self):
        terms, _ = self._parse("C#\n")
        self.assertEqual(terms, ["C#"])

    def test_surrounding_quotes_stripped(self):
        terms, _ = self._parse('"want to hear"\n')
        self.assertEqual(terms, ["want to hear"])

    def test_intentional_regex_terms_are_clean(self):
        terms, warnings = self._parse(r"\blie" "\n" "deceiv|decept" "\n")
        self.assertEqual(terms, [r"\blie", "deceiv|decept"])
        self.assertEqual(warnings, [])

    def _warns(self, text, needle):
        _, warnings = self._parse(text)
        self.assertTrue(
            any(needle in w for w in warnings),
            f"expected a warning containing {needle!r}, got {warnings}",
        )

    def test_list_marker_warns(self):
        self._warns("- calibrat\n", "list marker")

    def test_unmatched_quote_warns(self):
        self._warns('"calibrat\n', "quote")

    def test_trailing_colon_warns(self):
        self._warns("synonyms:\n", "section header")

    def test_prose_warns(self):
        self._warns("the model should express its uncertainty clearly and often\n", "prose")

    def test_unescaped_metacharacter_warns(self):
        self._warns("honest*\n", "metacharacter")

    def test_bracket_metacharacter_warns(self):
        self._warns("a[bc]\n", "metacharacter")

    def test_duplicate_warns(self):
        self._warns("calibrat\ncalibrat\n", "duplicate")

    def test_curly_quote_in_term_warns(self):
        self._warns("Claude’s values\n", "folded")

    def test_dash_in_term_warns(self):
        self._warns("cost—benefit\n", "folded")

    def test_empty_quoted_term_warns(self):
        self._warns('""\n', "empty term")

    def test_labeled_empty_pattern_warns(self):
        self._warns("mylabel ::\n", "empty term")

    def test_empty_label_warns(self):
        self._warns(":: honest\n", "empty label")


class CompileTermTest(unittest.TestCase):
    def test_plain_word_is_case_insensitive_substring(self):
        p = cite._compile_term("calibrat")
        self.assertTrue(p.search("recalibrated"))   # matches mid-word (substring)
        self.assertTrue(p.search("CALIBRAT"))        # case-insensitive

    def test_word_boundary(self):
        p = cite._compile_term(r"\blie")
        self.assertTrue(p.search("told a lie"))
        self.assertFalse(p.search("i believe you"))  # not inside "believe"

    def test_alternation(self):
        p = cite._compile_term("deceiv|decept")
        self.assertTrue(p.search("deceive"))
        self.assertTrue(p.search("deception"))
        self.assertFalse(p.search("honesty"))

    def test_invalid_regex_exits(self):
        with self.assertRaises(SystemExit):
            cite._compile_term("(unclosed")


class SweepErrorPathTest(unittest.TestCase):
    def _tmp(self, text):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def _run(self, path):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            cite.cmd_sweep([path])

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            self._run("/no/such/dir/terms.txt")

    def test_all_comment_file_exits(self):
        path = self._tmp("# just a comment\n\n")
        try:
            with self.assertRaises(SystemExit):
                self._run(path)
        finally:
            os.unlink(path)

    def test_bad_regex_exits_before_any_table_output(self):
        path = self._tmp("calibrat\n(unclosed\n")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    cite.cmd_sweep([path])
            self.assertEqual(out.getvalue(), "")  # compiled up-front: nothing printed pre-abort
        finally:
            os.unlink(path)


class SweepBlockCountingTest(unittest.TestCase):
    """Independent check of the block-counting unit: a hand-built spec whose counts
    are worked out by hand (not by the tool), so a counting bug can't hide behind a
    self-generated reference table. Routes through the same _fold_blocks/_block_hits
    the sweep uses, and pins block-vs-occurrence, wrap-independence, heading
    exclusion, fenced-example-counts-once, and match_normalize folding."""

    FIXTURE = (
        "# Doc\n"
        "\n"
        "First para says honest and honest twice.\n"     # 1 block, honest x2 -> 1
        "\n"
        "Second para says honest once.\n"                # 1 block, honest x1
        "\n"
        "A wrapped paragraph mentions wrapword here\n"   # one block spanning two source
        "and wrapword again on the second line.\n"       #   lines: wrapword -> 1 block
        "\n"
        "The model shouldn’t deceive anyone.\n"          # curly apostrophe -> folding
        "\n"
        "Third para is about something else.\n"          # no honest
        "\n"
        "## Zzq marker heading\n"                        # heading -> not a block
        "\n"
        "**Example**: xyzzy in the caption\n"            # caption + fence merge into one
        "```\n"                                          #   block: honest x1, xyzzy x2
        "honest and xyzzy inside the fenced example\n"
        "```\n"
    )

    def _count(self, term):
        blocks = cite._fold_blocks(self.FIXTURE.split("\n"))
        return cite._block_hits(cite._compile_term(term), blocks)

    def test_counts_distinct_blocks_not_occurrences(self):
        # honest is in 3 blocks: para 1 (twice -> counts once), para 2, the example block.
        self.assertEqual(self._count("honest"), 3)

    def test_wrapped_paragraph_is_one_block(self):
        # wrapword is on two source lines of one block -> counts once (wrap-independent).
        self.assertEqual(self._count("wrapword"), 1)

    def test_fenced_example_counts_once(self):
        # xyzzy is in the Example caption and the fenced code -- one merged block.
        self.assertEqual(self._count("xyzzy"), 1)

    def test_heading_text_is_not_a_block(self):
        self.assertEqual(self._count("zzq"), 0)

    def test_matching_uses_match_normalize_folding(self):
        # a straight-apostrophe term matches the block's curly apostrophe via folding.
        self.assertEqual(self._count("shouldn't"), 1)


if __name__ == "__main__":
    unittest.main()
