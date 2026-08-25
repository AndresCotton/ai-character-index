# site/spec-reader-test/ -- the reader test bench

A separate tab (`/spec-reader-test/`) that is a copy of the published spec reader
([`site/spec-reader/`](../spec-reader/)), carrying the v5 9-point panel run: ten behaviours
judged against both specifications, pre-filtered to the panel's band boundary. It exists so
those results can be published, revised and withdrawn without touching the index's own reader,
whose behaviour set is the gate-approved output of the
[behaviour sweeps](../../.claude/skills/README.md).

**Current state:** ten behaviours render, 363 citations across the two specifications
(43 defining, 57 core, 263 related). Eight appear under the menu heading "Behaviours under
test" as a flat list; the other two make up a second group, "General Guidelines", which is
drawn differently -- see below. Those two are one supplied definition read two ways: General
welfare impacts, and a strict reading of it that keeps a passage only where both
specifications state the same rule, so the reader can hold the two side by side. The strict
reading's source judgment -- including the asymmetric cut it found, constitution 29 -> 16 vs
model spec 22 -> 22 -- is preserved in
[`archive/general-welfare-strict-reading/`](../../archive/general-welfare-strict-reading/README.md).

## What is shared, what is not

| | Source | Why |
|---|---|---|
| Spec text | `../spec-reader/data/documents.json` (shared) | Both surfaces must show the identical document versions; duplicating ~500 KB of spec markdown would let them drift |
| Behaviour set + passage mappings | [`../llm-panel-review/data/behaviours-v5-reader.json`](../llm-panel-review/data/behaviours-v5-reader.json) (own, built) | This is the part under test, and must not reach the published reader |

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

## Taking the reading away

**Download passages**, at the foot of the menu just above the key, writes whatever is ticked
to a single Markdown file: per behaviour its group and definition, then per specification the
coverage verdict, depth and note, and every citation as its locator, its quote as a blockquote,
and the role sentence recording why it was picked. It is the whole citation rather than the
highlighted text alone, because the file is meant to be read away from the reader -- pasted
into a review, diffed against a later spec version, annotated by hand.

Both specifications are written out whichever one is open (a behaviour's coverage is the pair),
and a spec that maps nothing to a behaviour is named and said so rather than left out --
absence of coverage is an index finding. Citations are counted, not blocks: two sentences of
one paragraph are two entries in the file even where they light one passage in the reader,
which is why the count under the button can exceed the reader's passage count. The file is
named `reader-test-<slug>-passages-<date>.md` for one behaviour and
`reader-test-<n>-behaviors-passages-<date>.md` for several.

## The bench payload's shape

`../llm-panel-review/data/behaviours-v5-reader.json` is `{"behaviours": [...]}`, each entry
the same shape the reader's payload uses:

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

Never hand-edit that file. It is the panel builder's band-boundary build of the committed v5
run (`engine/panel/runlog-v5.jsonl`, panel `frontier_fast`, rubric v5), cut at the 3-judge
band boundary (relatedCut = j+1 = 4, coreCut = 2j = 6) so the bench shows exactly what the
panel view renders:

```sh
python3 engine/panel/build_site_data.py --threshold=4 --solid-threshold=6 \
    --run-date=2026-08-17 --out=behaviours-v5-reader.json
```

The payload lives in `../llm-panel-review/data/` beside the panel payloads; `BEHAVIOURS_URL`
in `app.js` points at it. Behaviour metadata is registry-driven (`data/behaviours.json`); the
cell verdict/depth/verifiedDate rows come from `data/panel-cell-curation.json`.

## Verifying

```sh
node engine/verify-reader-test.mjs     # requires Chrome
```
