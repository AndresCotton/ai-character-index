# site/llm-panel-review/

The spec reader with passages scored for behaviour relevance by a panel of frontier
LLMs -- a copy of `site/spec-reader-test/` whose highlights come from model verdicts
instead of the curated coverage sweeps.

## What it shows
Three behaviours (Helpfulness, Harm avoidance to third parties, Avoiding both over-
and under-caution), each passage of both specifications graded by three judges --
GPT-5.6 Sol, Claude Fable 5, Kimi-K3 -- on a 3-point scale (2 core / 1 related /
0 neither). A passage's score is the sum over judges (max 6). Claude Opus 4.8
substitutes for Fable on one cell (harm-to-third-parties × model spec) where Fable's
output was content-filtered; the "?" popup on any highlight names each judge and
its decision.

## Display tuning (URL params, no UI)
- `?threshold=N` -- minimum score to highlight [default 6 = unanimous core, clamped
  to a cell's max where a judge's votes are pending]
- `?related=W` -- weight of a "related" vote when scoring (core is always 2)
  [default 1; try 0.5 or 0]
Params compose with the page's own `?spec=` and `?behavior=`. Scores are recomputed
client-side from each citation's raw per-model verdicts.

## Regenerating the data
`data/behaviours.json` is built by `engine/panel/build_site_data.py` from a verdict
runlog (see `engine/panel/README.md`). Behaviour names/definitions pass through from
`data/reader-test-coverage.json` unmodified.

## Which payload the page loads
Resolution order, no selection UI:
1. `?data=<name>` -- a pin naming a `behaviours*.json` payload in `data/` (e.g. a
   timestamped run or a calibration variant like `?data=behaviours-v4a`); name only,
   no paths; `manifest.json` is never a valid pin, and non-`behaviours*` files are
   refused, so the ledger can't be rendered as a behaviour set;
2. `data/manifest.json` `latest` -- the newest timestamped run the builder emitted;
3. `data/behaviours.json` -- the shipped fallback, always tracked.

A source that fails to fetch or parse falls through to the next, so a stale pin or a
fresh clone (no manifest yet) still renders. Each `build_site_data.py` run writes
`data/behaviours-<YYYY-MM-DDTHH-MM-SS>.json` and updates the manifest; both are
gitignored and stay local. `engine/panel/select_run.py` resolves/verifies pins from
the CLI the same way the page does (`--pin <name>`, `--latest`).
