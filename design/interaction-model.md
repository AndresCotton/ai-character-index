# Interaction model -- the core index page

*The core page keeps the founding-document structure settled with Andrés on 2026-07-12, but its visual register changed on 2026-07-20 to **Open Standard**: independent, analytical, and public. Reference for the hover → drill grammar: [OWID's food-trade interactive](https://ourworldindata.org/how-does-food-get-traded-around-the-world).*

The core page is a drill-down with clear depth levels. The grammar throughout: **hover = preview** (says "there is more inside"), **click = commit** one level deeper, **back/Esc = one level up**.

## The depth ladder

### L0 -- The title sheet (groups only)

The page opens showing **only the group names** -- large IBM Plex Sans titles stacked in the framed register, nothing else (no article numbering; Andrés removed it). The group list is **data-driven** from Notion. Current groups: Honesty & epistemics · Instruction & task fidelity · Power concentration & large-scale harm · Interaction with others (in deliberation). Hovering (or focusing) a group unfolds its IBM Plex Serif preamble and clause ledger in-flow, **one group at a time** -- opening one closes the others. The only orchestrated motion is on load: groups settle in with a staggered fade. No idle animation.

### L1 -- Clauses, definitions, and the two levers

Every behaviour is a **numbered clause (§ 1-13) in an aligned ledger**, always visible -- a constitution shows its clauses. Each clause row carries **one mark** at its right edge: instrument strength, the lab-free stratum ("instruments `●●○○` limited"; red "no public evals `····`" where none exist) -- never a cross-lab average, which would report nothing true about either lab. Where the measurement gaps are is readable at a glance.

Hovering (or focusing) a clause unfolds **its definition first** (italic, in-flow -- the document breathes, rows shift down, every left edge stays aligned). Beneath the definition sit two openable **levers**:

1. **Coverage -- what each spec declares.** Opens per-lab lines: depth on the 5-point scale + the actual section (e.g. *Being honest · Truthful*, `#avoid_sycophancy`).
2. **Adherence -- what the evals show.** Opens a small labelled matrix -- instrument | Anthropic | OpenAI -- every cell a run **with its word** (`●○○○` poor; a cell a paper didn't report reads muted "not reported"). Per-eval rubric quality does not appear here (its home is the full record), and the instrument-strength aggregate lives on the clause row. Where no evals exist it reads *unmeasured* -- the gap is stated, not hidden.

Then "open the full record →" (→ L2). Hovering an article softly dims its siblings (never removes them). Draft clauses ("in deliberation") show their draft note on hover and do not open a record.

### The three strata (how the lab axis is located)

- **Coverage** *(per lab)*: what the spec declares -- depth 0-4: not in spec / implied / touched on / covered / covered in depth. Dot run in archival blue, filled count = depth.
- **Instruments** *(lab-independent)*: the public evals and their rubric quality (0-4 per dimension). This is the measuring equipment; no lab axis here. Its 0-4 strength mark is the clause row's only mark -- a fact about the field, kept visibly apart from the per-lab strata.
- **Adherence** *(lab × eval)*: how each lab's model scores on those instruments, 0-4: failing / poor / mixed / good / meets target. In the full record this is a **matrix: evals as rows, labs as columns**, with per-lab aggregates. Adherence is *unmeasured* (a dashed run `····`) where no instruments exist -- and unmeasured is the **floor of the evidence scale**, below "failing", not a parallel category: no instruments is worse than weak instruments, so behaviour-level absence renders in gap-red. Only a cell a paper merely didn't report stays muted ("not reported").

All scales are **5-point (0-4)**, rendered as **typographic dot runs** (`●●●○` -- filled count = level) in the document's own type, replacing the earlier geometric glyphs Andrés found too salient: coverage runs in spec-blue, adherence/strength runs hue-banded (0-1 red, 2 amber, 3-4 green -- reinforcement, never the sole carrier; the fill count and the word carry the meaning), `····` for unmeasured (gap-red at behaviour level, muted for a single unreported cell), ink-toned runs for rubric quality. One mark language across rows, levers, and the record; the scales are taught in one place, the sheet's folded "notes on reading" closing note.

### L2 -- Behaviour detail

A dedicated, deep-linkable page (`/b/<slug>`), opened with a short zoom transition from the clause row so continuity is preserved; back returns to the sheet exactly as you left it. Contains:

1. **Definition and scope** (verbatim from the canonical behaviour list).
2. **Spec coverage, per lab:** verdict + the cited quote(s), each with *"read in context →"* (→ L4).
3. **Evidence:** the aggregate strength run (same encoding as L1), the facet list, and *"see the evals →"* (→ L3). If there are no evals, the gap is stated as a finding, with a "want to build this? → contribute" link.

### L3 -- Eval breakdown

Progressive disclosure inside the L2 page (the "subtitles" level): one row per eval -- name, org, external link, featured badge, overall grade, and **per-dimension rubric scores** (dimensions synced from the Notion "Evals Rubric" page; e.g. construct validity, reproducibility). Each row expands for our short assessment note.

### L4 -- The spec reader

Self-hosted, rendered copies of the specs we score against. **Both are CC0 (verified 2026-07-12: OpenAI Model Spec and the Claude constitution), so hosting annotated copies is legally clean.** Arriving from a behaviour highlights the cited passages and pins a sticky *"← back to \<behaviour\>"* chip. Every citation anywhere in the index links to a stable anchor here. This is the feature that makes every verdict checkable in one click.

#### Spec-reader variation -- source typography within neutral chrome

The reader chrome remains an L4 variation of Open Standard, not a separate evaluator language. Controls, surfaces, highlights, and structural labels use the same IBM Plex and cool daylight/graphite tokens as the rest of the site. Only the rendered source document's typography varies by provenance: Anthropic uses EB Garamond; OpenAI uses a clean Helvetica-style sans. This preserves each source's reading character without allowing company colour or branding to bias the comparison. Long-form text sits on the neutral `paper` surface.

- **Default = Focus highlights.** Sections with mapped passages remain open; sections without them collapse to compact, clickable heading rows. Heading nesting is respected, and mapped example blocks remain indivisible. “Expand all” restores the literal full document. In split view this state belongs to each document independently.
- **Passage tint tokens (L4 only).** Core passage: a low-chroma tint derived from standard blue (`#E3EBF1` daylight / `#263943` graphite); current core passage: the stronger tint (`#C9DAE6` / `#335264`). Adjacent passages use the neutral panel tint and an amber edge. Text, labels, and borders continue to carry meaning, so the tints are never the only signal.
- **Find rail.** Each document has a full-height right-edge track, analogous to browser find markers. Blue ticks = core passages; amber ticks = adjacent/boundary passages; the current tick becomes wider and gap-red. Every tick is a keyboard-focusable button with a passage-role label. The global previous/next controls traverse the same anchors.
- **Reader chrome.** Lab/version, coverage depth, focus/full-document control, and the two-mark legend live in the document header. Split mode duplicates this chrome rather than creating a cross-lab aggregate. Absence is explicit: a zero-passage document states that no mapped passages exist and that this is an index finding.

#### Contextual reading-room modal

From a behaviour record, “read in context” and “compare both specs” open the same L4 reader in a large modal rather than navigating away by default. This preserves the open group, clause, record scroll position, and the user's place in the evidence review. The modal is an integration surface only: it embeds the canonical reader with URL state (`behavior`, `spec`, `compare`, `embedded`) and never duplicates passage rendering or navigation.

- The modal fills most of the viewport, becomes edge-to-edge on mobile, and retains one quiet header with the reading context, a direct “open full reader” link, and close.
- Focus moves to the close control on open and returns to the exact invoking control on close. Focus stays inside while open; Escape works both from the modal chrome and from inside the embedded reader.
- Backdrop click closes. The page beneath is inert, remains visually present, and resumes unchanged.
- The embedded presentation removes only redundant global navigation and the behaviour list. Spec switching, compare mode, focus/expand controls, passage rails, keyboard passage navigation, and source links remain the reader's own implementation.

## Interaction rules (what keeps it coherent)

- Hover previews, click commits, back ascends. No exceptions, so the grammar becomes muscle memory.
- Nothing is hover-only: keyboard focus triggers the same previews; touch is tap-to-preview, tap-again-to-commit.
- Dim siblings, never remove them.
- Motion budget: the one idle animation + transitions under ~250 ms. Honor `prefers-reduced-motion`.

## Visual encoding

- **Evidence marks:** dot runs -- filled count carries the meaning, hue reinforces it (on graphite: green `#67A589` / amber `#C0A05C` / red `#D27B7D`; on daylight: `#2F6F5B` / `#876622` / `#9E4A4F`; always paired with a text label).
- **Coverage:** standard blue (`#79A2C2` on graphite, `#315F88` on daylight), filled count = depth · not in spec = an explicit label (an absence is a finding, not blank space).
- **Color speaks only about data.** Everything structural -- rules, section marks, small caps, borders -- is ink and hairline gray. Drafts are italic + "in deliberation" tag; parked behaviours keep their exclusion reason one hover away.
- **Two surfaces:** **daylight** (default -- cool neutral `#E8ECEE`, panel `#F7F8FA`, ink `#18212B`) and **graphite** (`#101417`, panel `#1D2226`, ink `#E7EAEC`), toggled by the moon glyph (☾/☼) in the menu bar. IBM Plex Sans carries interface and headings, IBM Plex Serif is reserved for preambles and quotations, and IBM Plex Mono appears only for literal spec anchors. The L4 source body is the sole provenance-based exception described above.

## Data requirements this adds (fold into `data/` schemas)

- `coverage.json` citations need **stable anchor ids** into the mirrored specs, for L4 highlighting.
- `evals.json` needs per-rubric-dimension scores, the featured flag, and a short assessment note.
- Groups become data (`behaviours.json` gains group id + display order, or a small `groups.json`), since the group list will change.

## Prototype

[`prototypes/core-page.html`](prototypes/core-page.html) -- self-contained, demonstrates L0 → L3 with real behaviour names, definitions, and spec anchors from the canonical list; **eval scores are illustrative placeholders and labeled as such**. L4 is stubbed. Open it in a browser and hover.
