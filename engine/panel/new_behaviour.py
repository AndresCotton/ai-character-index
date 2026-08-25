#!/usr/bin/env python3
"""Register a new user behaviour and print the commands that judge and display it.

  python3 engine/panel/new_behaviour.py <slug> --name="..." --definition="..." \
      [--facet="..."]... [--scope="..."] [--group="..."]

Writes the registry row (data/behaviours.json: set "user", next free numeric_id).
--scope additionally writes the judge-prompt entry in this directory's
behaviours.json -- the boundary field the registry shape cannot carry -- and the
printed judge command then drops --registry= so whole_doc.py reads that entry.
Refuses an existing slug; never rewrites other entries' bytes.

  --registry=PATH     registry file to write (default data/behaviours.json)
  --panel-file=PATH   judge-prompt file for --scope (default engine/panel/behaviours.json)
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FLAGS = ("--name=", "--definition=", "--facet=", "--scope=", "--group=",
         "--registry=", "--panel-file=")


def parse_args(argv):
    """Options dict from = -form flags; loud exit on anything else (a space-form
    flag would be eaten as a positional, the failure whole_doc.py documents)."""
    opts = {"facets": []}
    positional = []
    for a in argv:
        if a in ("--help", "-h"):
            sys.exit(__doc__.strip())
        if a.startswith("-"):
            for f in FLAGS:
                if a.startswith(f):
                    if f == "--facet=":
                        opts["facets"].append(a[len(f):])
                    else:
                        opts[f[2:-1].replace("-", "_")] = a[len(f):]
                    break
            else:
                sys.exit(f"unknown argument {a!r} -- valid: "
                         + " ".join(f + "..." for f in FLAGS) + " (use =, not a space)")
        else:
            positional.append(a)
    if len(positional) != 1:
        sys.exit(__doc__.strip())
    slug = positional[0]
    if not SLUG.match(slug):
        sys.exit(f"slug {slug!r} must be kebab-case: lowercase letters/digits, single hyphens")
    if not (opts.get("name") or "").strip():
        sys.exit("--name= is required and must be non-empty")
    if not (opts.get("definition") or "").strip():
        sys.exit("--definition= is required and must be non-empty: "
                 "the statement the judges score against")
    if any(not f.strip() for f in opts["facets"]):
        sys.exit("--facet= values must be non-empty")
    opts["slug"] = slug
    return opts


def next_user_id(registry):
    """Next numeric_id in the user set. Ids are per-set (file-local), so index
    and reader-test rows never count."""
    ids = [e["numeric_id"] for e in registry.values()
           if isinstance(e, dict) and e.get("set") == "user"]
    return max(ids, default=0) + 1


def load_json(path):
    """(parsed, had_trailing_newline) -- the newline state rides along so the
    write puts the file back exactly as formatted."""
    try:
        raw = path.read_text()
    except FileNotFoundError:
        sys.exit(f"not found: {path}")
    try:
        return json.loads(raw), raw.endswith("\n")
    except json.JSONDecodeError as e:
        sys.exit(f"{path} is not valid JSON: {e}")


def write_json(path, data, trailing_newline):
    """The format both registry files carry -- 2-space indent, unescaped
    unicode -- plus the file's own trailing-newline state, so every byte
    outside the new entry survives."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)
                    + ("\n" if trailing_newline else ""))


def main(argv=None):
    o = parse_args(sys.argv[1:] if argv is None else argv)
    registry_path = Path(o.get("registry") or ROOT / "data" / "behaviours.json")
    panel_path = Path(o.get("panel_file") or HERE / "behaviours.json")
    scoped = bool((o.get("scope") or "").strip())

    registry, reg_nl = load_json(registry_path)
    if o["slug"] in registry:
        sys.exit(f"{o['slug']!r} already exists in {registry_path} -- pick another "
                 "slug or edit that entry by hand")
    if scoped:
        panel, panel_nl = load_json(panel_path)
        if o["slug"] in panel:
            sys.exit(f"{o['slug']!r} already exists in {panel_path}")

    nid = next_user_id(registry)
    registry[o["slug"]] = {
        "name": o["name"].strip(),
        "set": "user",
        "numeric_id": nid,
        "group": (o.get("group") or "").strip() or None,
        "definition": o["definition"].strip(),
        "facets": [f.strip() for f in o["facets"]],
    }
    write_json(registry_path, registry, reg_nl)
    lines = [f"registered {o['slug']!r} (user set, id {nid}) in {registry_path}"]

    if scoped:
        entry = {"label": o["name"].strip(), "title": o["name"].strip(),
                 "query": o["definition"].strip()}
        if o["facets"]:
            entry["clarifications"] = " ".join(f.strip() for f in o["facets"])
        entry["boundary"] = o["scope"].strip()
        panel[o["slug"]] = entry
        write_json(panel_path, panel, panel_nl)
        lines.append(f"wrote the judge-prompt entry (with scope) in {panel_path}")

    judge_registry = "" if scoped else " --registry=data/behaviours.json"
    lines += [
        "",
        "Judge it -- needs keys (see engine/panel/.env.example); swap frontier_fast",
        "for itest to rehearse the whole flow for about two cents:",
        f"  python3 engine/panel/whole_doc.py {o['slug']} constitution,model-spec "
        f"frontier_fast{judge_registry} --runlog=engine/panel/runlog-user.jsonl",
        "",
        "Build the viewer payload (judged on another panel? mirror it in --panel=):",
        f"  python3 engine/panel/build_site_data.py --runlog=engine/panel/runlog-user.jsonl "
        f"--panel=frontier_fast --behaviours={o['slug']}",
        "",
        "View it:",
        "  python3 -m http.server 8080 --directory site",
        "  then open http://localhost:8080/spec-reader/",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
