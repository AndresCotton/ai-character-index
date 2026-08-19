# data/

The canonical machine-readable data the site renders from. **The dynamic site surfaces contain no data of their own** — the one exception is `site/index.html`, whose inline prototype data (`const B = {...}`) is hand-maintained and connected to nothing here; Notion is never read directly by the site. Changes arrive here via reviewed pull requests. The `coverage.json` records for behaviours 2–3 are published by `engine/publish-coverage.py` from gate-approved stage-4 sweep artifacts (`research/sweeps/NN-<slug>/4-spec-coverage.md`); behaviour 1's records predate that pipeline and were written by hand (not regenerable today — see `data/OVERVIEW.md`). The other files are hand-maintained. `engine/notion-sync/` (the planned Notion → data/ sync) is a placeholder, not built.

Current files:

| File | One row per | Writer |
|---|---|---|
| `coverage.json` | behaviour × lab verdict, with citations | behaviours 2–3: `engine/publish-coverage.py` (re-verifies every quote via `engine/spec-cite/cite.py` before writing); behaviour 1: hand-written, predates the pipeline |
| `labs.json` | lab | hand-maintained (changes rarely); no code reads it today |
| `evals.json` | eval, with rubric quality scores | hand-maintained (predates the staged pipeline: its `sweep_date` 2026-07-12 is earlier than any stage-5 run); no code reads it today |
| `reader-test-coverage.json` | see below | hand-transcribed from [`behaviours-for-adria/`](../behaviours-for-adria/README.md) |

Planned but absent: `behaviours.json` (the single behaviour registry — see the closeout list) and `meta.json` (site-wide metadata).

One file here is deliberately **not** index data: `reader-test-coverage.json`, the ledger behind the [reader test bench](../site/spec-reader-test/README.md). It holds an external reviewer's behaviour set -- definitions plus one coverage record per behaviour × lab, in the same record shape as `coverage.json` so a record can be lifted from a sweep unchanged. Consumers: `engine/build-reader-test-data.py` (the whole set → `site/spec-reader-test/`) and `engine/panel/build_site_data.py` (three rows — helpfulness, harm-avoidance-to-third-parties, avoiding-over-and-under-caution — carried through untouched into `site/llm-panel-review/`). Nothing in it is an index verdict, and nothing in it reaches `coverage.json` or the published `site/spec-reader/`.

`schema/` is currently empty (`.gitkeep` only), and no CI validates data files (the only workflow is `.github/workflows/deploy.yml`). Rules worth encoding when schemas land: no coverage verdict without at least one citation (quote + spec version + date verified), no eval without a URL, no unknown behaviour IDs.

Derived views (evidence strength per cell, the gap list) are planned but computed nowhere today; the only evidence-strength display is hand-maintained inline data in `site/index.html`. When implemented they should be computed at render time and never stored here, so they can never go stale.
