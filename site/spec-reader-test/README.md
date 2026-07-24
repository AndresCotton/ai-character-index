# site/spec-reader-test/ -- the reader test bench

A separate tab (`/spec-reader-test/`) that is a copy of the published spec reader
([`site/spec-reader/`](../spec-reader/)), carrying its own behaviour set: the behaviours an
external reviewer asked us to trace through the specs. It exists so those results can be
published, revised and withdrawn without touching the index's own reader, whose behaviour
set is the gate-approved output of the [behaviour sweeps](../../.claude/skills/README.md).

**Current state:** the behaviour set is empty. Both specifications render in full, with no
highlighted passages, no coverage-depth chip and no highlight legend.

## What is shared, what is not

| | Source | Why |
|---|---|---|
| Spec text | `../spec-reader/data/documents.json` (shared) | Both surfaces must show the identical document versions; duplicating ~500 KB of spec markdown would let them drift |
| Behaviour set + passage mappings | [`data/behaviours.json`](data/behaviours.json) (own) | This is the part under test, and must not reach the published reader |

`app.js` and `styles.css` are a deliberate fork of the reader's, not a shared module: the
bench can diverge freely, and nothing done here can regress the live reader. The two
differences from the original are marked in the header comment of `app.js` -- the behaviour
menu is built from whatever set has been published here (grouped by `category`) rather than
the index's fixed thirteen, and the reader degrades to plain reading when that set is empty.

## Publishing a behaviour to the bench

`data/behaviours.json` is `{"behaviours": [...]}`, each entry the same shape the reader's
payload uses:

```json
{
  "id": 1,
  "slug": "no-sycophancy",
  "name": "No sycophancy",
  "definition": "…",
  "category": "Honesty & epistemics",
  "coverage": {
    "anthropic": { "verdict": "covered", "depth": 3, "note": "…", "verifiedDate": "2026-07-13",
                   "passages": [{ "id": "…", "locator": "…", "quote": "…", "role": "…",
                                  "adjacent": false, "exampleBlock": false }] },
    "openai": { … }
  }
}
```

Every entry needs a `coverage` record for **both** `anthropic` and `openai` (use
`"passages": []` for a spec with no coverage -- absence is a finding, and the reader says so).
Quotes must be resolver output for a pinned locator, per
[`specs/CITATION.md`](../../specs/CITATION.md); build them with
`engine/build-reader-test-data.py` rather than by hand.

## Verifying

```sh
node engine/verify-reader-test.mjs     # requires Chrome
```
