# site/ — five static surfaces, no build step, data via committed JSON payloads

> Current-state doc: describes what exists now, not what should exist. Brought current with the Phase-2 stack (#28–#41).

## Purpose

The public presentation layer: renders engine-generated JSON payloads into static pages. Plain HTML + vanilla JS everywhere — the three reader apps are ES modules (`<script type="module" src="./app.js">`), while `index.html` and `methodology.html` use inline classic scripts. No framework, no build step (the Astro stack PLAN.md recommended was never adopted). Deploys to Cloudflare Pages via `.github/workflows/deploy.yml` on merges that touch `site/**`, or manually via `pnpm deploy:site`.

## Contents

| Path | What it is |
|---|---|
| `index.html` | Core-page **prototype**: all data is inline JS (`const B = {...}`, `const GROUPS = [...]`); only behaviour 1 carries real sweep data, the rest are labeled illustrative placeholders. Embeds `spec-reader/` in an iframe modal. Hand-maintained copy of `design/prototypes/core-page.html`; the two have diverged. |
| `methodology.html` | Static prose page. Describes coverage assessment: the LLM panel procedure as operative, the fixed term-list search as the predecessor that produced behaviours 1–3. |
| `spec-reader/` | The published reader. Fetches `data/documents.json` (built by `engine/build-spec-reader-data.py`; currently behaviours 1–3). `app.js` `GROUPS` is registry-derived (the 13 index behaviours in 4 categories) while the payload carries only the 3 covered behaviours — expected sequencing, not drift. |
| `spec-reader-test/` | Reader test bench (deliberate fork of the reader UI). Renders the v5 panel run pre-filtered to the panel's band boundary: fetches the shared `../spec-reader/data/documents.json` plus `../llm-panel-review/data/behaviours-v5-reader.json` (built by `engine/panel/build_site_data.py` with `--threshold=4 --solid-threshold=6`). Self-describing README. |
| `llm-panel-review/` | Panel-judged reader: raw per-judge verdicts per passage, scores recomputed client-side (`?threshold=`/`?solid=`/`?related=`). Fetches shared `documents.json` + own `data/behaviours.json` (built by `engine/panel/build_site_data.py`); `?data=<name>` loads a sibling payload instead (`data/` also holds the calibration variants v3w-fresh / v4a / v4a-ds / v5 / v5-1 side by side). 3 behaviours × 3 judges. **Not linked from any nav.** |
| `README.md` | Layer status; lists all five tabs, with `llm-panel-review/` noted as deployed-but-unlinked. |

## Relationships

- All dynamic content arrives as committed JSON under each app's `data/`; the deploy's `paths: site/**` filter works precisely because payloads live inside `site/`.
- Producer map: `engine/build-spec-reader-data.py` → spec-reader payload; `engine/panel/build_site_data.py` → panel payload, and with `--threshold=4 --solid-threshold=6` the bench payload (`behaviours-v5-reader.json`).
- `engine/verify-spec-reader.mjs` / `verify-reader-test.mjs` / `verify-panel-features.mjs` are the E2E tests of these surfaces (repo-wide, `engine/panel/test_panel.py` covers the panel pipeline): they boot Chrome against these pages and assert every passage anchors, and `verify-panel-features.mjs` additionally exercises the panel's URL/DOM-state features and the reader's user-data path; they hardcode the DOM selectors used here.
- `index.html` is connected to **no** pipeline — its inline data is hand-maintained.

## Dependency map

```mermaid
graph LR
  docpayload["spec-reader/data/documents.json"] --> reader["spec-reader/"]
  docpayload --> bench["spec-reader-test/"]
  benchdata["llm-panel-review/data/behaviours-v5-reader.json"] --> bench
  docpayload --> panel["llm-panel-review/"]
  paneldata["llm-panel-review/data/behaviours.json"] --> panel
  index["index.html (inline prototype data)"] -.->|iframe modal| reader
  methodology["methodology.html (static prose)"]
  reader -->|nav links| index
  bench -->|nav links| methodology
  panel -.->|not linked from any nav| nowhere["(orphan surface)"]
```

## As-is observations

- Five surfaces, one orphan: `llm-panel-review/` is built, documented in its own README, deployed, and listed in `site/README.md` — but unreachable from every navigation.
- `index.html` carries hand-maintained inline prototype data (`data/README.md` carves this exception out explicitly); `site/README.md` documents the divergence from the prototype and warns against re-copying it without reconciling.
- `methodology.html` describes the term-list method while the operative procedure is the LLM panel; nothing tells readers which method produced which published records (behaviours 1–3: term-list; panel-scored records live in `llm-panel-review/`).
- `spec-reader/app.js`'s `GROUPS` enumerates the registry's 13 index behaviours while its payload ships only the 3 covered behaviours — expected sequencing, not drift (the nav anchors it points to, `../#methodology` and `../#about`, now resolve; the verifier fails on any unresolved same-site link/fragment).
- The verifiers' DOM-selector coupling means a markup refactor silently invalidates the only E2E checks.
