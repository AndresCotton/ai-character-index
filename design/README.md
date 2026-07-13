# Design

The place to discuss and settle the aesthetics of the site before/while building. Drop candidates, screenshots, and opinions; decisions get promoted to the "decided" list when made.

## Decided

- **2026-07-12 -- Core-page metaphor: the founding document** *(supersedes the constellation map of earlier that day -- Andrés: too sci-fi)*. The index reads like the constitution of a new country: a bordered sheet, Articles I-IV with italic preambles, an aligned ledger of numbered clauses (§ 1-13). Hovering a clause unfolds its annotation **in-flow** (Anthropic coverage / OpenAI coverage / evidence), so nothing ever overlaps or misaligns; click opens the full clause record. Draft behaviours render italic with an "in deliberation" tag. Prototype: [prototypes/core-page.html](prototypes/core-page.html).
- **2026-07-12 -- Register: contractual, clean, principled.** Alive but calm: no idle animation; motion lives only in the load settle (staggered article fade) and the unfold/panel transitions. Typography is Garamond throughout (EB Garamond, falling back to Hoefler Text/Iowan), small caps for structure, italics for preambles and quotes; monospace appears only for literal spec anchors like `#do_not_lie`.
- **2026-07-12 -- Visual temperature: constitutional midnight.** Dark kept, but warmed: deep ink `#121419`, vellum text `#EAE4D6`. **Color speaks only about data** (coverage = archival blue `#7B85D6`; evidence = green `#3FA96C` / amber `#BC8A2F` / red `#C95550`, all validator-passed); every structural element is ivory and hairline gray.
- **2026-07-12 -- Interaction grammar:** hover = preview, click = commit one level deeper, back = ascend; nothing hover-only; dim siblings, never remove. Details in [interaction-model.md](interaction-model.md).
- **2026-07-13 -- Three strata, all on 5-point (0-4) scales.** Per behaviour: **Coverage** (per lab -- how deeply the spec declares it: not in spec / implied / touched on / covered / covered in depth), **Instruments** (lab-independent -- which public evals exist, rubric-scored), **Adherence** (lab × eval matrix -- labs as columns, evals as rows; explicitly *unmeasured* where no instruments exist). Hovering a clause shows its **definition first**, then two openable levers (Coverage → labs, Adherence → evals). Glyphs: square = coverage (fill height), circle = adherence/strength (pie fill), dashed = unmeasured.
- **2026-07-13 -- Surface colour: under exploration.** Midnight black felt off; the prototype footer has a live switcher: midnight / **umber** (current default) / archive green / parchment. All four data-palettes validator-passed. Awaiting Andrés's pick.
- **2026-07-13 -- The index opens as a title sheet.** Initially only the group names are visible (large small-caps Garamond in the framed sheet; the "Article I-IV" labels are gone). Hovering a group unfolds its definition and clause list in-flow, **one group at a time**; everything deeper (clause definition → Coverage/Adherence levers → full record) nests inside.
- **2026-07-13 -- Scores are typographic dot runs, not badges.** The geometric square/circle SVG chips were too salient and foreign. All 0-4 scales now render as small dot runs (`●●●○`) in the document's own type: coverage in spec-blue, adherence/strength hue-banded, `····` for unmeasured, ink-toned for rubric quality. One mark language everywhere.

## To discuss

- **Typography:** candidates for a serious-but-modern pairing (data UI + longform methodology text), tuned for light-on-dark reading.
- **Colour palette:** needs to encode two dimensions at once (coverage = border, evidence = fill) plus a "gap/absent" state that reads as a finding, not an error. Must survive color-blindness (fill amount + label carry meaning, hue only reinforces).
- **Tone:** neutral, METR-like. Rigorous without being cold; no advocacy styling. The dark theme must read "observatory", not "gamer".
- **Reference sites** (add screenshots to `references/`): AI Lab Watch (the model for the genre), METR (neutral-evaluator tone), Epoch AI (data-forward credibility), [Our World in Data's food-trade interactive](https://ourworldindata.org/how-does-food-get-traded-around-the-world) (the hover → drill grammar we adopted).

## references/

- `2026-07-02-index-pipeline-mockup.png` -- screenshot of the v0 HTML mockup's pipeline diagram (behaviours → model spec → evidence quality). The visual encoding it established (tile border = spec coverage, fill = evidence strength, lens toggle) is the starting point for the matrix design.
