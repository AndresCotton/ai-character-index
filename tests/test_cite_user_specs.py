"""Tests for cite.py's user-spec manifest (engine/spec-cite/cite.py).

The manifest (specs/user/specs.json by default, gitignored) registers a
user's own spec documents alongside the bundled constitution/model-spec
without editing cite.py. These tests cover:

- CLI: outline/show/resolve/find against a synthetic user-spec fixture
  (tests/fixtures/user-spec-sample.md), via subprocess with the manifest
  location overridden through SPEC_CITE_USER_SPECS -- the same override
  production users get, exercised here against a temp file so the suite
  never touches specs/.
- Library path: cite.load_spec("<user-spec>", None) with a manifest
  present (engine/panel/harness.py imports cite this way).
- The loud failures: shadowing a bundled spec name, malformed manifests,
  unknown specs (the error must list bundled AND user specs).
- The quiet one: an absent manifest is the normal bundled-only state.

In-process tests rebuild cite's registry through load_user_manifest() and
restore the ambient state in a cleanup, so no test leaks registry changes
into the rest of the suite.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITE = ROOT / "engine" / "spec-cite" / "cite.py"

# Repo-relative, because manifest paths resolve against the repo root.
FIXTURE_PATH = "tests/fixtures/user-spec-sample.md"

sys.path.insert(0, str(ROOT / "engine" / "spec-cite"))
import cite  # noqa: E402


def make_manifest(tmp, manifest):
    """Write manifest (a dict) as JSON into tmp dir; return its path."""
    path = Path(tmp) / "specs.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


SINGLE_VERSION = {
    "user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "default": True}}
}


class UserSpecCliTest(unittest.TestCase):
    """All four commands against the user fixture, as subprocesses."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.manifest = make_manifest(self._tmp.name, SINGLE_VERSION)

    def cli(self, *args, check=True):
        env = dict(os.environ, **{cite.MANIFEST_ENV_VAR: str(self.manifest)})
        result = subprocess.run(
            [sys.executable, str(CITE), *args],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        if result.returncode != 0:
            if check:
                self.fail(f"cite.py {' '.join(args)} failed:\n{result.stderr}")
            return result.stdout, result.stderr
        return result.stdout, result.stderr

    def test_outline_lists_levels_and_anchor(self):
        out, _ = self.cli("outline", "user-spec")
        self.assertEqual(
            out.rstrip("\n"),
            "user-spec@2026-01-01\n"
            "Sample User Spec\n"
            "  Policies  {#policies}\n"
            "    Enforcement\n"
            "  Changelog",
        )

    def test_show_numbers_blocks_and_sentences(self):
        out, _ = self.cli("show", "user-spec > #policies")
        self.assertEqual(
            out.rstrip("\n"),
            "user-spec@2026-01-01 > #policies\n"
            "\n"
            "¶1\n"
            "  s1: Policies apply to all deployments.\n"
            "  s2: They bind e.g. Fine-tuned variants equally.\n"
            "\n"
            "¶2\n"
            "  s1: First obligation: do no harm.\n"
            "\n"
            "¶3\n"
            "  s1: Second obligation: be honest.\n"
            "\n"
            "¶4 [example/code block] ```bash",
        )

    def test_resolve_whole_block_and_sentence(self):
        # list items are blocks; normalize drops the leading bullet marker
        out, _ = self.cli("resolve", "user-spec@2026-01-01 > #policies > ¶2")
        self.assertEqual(out.rstrip("\n"), "First obligation: do no harm.")
        # the "e.g." abbreviation does not split the sentence
        out, _ = self.cli("resolve", "user-spec > Policies > ¶1 s2")
        self.assertEqual(
            out.rstrip("\n"), "They bind e.g. Fine-tuned variants equally."
        )

    def test_find_folds_quote_style_and_reports_span(self):
        out, _ = self.cli("find", "user-spec", '"Pending review" remains')
        self.assertEqual(
            out.rstrip("\n"),
            "user-spec@2026-01-01 > Sample User Spec > Changelog > ¶1 s2\n"
            "  “Pending review” remains the status.",
        )

    def test_find_miss_exits_with_hint(self):
        out, err = self.cli("find", "user-spec", "not in this fixture", check=False)
        self.assertIn("not found", err)

    def test_bundled_spec_still_resolves_with_manifest_loaded(self):
        out, _ = self.cli(
            "resolve",
            "constitution@2026-01-20 > Being broadly ethical > Being honest > ¶18 s1",
        )
        self.assertEqual(out.rstrip("\n"), "Sometimes being honest requires courage.")

    def test_unknown_spec_error_lists_bundled_and_user_specs(self):
        out, err = self.cli("resolve", "no-such-spec > Something > ¶1", check=False)
        self.assertIn("unknown spec 'no-such-spec@None'", err)
        for known in (
            "constitution@2026-01-20",
            "model-spec@2025-12-18",
            "user-spec@2026-01-01",
        ):
            self.assertIn(known, err)


class UserSpecLibraryTest(unittest.TestCase):
    """cite as an imported library (the engine/panel/harness.py path)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.manifest = make_manifest(self._tmp.name, SINGLE_VERSION)
        os.environ[cite.MANIFEST_ENV_VAR] = str(self.manifest)

        def restore():
            os.environ.pop(cite.MANIFEST_ENV_VAR, None)
            cite.load_user_manifest()  # ambient state: default location

        self.addCleanup(restore)
        cite.load_user_manifest()

    def test_load_spec_with_default_version(self):
        version, sections, lines = cite.load_spec("user-spec", None)
        self.assertEqual(version, "2026-01-01")
        self.assertTrue(lines)
        self.assertEqual(
            [s.title for s in sections],
            ["Sample User Spec", "Policies", "Enforcement", "Changelog"],
        )

    def test_anchor_resolves_through_find_section(self):
        _, sections, _ = cite.load_spec("user-spec", None)
        sec = cite.find_section(sections, "#policies")
        self.assertEqual(sec.title, "Policies")

    def test_bundled_specs_unaffected(self):
        version, _, _ = cite.load_spec("constitution", None)
        self.assertEqual(version, "2026-01-20")
        version, _, _ = cite.load_spec("model-spec", None)
        self.assertEqual(version, "2025-12-18")

    def test_absolute_manifest_path_also_works(self):
        absolute = str(ROOT / FIXTURE_PATH)
        manifest = make_manifest(
            self._tmp.name,
            {"abs-spec": {"2026-03-03": {"path": absolute}}},
        )
        cite.load_user_manifest(manifest)
        version, sections, _ = cite.load_spec("abs-spec", None)
        self.assertEqual(version, "2026-03-03")
        self.assertTrue(sections)

    def test_unknown_spec_error_lists_all_known_specs(self):
        with self.assertRaises(SystemExit) as cm:
            cite.load_spec("no-such-spec", None)
        message = str(cm.exception)
        self.assertIn("unknown spec 'no-such-spec@None'", message)
        self.assertIn("constitution@2026-01-20", message)
        self.assertIn("user-spec@2026-01-01", message)

    def test_missing_document_fails_with_message_not_traceback(self):
        manifest = make_manifest(
            self._tmp.name,
            {"ghost-spec": {"2026-01-01": {"path": "specs/user/absent.md"}}},
        )
        cite.load_user_manifest(manifest)
        with self.assertRaises(SystemExit) as cm:
            cite.load_spec("ghost-spec", None)
        message = str(cm.exception)
        self.assertIn("cannot read spec document", message)
        self.assertIn("ghost-spec@2026-01-01", message)


class ManifestValidationTest(unittest.TestCase):
    """A malformed manifest must fail loudly, at manifest-load time."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def assert_manifest_rejected(self, manifest_or_text, *fragments):
        if isinstance(manifest_or_text, str):
            path = Path(self._tmp.name) / "specs.json"
            path.write_text(manifest_or_text, encoding="utf-8")
        else:
            path = make_manifest(self._tmp.name, manifest_or_text)
        before_specs = dict(cite.SPECS)
        before_defaults = dict(cite.DEFAULT_VERSION)
        before_meta = dict(cite.USER_SPEC_META)
        with self.assertRaises(SystemExit) as cm:
            cite.load_user_manifest(path)
        message = str(cm.exception)
        for fragment in fragments:
            self.assertIn(fragment, message)
        # a rejected manifest must leave the registry exactly as it was
        self.assertEqual(cite.SPECS, before_specs)
        self.assertEqual(cite.DEFAULT_VERSION, before_defaults)
        self.assertEqual(cite.USER_SPEC_META, before_meta)

    def test_shadowing_constitution_fails(self):
        self.assert_manifest_rejected(
            {"constitution": {"2026-01-20": {"path": FIXTURE_PATH}}},
            "'constitution'", "bundled",
        )

    def test_shadowing_model_spec_fails(self):
        self.assert_manifest_rejected(
            {"model-spec": {"2099-01-01": {"path": FIXTURE_PATH}}},
            "'model-spec'", "bundled",
        )

    def test_bad_spec_name_rejected(self):
        # uppercase / spaces can never appear in a locator's [a-z-]+ spec id
        self.assert_manifest_rejected(
            {"My Spec": {"2026-01-01": {"path": FIXTURE_PATH}}},
            "bad spec name",
        )

    def test_bad_version_key_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"v1": {"path": FIXTURE_PATH}}},
            "bad version", "YYYY-MM-DD",
        )

    def test_missing_path_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"default": True}}},
            '"path"',
        )

    def test_unknown_entry_key_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "flavour": "x"}}},
            "unknown key", "flavour",
        )

    def test_non_string_title_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "title": 42}}},
            "'title'", "non-empty string",
        )

    def test_empty_title_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "title": ""}}},
            "'title'", "non-empty string",
        )

    def test_non_string_source_url_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "sourceUrl": 7}}},
            "'sourceUrl'", "non-empty string",
        )

    def test_empty_source_url_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "sourceUrl": ""}}},
            "'sourceUrl'", "non-empty string",
        )

    def test_non_boolean_default_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH, "default": "yes"}}},
            "'default'", "boolean",
        )

    def test_multiple_defaults_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {
                "2026-01-01": {"path": FIXTURE_PATH, "default": True},
                "2026-02-02": {"path": FIXTURE_PATH, "default": True},
            }},
            "multiple versions default",
        )

    def test_empty_versions_rejected(self):
        self.assert_manifest_rejected(
            {"user-spec": {}}, "at least one version",
        )

    def test_invalid_json_rejected(self):
        self.assert_manifest_rejected("{ not json", "not readable JSON")

    def test_non_object_top_level_rejected(self):
        self.assert_manifest_rejected("[1, 2]", "top level must be a JSON object")


class DefaultVersionTest(unittest.TestCase):
    """How the version used for an unversioned locator is chosen."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(cite.load_user_manifest)  # restore ambient state

    def test_single_version_is_implicit_default(self):
        manifest = make_manifest(
            self._tmp.name,
            {"user-spec": {"2026-01-01": {"path": FIXTURE_PATH}}},  # no flag
        )
        cite.load_user_manifest(manifest)
        version, _, _ = cite.load_spec("user-spec", None)
        self.assertEqual(version, "2026-01-01")

    def test_explicit_default_wins_among_several_versions(self):
        manifest = make_manifest(
            self._tmp.name,
            {"user-spec": {
                "2026-01-01": {"path": FIXTURE_PATH},
                "2026-02-02": {"path": FIXTURE_PATH, "default": True},
            }},
        )
        cite.load_user_manifest(manifest)
        version, _, _ = cite.load_spec("user-spec", None)
        self.assertEqual(version, "2026-02-02")
        # the non-default version stays addressable when pinned explicitly
        version, _, _ = cite.load_spec("user-spec", "2026-01-01")
        self.assertEqual(version, "2026-01-01")

    def test_no_default_among_several_versions_is_an_error(self):
        manifest = make_manifest(
            self._tmp.name,
            {"user-spec": {
                "2026-01-01": {"path": FIXTURE_PATH},
                "2026-02-02": {"path": FIXTURE_PATH},
            }},
        )
        cite.load_user_manifest(manifest)
        with self.assertRaises(SystemExit) as cm:
            cite.load_spec("user-spec", None)
        message = str(cm.exception)
        self.assertIn("no default version", message)
        self.assertIn("user-spec@2026-01-01", message)
        self.assertIn("user-spec@2026-02-02", message)


class ManifestAbsenceTest(unittest.TestCase):
    """No manifest is the normal bundled-only state, never an error."""

    def test_absent_path_leaves_bundled_registry(self):
        cite.load_user_manifest("/nonexistent/specs.json")
        self.addCleanup(cite.load_user_manifest)
        self.assertEqual(cite.SPECS, dict(cite.BUNDLED_SPECS))
        self.assertEqual(cite.DEFAULT_VERSION, dict(cite.BUNDLED_DEFAULT_VERSION))
        version, _, _ = cite.load_spec("constitution", None)
        self.assertEqual(version, "2026-01-20")

    def test_env_var_pointing_nowhere_is_tolerated(self):
        os.environ[cite.MANIFEST_ENV_VAR] = "/nonexistent/specs.json"
        self.addCleanup(os.environ.pop, cite.MANIFEST_ENV_VAR, None)
        self.addCleanup(cite.load_user_manifest)
        cite.load_user_manifest()
        self.assertEqual(cite.SPECS, dict(cite.BUNDLED_SPECS))

    def test_documented_default_location(self):
        self.assertEqual(
            cite.USER_MANIFEST_PATH,
            cite.REPO_ROOT / "specs" / "user" / "specs.json",
        )


class SpecMetaTest(unittest.TestCase):
    """spec_meta(): rendering metadata (title / sourceUrl) for display
    surfaces. title passes through, else derives from the first heading;
    sourceUrl passes through, else None. Citation never reads this."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(cite.load_user_manifest)  # restore ambient state

    def load(self, manifest):
        path = make_manifest(self._tmp.name, manifest)
        cite.load_user_manifest(path)

    def test_title_and_source_url_pass_through(self):
        self.load({"user-spec": {"2026-01-01": {
            "path": FIXTURE_PATH, "default": True,
            "title": "My Custom Title",
            "sourceUrl": "https://example.com/spec",
        }}})
        meta = cite.spec_meta("user-spec")
        self.assertEqual(meta["title"], "My Custom Title")
        self.assertEqual(meta["sourceUrl"], "https://example.com/spec")

    def test_absent_title_derives_from_first_heading(self):
        # fixture's first heading is "# Sample User Spec"
        self.load({"user-spec": {"2026-01-01": {"path": FIXTURE_PATH}}})
        meta = cite.spec_meta("user-spec")
        self.assertEqual(meta["title"], "Sample User Spec")
        self.assertIsNone(meta["sourceUrl"])

    def test_absent_source_url_is_none(self):
        self.load({"user-spec": {"2026-01-01": {
            "path": FIXTURE_PATH, "title": "T",
        }}})
        self.assertIsNone(cite.spec_meta("user-spec")["sourceUrl"])

    def test_meta_follows_default_version(self):
        self.load({"user-spec": {
            "2026-01-01": {"path": FIXTURE_PATH, "title": "Old"},
            "2026-02-02": {"path": FIXTURE_PATH, "default": True, "title": "New"},
        }})
        self.assertEqual(cite.spec_meta("user-spec")["title"], "New")
        # an explicitly pinned version reads its own entry
        self.assertEqual(cite.spec_meta("user-spec", "2026-01-01")["title"], "Old")

    def test_no_title_and_no_heading_fails_loudly(self):
        headingless = Path(self._tmp.name) / "headingless.md"
        headingless.write_text("Just prose, no heading at all.\n", encoding="utf-8")
        self.load({"bare-spec": {"2026-01-01": {"path": str(headingless)}}})
        with self.assertRaises(SystemExit) as cm:
            cite.spec_meta("bare-spec")
        message = str(cm.exception)
        self.assertIn("no heading", message)
        self.assertIn("'title'", message)

    def test_bundled_specs_derive_title_from_heading(self):
        # bundled specs carry no manifest meta; the helper still works and
        # derives from the document, with no sourceUrl
        meta = cite.spec_meta("constitution")
        self.assertTrue(meta["title"])
        self.assertIsNone(meta["sourceUrl"])

    def test_unknown_spec_fails_like_load_spec(self):
        with self.assertRaises(SystemExit) as cm:
            cite.spec_meta("no-such-spec")
        self.assertIn("unknown spec", str(cm.exception))


class UserSpecsEnumerationTest(unittest.TestCase):
    """user_specs(): enumerate registered user specs (never the bundled)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(cite.load_user_manifest)

    def test_no_manifest_means_no_user_specs(self):
        cite.load_user_manifest("/nonexistent/specs.json")
        self.assertEqual(cite.user_specs(), {})

    def test_lists_only_user_specs_sorted(self):
        path = make_manifest(self._tmp.name, {
            "zeta-spec": {"2026-01-01": {"path": FIXTURE_PATH}},
            "alpha-spec": {
                "2026-02-02": {"path": FIXTURE_PATH},
                "2026-01-01": {"path": FIXTURE_PATH, "default": True},
            },
        })
        cite.load_user_manifest(path)
        self.assertEqual(cite.user_specs(), {
            "alpha-spec": ["2026-01-01", "2026-02-02"],
            "zeta-spec": ["2026-01-01"],
        })
        self.assertNotIn("constitution", cite.user_specs())
        self.assertNotIn("model-spec", cite.user_specs())


if __name__ == "__main__":
    unittest.main()
