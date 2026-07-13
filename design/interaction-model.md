# Interaction model -- the core index page

*Decided with Andrés on 2026-07-12 (second pass, superseding the constellation-map first pass, which read too sci-fi): the core page is a **founding document** -- contractual, clean, principled, Garamond. Reference for the hover → drill grammar: [OWID's food-trade interactive](https://ourworldindata.org/how-does-food-get-traded-around-the-world).*

The core page is a drill-down with clear depth levels. The grammar throughout: **hover = preview** (says "there is more inside"), **click = commit** one level deeper, **back/Esc = one level up**.

## The depth ladder

### L0 -- The title sheet (groups only)

The page opens showing **only the group names** -- large small-caps Garamond titles stacked in the framed sheet, nothing else (no article numbering; Andrés removed it). The group list is **data-driven** from Notion. Current groups: Honesty & epistemics · Instruction & task fidelity · Power concentration & large-scale harm · Interaction with others (in deliberation). Hovering (or focusing) a group unfolds its italic preamble and clause ledger in-flow, **one group at a time** -- opening one closes the others. The only orchestrated motion is on load: groups settle in with a staggered fade. No idle animation.

### L1 -- Clauses, definitions, and the two levers

Every behaviour is a **numbered clause (§ 1-13) in an aligned ledger**, always visible -- a constitution shows its clauses. Each clause row carries two glyphs at the right edge (coverage square + adherence circle), so the whole index is readable at a glance.

Hovering (or focusing) a clause unfolds **its definition first** (italic, in-flow -- the document breathes, rows shift down, every left edge stays aligned). Beneath the definition sit two openable **levers**:

1. **Coverage -- what each spec declares.** Opens per-lab lines: depth on the 5-point scale + the actual section (e.g. *Being honest · Truthful*, `#avoid_sycophancy`).
2. **Adherence -- what the evals show.** Opens the instrument list: strength aggregate, then one line per eval with its rubric-quality dots and per-lab adherence mini-scores. Where no evals exist it reads *unmeasured* -- the gap is stated, not hidden.

Then "open the full record →" (→ L2). Hovering an article softly dims its siblings (never removes them). Draft clauses ("in deliberation") show their draft note on hover and do not open a record.

### The three strata (how the lab axis is located)

- **Coverage** *(per lab)*: what the spec declares -- depth 0-4: not in spec / implied / touched on / covered / covered in depth. Square glyph, archival blue, fill height = depth.
- **Instruments** *(lab-independent)*: the public evals and their rubric quality (0-4 per dimension). This is the measuring equipment; no lab axis here.
- **Adherence** *(lab × eval)*: how each lab's model scores on those instruments, 0-4: failing / poor / mixed / good / meets target. In the full record this is a **matrix: evals as rows, labs as columns**, with per-lab aggregates. Adherence is *unmeasured* (dashed glyph) where no instruments exist -- evidence gates adherence, and the design makes that gate visible.

All scales are **5-point (0-4)**, rendered as **typographic dot runs** (`●●●○` -- filled count = level) in the document's own type, replacing the earlier geometric glyphs Andrés found too salient: coverage runs in spec-blue, adherence/strength runs hue-banded (0-1 red, 2 amber, 3-4 green -- reinforcement, never the sole carrier; the fill count and the word carry the meaning), `····` for unmeasured, ink-toned runs for rubric quality. One mark language across rows, levers, legend, and the record.

### L2 -- Behaviour detail

A dedicated, deep-linkable page (`/b/<slug>`), opened with a short zoom transition from the node so continuity is preserved; back returns to the constellation exactly as you left it. Contains:

1. **Definition and scope** (verbatim from the canonical behaviour list).
2. **Spec coverage, per lab:** verdict + the cited quote(s), each with *"read in context →"* (→ L4).
3. **Evidence:** the aggregate quality chip (same encoding as L1), the facet list, and *"see the evals →"* (→ L3). If there are no evals, the gap is stated as a finding, with a "want to build this? → contribute" link.

### L3 -- Eval breakdown

Progressive disclosure inside the L2 page (the "subtitles" level): one row per eval -- name, org, external link, featured badge, overall grade, and **per-dimension rubric scores** (dimensions synced from the Notion "Evals Rubric" page; e.g. construct validity, reproducibility). Each row expands for our short assessment note.

### L4 -- The spec reader

Self-hosted, rendered copies of the specs we score against. **Both are CC0 (verified 2026-07-12: OpenAI Model Spec and the Claude constitution), so hosting annotated copies is legally clean.** Arriving from a behaviour highlights the cited passages and pins a sticky *"← back to \<behaviour\>"* chip. Every citation anywhere in the index links to a stable anchor here. This is the feature that makes every verdict checkable in one click.

## Interaction rules (what keeps it coherent)

- Hover previews, click commits, back ascends. No exceptions, so the grammar becomes muscle memory.
- Nothing is hover-only: keyboard focus triggers the same previews; touch is tap-to-preview, tap-again-to-commit.
- Dim siblings, never remove them.
- Motion budget: the one idle animation + transitions under ~250 ms. Honor `prefers-reduced-motion`.

## Visual encoding

- **Evidence glyph:** none = hollow, weak = half-filled, strong = filled -- fill amount carries the meaning, hue reinforces it (green `#3FA96C` / amber `#BC8A2F` / red `#C95550`, validator-passed on `#121419`; always paired with a text label).
- **Coverage:** covered = archival blue (`#7B85D6`) · covered in part = same, annotated "(in part)" and dashed pill in the record · not in spec = muted with an explicit label (an absence is a finding, not blank space).
- **Color speaks only about data.** Everything structural -- rules, section marks, small caps, borders -- is vellum ivory and hairline gray. Drafts are italic + "in deliberation" tag; parked behaviours keep their exclusion reason one hover away.
- **Constitutional midnight:** deep warm ink (`#121419`), vellum text (`#EAE4D6`), Garamond throughout; monospace only for literal spec anchors. Text-heavy surfaces (L2 record, L4 reader) sit on a slightly lifted panel so long-form reading doesn't strain.

## Data requirements this adds (fold into `data/` schemas)

- `coverage.json` citations need **stable anchor ids** into the mirrored specs, for L4 highlighting.
- `evals.json` needs per-rubric-dimension scores, the featured flag, and a short assessment note.
- Groups become data (`behaviours.json` gains group id + display order, or a small `groups.json`), since the group list will change.

## Prototype

[`prototypes/core-page.html`](prototypes/core-page.html) -- self-contained, demonstrates L0 → L3 with real behaviour names, definitions, and spec anchors from the canonical list; **eval scores are illustrative placeholders and labeled as such**. L4 is stubbed. Open it in a browser and hover.
