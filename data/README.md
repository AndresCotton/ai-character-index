# data/

The canonical machine-readable data the site renders from. **The site contains no data of its own; Notion is never read directly by the site.** Changes arrive here via reviewed pull requests. `coverage.json` is written by `engine/publish-coverage.py` from gate-approved stage-4 sweep artifacts (`research/sweeps/NN-<slug>/4-spec-coverage.md`); the other files are hand-maintained. `engine/notion-sync/` (the planned Notion → data/ sync) is a placeholder, not built.

Current files:

| File | One row per | Writer |
|---|---|---|
| `coverage.json` | behaviour × lab verdict, with citations | `engine/publish-coverage.py` (re-verifies every quote via `engine/spec-cite/cite.py` before writing) |
| `labs.json` | lab | hand-maintained (changes rarely); no code reads it today |
| `evals.json` | eval, with rubric quality scores | hand-maintained (stage-5 transcription); no code reads it today |
| `reader-test-coverage.json` | see below | hand-transcribed from [`behaviours-for-adria/`](../behaviours-for-adria/README.md) |

Planned but absent: `behaviours.json` (the single behaviour registry — see the pre-publication punch list) and `meta.json` (site-wide metadata).

One file here is deliberately **not** index data: `reader-test-coverage.json`, the ledger behind the [reader test bench](../site/spec-reader-test/README.md). It holds an external reviewer's behaviour set -- definitions plus one coverage record per behaviour × lab, in the same record shape as `coverage.json` so a record can be lifted from a sweep unchanged. Consumers: `engine/build-reader-test-data.py` (the whole set → `site/spec-reader-test/`) and `engine/panel/build_site_data.py` (three rows — helpfulness, harm-avoidance-to-third-parties, avoiding-over-and-under-caution — carried through untouched into `site/llm-panel-review/`). Nothing in it is an index verdict, and nothing in it reaches `coverage.json` or the published `site/spec-reader/`.

`schema/` is currently empty (`.gitkeep` only), and no CI validates data files (the only workflow is `.github/workflows/deploy.yml`). Rules worth encoding when schemas land: no coverage verdict without at least one citation (quote + spec version + date verified), no eval without a URL, no unknown behaviour IDs.

Derived views (evidence strength per cell, the gap list) are computed client-side at render time and never stored here, so they can never go stale.
