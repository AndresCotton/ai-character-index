# site/

The public static site.

**Current state (v0):** `index.html` is a snapshot of the design prototype ([`design/prototypes/core-page.html`](../design/prototypes/core-page.html)), served via Cloudflare Pages so the page is reachable while the real site is built. Update it by re-copying the prototype and pushing. It will be replaced by the Phase 1 build below (see [PLAN.md §6](../PLAN.md)).

**Tabs:** `index.html` (the index), `methodology.html`, `spec-reader/` (the published reader),
and `spec-reader-test/` -- a copy of the reader carrying an external reviewer's own behaviour
set, kept separate from what the index publishes. See
[`spec-reader-test/README.md`](spec-reader-test/README.md).

Planned stack: Astro + TypeScript, static output, one small JS island for the interactive index matrix. Renders exclusively from [`data/`](../data/) at build time. Page map and layout sketches in [PLAN.md §3](../PLAN.md); aesthetics discussion in [`design/`](../design/).
