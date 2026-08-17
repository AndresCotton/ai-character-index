# site/

The public static site. Five surfaces, plain HTML + vanilla JS, no build step — what is committed here is what deploys to Cloudflare Pages (see `.github/workflows/deploy.yml`; the manual twin is `pnpm deploy:site`).

**Tabs:**

- `index.html` — the core-page **prototype**: hand-maintained inline data (`const B = {...}`), connected to no pipeline. Only behaviour 1 carries real sweep data; the rest are labeled illustrative placeholders, and the file has diverged from [`design/prototypes/core-page.html`](../design/prototypes/core-page.html) — do not re-copy the prototype over it without reconciling. Its future (generate from `data/` or retire) is on the pre-publication punch list.
- `methodology.html` — inclusion criteria, rubric, scoring, process.
- `spec-reader/` — the published reader: behaviour × spec coverage with cited passages, rendered from `spec-reader/data/documents.json` (built by `engine/build-spec-reader-data.py`).
- `spec-reader-test/` — a copy of the reader carrying an external reviewer's own behaviour set, kept separate from what the index publishes. See [`spec-reader-test/README.md`](spec-reader-test/README.md).
- `llm-panel-review/` — panel-judged coverage (raw per-judge verdicts per passage), rendered from data built by `engine/panel/build_site_data.py`. Currently deployed but not linked from any navigation; its production status is on the pre-publication punch list.

The two engine verifiers (`engine/verify-spec-reader.mjs`, `engine/verify-reader-test.mjs`) boot Chrome against these pages and assert every published passage anchors; run them after changing markup or payloads.

Page map and layout sketches in [PLAN.md §3](../PLAN.md) (the Astro stack sketched there was not adopted); aesthetics discussion in [`design/`](../design/).
