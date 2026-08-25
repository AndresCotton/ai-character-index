# site/

The public static site. Four surfaces, plain HTML + vanilla JS, no build step — what is committed here is what deploys to Cloudflare Pages (see `.github/workflows/deploy.yml`; the manual twin is `pnpm deploy:site`).

**Tabs:**

- `index.html` — the core-page **prototype**: hand-maintained inline data (`const B = {...}`), connected to no pipeline. Only behaviour 1 carries real coverage data; the rest are labeled illustrative placeholders, and the file has diverged from [`design/prototypes/core-page.html`](../design/prototypes/core-page.html) — do not re-copy the prototype over it without reconciling. Its future (generate from `data/` or retire) is on the closeout list.
- `methodology.html` — inclusion criteria, rubric, scoring, process.
- `spec-reader/` — the spec reader: both specifications in full, with a behaviour menu that highlights the cited passages. Renders the spec text from `spec-reader/data/documents.json` (built by `engine/build-spec-reader-data.py`) and its behaviour data from `llm-panel-review/data/behaviours-v5-reader.json` — the v5 panel run pre-filtered to the panel's band boundary (built by `engine/panel/build_site_data.py` with `--threshold=4 --solid-threshold=6`). The reader is pinned to that literal filename: the payload is band-filtered (a small fraction of the panel payloads) and `data/manifest.json` is gitignored, so resolving through the panel's manifest would feed the reader unfiltered data. A reader-side manifest is the designed fix; until it exists, `engine/verify-reader-test.mjs` asserts the pinned URL returns 200 so a moved or renamed payload fails loud.
- `llm-panel-review/` — panel-judged coverage (raw per-judge verdicts per passage), rendered from data built by `engine/panel/build_site_data.py`. Currently deployed but not linked from any navigation; its production status is on the closeout list.

The two engine verifiers (`engine/verify-reader-test.mjs`, `engine/verify-panel-features.mjs`) boot Chrome against these pages and assert every published passage anchors; run them after changing markup or payloads.

Page map and layout sketches in [PLAN.md §3](../PLAN.md) (the Astro stack sketched there was not adopted); aesthetics discussion in [`design/`](../design/).
