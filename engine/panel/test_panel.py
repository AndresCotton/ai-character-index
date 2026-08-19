#!/usr/bin/env python3
"""Unit tests for the panel pipeline's pure logic. No network, no keys, sub-second.

Each test class names the shipped bug it guards against (all found in review or
the ~2-cent integration run of 2026-07-30). Run:  python3 engine/panel/test_panel.py
"""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


h = load("harness")
rr = load("run_rollout")
wd = load("whole_doc")
bs = load("build_site_data")
sr = load("select_run")


class TestParseVerdicts(unittest.TestCase):
    """Guards the K3/whole-doc parsing failures: truncation, renumbering, noise."""

    def test_ternary_keyed_lines(self):
        out = "\n".join(f"{i}: {v}" for i, v in enumerate([2, 1, 0, 2], 1))
        self.assertEqual(h.parse_verdicts(out, 4), {1: 2, 2: 1, 3: 0, 4: 2})

    def test_out_of_range_indices_dropped(self):
        out = "1: 2\n2: 1\n999: 2\n3: 0\n4: 1"
        v = h.parse_verdicts(out, 4)
        self.assertNotIn(999, v)
        self.assertEqual(len(v), 4)

    def test_truncated_output_reports_missing_not_zeros(self):
        # 374-passage response cut off at 300 lines: the missing 74 must be ABSENT
        # from the dict (unparsed), never silently graded 0.
        out = "\n".join(f"{i}: 1" for i in range(1, 301))
        v = h.parse_verdicts(out, 374)
        self.assertEqual(len(v), 300)
        self.assertNotIn(374, v)

    def test_tail_fallback_requires_exact_count(self):
        # bare digits without "n:" keys, one short of n -- must refuse to guess
        out = "\n".join("2" for _ in range(9))
        self.assertEqual(h.parse_verdicts(out, 10), {})

    def test_reasoning_prose_does_not_shift_alignment(self):
        # in-content reasoning with digits above the verdict block (the K3 style)
        out = "Passage 3 discusses 2 things about 1 topic.\n" + \
              "\n".join(f"{i}: 0" for i in range(1, 41))
        v = h.parse_verdicts(out, 40)
        self.assertEqual(v, {i: 0 for i in range(1, 41)})


class TestBuildPlan(unittest.TestCase):
    """Guards the resume blocker: banked cells must be skipped, rubric-scoped."""

    FIRST = {"constitution": "c@1 > A > ¶1", "model-spec": "m@1 > #a > ¶1"}

    def setUp(self):
        self._runlog = h.RUNLOG
        self.addCleanup(lambda: setattr(h, "RUNLOG", self._runlog))

    def synth_runlog(self, rows):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        for r in rows:
            f.write(json.dumps(r) + "\n")
        f.close()
        self.addCleanup(lambda p=Path(f.name): p.unlink(missing_ok=True))
        return Path(f.name)

    def test_banked_cell_is_resumed(self):
        log = self.synth_runlog([{"behaviour": "b1", "spec": "constitution", "model": "sol",
                                  "locator": self.FIRST["constitution"], "rubric": "v3w"}])
        h.RUNLOG = log
        done = h.done_keys("v3w")
        plan, skipped = rr.build_plan(["b1"], ["constitution"], ["sol", "fable"], done, self.FIRST)
        self.assertEqual(skipped, [("b1", "constitution", "sol")])
        self.assertEqual(plan, [("b1", "constitution", "fable")])

    def test_other_rubric_rows_do_not_satisfy_resume(self):
        # the original bug's cousin: v1/v2 rows must never mark a v3w cell done
        log = self.synth_runlog([{"behaviour": "b1", "spec": "constitution", "model": "sol",
                                  "locator": self.FIRST["constitution"], "rubric": "v2"}])
        h.RUNLOG = log
        plan, skipped = rr.build_plan(["b1"], ["constitution"], ["sol"],
                                      h.done_keys("v3w"), self.FIRST)
        self.assertEqual(skipped, [])
        self.assertEqual(len(plan), 1)

    def test_empty_log_plans_full_grid(self):
        h.RUNLOG = Path("/nonexistent/runlog.jsonl")
        plan, skipped = rr.build_plan(["b1", "b2"], ["constitution", "model-spec"],
                                      ["sol", "fable", "kimi"], h.done_keys("v3w"), self.FIRST)
        self.assertEqual(len(plan), 12)
        self.assertEqual(skipped, [])


class TestEstimate(unittest.TestCase):
    """Estimate must be config-derived so it stays meaningful for ANY configured
    model (a hardcoded table crashed on new tags and guessed 10 cents)."""

    MODELS = {"pricey": {"price_per_mtok": [10.0, 50.0], "max_output": 32768},
              "cheap": {"price_per_mtok": [0.1, 0.3], "max_output": 8192}}
    TOK = {"constitution": 45000}
    NP = {"constitution": 374}

    def test_any_configured_model_gets_a_real_estimate(self):
        low, high = rr.estimate([("b", "constitution", "pricey")], self.TOK, self.NP, self.MODELS)
        self.assertAlmostEqual(low, 45000/1e6*10 + 374*rr.OUT_TOKENS_PER_PASSAGE/1e6*50, places=4)
        self.assertAlmostEqual(high, 45000/1e6*10 + 32768/1e6*50, places=4)
        self.assertLess(low, high)

    def test_price_ordering_follows_config(self):
        lo_c, hi_c = rr.estimate([("b", "constitution", "cheap")], self.TOK, self.NP, self.MODELS)
        lo_p, hi_p = rr.estimate([("b", "constitution", "pricey")], self.TOK, self.NP, self.MODELS)
        self.assertLess(hi_c, lo_p)


class TestJudgeKwargs(unittest.TestCase):
    """Guards the hardcoded-65k-cap crash and the provider param quirks."""

    CONFIG = {"models": {
        "kimi": {"max_output": 65536}, "qwen-big": {"max_output": 16384},
        "sol": {}, "fable": {}, "opus": {}, "mystery": {}}}

    def test_cap_comes_from_config(self):
        self.assertEqual(wd.judge_kwargs("kimi", "moonshotai/Kimi-K3", self.CONFIG)["max_tokens"], 65536)
        self.assertEqual(wd.judge_kwargs("qwen-big", "Qwen/Qwen3-235B", self.CONFIG)["max_tokens"], 16384)

    def test_unconfigured_model_gets_sane_default_not_65k(self):
        self.assertEqual(wd.judge_kwargs("mystery", "some/other-model", self.CONFIG)["max_tokens"], 32768)

    def test_anthropic_models_never_send_temperature(self):
        for model in ("claude-fable-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"):
            self.assertNotIn("temperature", wd.judge_kwargs("x", model, {"models": {"x": {}}}))

    def test_gpt5_uses_completion_tokens_and_effort(self):
        k = wd.judge_kwargs("sol", "gpt-5.6-sol", self.CONFIG)
        self.assertIn("max_completion_tokens", k)
        self.assertEqual(k["reasoning_effort"], "low")
        self.assertNotIn("temperature", k)

    def test_gpt5_quirks_survive_openrouter_prefix(self):
        # fallback-routed ids carry a vendor prefix (openai/gpt-5); quirks must still apply
        k = wd.judge_kwargs("sol", "openai/gpt-5.6-sol", self.CONFIG)
        self.assertIn("max_completion_tokens", k)
        self.assertNotIn("temperature", k)


class TestResolve(unittest.TestCase):
    """Guards the OpenRouter fallback (ported from experiment/panel-judges): native
    keys stay preferred, and no key at all must never silently reroute."""

    def fake_env(self, present):
        real = h.env
        h.env = lambda name: "sk-test" if name in present else None
        self.addCleanup(lambda: setattr(h, "env", real))

    def test_native_key_wins_even_with_openrouter_key(self):
        self.fake_env({"TOGETHER_API_KEY", "OPENROUTER_API_KEY"})
        self.assertEqual(h.resolve("kimi"), ("together", "moonshotai/Kimi-K3"))

    def test_missing_native_key_falls_back_to_mirror(self):
        self.fake_env({"OPENROUTER_API_KEY"})
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(h.resolve("kimi"), ("openrouter", "moonshotai/kimi-k3"))

    def test_no_openrouter_key_keeps_native_route(self):
        # client_for() then exits naming the missing native key -- the right error
        self.fake_env(set())
        self.assertEqual(h.resolve("kimi"), ("together", "moonshotai/Kimi-K3"))

    def test_native_openrouter_model_unchanged(self):
        self.fake_env({"OPENROUTER_API_KEY"})
        self.assertEqual(h.resolve("qwen-max"), ("openrouter", "qwen/qwen3.7-max"))


class TestBuilderGuards(unittest.TestCase):
    """Guards the 0-citations bug: the stray-vote guard must scale with panel size."""

    def test_single_judge_panel_keeps_its_votes(self):
        self.assertTrue(bs.keeps_citation(score=2, n_votes=1, panel_size=1))

    def test_lone_stray_vote_in_full_panel_dropped(self):
        self.assertFalse(bs.keeps_citation(score=2, n_votes=1, panel_size=3))

    def test_zero_score_dropped_regardless(self):
        self.assertFalse(bs.keeps_citation(score=0, n_votes=3, panel_size=3))

    def test_two_of_three_votes_kept(self):
        self.assertTrue(bs.keeps_citation(score=1, n_votes=2, panel_size=3))


class TestCleanQuote(unittest.TestCase):
    """Guards the constitution mid-word-bold anchor break (conten**t)."""

    def test_midword_bold_stripped(self):
        self.assertEqual(bs.clean_quote("**Information and educational conten**t: x"),
                         "Information and educational content: x")


class TestCitationQuote(unittest.TestCase):
    """Guards the 20-anchor demo failure: fenced examples render as code the
    matcher cannot see; quote must be the caption line + exampleBlock flag."""

    def test_example_block_quotes_caption_only(self):
        t = "**Example**: shoplifting deterrence tips ~~~xml <user> x </user> ~~~"
        q, ex = bs.citation_quote(t)
        self.assertEqual(q, "Example: shoplifting deterrence tips")
        self.assertTrue(ex)

    def test_fence_leading_passage_falls_back_to_full_text(self):
        q, ex = bs.citation_quote("~~~xml <user> no caption here </user> ~~~")
        self.assertTrue(q)          # never an empty quote (it would anchor wrongly)
        self.assertFalse(ex)

    def test_plain_passage_unchanged(self):
        q, ex = bs.citation_quote("An ordinary paragraph.")
        self.assertEqual(q, "An ordinary paragraph.")
        self.assertFalse(ex)


class TestRunTimestamp(unittest.TestCase):
    """Run filenames must be URL-safe and sort lexicographically == chronologically."""

    def test_shape_is_hyphen_separated(self):
        from datetime import datetime
        self.assertEqual(bs.run_timestamp(datetime(2026, 8, 18, 9, 5, 3)),
                         "2026-08-18T09-05-03")

    def test_lexicographic_order_is_chronological_across_year_boundary(self):
        from datetime import datetime, timedelta
        stamps = [bs.run_timestamp(datetime(2026, 12, 31, 23, 59, 58) + timedelta(seconds=i))
                  for i in range(5)]
        self.assertEqual(stamps, sorted(stamps))
        self.assertNotIn(":", "".join(stamps))   # colons would break URL params

    def test_same_second_suffix_still_sorts_chronologically(self):
        from datetime import datetime, timedelta
        dt = datetime(2026, 8, 18, 17, 26, 20)
        self.assertEqual(bs.run_timestamp(dt, 2), "2026-08-18T17-26-20-02")
        stamps = [bs.run_timestamp(dt), bs.run_timestamp(dt, 2), bs.run_timestamp(dt, 3),
                  bs.run_timestamp(dt + timedelta(seconds=1))]
        self.assertEqual(stamps, sorted(stamps))


class TestNextRunName(unittest.TestCase):
    """A same-second rebuild must never overwrite a run -- it takes a -02/-03/... suffix (zero-padded)."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="panel-names-"))
        self.addCleanup(lambda: shutil.rmtree(self.dir, ignore_errors=True))
        from datetime import datetime
        self.dt = datetime(2026, 8, 18, 17, 26, 20)

    def test_bare_name_when_the_second_is_free(self):
        self.assertEqual(bs.next_run_name(self.dir, self.dt),
                         ("behaviours-2026-08-18T17-26-20.json", "2026-08-18T17-26-20"))

    def test_sequence_suffix_until_unique(self):
        (self.dir / "behaviours-2026-08-18T17-26-20.json").write_text("{}")
        self.assertEqual(bs.next_run_name(self.dir, self.dt),
                         ("behaviours-2026-08-18T17-26-20-02.json", "2026-08-18T17-26-20-02"))
        (self.dir / "behaviours-2026-08-18T17-26-20-02.json").write_text("{}")
        self.assertEqual(bs.next_run_name(self.dir, self.dt),
                         ("behaviours-2026-08-18T17-26-20-03.json", "2026-08-18T17-26-20-03"))


class TestManifestUpdate(unittest.TestCase):
    """The manifest is the run ledger: newest first, one entry per filename."""

    def entry(self, ts, **extra):
        return {"filename": f"behaviours-{ts}.json", "timestamp": ts, **extra}

    def test_runs_listed_newest_first_regardless_of_insert_order(self):
        m = {"latest": None, "runs": []}
        m = bs.update_manifest(m, self.entry("2026-08-18T10-00-00"))
        m = bs.update_manifest(m, self.entry("2026-08-18T12-00-00"))
        m = bs.update_manifest(m, self.entry("2026-08-18T11-00-00"))
        self.assertEqual([r["timestamp"] for r in m["runs"]],
                         ["2026-08-18T12-00-00", "2026-08-18T11-00-00",
                          "2026-08-18T10-00-00"])
        self.assertEqual(m["latest"], "behaviours-2026-08-18T12-00-00.json")

    def test_same_filename_replaces_not_duplicates(self):
        m = bs.update_manifest({"latest": None, "runs": []},
                               self.entry("2026-08-18T10-00-00", citations=3))
        m = bs.update_manifest(m, self.entry("2026-08-18T10-00-00", citations=7))
        self.assertEqual(len(m["runs"]), 1)
        self.assertEqual(m["runs"][0]["citations"], 7)

    def test_late_older_insert_does_not_steal_latest(self):
        m = bs.update_manifest({"latest": None, "runs": []},
                               self.entry("2026-08-18T12-00-00"))
        m = bs.update_manifest(m, self.entry("2026-08-18T09-00-00"))
        self.assertEqual(m["latest"], "behaviours-2026-08-18T12-00-00.json")


class ResolveFixture(unittest.TestCase):
    """Shared temp-dir fixture: shipped fallback + two timestamped runs + a manifest."""

    OLD = "behaviours-2026-08-18T10-00-00.json"
    NEW = "behaviours-2026-08-18T12-00-00.json"

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="panel-data-"))
        self.addCleanup(lambda: shutil.rmtree(self.dir, ignore_errors=True))
        self.write("behaviours.json", {"behaviours": []})
        self.write(self.OLD, {"behaviours": ["a"]})
        self.write(self.NEW, {"behaviours": ["a", "b"]})
        self.manifest = {"latest": self.NEW, "runs": [
            {"filename": self.NEW, "timestamp": "2026-08-18T12-00-00"},
            {"filename": self.OLD, "timestamp": "2026-08-18T10-00-00"}]}
        self.write("manifest.json", self.manifest)

    def write(self, name, obj):
        (self.dir / name).write_text(json.dumps(obj))


class TestResolveDataName(ResolveFixture):
    """The fallback chain app.js implements: pin -> manifest latest -> shipped."""

    def test_pin_wins_over_latest(self):
        self.assertEqual(bs.resolve_data_name(self.dir, pin=self.OLD, manifest=self.manifest),
                         (self.OLD, "pin"))

    def test_pin_accepts_name_without_json_suffix(self):
        self.assertEqual(
            bs.resolve_data_name(self.dir, pin=self.OLD[:-5], manifest=self.manifest),
            (self.OLD, "pin"))

    def test_missing_pin_falls_through_to_latest(self):
        self.assertEqual(
            bs.resolve_data_name(self.dir, pin="behaviours-nope", manifest=self.manifest),
            (self.NEW, "latest"))

    def test_pin_with_path_characters_is_ignored(self):
        self.assertEqual(
            bs.resolve_data_name(self.dir, pin="../escape", manifest=self.manifest),
            (self.NEW, "latest"))

    def test_unparseable_pin_falls_through(self):
        (self.dir / "behaviours-broken.json").write_text("{not json")
        self.assertEqual(
            bs.resolve_data_name(self.dir, pin="behaviours-broken", manifest=self.manifest),
            (self.NEW, "latest"))

    def test_no_manifest_falls_back_to_shipped(self):
        self.assertEqual(bs.resolve_data_name(self.dir, manifest=None),
                         ("behaviours.json", "fallback"))

    def test_manifest_latest_missing_falls_back_to_shipped(self):
        self.assertEqual(
            bs.resolve_data_name(self.dir, manifest={"latest": "behaviours-gone.json"}),
            ("behaviours.json", "fallback"))

    def test_non_string_latest_falls_back_to_shipped(self):
        # mirrors app.js's `typeof latest === "string"` guard: a malformed manifest
        # must reach the shipped data, not crash the regex match
        for bad in (123, ["behaviours.json"], {"latest": "x"}, True):
            self.assertEqual(bs.resolve_data_name(self.dir, manifest={"latest": bad}),
                             ("behaviours.json", "fallback"), f"latest={bad!r}")

    def test_empty_directory_resolves_nothing(self):
        empty = Path(tempfile.mkdtemp(prefix="panel-empty-"))
        self.addCleanup(lambda: shutil.rmtree(empty, ignore_errors=True))
        self.assertEqual(bs.resolve_data_name(empty), (None, None))


class TestSelectRun(ResolveFixture):
    """The CLI pin path resolves/verifies exactly what the URL param would load."""

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sr.main(["--data-dir", str(self.dir), *args])
        return code, out.getvalue(), err.getvalue()

    def test_pin_resolves_and_reports_the_url_param(self):
        code, out, _ = self.run_cli("--pin", self.OLD[:-5])
        self.assertEqual(code, 0)
        self.assertIn(self.OLD, out)
        self.assertIn(f"?data={self.OLD[:-5]}", out)

    def test_pin_equals_form_and_json_suffix_both_work(self):
        self.assertEqual(self.run_cli(f"--pin={self.OLD}")[0], 0)
        self.assertEqual(self.run_cli("--pin", self.OLD)[0], 0)

    def test_unknown_pin_fails_and_names_what_the_page_would_load(self):
        code, _, err = self.run_cli("--pin", "behaviours-nope")
        self.assertEqual(code, 1)
        self.assertIn(self.NEW, err)   # the page would fall through to the latest run

    def test_latest_resolves_the_manifest_newest(self):
        code, out, _ = self.run_cli("--latest")
        self.assertEqual(code, 0)
        self.assertIn(self.NEW, out)

    def test_latest_without_manifest_fails(self):
        (self.dir / "manifest.json").unlink()
        code, _, err = self.run_cli("--latest")
        self.assertEqual(code, 1)
        self.assertIn("no manifest", err)

    def test_default_reports_what_the_page_loads(self):
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn(self.NEW, out)
        self.assertIn("(source: latest)", out)

    def test_default_on_fresh_clone_reports_fallback(self):
        (self.dir / "manifest.json").unlink()
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("behaviours.json (source: fallback)", out)


class TestBuildMain(unittest.TestCase):
    """Integration: build_site_data.main() end-to-end on a synthetic runlog -- the
    timestamped run file + manifest row, same-second collisions, and the --out= side
    road (explicit file, manifest untouched, unsafe names rejected)."""

    TS = "2026-08-18T17-26-20"
    LOC = "constitution@2026-01-20 > Overview > Claude and the mission of Anthropic > ¶1"

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="panel-build-"))
        self.addCleanup(lambda: shutil.rmtree(self.dir, ignore_errors=True))
        self._data_dir, self._datetime = bs.DATA_DIR, bs.datetime
        bs.DATA_DIR = self.dir
        self.addCleanup(lambda: setattr(bs, "DATA_DIR", self._data_dir))
        # three frontier judges on one helpfulness passage: score 5, 3 votes -> kept
        rows = [{"behaviour": "helpfulness", "spec": "constitution", "model": m,
                 "locator": self.LOC, "rubric": "v3w", "parsed": True, "verdict": v}
                for m, v in (("sol", 2), ("fable", 2), ("kimi", 1))]
        self.runlog = self.dir / "synth-runlog.jsonl"
        self.runlog.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def freeze(self):
        from datetime import datetime
        fixed = datetime(2026, 8, 18, 17, 26, 20)   # == self.TS
        bs.datetime = type("FrozenDT", (), {"now": staticmethod(lambda: fixed)})
        self.addCleanup(lambda: setattr(bs, "datetime", self._datetime))

    def build(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            bs.main([f"--runlog={self.runlog}", *extra])
        return out.getvalue()

    def test_timestamped_build_writes_run_file_and_manifest_row(self):
        self.freeze()
        self.build()
        name = f"behaviours-{self.TS}.json"
        payload = json.loads((self.dir / name).read_text())
        n = sum(len(c["passages"]) for b in payload["behaviours"]
                for c in b["coverage"].values())
        self.assertEqual(n, 1)
        manifest = json.loads((self.dir / "manifest.json").read_text())
        self.assertEqual(manifest["latest"], name)
        self.assertEqual(len(manifest["runs"]), 1)
        row = manifest["runs"][0]
        self.assertEqual(row["filename"], name)
        self.assertEqual(row["timestamp"], self.TS)
        self.assertEqual(row["rubric"], "v3w")
        self.assertEqual(row["panel"], "frontier")
        self.assertEqual(row["judges"], ["fable", "kimi", "sol"])
        self.assertEqual(row["runlog"], self.runlog.name)
        self.assertEqual(row["citations"], 1)

    def test_same_second_double_build_keeps_both_runs(self):
        self.freeze()
        self.build()
        self.build()
        first, second = f"behaviours-{self.TS}.json", f"behaviours-{self.TS}-02.json"
        self.assertTrue((self.dir / first).exists())
        self.assertTrue((self.dir / second).exists())
        manifest = json.loads((self.dir / "manifest.json").read_text())
        self.assertEqual([r["filename"] for r in manifest["runs"]], [second, first])
        self.assertEqual(manifest["latest"], second)

    def test_out_writes_named_file_and_leaves_manifest_alone(self):
        self.build("--out=explicit.json")
        json.loads((self.dir / "explicit.json").read_text())
        self.assertFalse((self.dir / "manifest.json").exists())
        self.assertFalse(any(self.dir.glob("behaviours-*.json")))

    def test_out_rejects_unsafe_names(self):
        for bad in ("../evil.json", "sub/dir.json", "..", "bad name!.json"):
            with self.assertRaises(SystemExit) as cm:
                self.build(f"--out={bad}")
            self.assertIn(repr(bad), str(cm.exception.code))
        # nothing was written anywhere: the data dir still holds only the runlog
        self.assertEqual([p.name for p in self.dir.iterdir()], ["synth-runlog.jsonl"])
        self.assertFalse((self.dir.parent / "evil.json").exists())

    def test_out_rejects_manifest_name(self):
        # a build must never clobber the manifest/ledger, even via --out=
        with self.assertRaises(SystemExit) as cm:
            self.build("--out=manifest.json")
        self.assertIn("manifest.json", str(cm.exception.code))
        self.assertIn("ledger", str(cm.exception.code))
        # rejection fires before any build work: runlog still the only file
        self.assertEqual([p.name for p in self.dir.iterdir()], ["synth-runlog.jsonl"])



class TestPR32ReviewFixes(unittest.TestCase):
    """Pins for the PR-level review findings."""

    def test_sequence_suffix_pads_past_nine(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bsd_under_test",
            Path(__file__).resolve().parents[0] / "build_site_data.py")
        bsd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bsd)
        from datetime import datetime
        dt = datetime(2026, 8, 18, 17, 26, 20)
        names = [bsd.run_timestamp(dt, seq=s) for s in (0, 2, 9, 10, 11)]
        self.assertEqual(names, [
            "2026-08-18T17-26-20",
            "2026-08-18T17-26-20-02",
            "2026-08-18T17-26-20-09",
            "2026-08-18T17-26-20-10",
            "2026-08-18T17-26-20-11",
        ])
        # lexical order stays chronological across the padding boundary
        self.assertEqual(sorted(names), names)

    def test_run_date_tripwire_fails_on_drift(self):
        import importlib.util, tempfile, json, shutil
        here = Path(__file__).resolve().parents[0]
        spec = importlib.util.spec_from_file_location("vpp_under_test",
            here / "verify_panel_provenance.py")
        v = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(v)
        with tempfile.TemporaryDirectory() as tmp:
            payload = Path(tmp) / "behaviours.json"
            doc = {"provenance": {"runDate": "2026-08-18"}, "behaviours": []}
            payload.write_text(json.dumps(doc))
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = v.verify(runlog=v.DEFAULT_RUNLOG, payload=payload, verbose=True)
        self.assertEqual(rc, 1)
        self.assertIn("differs from the", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
