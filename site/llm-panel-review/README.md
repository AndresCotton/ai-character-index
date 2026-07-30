# site/llm-panel-review/

The spec reader with passages scored for behaviour relevance by a panel of frontier
LLMs -- a copy of `site/spec-reader-test/` whose highlights come from model verdicts
instead of the curated stage-4 sweeps.

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
- `?solid=N` -- score at/above which a highlight renders Core-style; below renders
  Related-style [default 6, clamped likewise]
- `?related=W` -- weight of a "related" vote when scoring (core is always 2)
  [default 1; try 0.5 or 0]
Params compose with the page's own `?spec=` and `?behavior=`. Scores are recomputed
client-side from each citation's raw per-model verdicts.

## Regenerating the data
`data/behaviours.json` is built by `engine/panel/build_site_data.py` from a verdict
runlog (see `engine/panel/README.md`). Behaviour names/definitions pass through from
`data/reader-test-coverage.json` unmodified.
