#!/usr/bin/env python3
"""Validate data/*.json against the JSON Schemas in data/schema/.

Usage:
    python3 engine/validate_data.py            # validate all canonical data files
    python3 engine/validate_data.py --stdlib   # force the built-in fallback validator

Uses the `jsonschema` package when it is installed; otherwise falls back to a
built-in stdlib validator covering the keyword subset data/schema/ uses
($ref within the same document, type, enum, required, properties,
additionalProperties, propertyNames, items, minItems, minLength, minimum, maximum, pattern).
Neither path needs a dependency installed, and exit code is non-zero on any
failure, so this can gate CI as-is.

Beyond the per-file schemas, this encodes the cross-file rules from
data/README.md that a single-file schema cannot express:
  - every coverage record's lab_id must exist in data/labs.json;
  - every coverage record's behaviour_id must exist in the behaviour registry
    (data/behaviours.json, index set);
  - every reader-test coverage record's behaviour_id must exist in that
    file's own behaviours list (no unknown behaviour IDs).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (data file, its schema) -- every *.json in data/ must appear here.
# Schemas for artifacts outside data/ live in data/schema/ too but NOT in this
# tuple: spec-coverage-sidecar.schema.json validates the coverage sidecar
# research/sweeps/NN-<slug>/spec-coverage.json and is enforced at publish
# time by engine/publish-coverage.py, not by this gate.
CHECKS = (
    ("behaviours.json", "behaviours.schema.json"),
    ("coverage.json", "coverage.schema.json"),
    ("labs.json", "labs.schema.json"),
    ("panel-cell-curation.json", "panel-cell-curation.schema.json"),
)


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

def _jsonschema_available() -> bool:
    try:
        import jsonschema  # noqa: F401
        return True
    except ImportError:
        return False


def backend_name(force_stdlib: bool = False) -> str:
    if not force_stdlib and _jsonschema_available():
        try:
            from importlib.metadata import version
            return f"jsonschema {version('jsonschema')}"
        except Exception:
            return "jsonschema"
    return "built-in stdlib validator"


def _validate_with_jsonschema(instance, schema) -> list:
    import jsonschema

    validator_cls = jsonschema.validators.validator_for(
        schema, default=jsonschema.Draft202012Validator
    )
    validator_cls.check_schema(schema)
    errors = []
    for error in sorted(
        validator_cls(schema).iter_errors(instance),
        key=lambda e: [str(part) for part in e.absolute_path],
    ):
        where = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        errors.append(f"{where}: {error.message}")
    return errors


# --- built-in fallback (stdlib only) ----------------------------------------

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}


def _json_type_name(value) -> str:
    for name, check in _TYPE_CHECKS.items():
        if name != "number" and check(value):
            return name
    return type(value).__name__


def _resolve_ref(ref: str, root_schema: dict) -> dict:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported $ref {ref!r}: only same-document refs (#/...) are handled")
    node = root_schema
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"$ref {ref!r} does not resolve to a schema object")
    return node


# Validation keywords the fallback implements (the subset data/schema/ uses).
_SUPPORTED_KEYWORDS = {
    "type", "enum", "required", "properties", "additionalProperties",
    "propertyNames", "items", "minItems", "minLength", "minimum", "maximum",
    "pattern", "$ref",
}

# Annotation/meta keywords with no validation semantics (draft 2020-12);
# safe for the fallback to ignore.
_ANNOTATION_KEYWORDS = {
    "$schema", "$id", "$defs", "$comment", "title", "description",
    "default", "examples", "deprecated", "readOnly", "writeOnly",
}


def _check_supported_keywords(schema, location, errors) -> None:
    """Fail loudly on any validation keyword the fallback does not implement.

    Scans the whole schema document (not just the parts one instance reaches),
    so a future edit that leans on e.g. oneOf, format or uniqueItems breaks
    the gate here instead of silently validating less than the jsonschema
    backend does.
    """
    if not isinstance(schema, dict):
        return
    for key in schema:
        if key not in _SUPPORTED_KEYWORDS and key not in _ANNOTATION_KEYWORDS:
            errors.append(
                f"schema at {location}: unsupported keyword {key!r} -- the built-in "
                f"validator implements only: {', '.join(sorted(_SUPPORTED_KEYWORDS))}; "
                f"extend the fallback or install jsonschema"
            )
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name, sub in properties.items():
            _check_supported_keywords(sub, f"{location}.properties.{name}", errors)
    items = schema.get("items")
    if isinstance(items, dict):
        _check_supported_keywords(items, f"{location}.items", errors)
    elif isinstance(items, list):
        errors.append(
            f"schema at {location}.items: list-valued items (tuple validation) "
            f"is not implemented by the built-in validator -- extend the "
            f"fallback or install jsonschema"
        )
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        _check_supported_keywords(additional, f"{location}.additionalProperties", errors)
    prop_names = schema.get("propertyNames")
    if isinstance(prop_names, dict):
        _check_supported_keywords(prop_names, f"{location}.propertyNames", errors)
    defs = schema.get("$defs")
    if isinstance(defs, dict):
        for name, sub in defs.items():
            _check_supported_keywords(sub, f"{location}.$defs.{name}", errors)


def _validate_node(instance, schema, root_schema, path, errors) -> None:
    if "$ref" in schema:
        # Single-level resolution: the referenced node must not itself be a
        # $ref. All schemas in data/schema/ use one hop into $defs; if a
        # future schema chains refs, loop here instead.
        schema = _resolve_ref(schema["$ref"], root_schema)

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        unknown = [t for t in types if t not in _TYPE_CHECKS]
        if unknown:
            raise ValueError(f"unknown type name(s) {unknown!r} in schema at {path}")
        if not any(_TYPE_CHECKS[t](instance) for t in types):
            errors.append(
                f"{path}: expected type {' or '.join(types)}, got {_json_type_name(instance)}"
            )
            return  # further checks on a mistyped value are only noise

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string is shorter than minLength {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: {instance!r} does not match pattern {schema['pattern']!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} is less than minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} is greater than maximum {schema['maximum']}")

    if isinstance(instance, dict):
        prop_names = schema.get("propertyNames")
        if isinstance(prop_names, dict):
            for key in instance:
                _validate_node(key, prop_names, root_schema, f"{path}.<propertyNames:{key}>", errors)
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required key '{key}'")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                _validate_node(value, properties[key], root_schema, f"{path}.{key}", errors)
            elif additional is False:
                errors.append(f"{path}: unexpected key '{key}'")
            elif isinstance(additional, dict):
                _validate_node(value, additional, root_schema, f"{path}.{key}", errors)

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: array has {len(instance)} item(s), minItems is {schema['minItems']}")
        if "items" in schema:
            for index, item in enumerate(instance):
                _validate_node(item, schema["items"], root_schema, f"{path}[{index}]", errors)


def _validate_with_stdlib(instance, schema) -> list:
    errors = []
    _check_supported_keywords(schema, "$", errors)
    if errors:
        return errors  # the schema itself is broken for this backend
    _validate_node(instance, schema, schema, "$", errors)
    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_instance(instance, schema, force_stdlib: bool = False) -> list:
    """Validate one already-loaded JSON value against one schema.

    Returns a list of error strings; empty means valid.
    """
    if not force_stdlib and _jsonschema_available():
        return _validate_with_jsonschema(instance, schema)
    return _validate_with_stdlib(instance, schema)


# Sentinel distinguishing "load failed" from a successfully parsed JSON
# `null` (json.loads("null") is None, which is valid JSON the schemas must
# reject as a mistyped document, not skip as a read error).
_MISSING = object()


def _load_json(path: Path, errors: list):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path.name}: file not found at {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
    return _MISSING


def _cross_file_checks(files: dict) -> list:
    """Rules a single-file schema cannot express (see data/README.md)."""
    errors = []

    labs = files.get("labs.json")
    lab_ids = {
        lab.get("id")
        for lab in labs.get("labs", [])
        if isinstance(lab, dict)
    } if isinstance(labs, dict) else set()
    if not lab_ids:
        # Without a usable registry the membership checks below cannot run.
        # Say so loudly: a broken registry must not masquerade as a passing
        # gate just because nothing got checked against it.
        errors.append("cross-file lab_id checks skipped: labs.json missing or empty")

    def check_lab_ids(file_name, records, array_name="coverage"):
        for index, record in enumerate(records or []):
            if not isinstance(record, dict):
                continue
            lab_id = record.get("lab_id")
            if lab_id is not None and lab_ids and lab_id not in lab_ids:
                errors.append(
                    f"{file_name}: {array_name}[{index}]: lab_id {lab_id!r} is not "
                    f"defined in data/labs.json (known: {sorted(lab_ids, key=str)})"
                )

    def check_unique_records(file_name, records):
        # Exactly one record per (behaviour_id, lab_id): the published reader
        # silently absorbs duplicates (first record wins) and the bench
        # builder hard-crashes on them, so duplicates must fail at the gate.
        seen = {}
        for index, record in enumerate(records or []):
            if not isinstance(record, dict):
                continue
            if record.get("behaviour_id") is None or record.get("lab_id") is None:
                continue  # schema-invalid record; the schema errors cover it
            key = (record.get("behaviour_id"), record.get("lab_id"))
            if key in seen:
                errors.append(
                    f"{file_name}: coverage[{index}]: duplicate record for "
                    f"behaviour_id={key[0]!r} lab_id={key[1]!r} "
                    f"(first at coverage[{seen[key]}])"
                )
            else:
                seen[key] = index

    coverage = files.get("coverage.json")
    if isinstance(coverage, dict):
        check_lab_ids("coverage.json", coverage.get("coverage"))
        check_unique_records("coverage.json", coverage.get("coverage"))

    registry = files.get("behaviours.json")
    index_ids = {
        entry.get("numeric_id")
        for entry in registry.values()
        if isinstance(entry, dict) and entry.get("set") == "index"
    } if isinstance(registry, dict) else set()

    if not index_ids:
        errors.append(
            "behaviour registry checks skipped: behaviours.json missing or "
            "has no index-set entries"
        )

    if index_ids and isinstance(coverage, dict):
        for index, record in enumerate(coverage.get("coverage") or []):
            if not isinstance(record, dict):
                continue
            behaviour_id = record.get("behaviour_id")
            if behaviour_id is not None and behaviour_id not in index_ids:
                errors.append(
                    f"coverage.json: coverage[{index}]: behaviour_id {behaviour_id!r} "
                    f"is not an index-set id in the behaviour registry (data/behaviours.json)"
                )

    curation = files.get("panel-cell-curation.json")
    if isinstance(curation, dict):
        cells = curation.get("cells")
        check_lab_ids("panel-cell-curation.json", cells, "cells")
        registry_slugs = set(registry) if isinstance(registry, dict) else set()
        if not registry_slugs:
            # Same rule as above: with no registry there is nothing to check
            # the slugs against, and that must fail the gate instead of
            # silently skipping the membership check.
            errors.append(
                "cross-file slug checks skipped: behaviours.json missing or empty"
            )
        seen = {}
        for index, cell in enumerate(cells or []):
            if not isinstance(cell, dict):
                continue
            slug = cell.get("slug")
            if slug is not None and registry_slugs and slug not in registry_slugs:
                errors.append(
                    f"panel-cell-curation.json: cells[{index}]: slug {slug!r} "
                    f"is not a behaviour slug in the registry (data/behaviours.json)"
                )
            if slug is None or cell.get("lab_id") is None:
                continue  # schema-invalid cell; the schema errors cover it
            key = (slug, cell["lab_id"])
            if key in seen:
                errors.append(
                    f"panel-cell-curation.json: cells[{index}]: duplicate cell for "
                    f"slug={key[0]!r} lab_id={key[1]!r} (first at cells[{seen[key]}])"
                )
            else:
                seen[key] = index

    return errors


def validate_all(root=None, force_stdlib: bool = False) -> list:
    """Validate every data file in CHECKS plus the cross-file rules.

    Returns a list of error strings; empty means all committed data is valid.
    """
    root = Path(root) if root is not None else ROOT
    data_dir = root / "data"

    errors = []
    files = {}
    for data_name, schema_name in CHECKS:
        instance = _load_json(data_dir / data_name, errors)
        schema = _load_json(data_dir / "schema" / schema_name, errors)
        if instance is _MISSING or schema is _MISSING:
            continue
        files[data_name] = instance
        errors.extend(
            f"{data_name}: {error}"
            for error in validate_instance(instance, schema, force_stdlib=force_stdlib)
        )

    errors.extend(_cross_file_checks(files))
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--stdlib",
        action="store_true",
        help="force the built-in fallback validator even if jsonschema is installed",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to validate (default: this repo)",
    )
    args = parser.parse_args(argv)

    errors = validate_all(args.root, force_stdlib=args.stdlib)
    for error in errors:
        print(error)

    checked = ", ".join(name for name, _ in CHECKS)
    if errors:
        print(f"\nFAIL: {len(errors)} validation error(s) across {checked}", file=sys.stderr)
        return 1
    print(f"OK: {checked} validate against data/schema/ (backend: {backend_name(args.stdlib)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
