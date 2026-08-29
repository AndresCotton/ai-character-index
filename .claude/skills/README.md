# .claude/skills/ — retired procedure layer

This directory holds no agent-executable skills. The coverage-sweep pipeline
(extraction → publish → verify, with human gates between stages) is retired
with the publish path, and the coverage ledger (`data/coverage.json`) is
frozen: nothing writes it, and CI keeps its citations machine-verified.

Live procedures live elsewhere:

- **Clone/fork pathway** — register your own spec and behaviours and run the
  panel against them: root [`AGENTS.md`](../../AGENTS.md), with mechanics in
  [`engine/README.md`](../../engine/README.md) (user specs) and
  [`engine/panel/README.md`](../../engine/panel/README.md).
- **Site verification** — `engine/verify-reader-test.mjs` and
  `engine/verify-reader-features.mjs` (both need Chrome).
- **Fixed locations** — spec versions and canonical paths:
  [`references/locations.md`](references/locations.md).
