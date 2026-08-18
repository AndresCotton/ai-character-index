"""Gate test: every citation in data/coverage.json re-resolves byte-for-byte.

The publish --check gate (test_publish_check.py) only covers behaviours
with a stage-4 artifact (`4-spec-coverage.md` or its structured sidecar
`4-spec-coverage.json`). This test is the net under that: it re-resolves
every stored locator in data/coverage.json against cite.py and
byte-compares the quote, whether or not the behaviour has any artifact --
the same guarantee PLAN.md promises CI will enforce on every PR, run here
directly against the data.

Resolution runs in-process (cite's own functions, one spec load per spec)
rather than one subprocess per citation: the CLI surface is already pinned
exhaustively by the corpus golden, and per-citation subprocesses would grow
the suite's runtime linearly with every published behaviour.

Mirrors the comparison rule in publish-coverage.py: example blocks store the
caption line, i.e. the first line of resolver output.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data" / "coverage.json"

sys.path.insert(0, str(ROOT / "engine" / "spec-cite"))
import cite  # noqa: E402


def resolve_in_process(specs_cache, locator):
    """cmd_resolve's logic without the subprocess. Returns the resolved text.

    cite.py's internals report errors via sys.exit; translate that into a
    test failure with the message instead of aborting the run.
    """
    spec, version, ref, span = cite.parse_locator(locator)
    key = (spec, version)
    if key not in specs_cache:
        specs_cache[key] = cite.load_spec(spec, version)
    _, sections, lines = specs_cache[key]
    sec = cite.find_section(sections, ref)
    if span is None:
        blocks = cite.section_blocks(sec, lines)
        span = (1, None, len(blocks), None)
    return cite.get_span_text(sec, lines, span)


class CoverageJsonResolutionTest(unittest.TestCase):
    def test_every_published_quote_re_resolves(self):
        data = json.loads(COVERAGE.read_text(encoding="utf-8"))
        self.assertTrue(data["coverage"], "coverage.json is empty")
        specs_cache = {}
        for record in data["coverage"]:
            for citation in record["citations"]:
                locator = citation["locator"]
                with self.subTest(locator=locator):
                    try:
                        resolved = resolve_in_process(specs_cache, locator)
                    except SystemExit as e:
                        self.fail(f"locator failed to resolve: {e}")
                    expected = (
                        resolved.splitlines()[0]
                        if citation.get("example_block")
                        else resolved
                    )
                    self.assertEqual(
                        citation["quote"], expected,
                        f"behaviour {record['behaviour_id']} "
                        f"({record['lab_id']}): stored quote does not match "
                        f"resolver output",
                    )


if __name__ == "__main__":
    unittest.main()
