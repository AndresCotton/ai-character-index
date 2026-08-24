"""Drift gate: data/behaviours.json is the single source of behaviour identity.

The registry (data/behaviours.json) carries every behaviour in every set, keyed
by slug. The derived constants regenerate from it via
engine/generate_behaviour_constants.py:

  - GROUPS in site/spec-reader/app.js
  - BEHAVIOURS in engine/build-spec-reader-data.py
  - key order + titles in engine/panel/behaviours.json
  - display.behaviours in engine/panel/panel-config.json

This suite fails when the registry's structure breaks, when the registry
disagrees with the published ledgers it mirrors (data/coverage.json names,
data/reader-test-coverage.json behaviours), or when any derived constant has
drifted from the registry's rendering. Editing a derived copy without updating
the registry -- or the registry without regenerating the copies -- fails here.
After an intentional registry change: run the generator, commit both sides.

Run:  python3 -m unittest discover -s tests   (or unittest tests.test_behaviour_registry)
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "engine" / "generate_behaviour_constants.py"

sys.path.insert(0, str(ROOT / "engine"))
import generate_behaviour_constants as gbc  # noqa: E402


def load_registry():
    return json.loads((ROOT / "data" / "behaviours.json").read_text(encoding="utf-8"))


class TestRegistryStructure(unittest.TestCase):
    """The registry's shape invariants: slug keys, closed entries, per-set ids."""

    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()

    def test_slugs_are_kebab_case(self):
        for slug in self.registry:
            with self.subTest(slug=slug):
                self.assertRegex(slug, r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def test_entries_are_closed_and_typed(self):
        fields = {"name", "set", "numeric_id", "group", "definition", "facets"}
        for slug, entry in self.registry.items():
            with self.subTest(slug=slug):
                self.assertEqual(set(entry), fields)
                self.assertIsInstance(entry["name"], str)
                self.assertIn(entry["set"], gbc.SETS)
                self.assertIsInstance(entry["numeric_id"], int)
                self.assertGreaterEqual(entry["numeric_id"], 1)
                self.assertTrue(entry["group"] is None or isinstance(entry["group"], str))
                self.assertIsInstance(entry["definition"], str)
                self.assertIsInstance(entry["facets"], list)

    def test_numeric_ids_are_unique_per_set(self):
        seen = {}
        for slug, entry in self.registry.items():
            key = (entry["set"], entry["numeric_id"])
            self.assertNotIn(key, seen, f"{key} claimed by {slug!r} and {seen.get(key)!r}")
            seen[key] = slug

    def test_published_index_slugs_are_pinned(self):
        # coverage.json joins on these ids and the reader URLs carry the slugs,
        # so the three published behaviours cannot be renamed silently.
        slugs_by_id = {
            e["numeric_id"]: slug for slug, e in self.registry.items() if e["set"] == "index"
        }
        for numeric_id, slug in [(1, "no-sycophancy"), (2, "calibration"), (3, "action-honesty")]:
            with self.subTest(numeric_id=numeric_id):
                self.assertEqual(slugs_by_id.get(numeric_id), slug)

    def test_every_index_behaviour_has_a_group(self):
        # GROUPS renders the whole index set; a group-less entry cannot appear.
        for slug, entry in self.registry.items():
            if entry["set"] == "index":
                with self.subTest(slug=slug):
                    self.assertTrue(entry["group"])


class TestRegistryMatchesPublishedLedgers(unittest.TestCase):
    """The registry mirrors two published files that never change their ids."""

    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()
        cls.coverage = json.loads((ROOT / "data" / "coverage.json").read_text(encoding="utf-8"))
        cls.reader_test = json.loads(
            (ROOT / "data" / "reader-test-coverage.json").read_text(encoding="utf-8")
        )

    def test_index_names_match_coverage_records(self):
        # coverage.json repeats the behaviour name on every record; the registry
        # is the source of truth, so a rename must land in both or fail here.
        by_id = {
            e["numeric_id"]: e for e in self.registry.values() if e["set"] == "index"
        }
        for index, record in enumerate(self.coverage["coverage"]):
            with self.subTest(record=index):
                entry = by_id.get(record["behaviour_id"])
                self.assertIsNotNone(entry, f"behaviour_id {record['behaviour_id']} not in registry")
                self.assertEqual(entry["name"], record["behaviour_name"])

    def test_reader_test_entries_mirror_the_ledger(self):
        ledger = {b["slug"]: b for b in self.reader_test["behaviours"]}
        registered = {
            slug: e for slug, e in self.registry.items() if e["set"] == "reader-test"
        }
        self.assertEqual(set(registered), set(ledger))
        for slug, behaviour in ledger.items():
            with self.subTest(slug=slug):
                entry = registered[slug]
                self.assertEqual(entry["numeric_id"], behaviour["id"])
                self.assertEqual(entry["name"], behaviour["name"])
                self.assertEqual(entry["definition"], behaviour["definition"])
                self.assertEqual(entry["group"], behaviour["category"])


class TestDerivedConstantsMatchRegistry(unittest.TestCase):
    """The four derived constants must equal the generator's rendering."""

    @classmethod
    def setUpClass(cls):
        cls.registry = gbc.load_registry(ROOT)

    def test_groups_block_matches_app_js(self):
        app_js = (ROOT / "site" / "spec-reader" / "app.js").read_text(encoding="utf-8")
        start = app_js.index("const GROUPS = [")
        end = app_js.index("\n];\n", start) + len("\n];\n")
        self.assertEqual(
            app_js[start:end],
            gbc.render_groups_js(self.registry) + "\n",
            "GROUPS in site/spec-reader/app.js drifted from the registry",
        )

    def test_behaviours_block_matches_builder(self):
        builder = (ROOT / "engine" / "build-spec-reader-data.py").read_text(encoding="utf-8")
        start = builder.index("BEHAVIOURS = [")
        end = builder.index("\n]\n", start) + len("\n]\n")
        covered = gbc.coverage_ids(ROOT)
        self.assertEqual(
            builder[start:end],
            gbc.render_behaviours_py(self.registry, covered) + "\n",
            "BEHAVIOURS in engine/build-spec-reader-data.py drifted from the registry",
        )

    def test_display_behaviours_match_panel_config(self):
        config = (ROOT / "engine" / "panel" / "panel-config.json").read_text(encoding="utf-8")
        display_start = config.index('"display": {')
        array_start = config.index('"behaviours": [', display_start)
        open_bracket = config.index("[", array_start)
        close_bracket = config.index("]", open_bracket)
        self.assertEqual(
            config[open_bracket:close_bracket + 1],
            gbc.render_display_array(),
            "display.behaviours in engine/panel/panel-config.json drifted from the generator",
        )
        rendered = json.loads(config[open_bracket:close_bracket + 1])
        self.assertEqual(rendered, list(gbc.PANEL_DISPLAY_SLUGS))

    def test_panel_behaviours_json_matches(self):
        path = ROOT / "engine" / "panel" / "behaviours.json"
        self.assertEqual(
            path.read_bytes(),
            gbc.render_panel_behaviours(ROOT, self.registry).encode("utf-8"),
            "engine/panel/behaviours.json drifted from the registry",
        )

    def test_check_mode_passes_on_committed_tree(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ScratchTreeTestCase(unittest.TestCase):
    """Shared scaffolding: run the generator against a scratch copy of the
    committed tree (--root) so the real files stay pristine."""

    COPIES = (
        "data/behaviours.json",
        "data/coverage.json",
        "data/schema/behaviours.schema.json",
        "site/spec-reader/app.js",
        "engine/build-spec-reader-data.py",
        "engine/panel/panel-config.json",
        "engine/panel/behaviours.json",
    )

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="behaviour-registry-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for relative in self.COPIES:
            source = ROOT / relative
            dest = self.tmp / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)

    def run_check(self):
        return subprocess.run(
            [sys.executable, str(GENERATOR), "--check", "--root", str(self.tmp)],
            capture_output=True, text=True,
        )

    def run_write(self):
        return subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.tmp)],
            capture_output=True, text=True,
        )

    def mutate_registry(self, mutate):
        path = self.tmp / "data" / "behaviours.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        mutate(registry)
        path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class TestDriftIsCaught(ScratchTreeTestCase):
    """Mutate a copy, expect --check to fail: the gate must have teeth."""

    def test_renaming_a_registry_behaviour_fails(self):
        def mutate(registry):
            registry["no-sycophancy"]["name"] = "Anti-sycophancy"
        self.mutate_registry(mutate)
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("app.js", result.stdout + result.stderr)

    def test_editing_groups_without_the_registry_fails(self):
        # The exact failure mode: a hand-edit to the derived copy only.
        path = self.tmp / "site" / "spec-reader" / "app.js"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace('[2, "Calibration"]', '[2, "Model calibration"]'), encoding="utf-8")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("app.js", result.stdout + result.stderr)

    def test_reordering_display_behaviours_fails(self):
        path = self.tmp / "engine" / "panel" / "panel-config.json"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                '"helpfulness",\n      "harm-avoidance-to-third-parties"',
                '"harm-avoidance-to-third-parties",\n      "helpfulness"',
            ),
            encoding="utf-8",
        )
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("panel-config.json", result.stdout + result.stderr)

    def test_renaming_a_ledger_slug_fails_loudly(self):
        # A display slug the registry no longer carries is an error, not a skip.
        def mutate(registry):
            registry["helpful"] = registry.pop("helpfulness")
        self.mutate_registry(mutate)
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("helpfulness", result.stdout + result.stderr)

    def test_bool_numeric_id_is_rejected(self):
        # bool is an int subclass in Python (True == 1), so a JSON `true` would
        # otherwise pass the integer >= 1 check; the loader's explicit
        # isinstance(numeric_id, bool) guard is what rejects it.
        def mutate(registry):
            registry["calibration"]["numeric_id"] = True
        self.mutate_registry(mutate)
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("numeric_id must be an integer >= 1", result.stdout + result.stderr)

    def test_entry_missing_required_field_fails_loudly(self):
        # An entry missing a required field used to die as a bare KeyError deep
        # in a renderer; the loader must name the slug and the missing field.
        # The loader's required list comes from behaviours.schema.json, so this
        # covers every field the schema marks required.
        def mutate(registry):
            del registry["calibration"]["name"]
        self.mutate_registry(mutate)
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("calibration", result.stdout + result.stderr)
        self.assertIn("missing required field 'name'", result.stdout + result.stderr)

    def test_entry_missing_group_fails_loudly(self):
        # Before the loader validated the full schema-required set, a missing
        # `group` on an index entry died as a bare KeyError in render_groups_js
        # instead of being reported against the slug.
        def mutate(registry):
            del registry["calibration"]["group"]
        self.mutate_registry(mutate)
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("calibration", result.stdout + result.stderr)
        self.assertIn("missing required field 'group'", result.stdout + result.stderr)

    def test_entry_missing_definition_fails_loudly(self):
        # Before the loader validated the full schema-required set, a missing
        # `definition` on a reader-test entry passed the whole --check run
        # silently: no renderer reads it. The loader must catch it anyway.
        def mutate(registry):
            del registry["helpfulness"]["definition"]
        self.mutate_registry(mutate)
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("helpfulness", result.stdout + result.stderr)
        self.assertIn("missing required field 'definition'", result.stdout + result.stderr)

    def test_duplicate_top_level_slug_fails_loudly(self):
        # JSON parsing silently keeps the LAST of duplicate keys in an object,
        # which in the identity registry would erase an entry without a trace.
        # json.dumps cannot emit duplicate keys, so splice the duplicate in as
        # raw text; the loader must reject it at parse time and name the slug.
        path = self.tmp / "data" / "behaviours.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        raw = json.dumps(registry, indent=2, ensure_ascii=False)
        self.assertTrue(raw.endswith("\n}"))
        slug = "calibration"
        entry_text = json.dumps(registry[slug], ensure_ascii=False)
        path.write_text(raw[:-2] + f',\n  "{slug}": {entry_text}\n}}', encoding="utf-8")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate top-level slug 'calibration'", result.stdout + result.stderr)

    def test_unmutated_copy_passes(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TestWriteModeRoundTrip(ScratchTreeTestCase):
    """generate -> re-load -> unchanged: write mode must restore consistency
    and then be idempotent, so a clean --check implies the tree really is
    byte-stable under regeneration."""

    def test_write_mode_round_trip(self):
        pristine = {
            relative: (self.tmp / relative).read_bytes() for relative in self.COPIES
        }

        # Disturb a derived constant, then let write mode restore it.
        app_js = self.tmp / "site" / "spec-reader" / "app.js"
        app_js.write_text(
            app_js.read_text(encoding="utf-8").replace(
                '[2, "Calibration"]', '[2, "DRIFT"]'
            ),
            encoding="utf-8",
        )
        write = self.run_write()
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertEqual(
            pristine,
            {relative: (self.tmp / relative).read_bytes() for relative in self.COPIES},
            "write mode must regenerate the committed tree byte-identically",
        )

        # Re-load: a second write run and --check must both see no drift.
        rewrite = self.run_write()
        self.assertEqual(rewrite.returncode, 0, rewrite.stdout + rewrite.stderr)
        self.assertEqual(
            pristine,
            {relative: (self.tmp / relative).read_bytes() for relative in self.COPIES},
            "write mode on an already-consistent tree must change nothing",
        )
        check = self.run_check()
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
