#!/usr/bin/env python3
"""Build site/llm-panel-review/data/behaviours.json from panel verdicts.

Implements the MVP display rules from panel-config.json `display`:
  - only the listed behaviours appear in the sidebar;
  - each passage gets score = sum over panel models of (core=2, related=1, unrelated=0);
  - every passage with score >= 1 is emitted as a citation (the page filters at
    render time via ?threshold= / ?related= URL params, defaults 6/1);
  - the citation `role` (shown when the reader clicks "?") lists each model's decision.

Behaviour names/definitions come from data/reader-test-coverage.json exactly as supplied
(no rewriting). Curated row-level verdict/depth/notes are carried through untouched.

  python3 build_site_data.py --runlog=<runlog> --rubric=v3w --panel=frontier
  (the shipped data: --runlog=runlog-v3.jsonl committed in engine/panel/, rubric v3w)

Output: by DEFAULT each run emits its own timestamped file
  site/llm-panel-review/data/behaviours-<YYYY-MM-DDTHH-MM-SS>.json
(hyphen-separated: lexicographically sortable = chronological, URL-safe) and updates
  site/llm-panel-review/data/manifest.json
({"latest": <filename>, "runs": [newest-first]}), which the page reads to pick what to
show. A second build in the same second takes a numeric sequence suffix
(behaviours-<ts>-02.json, then -03, ... -- zero-padded) so a run is never silently
overwritten.
--out=<name> writes that exact file instead and leaves the manifest alone --
--out=behaviours.json rebuilds the shipped fallback a fresh clone loads. The name is
validated (SAFE_NAME chars, no path separators or .. traversal), so it cannot write
outside the data dir.
"""
import collections
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONFIG = json.loads((HERE / "panel-config.json").read_text())
DISPLAY = CONFIG["display"]
LAB = {"constitution": "anthropic", "model-spec": "openai"}
MODEL_LABEL = {"sol": "GPT-5.6 Sol", "fable": "Claude Fable 5", "qwen-max": "Qwen3.7-Max", "kimi": "Kimi-K3", "kimi-k2": "Kimi-K2.6", "qwen-big": "Qwen3-235B", "opus": "Claude Opus 4.8",
               "gpt-mini": "GPT-5 mini", "haiku": "Claude Haiku 4.5", "qwen-small": "Qwen3-32B"}
# panel behaviour keys -> site slugs
SLUGS = {"helpfulness": "helpfulness", "third-party-harm": "harm-avoidance-to-third-parties",
         "over-under-caution": "avoiding-over-and-under-caution",
         "harmlessness-to-user": "harmlessness-to-the-user",
         "proportionate-risk": "proportionate-risk-mitigation", "tradeoffs": "how-to-approach-tradeoffs",
         "objectivity": "objectivity-on-contested-questions", "user-autonomy": "user-autonomy",
         "general-welfare": "animal-welfare-impacts"}
SLUGS_EXTRA = {"general-welfare": ["general-welfare-impacts-strict"]}   # one run feeds both general-guidelines rows

DATA_DIR = ROOT / "site" / "llm-panel-review" / "data"
MANIFEST_NAME = "manifest.json"
FALLBACK_NAME = "behaviours.json"
# The same character set app.js admits for ?data= -- a run name doubles as a URL param.
# re.ASCII: JavaScript's \w is ASCII [A-Za-z0-9_], but Python's \w is Unicode by
# default and would admit accented/non-Latin names the page's DATA_NAME rejects.
SAFE_NAME = re.compile(r"^[\w.-]+$", re.ASCII)


def run_timestamp(dt, seq=0):
    """Run-file timestamp: hyphen-separated so it is URL-safe, and lexicographically
    sortable = chronological. A same-second rerun takes a sequence suffix (seq >= 2, zero-padded to two digits,
    e.g. …T17-26-20-02) that still sorts after the bare stamp and before the next
    second, so lexical == chronological survives collisions."""
    ts = dt.strftime("%Y-%m-%dT%H-%M-%S")
    return f"{ts}-{seq:02d}" if seq else ts


def next_run_name(data_dir, dt):
    """(filename, timestamp) for a new run: behaviours-<ts>.json, or the first free
    behaviours-<ts>-N.json (N = 2, 3, ...) when that second already has a run file --
    a provenance ledger must never silently overwrite a run."""
    ts = run_timestamp(dt)
    name = f"behaviours-{ts}.json"
    seq = 2
    while (Path(data_dir) / name).exists():
        ts = run_timestamp(dt, seq)
        name = f"behaviours-{ts}.json"
        seq += 1
    return name, ts


def update_manifest(manifest, entry):
    """Pure: the manifest that results from inserting `entry` (replacing any entry with
    the same filename). Runs stay newest-first and `latest` names the newest one.
    Same-second runs carry run_timestamp() sequence suffixes, so the timestamp sort
    alone keeps them in build order."""
    runs = [r for r in manifest.get("runs", []) if r.get("filename") != entry["filename"]]
    runs.append(entry)
    runs.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return {"latest": runs[0]["filename"], "runs": runs}


def read_manifest(path):
    """The manifest at `path`; a fresh clone (none yet) is an empty one. A file that
    parses to something other than a dict (a JSON null or array) is treated exactly
    like an absent one -- the page tolerates an odd manifest by falling through its
    fetch/parse guards, so the builder/CLI must degrade to the empty default too,
    never crash on .get(). A `runs` value that is not a list of dicts is normalized
    the same way (dropped to [] / non-dict entries filtered), so a half-written or
    hand-edited ledger degrades instead of tracebacking update_manifest/select_run."""
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {"latest": None, "runs": []}
    if not isinstance(doc, dict):
        return {"latest": None, "runs": []}
    runs = doc.get("runs")
    doc["runs"] = [r for r in runs if isinstance(r, dict)] if isinstance(runs, list) else []
    return doc


def _loadable(path):
    """True when the file exists and parses as JSON -- how the page consumes it."""
    try:
        json.loads(Path(path).read_text())
        return True
    except (OSError, ValueError):
        return False


def as_json_name(name):
    """Normalize a pin/latest entry to its .json filename."""
    return name[:-5] + ".json" if name.endswith(".json") else name + ".json"


def _payload_name(name):
    """Whether `name` may resolve as a payload in the pin/latest chain. It must pass
    the SAFE_NAME charset AND be a behaviours payload -- never the manifest. Pinning
    (or pointing `latest` at) manifest.json would render the run ledger as if it were
    a behaviour set, so the chain refuses it; only behaviours*.json files are payloads
    here. A non-string (malformed manifest latest) is refused too -- that subsumes the
    old isinstance guard / app.js's `typeof latest === "string"` check. Mirrors
    payloadName() in site/llm-panel-review/app.js."""
    if not isinstance(name, str) or not name:
        return False
    if not SAFE_NAME.match(name):
        return False
    fname = as_json_name(name)
    if fname == MANIFEST_NAME:
        return False
    return fname.startswith("behaviours")


def resolve_data_name(data_dir, pin=None, manifest=None):
    """The resolution chain site/llm-panel-review/app.js implements, for CLI tooling:
    pin (?data= / --pin) -> manifest latest -> shipped behaviours.json.
    Returns (filename, source) with source one of pin/latest/fallback; a name that
    fails _payload_name (charset, the manifest itself, a non-behaviours file, or a
    non-string) or a file that is absent or unparseable falls through to the next
    source. (None, None) when nothing would load."""
    data_dir = Path(data_dir)

    if _payload_name(pin):
        fname = as_json_name(pin)
        if _loadable(data_dir / fname):
            return fname, "pin"
    latest = (manifest or {}).get("latest")
    if _payload_name(latest):
        fname = as_json_name(latest)
        if _loadable(data_dir / fname):
            return fname, "latest"
    if _loadable(data_dir / FALLBACK_NAME):
        return FALLBACK_NAME, "fallback"
    return None, None


def check_out_name(name):
    """Loud-fail an --out= name that could write outside the site data dir: the same
    SAFE_NAME charset ?data= admits (so no path separators), no .. traversal, and
    never the manifest itself (case-insensitively -- on a case-insensitive
    filesystem Manifest.JSON would clobber it too) -- a build must not overwrite
    the provenance ledger."""
    if name.casefold() == MANIFEST_NAME:
        sys.exit(f"error: --out={name!r} would overwrite the manifest/ledger -- "
                 "pick any other name; only the builder maintains the manifest")
    if not SAFE_NAME.match(name) or ".." in name or name.startswith("."):
        sys.exit(f"error: --out={name!r} is not a safe name for the site data dir -- "
                 "use a plain filename (word chars, dots, hyphens; no paths or ..)")


def _shown(path):
    """Repo-relative for display when inside the repo, absolute otherwise (tests run
    the builder against a temp data dir)."""
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def keeps_citation(score, n_votes, panel_size):
    """Pure: stray-vote guard -- scales to panel size so a 1-judge panel is legal."""
    return score >= 1 and n_votes >= min(2, panel_size)


def clean_quote(text):
    """Pure: strip bold markers -- mid-word bold in spec source breaks anchor matching."""
    return text.replace("**", "")


def citation_quote(text):
    """Pure: (quote, is_example_block). Fenced example blocks render as code the
    matcher cannot see, so -- like the curated data -- the quote is the caption
    line before the fence and the exampleBlock flag extends the highlight."""
    if "~~~" in text:
        caption = clean_quote(text.split("~~~")[0].strip())
        if caption:                       # a fence-leading passage has no caption --
            return caption, True          # an empty quote would anchor to the wrong block
    return clean_quote(text), False


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    runlog = HERE / "runlog-v3.jsonl"   # same default as whole_doc.py and run_rollout.py
    rubric = CONFIG["rubric"]
    out_name = None
    for a in argv:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
        elif a.startswith("--rubric="):
            rubric = a.split("=", 1)[1]
        elif a.startswith("--panel="):
            DISPLAY["panel"] = a.split("=", 1)[1]
        elif a.startswith("--behaviours="):     # site slugs, comma-separated; overrides display list
            DISPLAY["behaviours"] = a.split("=", 1)[1].split(",")
        elif a.startswith("--out="):            # alternate FILENAME in site data dir (iteration builds)
            out_name = a.split("=", 1)[1]
            check_out_name(out_name)            # loud error before any build work
    panel = set(CONFIG["panels"][DISPLAY["panel"]])
    votes = collections.defaultdict(dict)
    spec_of = {}
    for line in runlog.read_text().splitlines():
        d = json.loads(line)
        if d.get("rubric", "v1") != rubric or not d.get("parsed", True) or d["model"] not in panel:
            continue
        votes[(d["behaviour"], d["locator"])][d["model"]] = d.get("verdict", 0)
        spec_of[(d["behaviour"], d["locator"])] = d["spec"]

    import importlib.util
    sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
    h = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(h)
    text = {}
    for s in CONFIG["specs"]:
        for loc, sec, t in h.passages(s):
            text[loc] = t

    src = json.loads((ROOT / "data" / "reader-test-coverage.json").read_text())
    keep = DISPLAY["behaviours"]
    behaviours = [b for b in src["behaviours"] if b["slug"] in keep]
    by_slug_lab = {(e["behaviour_id"], e["lab_id"]): e for e in src["coverage"]}
    id_of = {b["slug"]: b["id"] for b in behaviours}

    out_behaviours = []
    for b in behaviours:
        cov = {}
        for spec_name, lab in LAB.items():
            src_entry = by_slug_lab.get((b["id"], lab), {})
            cits = []
            for (beh, loc), mv in votes.items():
                slug_matches = (SLUGS.get(beh) == b["slug"]
                                or b["slug"] in SLUGS_EXTRA.get(beh, []))
                if not slug_matches or spec_of[(beh, loc)] != spec_name:
                    continue
                if "fable" in mv and "opus" in mv:
                    mv = {m: v for m, v in mv.items() if m != "opus"}   # opus is fable's SUBSTITUTE, never an extra seat
                if "kimi" in mv and "kimi-k2" in mv:
                    mv = {m: v for m, v in mv.items() if m != "kimi-k2"}   # k2.6 is kimi's stand-in; k3 wins when present
                score = sum(mv.values())
                if not keeps_citation(score, len(mv), len(panel)):   # emit all scored; page filters by ?threshold=
                    continue
                SYM = {3: "\u2713\u2713", 2: "\u2713", 1: "~", 0: "\u2717"}   # defining = doubled core tick, no star
                WORD = {3: "defining", 2: "core", 1: "related", 0: "not relevant"}
                decisions = "\n".join(f"{SYM[v]} {MODEL_LABEL.get(m, m)} \u2014 {WORD[v]}"
                                      for m, v in sorted(mv.items(), key=lambda x: -x[1]))
                quote, is_example = citation_quote(text.get(loc, ""))
                cits.append({
                    "id": f"{lab}-{b['slug']}-panel-{len(cits)+1}",
                    "locator": loc, "quote": quote, "exampleBlock": is_example,
                    "role": f"Model determined relevance (score {score}/{2*len(mv)}):\n{decisions}",
                    "adjacent": score < DISPLAY["solid_threshold"],
                    "verdicts": dict(sorted(mv.items())), "score": score,
                })
            cits.sort(key=lambda c: (-c["score"], c["locator"]))
            cov[lab] = {"verdict": src_entry.get("verdict"), "depth": src_entry.get("depth_0_4"),
                        # depth_note stays in the stage-4 record; beside re-run panel data the
                        # curation-era prose goes stale, so the bench ships passage sets only
                        "note": "",
                        "verifiedDate": src_entry.get("verified_date", ""),
                        "passages": cits}
        out_behaviours.append({"id": len(out_behaviours) + 1,   # renumber 01..N for display
                               "slug": b["slug"], "name": b["name"],
                               "definition": b["definition"], "category": b["category"],
                               "coverage": cov})
    seats = sorted({m for b_ in out_behaviours for cov in b_["coverage"].values()
                    for p in cov["passages"] for m in p.get("verdicts", {})})
    out = {"generatedFrom": [f"engine/panel/build_site_data.py ({rubric})"],
           "provenance": {
               "method": "llm-panel whole-document judging", "rubric": rubric,
               "panel_config": DISPLAY["panel"],
               "panel": ["sol (gpt-5.6-sol)", "fable (claude-fable-5)", "kimi (moonshotai/Kimi-K3)"]
                        if DISPLAY["panel"] == "frontier" else sorted(panel),
               "substitution": "opus (claude-opus-4-8) replaces fable on harm-to-third-parties x model-spec (fable output content-filtered, 3 attempts); kimi-k2 (Kimi-K2.6) replaces kimi on over-under-caution x model-spec (K3 exhausted a 65k output budget on reasoning without emitting verdicts, finish_reason length)",
               "judges_seen_in_data": seats,
               "runDate": str(date.today()),
               "scoring": "per passage: sum over judges of core=2/related=1/neither=0; display thresholds are client-side URL params"},
           "behaviours": out_behaviours}
    n = sum(len(c["passages"]) for b in out_behaviours for c in b["coverage"].values())
    summary = f"{len(out_behaviours)} behaviours, {n} citations " \
              f"(threshold {DISPLAY['threshold']}, solid {DISPLAY['solid_threshold']})"
    payload = json.dumps(out, indent=1, ensure_ascii=False)
    if out_name:
        # Explicit destination: iteration builds, or --out=behaviours.json to rebuild
        # the shipped fallback. Written exactly there; the manifest is left alone.
        dest = DATA_DIR / out_name
        dest.write_text(payload)
        print(f"{_shown(dest)}: {summary}")
        return
    out_name, ts = next_run_name(DATA_DIR, datetime.now())
    dest = DATA_DIR / out_name
    dest.write_text(payload)
    entry = {"filename": out_name, "timestamp": ts, "rubric": rubric,
             "panel": DISPLAY["panel"], "judges": seats, "behaviours": keep,
             "runlog": runlog.name, "citations": n}
    manifest_path = DATA_DIR / MANIFEST_NAME
    manifest = update_manifest(read_manifest(manifest_path), entry)
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"{_shown(dest)}: {summary}")
    print(f"{_shown(manifest_path)}: latest = {out_name} ({len(manifest['runs'])} runs)")


if __name__ == "__main__":
    main()
