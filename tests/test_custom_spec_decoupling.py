"""End-to-end tests for custom spec/behaviour decoupling.

The guarantee under test: a user who clones the repo can register their OWN
spec and/or behaviour, run the panel pipeline on it, and see it in the UI --
WITHOUT pushing any data to the repo. Everything user-side lives in
gitignored/untracked locations (a temp manifest, a temp spec file, a temp
registry, a temp runlog); nothing is committed.

Two byte-identity pins guard the flip side of the same guarantee: when NO
user manifest is present, the bundled outputs rebuild byte-for-byte.

  * documents.json -- engine/build-spec-reader-data.py with no user manifest
    reproduces the committed site/spec-reader/data/documents.json exactly.
  * panel payload -- engine/panel/build_site_data.py, run against the
    committed runlogs with --run-date pinned to the committed build date,
    reproduces the committed payloads exactly. (runDate is the one field the
    builder stamps with date.today(), so a rebuild pins it to compare.)

The synthetic end-to-end cases register a tiny user spec + a set:user
behaviour and assert they flow through:

  * the user spec appears in documents.json alongside the bundled specs;
  * the set:user behaviour flows into the panel payload from a synthetic
    runlog (the same row shape engine/panel/test_panel.py uses).

Run:  python3 -m unittest tests.test_custom_spec_decoupling -v
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_OUT = ROOT / "site" / "spec-reader" / "data" / "documents.json"
PANEL_DATA = ROOT / "site" / "llm-panel-review" / "data"
SPEC_READER_BUILDER = ROOT / "engine" / "build-spec-reader-data.py"
PANEL_BUILDER = ROOT / "engine" / "panel" / "build_site_data.py"

sys.path.insert(0, str(ROOT / "engine" / "spec-cite"))
import cite  # noqa: E402


def run_builder(script, args, env_extra=None, cwd=ROOT):
    """Run a builder script in a subprocess; return CompletedProcess."""
    env = dict(os.environ)
    # the ambient manifest must never leak into a pinned build
    env.pop(cite.MANIFEST_ENV_VAR, None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(cwd),
    )


def run_panel_builder(argv, data_dir, manifest=None):
    """build_site_data.main() in-process with DATA_DIR rebound to data_dir --
    the stacked `--out=` contract writes a bare filename inside DATA_DIR (a
    path is rejected by check_out_name), so isolation means rebinding the
    directory, not pointing --out elsewhere. manifest=None pins the
    bundled-only state so an ambient local manifest cannot leak into a pinned
    build; otherwise the given manifest is loaded first. Returns data_dir."""
    import importlib.util
    saved = os.environ.get(cite.MANIFEST_ENV_VAR)
    os.environ[cite.MANIFEST_ENV_VAR] = (
        str(manifest) if manifest is not None else "/nonexistent/specs.json")
    cite.load_user_manifest()
    try:
        sp = importlib.util.spec_from_file_location(
            "panel_builder_under_test", PANEL_BUILDER)
        bs = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(bs)
        data_dir.mkdir(parents=True, exist_ok=True)
        bs.DATA_DIR = data_dir
        with contextlib.redirect_stdout(io.StringIO()):
            bs.main(argv)
        return data_dir
    finally:
        if saved is None:
            os.environ.pop(cite.MANIFEST_ENV_VAR, None)
        else:
            os.environ[cite.MANIFEST_ENV_VAR] = saved
        cite.load_user_manifest()


class DocumentsByteIdentityTest(unittest.TestCase):
    """With NO user manifest, the spec-reader payload is byte-for-byte the
    committed file. This is the behaviour-preservation pin."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_no_manifest_rebuild_is_byte_identical(self):
        out = Path(self._tmp.name) / "documents.json"
        # --user-manifest pointed at an absent file forces the bundled-only
        # state even if a developer has a local specs/user/specs.json
        result = run_builder(
            SPEC_READER_BUILDER,
            ["--user-manifest=/nonexistent/specs.json", f"--out={out}"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(out.read_bytes(), DOCS_OUT.read_bytes())

    def test_env_var_pointing_nowhere_is_also_byte_identical(self):
        out = Path(self._tmp.name) / "documents.json"
        result = run_builder(
            SPEC_READER_BUILDER, [f"--out={out}"],
            env_extra={cite.MANIFEST_ENV_VAR: "/nonexistent/specs.json"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(out.read_bytes(), DOCS_OUT.read_bytes())


class UserSpecInDocumentsTest(unittest.TestCase):
    """A registered user spec appears in documents.json alongside the bundled
    specs; the bundled documents are untouched."""

    SPEC_NAME = "acme-spec"
    SPEC_VERSION = "2026-01-01"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # a tiny synthetic spec: a heading + paragraphs (cite.py's passage
        # source and the reader's markdown), living OUTSIDE specs/ to prove
        # the document can sit anywhere
        self.spec_file = Path(self._tmp.name) / "acme-spec.md"
        self.spec_file.write_text(
            "# Acme Transparency Spec\n"
            "\n"
            "The provider must disclose compute usage.\n"
            "\n"
            "## Reporting\n"
            "\n"
            "Reports are published quarterly.\n",
            encoding="utf-8",
        )
        self.manifest = Path(self._tmp.name) / "specs.json"
        self.manifest.write_text(json.dumps({
            self.SPEC_NAME: {self.SPEC_VERSION: {
                "path": str(self.spec_file),
                "default": True,
                "title": "Acme Transparency Spec",
                "sourceUrl": "https://acme.example.com/spec",
            }},
        }), encoding="utf-8")

    def build(self, env_extra=None, extra_args=()):
        out = Path(self._tmp.name) / "documents.json"
        result = run_builder(
            SPEC_READER_BUILDER,
            [f"--user-manifest={self.manifest}", f"--out={out}", *extra_args],
            env_extra=env_extra,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(out.read_text())

    def test_user_spec_appears_alongside_bundled(self):
        payload = self.build()
        ids = [d["id"] for d in payload["documents"]]
        self.assertEqual(ids, ["anthropic", "openai", self.SPEC_NAME])

    def test_bundled_documents_untouched(self):
        payload = self.build()
        committed = json.loads(DOCS_OUT.read_text())
        by_id = {d["id"]: d for d in payload["documents"]}
        for doc_id in ("anthropic", "openai"):
            self.assertEqual(by_id[doc_id], self._committed_doc(committed, doc_id))

    @staticmethod
    def _committed_doc(committed, doc_id):
        return next(d for d in committed["documents"] if d["id"] == doc_id)

    def test_user_document_carries_manifest_metadata(self):
        payload = self.build()
        doc = next(d for d in payload["documents"] if d["id"] == self.SPEC_NAME)
        self.assertEqual(doc["title"], "Acme Transparency Spec")
        self.assertEqual(doc["version"], self.SPEC_VERSION)
        self.assertEqual(doc["sourceUrl"], "https://acme.example.com/spec")
        self.assertEqual(doc["lab"], "User")
        self.assertEqual(doc["markdown"], self.spec_file.read_text())

    def test_title_falls_back_to_first_heading_when_absent(self):
        # rewrite the manifest without an explicit title
        self.manifest.write_text(json.dumps({
            self.SPEC_NAME: {self.SPEC_VERSION: {
                "path": str(self.spec_file), "default": True,
            }},
        }), encoding="utf-8")
        payload = self.build()
        doc = next(d for d in payload["documents"] if d["id"] == self.SPEC_NAME)
        self.assertEqual(doc["title"], "Acme Transparency Spec")  # from "# ..." heading
        self.assertNotIn("sourceUrl", doc)

    def test_generatedFrom_lists_user_spec(self):
        payload = self.build()
        self.assertIn(str(self.spec_file), payload["generatedFrom"])

    def test_behaviours_carry_empty_coverage_for_user_doc(self):
        payload = self.build()
        for behaviour in payload["behaviours"]:
            with self.subTest(slug=behaviour["slug"]):
                cov = behaviour["coverage"][self.SPEC_NAME]
                self.assertEqual(cov["passages"], [])
                self.assertEqual(cov["depth"], 0)

    def test_explicit_flag_overrides_env_var(self):
        # --user-manifest wins over SPEC_CITE_USER_SPECS when both are given:
        # an absent-path flag forces the bundled-only state even with the env
        # var pointing at a live manifest (env-var inclusion is tested below)
        payload = self.build(env_extra={cite.MANIFEST_ENV_VAR: str(self.manifest)},
                             extra_args=["--user-manifest=/nonexistent/specs.json"])
        ids = [d["id"] for d in payload["documents"]]
        self.assertEqual(ids, ["anthropic", "openai"])

    def test_env_var_alone_includes_user_spec(self):
        out = Path(self._tmp.name) / "documents.json"
        result = run_builder(
            SPEC_READER_BUILDER, [f"--out={out}"],
            env_extra={cite.MANIFEST_ENV_VAR: str(self.manifest)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        ids = [d["id"] for d in json.loads(out.read_text())["documents"]]
        self.assertEqual(ids, ["anthropic", "openai", self.SPEC_NAME])


class UserBehaviourInPanelTest(unittest.TestCase):
    """A set:user behaviour flows from a synthetic runlog into the panel
    payload. Runlog rows reuse the shape engine/panel/test_panel.py banks on."""

    SPEC_NAME = "acme-spec"
    SPEC_VERSION = "2026-01-01"
    BEHAVIOUR = "acme-transparency"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.spec_file = Path(self._tmp.name) / "acme-spec.md"
        self.spec_file.write_text(
            "# Acme Transparency Spec\n"
            "\n"
            "The provider must disclose compute usage.\n"
            "\n"
            "## Reporting\n"
            "\n"
            "Reports are published quarterly.\n",
            encoding="utf-8",
        )
        self.manifest = Path(self._tmp.name) / "specs.json"
        self.manifest.write_text(json.dumps({
            self.SPEC_NAME: {self.SPEC_VERSION: {
                "path": str(self.spec_file), "default": True,
            }},
        }), encoding="utf-8")

        # registry = the committed one + a set:user behaviour (the clone/fork
        # seam), written to a temp file so data/behaviours.json stays pristine
        registry = json.loads((ROOT / "data" / "behaviours.json").read_text())
        registry[self.BEHAVIOUR] = {
            "name": "Acme transparency",
            "set": "user",
            "numeric_id": 1,
            "group": None,
            "definition": "The provider must disclose compute usage to users.",
            "facets": [],
        }
        self.registry = Path(self._tmp.name) / "behaviours.json"
        self.registry.write_text(json.dumps(registry, indent=2, ensure_ascii=False),
                                 encoding="utf-8")

        self.addCleanup(os.environ.pop, cite.MANIFEST_ENV_VAR, None)
        self.addCleanup(cite.load_user_manifest)  # restore ambient registry

    def _user_spec_locators(self):
        """Real passage locators for the user spec, via the same harness the
        builder uses. The manifest must be loaded in-process first."""
        os.environ[cite.MANIFEST_ENV_VAR] = str(self.manifest)
        cite.load_user_manifest()
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "panel-harness-e2e", ROOT / "engine" / "panel" / "harness.py")
        harness = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(harness)
        return [loc for loc, _sec, _text in harness.passages(self.SPEC_NAME)]

    def _write_runlog(self, rows):
        path = Path(self._tmp.name) / "runlog.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return path

    def build(self, runlog, behaviours, panel="itest", rubric="v3w"):
        data_dir = Path(self._tmp.name) / "panel-data"
        run_panel_builder(
            [f"--runlog={runlog}", f"--registry={self.registry}",
             f"--behaviours={behaviours}", f"--panel={panel}",
             f"--rubric={rubric}", "--run-date=2026-08-19",
             "--out=panel-payload.json"],
            data_dir, manifest=self.manifest,
        )
        return json.loads((data_dir / "panel-payload.json").read_text())

    def test_user_behaviour_flows_into_payload(self):
        locators = self._user_spec_locators()
        self.assertTrue(locators, "the synthetic spec must expose passages")
        rows = [
            {"behaviour": self.BEHAVIOUR, "spec": self.SPEC_NAME, "model": "qwen-big",
             "locator": loc, "rubric": "v3w", "parsed": True, "verdict": 2}
            for loc in locators
        ]
        payload = self.build(self._write_runlog(rows), behaviours=self.BEHAVIOUR)

        self.assertEqual([b["slug"] for b in payload["behaviours"]], [self.BEHAVIOUR])
        behaviour = payload["behaviours"][0]
        # identity comes from the (temp) registry
        self.assertEqual(behaviour["name"], "Acme transparency")
        self.assertEqual(behaviour["definition"],
                         "The provider must disclose compute usage to users.")
        self.assertIsNone(behaviour["category"])  # user-set group is null

    def test_user_spec_citations_land_under_user_coverage_key(self):
        locators = self._user_spec_locators()
        rows = [
            {"behaviour": self.BEHAVIOUR, "spec": self.SPEC_NAME, "model": "qwen-big",
             "locator": loc, "rubric": "v3w", "parsed": True, "verdict": 2}
            for loc in locators
        ]
        payload = self.build(self._write_runlog(rows), behaviours=self.BEHAVIOUR)
        coverage = payload["behaviours"][0]["coverage"]
        # the user spec keys coverage by its own name (its documents.json id)
        self.assertIn(self.SPEC_NAME, coverage)
        passages = coverage[self.SPEC_NAME]["passages"]
        self.assertEqual(len(passages), len(locators))
        quotes = {p["quote"] for p in passages}
        self.assertIn("The provider must disclose compute usage.", quotes)
        self.assertIn("Reports are published quarterly.", quotes)
        # the bundled labs are present but empty for a user-spec behaviour
        self.assertEqual(coverage["anthropic"]["passages"], [])
        self.assertEqual(coverage["openai"]["passages"], [])

    def test_user_behaviour_coexists_with_bundled(self):
        locators = self._user_spec_locators()
        rows = [
            {"behaviour": self.BEHAVIOUR, "spec": self.SPEC_NAME, "model": "qwen-big",
             "locator": locators[0], "rubric": "v3w", "parsed": True, "verdict": 2},
            {"behaviour": "helpfulness", "spec": "constitution", "model": "qwen-big",
             "locator": "constitution@2026-01-20 > Overview > Claude and the mission of Anthropic > ¶1",
             "rubric": "v3w", "parsed": True, "verdict": 1},
        ]
        payload = self.build(self._write_runlog(rows),
                             behaviours=f"helpfulness,{self.BEHAVIOUR}")
        slugs = [b["slug"] for b in payload["behaviours"]]
        # reader-test bench order first, then the user seam
        self.assertEqual(slugs, ["helpfulness", self.BEHAVIOUR])
        self.assertEqual(payload["behaviours"][0]["name"], "Helpfulness")

    def test_unknown_display_behaviour_fails_loudly(self):
        rows = [{"behaviour": "helpfulness", "spec": "constitution", "model": "qwen-big",
                 "locator": "x", "rubric": "v3w", "parsed": True, "verdict": 1}]
        data_dir = Path(self._tmp.name) / "panel-data"
        with self.assertRaises(SystemExit) as ctx:
            run_panel_builder(
                [f"--runlog={self._write_runlog(rows)}", f"--registry={self.registry}",
                 "--behaviours=no-such-behaviour", "--panel=itest",
                 "--rubric=v3w", "--out=panel-payload.json"],
                data_dir, manifest=self.manifest,
            )
        self.assertIn("no-such-behaviour", str(ctx.exception.code))


class PanelByteIdentityTest(unittest.TestCase):
    """The registry-drive refactor preserves the shipped panel payloads
    byte-for-byte: rebuild from the committed runlogs with --run-date pinned
    to the committed build date and diff against the committed files.

    runDate is the builder's one time-dependent field (date.today()); pinning
    it is what makes a rebuild reproducible. Only payloads whose source
    runlog is committed on this branch are pinned here (v4a, v5); the v3w
    primary ships from runlog-v3.jsonl and is pinned by
    engine/panel/verify_panel_provenance.py (byte-identical modulo the
    documented runDate allowance)."""

    def _assert_rebuild_identical(self, payload_name, runlog, rubric, panel,
                                 behaviours, run_date):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        # manifest=None pins the bundled-only state: an ambient local manifest
        # must never leak into a byte-identity rebuild.
        run_panel_builder(
            [f"--runlog={ROOT / runlog}", f"--rubric={rubric}", f"--panel={panel}",
             f"--behaviours={behaviours}", f"--run-date={run_date}",
             f"--out={payload_name}"],
            data_dir, manifest=None,
        )
        committed = (PANEL_DATA / payload_name).read_bytes()
        self.assertEqual((data_dir / payload_name).read_bytes(), committed,
                         f"{payload_name} rebuild diverged from the committed payload")

    def test_v4a_payload_rebuilds_byte_identical(self):
        self._assert_rebuild_identical(
            "behaviours-v4a.json",
            "experiments/panel-calibration/runlog-v4a.jsonl",
            rubric="v4a", panel="frontier_primary",
            behaviours="helpfulness,proportionate-risk-mitigation,"
                       "how-to-approach-tradeoffs,avoiding-over-and-under-caution",
            run_date="2026-08-17",
        )

    def test_v5_payload_rebuilds_byte_identical(self):
        # v5 exercises the SLUGS_EXTRA dual-slug path (animal-welfare-impacts feeds
        # both general-guidelines rows) as well as all ten reader-test slugs
        self._assert_rebuild_identical(
            "behaviours-v5.json",
            "experiments/panel-calibration/runlog-v5.jsonl",
            rubric="v5", panel="frontier_fast",
            behaviours="helpfulness,harmlessness-to-the-user,harm-avoidance-to-third-parties,"
                       "proportionate-risk-mitigation,how-to-approach-tradeoffs,"
                       "avoiding-over-and-under-caution,objectivity-on-contested-questions,"
                       "user-autonomy,animal-welfare-impacts,general-welfare-impacts-strict",
            run_date="2026-08-17",
        )


if __name__ == "__main__":
    unittest.main()
