# engine/panel

Pipeline that produces the LLM-panel relevance data for `site/llm-panel-review/`.

Credentials: `panel-config.json` holds env-var NAMES only; keys live in the
environment or a gitignored `.env` in this directory.

## Pieces
- `panel-config.json` -- providers, model tags, panels, rubric, display behaviours.
- `harness.py` -- shared library: config load, prompt builders (rubrics v1 binary /
  v2 ternary+scope / v3 ternary+form-fields, frozen for provenance), verdict
  parsing, run-log resume conventions. Not a CLI.
- `whole_doc.py` -- whole-document judging (entire spec in one prompt, all verdicts
  in one response; rubric tag `v3w`). This mode produced the shipped data, winning
  an empirical dense-vs-sparse comparison.
- `select_strata.py` + `smoke-*.txt` -- stratified validation sample (pinned).
- `run_rollout.py` -- the driver: full-dataset plan, dry-run by default, --go to spend.
- `build_site_data.py` -- runlog -> site payload (see "Run outputs" below).
- `select_run.py` -- resolve/verify which payload the site page will load; the CLI
  half of run pinning (the other half is the page's `?data=` URL param).

## Run outputs, manifest, pinning
Each `build_site_data.py` run emits its own timestamped file
`site/llm-panel-review/data/behaviours-<YYYY-MM-DDTHH-MM-SS>.json` (hyphen-separated:
lexicographically sortable = chronological, URL-safe) and updates
`site/llm-panel-review/data/manifest.json`:
`{"latest": <filename>, "runs": [newest-first entries with filename, timestamp,
rubric, panel and citation metadata]}`. Run files and the manifest are gitignored --
they stay local; the tracked `behaviours.json` is the fallback a fresh clone loads.

The page (`site/llm-panel-review/app.js`) resolves its payload in this order:
1. `?data=<name>` URL param (a pin; name only, no paths);
2. manifest `latest`;
3. the shipped `behaviours.json`.
A source that fails to fetch or parse falls through to the next, so a stale pin or a
missing manifest never breaks the page. Pinning is the inclusive OR of the URL param
and the CLI:

```
python3 engine/panel/select_run.py                   # run ledger + what the page loads now
python3 engine/panel/select_run.py --pin <name>      # verify a ?data= value before sharing it
python3 engine/panel/select_run.py --latest          # verify the manifest's latest run
```

Both paths resolve the same way: a name counts only when the file exists and parses
as JSON. To rebuild the shipped fallback (or any fixed filename) instead of emitting
a timestamped run, pass `--out=` -- e.g. `--out=behaviours.json`; the manifest is
left alone on that path.

## The procedure
The end-to-end stage-4 procedure (dry run, execution, failure substitutions,
Gate 4 checks) is `.claude/skills/4-sweep-spec-coverage/SKILL.md`. This README
covers only the mechanics of the individual scripts.

## Tests
`python3 engine/panel/test_panel.py` -- unit tests for the pure logic (verdict
parsing, resume planning, cost estimate, per-model API params, builder guards),
no network or keys, sub-second. Each test class names the shipped bug it guards.

## Reproducing the shipped data
1. Verdicts: `python3 whole_doc.py <behaviour> <spec> sol,fable,kimi` per cell
   (runlog is append-only + resume-safe; rerunning skips banked cells).
2. Site data: `python3 build_site_data.py --runlog=<runlog> --rubric=v3w --panel=frontier
   --out=behaviours.json` (without `--out=` the build lands in a new timestamped run
   file instead, which is what ordinary re-runs should do).
The runlog behind the shipped data is committed in this directory
(`engine/panel/runlog-v3.jsonl`; see `runlog-v3.md`).
