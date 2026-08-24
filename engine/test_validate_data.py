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


class TestBehavioursSchema(MutationMixin, unittest.TestCase):
    """data/behaviours.json: the behaviour registry, slug-keyed and closed.

    Per-set numeric_id uniqueness is NOT a schema property (JSON Schema has
    no cross-entry uniqueness keyword that fits); it is pinned by
    tests/test_behaviour_registry.py::test_numeric_ids_are_unique_per_set.
    """

    DATA_FILE = "behaviours.json"
    SCHEMA_FILE = "behaviours.schema.json"

    def test_valid_as_committed(self):
        self.assert_valid()

    def test_bad_top_level_slug_key_fails(self):
        # Top-level keys are kebab-case slugs (the schema's propertyNames);
        # the stdlib fallback implements propertyNames, so both backends run.
        def mutate(d):
            d["Not Kebab Case!"] = d.pop("no-sycophancy")
        # Both backends name the offending key (jsonschema doesn't echo the
        # word "propertyNames" itself).
        self.assert_invalid(mutate, "Not Kebab Case")


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

    def test_negative_depth_fails(self):
        # Pins the schema's minimum bound, not just its maximum.
        def mutate(d):
            d["coverage"][0]["depth_0_4"] = -1
        self.assert_invalid(mutate, "depth_0_4")

    def test_unknown_record_key_fails(self):
        # Coverage records are closed: new fields need a schema change and review.
        def mutate(d):
            d["coverage"][0]["severity"] = "high"
        self.assert_invalid(mutate, "severity")

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

    def test_min_length_boundary_is_strict_less_than(self):
        # minLength means `<`, not `<=`: a string of length minLength-1 fails,
        # length minLength passes. Pins the stdlib fallback's boundary to the
        # jsonschema backend's (citation quote has minLength 1).
        def below_boundary(d):
            d["coverage"][0]["citations"][0]["quote"] = ""  # length 0 < 1
        self.assert_invalid(below_boundary, ".quote")

        def at_boundary(d):
            d["coverage"][0]["citations"][0]["quote"] = "x"  # length 1 == minLength
        self.assert_valid(at_boundary)


class TestLabsSchema(MutationMixin, unittest.TestCase):
    """data/labs.json: the lab registry coverage records join against."""

    DATA_FILE = "labs.json"
    SCHEMA_FILE = "labs.schema.json"

    def test_valid_as_committed(self):
        self.assert_valid()

    def test_empty_required_string_fails(self):
        # Pins the minLength bound: an empty join key is not a lab.
        def mutate(d):
            d["labs"][0]["id"] = ""
        self.assert_invalid(mutate, ".id")

    def test_unknown_lab_key_fails(self):
        # Lab records are closed: new fields need a schema change and review.
        def mutate(d):
            d["labs"][0]["headquarters"] = "SF"
        self.assert_invalid(mutate, "headquarters")


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

    def test_unknown_record_key_fails(self):
        # Bench coverage records are closed, same policy as data/coverage.json.
        def mutate(d):
            d["coverage"][0]["severity"] = "high"
        self.assert_invalid(mutate, "severity")

    def test_null_verified_against_version_is_allowed(self):
        # Most bench records predate the field; the two that have it carry null.
        def mutate(d):
            d["coverage"][0]["verified_against_version"] = None
        self.assert_valid(mutate)

    def test_empty_citations_allowed_for_absence_findings(self):
        # The bench models "the spec says nothing about this behaviour" as a
        # record whose citations are empty, never a missing record (see
        # engine/build-reader-test-data.py). The published coverage.json keeps
        # the >=1 rule; only the bench relaxes it.
        def mutate(d):
            d["coverage"][0]["citations"] = []
        self.assert_valid(mutate)


class TestPropertyNamesFallback(unittest.TestCase):
    """The stdlib fallback enforces propertyNames (the registry's slug rule)."""

    SCHEMA = {"type": "object", "propertyNames": {"pattern": "^[a-z][a-z0-9-]*$"}}

    def test_invalid_property_name_fails_on_stdlib(self):
        errors = vd._validate_with_stdlib({"Bad Key!": 1}, self.SCHEMA)
        self.assertTrue(
            any("propertyNames" in e and "pattern" in e for e in errors),
            f"no propertyNames error; got: {errors}",
        )

    def test_valid_property_names_pass_on_stdlib(self):
        self.assertEqual(vd._validate_with_stdlib({"good-key": 1}, self.SCHEMA), [])


class TestStdlibKeywordGuard(unittest.TestCase):
    """The stdlib fallback implements a keyword subset; any other validation
    keyword must fail loudly, never be silently skipped -- otherwise a schema
    edit silently diverges the two backends."""

    def assert_flagged(self, schema, instance, keyword, location):
        errors = vd.validate_instance(instance, schema, force_stdlib=True)
        self.assertTrue(errors, f"unsupported keyword {keyword!r} passed silently")
        self.assertTrue(
            any(keyword in error and location in error for error in errors),
            f"no error names {keyword!r} at {location!r}; got: {errors}",
        )

    def test_format_is_flagged(self):
        schema = {"type": "string", "format": "date"}
        self.assert_flagged(schema, "2026-01-01", "format", "$")

    def test_one_of_is_flagged(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        self.assert_flagged(schema, 1, "oneOf", "$")

    def test_unique_items_nested_under_items_is_flagged_with_location(self):
        schema = {"type": "array", "items": {"type": "integer", "uniqueItems": True}}
        self.assert_flagged(schema, [1, 2], "uniqueItems", "$.items")

    def test_supported_keywords_pass_the_guard(self):
        # Positive control: the keyword subset the committed schemas use.
        schema = {
            "type": "object",
            "required": ["a"],
            "additionalProperties": False,
            "properties": {
                "a": {"type": "string", "minLength": 1, "pattern": "^[a-z]+$"},
                "b": {"type": "array", "minItems": 1, "items": {"type": "integer", "minimum": 0, "maximum": 4}},
                "c": {"enum": ["x", "y"]},
            },
        }
        self.assertEqual(
            vd.validate_instance({"a": "ok", "b": [1], "c": "x"}, schema, force_stdlib=True),
            [],
        )


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

    def test_missing_behaviour_registry_fails_loudly(self):
        # Without behaviours.json the registry membership checks cannot run;
        # the gate must say so explicitly, not pass silently.
        (self.tmp / "data" / "behaviours.json").unlink()
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("behaviour registry checks skipped" in e for e in errors),
            f"no registry-skip error; got: {errors}",
        )

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

    def test_missing_labs_registry_fails_loudly(self):
        # Without labs.json the lab_id membership checks cannot run; the gate
        # must say so explicitly instead of passing because nothing was checked.
        (self.tmp / "data" / "labs.json").unlink()
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("lab_id checks skipped" in e and "labs.json" in e for e in errors),
            f"no registry-skip error; got: {errors}",
        )

    def test_empty_reader_test_behaviours_fails_loudly(self):
        # Same rule for the bench's own registry: an empty behaviours list
        # disables the behaviour_id membership check and must fail the gate.
        def mutate(d):
            d["behaviours"] = []
        self.rewrite("reader-test-coverage.json", mutate)
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("behaviour_id checks skipped" in e for e in errors),
            f"no behaviours-skip error; got: {errors}",
        )

    def test_unsupported_keyword_in_schema_fails_loudly_on_stdlib(self):
        # A schema edit leaning on a keyword the stdlib fallback does not
        # implement must break the gate, naming the keyword -- never silently
        # skip the check and diverge from the jsonschema backend.
        def mutate(schema):
            schema["$defs"]["citation"]["uniqueItems"] = True
        self.rewrite("schema/coverage.schema.json", mutate)
        errors = vd.validate_all(self.tmp, force_stdlib=True)
        self.assertTrue(
            any("uniqueItems" in e and "unsupported keyword" in e for e in errors),
            f"no unsupported-keyword error; got: {errors}",
        )

    def test_behaviour_id_unknown_to_the_registry_fails(self):
        # coverage.json behaviour_ids join against the index set of the
        # behaviour registry (data/behaviours.json).
        def mutate(d):
            d["coverage"][0]["behaviour_id"] = 999
        self.rewrite("coverage.json", mutate)
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("behaviour_id" in e and "999" in e and "registry" in e for e in errors),
            f"no unknown-registry-behaviour error; got: {errors}",
        )

    def test_malformed_json_fails(self):
        # Unparseable data must fail the gate loudly, never pass silently.
        (self.tmp / "data" / "coverage.json").write_text("{ not json", encoding="utf-8")
        errors = vd.validate_all(self.tmp)
        self.assertTrue(
            any("coverage.json" in e and "invalid JSON" in e for e in errors),
            f"no invalid-JSON error; got: {errors}",
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            self.assertEqual(vd.main(["--root", str(self.tmp)]), 1)

    def test_null_json_file_fails(self):
        # A file containing literal JSON null parses fine (json.loads("null")
        # is None) but is a wrong-type document: the gate must reject it, not
        # confuse it with a load failure and skip it silently.
        (self.tmp / "data" / "coverage.json").write_text("null", encoding="utf-8")
        errors = vd.validate_all(self.tmp)
        # Both backends report the top-level type mismatch, in their own
        # wording ("None is not of type 'object'" vs "expected type object").
        self.assertTrue(
            any("coverage.json" in e and "type" in e for e in errors),
            f"null coverage.json passed silently; got: {errors}",
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            self.assertEqual(vd.main(["--root", str(self.tmp)]), 1)

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
