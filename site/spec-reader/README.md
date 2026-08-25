# site/spec-reader/ -- the product reader

The public reader: ten behaviours traced through both lab specifications,
rendered from the v5 9-point panel run.

- Payload: `../llm-panel-review/data/behaviours-v5-reader.json` -- the band-boundary
  build of `engine/panel/runlog-v5.jsonl` (`--threshold=4 --solid-threshold=6`):
  363 citations (43 defining, 57 core, 263 related). A fork user's freshly built
  payload appears in `llm-panel-review/` but not here (the reader stays pinned;
  a reader-side manifest is the documented later fix).
- Spec text: `data/documents.json`, shared with the published surfaces; never
  duplicated.
- Menu: 01-08 "Behaviours under test" (flat, as supplied) + 09-10 "General
  Guidelines" -- one supplied definition read two ways; the strict reading's
  source judgment (constitution 29 -> 16 vs model spec 22 -> 22) is preserved
  in `archive/general-welfare-strict-reading/`.
- Multi-behaviour reading: passages cited by more than one selected behaviour
  blend their tints and carry a shared mark; the finding bar counts them once.
- Verified by `engine/verify-reader-test.mjs` (anchoring, nav, tint/role
  agreement, export, BEHAVIOURS_URL 200) on every PR.
