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

    def test_verify_is_read_only(self):
        # verify() must never mutate the shipped payload or the frozen log:
        # hash both before and after a green run.
        def digest(path):
            return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        payload, runlog = v.DEFAULT_PAYLOAD, v.DEFAULT_RUNLOG
        before = (digest(payload), digest(runlog))
        rc, out = quietly(v.verify)
        self.assertEqual(rc, 0, out)
        self.assertEqual((digest(payload), digest(runlog)), before,
                         "verify() modified the shipped payload or the frozen runlog")

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

    def test_shipped_payload_blob_hash_tripwire(self):
        # Fast byte-identity tripwire for the committed payload (no rebuild needed).
        # The shipped behaviours.json was once accidentally rebuilt in a worktree during
        # assembly (provenance.runDate re-stamped) and had to be restored byte-identical;
        # any rebuild or byte-level tamper of the committed file trips here. If a change
        # is deliberate, update this hash AND the runlog-v5.md / runDate record together.
        # Hash updated 2026-08-24: role fractions now carry the cell's true maximum
        # (score N/9 on v5 cells, was the impossible N/6); runDate unchanged (2026-08-17).
        sha = hashlib.sha256(v.DEFAULT_PAYLOAD.read_bytes()).hexdigest()
        self.assertEqual(
            sha, "f20879b019b8461be8c1fe47e6e7605259371b3dc1810d12470817c434ff1ef5",
            "committed site/spec-reader/data/behaviours.json changed bytes")

    def test_unreadable_panel_config_fails_not_traceback(self):
        # the panel-config.json read must honor the FAIL-not-traceback contract (rc 2),
        # same as the runlog/payload reads. Point HERE at a dir with a broken config;
        # verify() reaches the config read (real runlog/payload pass the earlier gates)
        # and must return 2, not raise.
        real_here = v.HERE
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "panel-config.json").write_text("{not json")
            v.HERE = Path(tmp)
            try:
                rc, out = quietly(v.verify)
            finally:
                v.HERE = real_here
        self.assertEqual(rc, 2)
        self.assertIn("FAIL", out)
        self.assertIn("panel config", out)

    def test_row_missing_consumed_key_fails_rc2_not_traceback(self):
        # a rubric-matching row that lacks a key runlog_facts consumes (here:
        # "model") is a malformed log -- it must hit the same rc-2 FAIL contract
        # as an unreadable/unparseable one, naming the missing key, never a raw
        # KeyError traceback
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"behaviour": "helpfulness", "spec": "constitution",
                                "locator": "x", "verdict": 2,
                                "parsed": True, "rubric": v.DEFAULT_RUBRIC}) + "\n")
            malformed = Path(f.name)
        self.addCleanup(malformed.unlink, missing_ok=True)
        rc, out = quietly(v.verify, runlog=malformed, verbose=True)
        self.assertEqual(rc, 2)
        self.assertIn("FAIL", out)
        self.assertIn("'model'", out)
        self.assertNotIn("Traceback", out)


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
                                "parsed": True, "rubric": v.DEFAULT_RUBRIC}) + "\n")
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

    def test_keyboard_interrupt_propagates_not_swallowed(self):
        # Ctrl-C during the rebuild is NOT a verification failure -- it must propagate,
        # not be swallowed into the FAIL/crash path by the except-BaseException handler.
        class StubBuilder:
            ROOT = None
            @staticmethod
            def main():
                raise KeyboardInterrupt
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(v, "_load", lambda name, path: StubBuilder):
            with self.assertRaises(KeyboardInterrupt):
                v.verify(verbose=True)


class TestRunlogFacts(unittest.TestCase):
    """Tripwires on the canonical log's identity (it is frozen data; if these
    fail, the log changed -- runlog-v5.md must change with it, deliberately)."""

    def test_canonical_log_identity(self):
        facts = v.runlog_facts(v.DEFAULT_RUNLOG, v.DEFAULT_RUBRIC)
        self.assertEqual(facts["rows_total"], 31293)
        self.assertEqual(facts["rows_rubric"], 31293)
        self.assertEqual(facts["parsed_false"], 8)
        # the log also holds the audition rows (glm, deepseek-v4, qwen38-max);
        # build_site_data admits only the frontier_fast seats from it
        self.assertEqual(set(facts["models"]),
                         {"sol", "fable", "deepseek", "glm", "deepseek-v4", "qwen38-max"})
        self.assertEqual(set(facts["behaviours"]),
                         {"helpfulness", "harmlessness-to-the-user",
                          "harm-avoidance-to-third-parties", "proportionate-risk-mitigation",
                          "how-to-approach-tradeoffs", "avoiding-over-and-under-caution",
                          "objectivity-on-contested-questions", "user-autonomy",
                          "animal-welfare-impacts"})
        # full sha256 recorded in engine/panel/runlog-v5.md -- any byte-level
        # alteration of the frozen log trips here, via the documented hash
        sha = hashlib.sha256(v.DEFAULT_RUNLOG.read_bytes()).hexdigest()
        self.assertEqual(sha, "05ba1e1c010e39ac6f8574e208af780e3a5354682e7aa2a39868bb265caffb9c")

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
