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
- `build_site_data.py` -- runlog -> site payload; behaviour metadata is
  registry-driven (see "Behaviour metadata is registry-driven" below) and run
  outputs are timestamped (see "Run outputs" below).
- `select_run.py` -- resolve/verify which payload the site page will load; the CLI
  half of run pinning (the other half is the page's `?data=` URL param).

## Run outputs, manifest, pinning
Each `build_site_data.py` run emits its own timestamped file
`site/llm-panel-review/data/behaviours-<YYYY-MM-DDTHH-MM-SS>.json` (hyphen-separated:
lexicographically sortable = chronological, URL-safe) and updates
`site/llm-panel-review/data/manifest.json`:
`{"latest": <filename>, "runs": [newest-first entries with filename, timestamp,
rubric, panel and citation metadata]}`. A second build in the same second takes a
numeric sequence suffix (`behaviours-<ts>-02.json`, then `-03`, ... -- zero-padded to
two digits) so a run is never silently overwritten; the suffix sorts after the bare
stamp and before the next second, so lexical order stays chronological. Run files and
the manifest are
gitignored -- they stay local; the tracked `behaviours.json` is the fallback a fresh
clone loads.

The page (`site/llm-panel-review/app.js`) resolves its payload in this order:
1. `?data=<name>` URL param (a pin; name only, no paths);
2. manifest `latest`;
3. the shipped `behaviours.json`.
A source that fails to fetch or parse falls through to the next, so a stale pin or a
missing manifest never breaks the page. Pin and `latest` targets are validated the same
way on both sides (`build_site_data.py::_payload_name` / `app.js::payloadName`): only
`behaviours*.json` payloads resolve -- the manifest itself is never loadable as a
payload. Pinning is the inclusive OR of the URL param and the CLI:

```
python3 engine/panel/select_run.py                   # run ledger + what the page loads now
python3 engine/panel/select_run.py --pin <name>      # verify a ?data= value before sharing it
python3 engine/panel/select_run.py --latest          # verify the manifest's latest run
```

Both paths resolve the same way: a name counts only when the file exists and parses
as JSON. To rebuild the shipped fallback (or any fixed filename) instead of emitting
a timestamped run, pass `--out=` -- e.g. `--out=behaviours.json`; the manifest is
left alone on that path. The name is validated (URL-safe chars, no path separators
or `..`), so `--out=` cannot write outside the data dir.
- `runlog-v3.jsonl` -- the committed canonical runlog that produced the shipped
  payload (`runlog-v3.md` documents its contents and provenance). Every other
  `runlog*.jsonl` stays gitignored.
- `verify_panel_provenance.py` -- proves the shipped payload rebuilds from that
  log; `test_verify_panel_provenance.py` is its test suite.

## Behaviour metadata is registry-driven
The displayed behaviours (sidebar names, definitions, categories, numeric ids)
come from the behaviour registry `data/behaviours.json`, not from the payload's
source runlog: the reader-test bench set in registry `numeric_id` order (the
shipped order), then any `set:user` behaviours the run covers. A `set:user`
runlog key is its registry slug (the clone/fork seam: a user behaviour's panel
run flows straight into the page once it is registered in a local registry
copy). A `--behaviours=` entry the registry does not carry fails the build
loudly. Flags: `--registry=PATH` (default `data/behaviours.json`; tests and
user forks point it elsewhere) and `--run-date=YYYY-MM-DD` (pins
`provenance.runDate`, default today, so a rebuild can reproduce a committed
payload byte-for-byte).

## The procedure
The end-to-end stage-4 procedure (dry run, execution, failure substitutions,
Gate 4 checks) is `.claude/skills/4-sweep-spec-coverage/SKILL.md`. This README
covers only the mechanics of the individual scripts.

## Tests
`python3 engine/panel/test_panel.py` -- unit tests for the pure logic (verdict
parsing, resume planning, cost estimate, per-model API params, builder guards),
no network or keys, sub-second. Each test class names the shipped bug it guards.
`python3 engine/panel/test_verify_panel_provenance.py` -- tests for the
provenance check below (green rebuild, tamper detection, missing-input failure).

## Verifying + reproducing the shipped data
The canonical runlog behind the shipped payload is committed here:
`runlog-v3.jsonl` (see `runlog-v3.md` for its contents and provenance record).

```sh
python3 engine/panel/verify_panel_provenance.py
```

rebuilds the payload from that log into a scratch directory and proves
`site/llm-panel-review/data/behaviours.json` matches byte-for-byte, with one
documented exception: `provenance.runDate`, which the builder stamps with the
build date (`date.today()`) and which cannot be re-derived because the log
schema carries no timestamps. Exit 0 = verified.

Manual rebuild: `python3 build_site_data.py` (defaults `--runlog=runlog-v3.jsonl
--rubric=v3w --panel=frontier` are the shipped configuration). Without `--out=`
the build lands in a new timestamped run file (see "Run outputs, manifest,
pinning" above) -- what ordinary re-runs should do; `--out=behaviours.json`
rebuilds the shipped payload in place, whose `runDate` a plain rebuild
re-stamps with today's date.

A NEW panel run must write a new runlog, and a regenerated payload needs its
own committed log + passing check -- provenance travels with the data.
(Regenerating verdicts from scratch: `python3 whole_doc.py <behaviour> <spec>
sol,fable,kimi` per cell; the runlog is append-only + resume-safe.)
