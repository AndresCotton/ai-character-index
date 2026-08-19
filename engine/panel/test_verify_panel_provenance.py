#!/usr/bin/env python3
"""Tests for verify_panel_provenance.py -- the shipped-payload provenance check.

Guards: a fresh clone must be able to prove the shipped panel payload
reproduces from the committed runlog (Decision 3). The green-path tests run a
real rebuild from engine/panel/runlog-v3.jsonl (~seconds each, not sub-second
like test_panel.py); tamper tests reuse one class-level rebuild. No network,
no keys.

Run:  python3 engine/panel/test_verify_panel_provenance.py   (or pytest)
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v = load("verify_panel_provenance")


def quietly(fn, *args, **kwargs):
    """Run fn capturing stdout; return (result, captured)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


class TestEndToEnd(unittest.TestCase):
    """The committed log must reproduce the committed payload."""

    def test_committed_state_verifies_green(self):
        rc, out = quietly(v.verify, verbose=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS", out)
        self.assertIn("byte-identical after splicing the shipped runDate", out)

    def test_cli_defaults_verify_green(self):
        rc, out = quietly(v.main, [])
        self.assertEqual(rc, 0, out)

    def test_missing_runlog_fails_loudly(self):
        missing = HERE / "no-such-runlog.jsonl"
        rc, out = quietly(v.verify, runlog=missing, verbose=True)
        self.assertEqual(rc, 2)
        self.assertIn("FAIL", out)
        self.assertIn(str(missing), out)

    def test_missing_payload_fails_loudly(self):
        missing = HERE / "no-such-payload.json"
        rc, out = quietly(v.verify, payload=missing, verbose=True)
        self.assertEqual(rc, 2)
        self.assertIn("FAIL", out)
        self.assertIn(str(missing), out)

    def test_log_without_matching_rubric_fails_loudly(self):
        # a v2-only log cannot be the source of a v3w payload -- refuse, don't rebuild
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"behaviour": "helpfulness", "spec": "constitution",
                                "model": "sol", "locator": "x", "verdict": 2,
                                "parsed": True, "rubric": "v2"}) + "\n")
            wrong = Path(f.name)
        self.addCleanup(wrong.unlink, missing_ok=True)
        rc, out = quietly(v.verify, runlog=wrong, verbose=True)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)
        self.assertIn("no rubric=", out)


class TestBuilderCrashPath(unittest.TestCase):
    """Any BaseException raised inside the builder's main() must be reported as
    FAIL + exit 1 -- never an unhandled traceback, and never a re-raised
    SystemExit carrying the builder's own exit code."""

    def assert_crash_reported(self, rc, out, err, exc_name):
        self.assertEqual(rc, 1, out + err)
        self.assertIn("FAIL", out)
        self.assertIn("crashed", out)
        self.assertIn(exc_name, out)
        self.assertNotIn("Traceback", err)

    def test_builder_exception_reports_fail_not_traceback(self):
        # Crafted input through the script's own override path: a row that
        # passes runlog_facts (model/behaviour/spec present, so the script's
        # zero-row guard lets it through) but omits "locator" -- a key only
        # build_site_data.py touches. The builder KeyErrors on the row.
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"behaviour": "helpfulness", "spec": "constitution",
                                "model": "sol", "verdict": 2,
                                "parsed": True, "rubric": "v3w"}) + "\n")
            crashy = Path(f.name)
        self.addCleanup(crashy.unlink, missing_ok=True)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = v.verify(runlog=crashy, verbose=True)
        self.assert_crash_reported(rc, out.getvalue(), err.getvalue(), "KeyError")

    def test_builder_systemexit_reports_fail_not_traceback(self):
        # SystemExit is a BaseException, not an Exception -- exactly the class
        # the old `except Exception` wrapper re-raised unreported. Spoof the
        # builder load so its main() exits; no real rebuild needed.
        class StubBuilder:
            ROOT = None
            @staticmethod
            def main():
                raise SystemExit(2)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(v, "_load", lambda name, path: StubBuilder):
            rc = v.verify(verbose=True)
        self.assert_crash_reported(rc, out.getvalue(), err.getvalue(), "SystemExit")


class TestRunlogFacts(unittest.TestCase):
    """Tripwires on the canonical log's identity (it is frozen data; if these
    fail, the log changed -- runlog-v3.md must change with it, deliberately)."""

    def test_canonical_log_identity(self):
        facts = v.runlog_facts(v.DEFAULT_RUNLOG, v.DEFAULT_RUBRIC)
        self.assertEqual(facts["rows_total"], 10298)
        self.assertEqual(facts["rows_rubric"], 9415)
        self.assertEqual(facts["parsed_false"], 0)
        self.assertEqual(set(facts["models"]), {"sol", "fable", "kimi", "opus", "kimi-k2"})
        self.assertEqual(set(facts["behaviours"]),
                         {"helpfulness", "third-party-harm", "over-under-caution"})
        # full sha256 recorded in engine/panel/runlog-v3.md -- any byte-level
        # alteration of the frozen log trips here, via the documented hash
        sha = hashlib.sha256(v.DEFAULT_RUNLOG.read_bytes()).hexdigest()
        self.assertEqual(sha, "971f16c7459a16e9a52a7ea4a0e87c5c1db1c1f45e8b69b5ae80af6b58f85740")

    def test_zero_matching_rows_detected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"behaviour": "b", "spec": "constitution", "model": "sol",
                                "locator": "x", "verdict": 1, "parsed": True,
                                "rubric": "v2"}) + "\n")
            p = Path(f.name)
        self.addCleanup(p.unlink, missing_ok=True)
        facts = v.runlog_facts(p, "v3w")
        self.assertEqual(facts["rows_total"], 1)
        self.assertEqual(facts["rows_rubric"], 0)


class TestTamperDetection(unittest.TestCase):
    """A corrupted/tampered payload must fail the check. One shared rebuild
    feeds all cases so the suite pays the rebuild cost once."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="panel-provenance-test-")
        cls.addClassCleanup(cls._tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):   # silence the builder's summary line
            cls.rebuilt_path = v.rebuild(v.DEFAULT_RUNLOG, v.DEFAULT_RUBRIC,
                                         v.DEFAULT_PANEL, Path(cls._tmp.name))
        cls.rebuilt_raw = cls.rebuilt_path.read_bytes()
        cls.shipped_raw = v.DEFAULT_PAYLOAD.read_bytes()
        cls.shipped_doc = json.loads(cls.shipped_raw)
        cls.facts = v.runlog_facts(v.DEFAULT_RUNLOG, v.DEFAULT_RUBRIC)
        cls.config = json.loads((v.HERE / "panel-config.json").read_text())

    def check(self, shipped_raw):
        return v.compare(shipped_raw, self.rebuilt_raw, v.DEFAULT_RUBRIC,
                         v.DEFAULT_PANEL, self.facts, self.config)

    def tampered(self, mutate):
        doc = json.loads(self.shipped_raw)
        mutate(doc)
        return v.serialize(doc).encode("utf-8")

    def test_tampered_score_fails(self):
        def bump_score(doc):
            doc["behaviours"][0]["coverage"]["anthropic"]["passages"][0]["score"] = 99
        rc, lines = self.check(self.tampered(bump_score))
        self.assertEqual(rc, 1)
        self.assertTrue(any("$.behaviours[0].coverage.anthropic.passages[0].score" in l
                            for l in lines), lines)

    def test_tampered_verdict_fails(self):
        def flip_verdict(doc):
            p = doc["behaviours"][0]["coverage"]["anthropic"]["passages"][0]
            first_judge = next(iter(p["verdicts"]))
            p["verdicts"][first_judge] = 0
        rc, lines = self.check(self.tampered(flip_verdict))
        self.assertEqual(rc, 1)
        self.assertTrue(any("verdicts" in l for l in lines), lines)

    def test_removed_citation_fails(self):
        def drop_one(doc):
            doc["behaviours"][0]["coverage"]["anthropic"]["passages"].pop()
        rc, lines = self.check(self.tampered(drop_one))
        self.assertEqual(rc, 1)
        self.assertTrue(any("list length" in l for l in lines), lines)

    def test_tampered_rubric_provenance_fails(self):
        def wrong_rubric(doc):
            doc["provenance"]["rubric"] = "v2"
        rc, lines = self.check(self.tampered(wrong_rubric))
        self.assertEqual(rc, 1)
        self.assertTrue(any("provenance.rubric" in l for l in lines), lines)

    def test_invalid_json_payload_fails(self):
        rc, lines = self.check(b"{not json")
        self.assertEqual(rc, 1)
        self.assertTrue(any("not valid JSON" in l for l in lines), lines)

    def test_runDate_is_the_only_allowance(self):
        # splicing the shipped runDate into the rebuild must compare clean --
        # i.e. the allowance is exactly provenance.runDate and nothing else
        doc = json.loads(self.rebuilt_raw)
        doc["provenance"]["runDate"] = self.shipped_doc["provenance"]["runDate"]
        rc, lines = self.check(v.serialize(doc).encode("utf-8"))
        self.assertEqual(rc, 0, lines)


if __name__ == "__main__":
    unittest.main(verbosity=2)
