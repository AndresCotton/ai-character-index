# site/spec-reader-test/ -- the reader test bench

A separate tab (`/spec-reader-test/`) that is a copy of the published spec reader
([`site/spec-reader/`](../spec-reader/)), carrying its own behaviour set: the behaviours an
external reviewer asked us to trace through the specs. It exists so those results can be
published, revised and withdrawn without touching the index's own reader, whose behaviour
set is the gate-approved output of the [behaviour sweeps](../../.claude/skills/README.md).

**Current state:** nine behaviours are under test -- the set in
[`behaviours-for-adria/`](../../behaviours-for-adria/README.md), published from their stage-4
spec-coverage sweeps, 256 citations across the two specifications. Eight of them appear under
the menu heading "Behaviours under test", because that is how the set was supplied: a flat
list, with no grouping of ours imposed on it. The ninth,
[Animal Welfare impacts](../../behaviours-for-adria/general-guidelines/README.md), is the first
row of a second group, "General Guidelines", and is drawn differently -- see below. Each
behaviour's Gate-4 human spot-read is still open; this bench is the surface it happens on,
which is why the set is published before sign-off.

## What is shared, what is not

| | Source | Why |
|---|---|---|
| Spec text | `../spec-reader/data/documents.json` (shared) | Both surfaces must show the identical document versions; duplicating ~500 KB of spec markdown would let them drift |
| Behaviour set + passage mappings | [`data/behaviours.json`](data/behaviours.json) (own) | This is the part under test, and must not reach the published reader |

`app.js` and `styles.css` are a deliberate fork of the reader's, not a shared module: the
bench can diverge freely, and nothing done here can regress the live reader. The differences
from the original are marked in the header comment of `app.js` -- the behaviour menu is built
from whatever set has been published here (grouped by `category`) rather than the index's
fixed thirteen; the reader degrades to plain reading when that set is empty; and the menu is
a checklist rather than a single choice.

## Reading several behaviours at once

Any number of behaviours can be ticked, and the reader lays all of them over the same text,
so a passage that answers to more than one is visible as such rather than only in whichever
behaviour you happened to open. The encoding:

| | |
|---|---|
| Colour | One per behaviour, fixed by its place in the published set, so a passage keeps its colour as the selection changes around it. Twelve `--hue-N` slots, one set per surface (daylight, umber), in `styles.css` |
| Intensity | A core passage carries its colour at full strength, a related (`"adjacent": true`) one the same colour thinned -- `--tint-core` against `--tint-related` |
| Texture | One per **group**, not per behaviour, and carried by the margin rule rather than the wash: "Behaviours under test" takes a solid rule, "General Guidelines" one broken down its length. Nothing is laid over the text itself -- both versions that did (dots added, and the same lattice knocked out of the wash) cost more in legibility than the distinction was worth. `GROUP_TEXTURE` in `app.js` decides which rule, keyed by the behaviour's `category` |
| Margin | The rules hang off the **right** margin. The left one is already furnished -- an ordered list's numbers, a blockquote's rule -- and a highlighted list item had its marker struck through by the rule sitting in the same column. Nothing but the passage rail lives on the right, and the rail sits further out still |
| Overlap | A passage several behaviours cite blends their colours left to right and shows one margin rule per behaviour, in menu order; its rail mark is banded down its height. Rules from different groups stand side by side, each with its own texture |
| Labels | The role line of every behaviour that cites the passage, each in that behaviour's colour, named once more than one behaviour is ticked |

`?behavior=` takes a comma-separated list (`?behavior=helpfulness,user-autonomy`); a bare
slug still works, and with the parameter absent the reader opens on the first behaviour of
the set. Ticking never re-renders the specification, only the highlight layer over it, so
the reader keeps its place in the text as behaviours are added and taken away.

A third divergence lives in `findPassageBlocks`: a quote is matched as ordered *fragments*
rather than one literal run. Resolver output and rendered text differ in two places -- an
admonition's `!!! meta "Commentary"` marker, which the reader renders as the label alone, and
a cross-reference, which the published Markdown writes `[?](#anchor)`, the resolver expands to
`#anchor`, and the reader renders as the title of the section it points at. Six of the eight
behaviours' passages sit on one of those two shapes and would otherwise report as unresolved
anchors. A quote with neither feature yields a single fragment, i.e. the previous behaviour.

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
[`specs/CITATION.md`](../../specs/CITATION.md).

Never hand-edit that file. It is generated from
[`data/reader-test-coverage.json`](../../data/reader-test-coverage.json) -- the bench's own
ledger, one behaviour definition plus one record per behaviour x lab, in the same record shape
`data/coverage.json` uses, so a record can be lifted out of a sweep unchanged:

```sh
python3 engine/build-reader-test-data.py
```

Delete the ledger and re-run to empty the bench; the specs then render in full again.

## Verifying

```sh
node engine/verify-reader-test.mjs     # requires Chrome
```
