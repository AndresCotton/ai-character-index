#!/usr/bin/env python3
"""Unit tests for new_behaviour.py, the user-behaviour registrar. No network, no
keys, sub-second. Run:  python3 engine/panel/test_new_behaviour.py
"""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nb = load("new_behaviour")

REGISTRY = {
    "no-sycophancy": {"name": "No sycophancy", "set": "index", "numeric_id": 9,
                      "group": "Honesty", "definition": "d", "facets": []},
    "mine": {"name": "Mine", "set": "user", "numeric_id": 3,
             "group": None, "definition": "d", "facets": []},
}
PANEL = '{\n  "x": {\n    "label": "X",\n    "query": "q"\n  }\n}'   # no trailing \n


class Fixture(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        self.registry = d / "registry.json"
        self.registry.write_text(json.dumps(REGISTRY, indent=2) + "\n")
        self.panel = d / "panel.json"
        self.panel.write_text(PANEL)

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            nb.main([*args, f"--registry={self.registry}",
                     f"--panel-file={self.panel}"])
        return out.getvalue()


class UserIdsCountOnlyTheUserSet(Fixture):
    """Guards: numeric_id is per-set -- an index row's id 9 must not push the
    next user id to 10."""

    def test_next_id_is_max_user_plus_one(self):
        self.run_cli("fresh-slug", "--name=F", "--definition=D")
        entry = json.loads(self.registry.read_text())["fresh-slug"]
        self.assertEqual(entry["numeric_id"], 4)
        self.assertEqual(entry["set"], "user")

    def test_empty_user_set_starts_at_one(self):
        reg = {k: v for k, v in REGISTRY.items() if v["set"] != "user"}
        self.registry.write_text(json.dumps(reg, indent=2) + "\n")
        self.run_cli("fresh-slug", "--name=F", "--definition=D")
        self.assertEqual(json.loads(self.registry.read_text())["fresh-slug"]["numeric_id"], 1)


class RefusalsLeaveFilesUntouched(Fixture):
    """Guards: a refused run must not half-write -- the registry's bytes stay
    exactly as they were."""

    def refused(self, *args):
        before = self.registry.read_bytes()
        with self.assertRaises(SystemExit):
            self.run_cli(*args)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_duplicate_slug(self):
        self.refused("mine", "--name=M", "--definition=D")

    def test_bad_slug(self):
        self.refused("Bad_Slug", "--name=B", "--definition=D")

    def test_missing_definition(self):
        self.refused("fresh-slug", "--name=F")

    def test_space_form_flag(self):
        self.refused("fresh-slug", "--name", "F", "--definition=D")


class ScopeWritesTheJudgePromptEntry(Fixture):
    """Guards: --scope is the one field the registry shape cannot carry -- it
    must land in the panel file, and the printed judge command must not point
    whole_doc.py back at the registry (which would silently drop the scope)."""

    def test_scope_lands_as_boundary_and_registry_flag_is_dropped(self):
        out = self.run_cli("fresh-slug", "--name=F", "--definition=D",
                           "--scope=NOT this", "--facet=One.", "--facet=Two.")
        entry = json.loads(self.panel.read_text())["fresh-slug"]
        self.assertEqual(entry["boundary"], "NOT this")
        self.assertEqual(entry["query"], "D")
        self.assertEqual(entry["clarifications"], "One. Two.")
        self.assertNotIn("--registry=", out.split("build_site_data")[0])

    def test_no_scope_leaves_panel_file_alone_and_keeps_registry_flag(self):
        before = self.panel.read_bytes()
        out = self.run_cli("fresh-slug", "--name=F", "--definition=D")
        self.assertEqual(self.panel.read_bytes(), before)
        self.assertIn("--registry=data/behaviours.json", out)


class OtherEntriesBytesSurvive(Fixture):
    """Guards: registering must append, never reformat -- including each file's
    own trailing-newline state (the panel file ships without one)."""

    def test_registry_round_trips_and_keeps_existing_entries(self):
        self.run_cli("fresh-slug", "--name=F", "--definition=D", "--scope=s")
        reg_text = self.registry.read_text()
        reg = json.loads(reg_text)
        for slug, entry in REGISTRY.items():
            self.assertEqual(reg[slug], entry)
        self.assertEqual(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", reg_text)
        panel_text = self.panel.read_text()
        self.assertFalse(panel_text.endswith("\n"))
        self.assertEqual(json.loads(panel_text)["x"], {"label": "X", "query": "q"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
