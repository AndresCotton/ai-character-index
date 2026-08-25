# site/

The public static site. Three surfaces, plain HTML + vanilla JS, no build step — what is committed here is what deploys to Cloudflare Pages (see `.github/workflows/deploy.yml`; the manual twin is `pnpm deploy:site`).

**Tabs:**

- `index.html` — the core-page **prototype**: hand-maintained inline data (`const B = {...}`), connected to no pipeline. Only behaviour 1 carries real coverage data; the rest are labeled illustrative placeholders, and the file has diverged from [`design/prototypes/core-page.html`](../design/prototypes/core-page.html) — do not re-copy the prototype over it without reconciling. Its future (generate from `data/` or retire) is on the closeout list.
- `methodology.html` — inclusion criteria, rubric, scoring, process.
- `spec-reader/` — the spec reader: both specifications in full, with a behaviour menu that highlights the cited passages, each citation carrying raw per-judge verdicts scored client-side into tiers. Renders the spec text from `spec-reader/data/documents.json` (built by `engine/build-spec-reader-data.py`) and its behaviour data from `spec-reader/data/behaviours.json` (built by `engine/panel/build_site_data.py`), resolved ?data=<name> pin -> `data/manifest.json` latest -> that shipped fallback. `data/` also holds the calibration variants and the band-filtered keep-set (`behaviours-v5-reader.json`), each loadable as a `?data=` pin; `engine/verify-reader-test.mjs` walks the default state (no pin, no manifest) and holds every view to the keep-set counts, so a moved or renamed payload fails loud.

The two engine verifiers (`engine/verify-reader-test.mjs`, `engine/verify-reader-features.mjs`) boot Chrome against the page and assert every renderable passage anchors; run them after changing markup or payloads.

Page map and layout sketches in [PLAN.md §3](../PLAN.md) (the Astro stack sketched there was not adopted); aesthetics discussion in [`design/`](../design/).
