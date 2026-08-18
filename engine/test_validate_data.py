#!/usr/bin/env python3
"""Tests for engine/validate_data.py: the JSON Schema gate over data/.

The committed data must always pass; every mutation below is a regression the
gate is meant to catch. Both backends are exercised -- the jsonschema package
when installed, and the built-in stdlib fallback always.

Run:  python3 engine/test_validate_data.py
"""
import contextlib
import copy
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vd = load("validate_data")


def load_data(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def load_schema(name):
    return json.loads((ROOT / "data" / "schema" / name).read_text(encoding="utf-8"))


# False = jsonschema when installed, True = always the built-in fallback.
BACKENDS = (False, True)


class TestCommittedData(unittest.TestCase):
    """The gate must pass on what is committed, on both backends."""

    def test_all_data_files_validate(self):
        for force_stdlib in BACKENDS:
            with self.subTest(force_stdlib=force_stdlib):
                self.assertEqual(vd.validate_all(ROOT, force_stdlib=force_stdlib), [])

    def test_every_data_json_file_has_a_schema_check(self):
        # A new data file must not land without a schema and a check entry.
        on_disk = {p.name for p in (ROOT / "data").glob("*.json")}
        checked = {name for name, _ in vd.CHECKS}
        self.assertEqual(on_disk, checked)

    def test_schemas_are_valid_draft_2020_12(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        for _, schema_name in vd.CHECKS:
            with self.subTest(schema=schema_name):
                jsonschema.Draft202012Validator.check_schema(load_schema(schema_name))


class MutationMixin:
    """Shared machinery: mutate a copy of a committed file, expect failure."""

    DATA_FILE = None
    SCHEMA_FILE = None

    def setUp(self):
        self.schema = load_schema(self.SCHEMA_FILE)
        self.instance = load_data(self.DATA_FILE)

    def assert_invalid(self, mutate, fragment):
        instance = copy.deepcopy(self.instance)
        mutate(instance)
        for force_stdlib in BACKENDS:
            with self.subTest(force_stdlib=force_stdlib):
                errors = vd.validate_instance(instance, self.schema, force_stdlib=force_stdlib)
                self.assertTrue(errors, "mutation should fail validation")
                self.assertTrue(
                    any(fragment in error for error in errors),
                    f"no error mentions {fragment!r}; got: {errors}",
                )

    def assert_valid(self, mutate=None):
        instance = copy.deepcopy(self.instance)
        if mutate:
            mutate(instance)
        for force_stdlib in BACKENDS:
            with self.subTest(force_stdlib=force_stdlib):
                self.assertEqual(
                    vd.validate_instance(instance, self.schema, force_stdlib=force_stdlib), []
                )


class TestCoverageSchema(MutationMixin, unittest.TestCase):
    """data/coverage.json: verdicts need citations, scored fields stay in range."""

    DATA_FILE = "coverage.json"
    SCHEMA_FILE = "coverage.schema.json"

    def test_valid_as_committed(self):
        self.assert_valid()

    def test_missing_required_key_fails(self):
        def mutate(d):
            del d["coverage"][0]["behaviour_id"]
        self.assert_invalid(mutate, "behaviour_id")

    def test_verdict_without_citations_fails(self):
        # data/README.md: no coverage verdict without at least one citation.
        def mutate(d):
            d["coverage"][0]["citations"] = []
        self.assert_invalid(mutate, "citations")

    def test_depth_out_of_range_fails(self):
        def mutate(d):
            d["coverage"][0]["depth_0_4"] = 5
        self.assert_invalid(mutate, "depth_0_4")

    def test_unknown_verdict_fails(self):
        def mutate(d):
            d["coverage"][0]["verdict"] = "excellent"
        self.assert_invalid(mutate, "verdict")

    def test_badly_typed_citation_flag_fails(self):
        def mutate(d):
            d["coverage"][0]["citations"][0]["adjacent"] = "yes"
        self.assert_invalid(mutate, "adjacent")

    def test_unknown_citation_key_fails(self):
        # Citation objects are closed: a typo'd flag is silently ignored by
        # the site builders, so the schema must catch it instead.
        def mutate(d):
            d["coverage"][0]["citations"][0]["exmaple_block"] = True
        self.assert_invalid(mutate, "exmaple_block")

    def test_malformed_verified_date_fails(self):
        def mutate(d):
            d["coverage"][0]["verified_date"] = "last tuesday"
        self.assert_invalid(mutate, "verified_date")

    def test_top_level_wrapper_is_closed(self):
        def mutate(d):
            d["coverag"] = d.pop("coverage")
        self.assert_invalid(mutate, "coverag")


class TestEvalsSchema(MutationMixin, unittest.TestCase):
    """data/evals.json: no eval without a URL, rubric scores stay on the 0-4 scale."""

    DATA_FILE = "evals.json"
    SCHEMA_FILE = "evals.schema.json"

    def test_valid_as_committed(self):
        self.assert_valid()

    def test_eval_without_url_fails(self):
        # data/README.md: no eval without a URL.
        def mutate(d):
            del d["evals"][0]["url"]
        self.assert_invalid(mutate, "url")

    def test_quality_score_above_rubric_max_fails(self):
        def mutate(d):
            d["evals"][0]["quality"]["internal_validity"] = 7
        self.assert_invalid(mutate, "internal_validity")

    def test_unrecognised_facet_fails(self):
        def mutate(d):
            d["evals"][0]["facets"] = ["banana"]
        self.assert_invalid(mutate, "facets")

    def test_null_adherence_band_is_allowed(self):
        # Evals without per-lab results carry band: null, not a missing key.
        def mutate(d):
            d["evals"][0]["adherence"]["anthropic"]["band"] = None
        self.assert_valid(mutate)

    def test_null_source_url_is_allowed(self):
        # A source verified not to exist keeps its record with url: null.
        def mutate(d):
            d["evals"][0]["sources"][0]["url"] = None
        self.assert_valid(mutate)


class TestReaderTestCoverageSchema(MutationMixin, unittest.TestCase):
    """data/reader-test-coverage.json: the bench's behaviour + coverage ledger."""

    DATA_FILE = "reader-test-coverage.json"
    SCHEMA_FILE = "reader-test-coverage.schema.json"

    def test_valid_as_committed(self):
        self.assert_valid()

    def test_bad_slug_fails(self):
        def mutate(d):
            d["behaviours"][0]["slug"] = "Not A Slug"
        self.assert_invalid(mutate, "slug")

    def test_null_verified_against_version_is_allowed(self):
        # Most bench records predate the field; the two that have it carry null.
        def mutate(d):
            d["coverage"][0]["verified_against_version"] = None
        self.assert_valid(mutate)


class TestCrossFileRules(unittest.TestCase):
    """Rules a single-file schema cannot express, run against a scratch repo copy."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="validate-data-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        shutil.copytree(ROOT / "data", self.tmp / "data")

    def rewrite(self, name, mutate):
        path = self.tmp / "data" / name
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_unknown_behaviour_id_in_reader_test_fails(self):
        def mutate(d):
            d["coverage"][0]["behaviour_id"] = 999
        self.rewrite("reader-test-coverage.json", mutate)
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("behaviour_id" in e and "999" in e for e in errors),
            f"no unknown-behaviour error; got: {errors}",
        )

    def test_unknown_lab_id_fails(self):
        def mutate(d):
            d["coverage"][0]["lab_id"] = "deepmind"
        self.rewrite("coverage.json", mutate)
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("lab_id" in e and "deepmind" in e for e in errors),
            f"no unknown-lab error; got: {errors}",
        )

    def test_main_reports_failure_exit_code(self):
        def mutate(d):
            del d["labs"][0]["id"]
        self.rewrite("labs.json", mutate)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            self.assertEqual(vd.main(["--root", str(self.tmp)]), 1)

    def test_main_reports_success_exit_code(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            self.assertEqual(vd.main(["--root", str(self.tmp)]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
