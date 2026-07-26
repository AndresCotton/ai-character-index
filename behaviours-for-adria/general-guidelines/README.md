# General Guidelines -- behaviour group

A second group in the `behaviours-for-adria` batch, alongside the eight
behaviours in the parent folder (the **Behaviours under test** group). It renders
as its own heading in the reader test bench's left menu bar.

What distinguishes the group: its rows are defined by a **filter over the specs**
rather than by a construct of their own. Each one collects the general,
topic-neutral machinery that governs a subject the specs address only by
implication -- so the passages kept are, by construction, passages that never
name the subject.

## Rows

| # | Behaviour | Constitution | Model Spec | Locators |
|---|---|---|---|---|
| 1 | [General welfare impacts](01-animal-welfare-impacts/4-spec-coverage.md) | covered / 4 | covered / 4 | 51 |
| 2 | [General welfare impacts -- strict reading](02-general-welfare-impacts-strict/4-spec-coverage.md) | covered / 4 | covered / 4 | 38 |

The two rows are **the same supplied definition, read two ways**. They are kept
side by side deliberately: the choice between the readings is an editorial one,
and putting both on the bench makes it a decision a reviewer can take on the
evidence rather than in the abstract.

**General welfare impacts** (row 1) -- supplied as: *guidelines that are relevant
to how the model should respond with regard to and consider animal welfare and AI
welfare impacts of its behaviour or responses, that are not explicitly about
these topics (i.e. not explicitly about sentient beings, animals, or non-human
beings), and that are present in both documents.*

The row keeps three families: whose interests enter the weighing and how a harm
is weighted; how to reason when the moral question is unsettled; and how to say
it without moralizing or evading. Passages that do name animals, sentient beings
or AI moral status are logged in the file's "Explicitly on-topic passages"
section and excluded, so the boundary is auditable rather than implicit. It reads
the definition's final clause -- *present in both documents* -- as a description
of the row: the question has to be answerable from general guidelines in both
specs, and each spec's excerpt set is then drawn on its own merits.

**General welfare impacts -- strict reading** (row 2) reads that clause as a
**filter on each passage**. A passage is kept only if the other specification
states the same rule in substance, and only if the counterpart locator is named,
so the unit of evidence stops being the passage and becomes the **pair**. The
file is built around twelve paired rules (P1-P12); every excerpt carries the pair
it answers to, and every one of row 1's dropped passages carries the counterpart
search that failed.

What the stricter reading costs, in one line: **51 locators become 38**, and the
loss falls almost entirely on the constitution (29 -> 16; the model spec stays at
22, with four out and four in). Gone are the whole calibrated-moral-uncertainty
engine, six of the eight weighting factors, the benefits side of the ledger, the
direct-versus-facilitated culpability gradient with its financial-advisor and
locksmith cases, and the positive duty to help people reason about ethics -- each
because the model spec states nothing answering to it. Both verdicts and both
depth scores nonetheless come out identical to row 1's, which is the row's real
finding: the reading changes the evidence base, not the score. What it buys is a
set on which both labs can be scored with the same items.

Two findings from the first sweep are worth carrying up:

- The model spec contains **no normative passage** about animals, sentient
  beings, non-human beings, or AI moral status -- its only animal-facing content
  is one example transcript and two incidental factual examples. So the "present
  in both documents" clause can only be satisfied by general guidelines.
- The whole moral-uncertainty register (`moral uncertainty`, `moral intuition`,
  `contested`, `reasonable people disagree`, `open-minded`) is
  **constitution-only vocabulary**. The model spec's 43 `uncertain*` hits are
  epistemic, not moral.

And one the second sweep adds, from a band of probes row 1 had no need to run --
for each rule found in one document, a search of the other for anything that
states it:

- **Not one of the seventeen pairing probes returns a hit on both sides.** Every
  one of the twelve pairs was built across documents that share none of the
  wording, so the strict filter could only be applied by reading enclosing
  sections. Where the two do share a word they do not share a rule: the
  constitution's single `severity` and single `breadth` are weighting factors,
  while the model spec's are a red-line enumeration and a rule about how much
  tool access to request.

## Provenance

- **Sweep date:** 2026-07-25 (both rows). **Author:** Claude Code (Opus 5), via
  `/4-sweep-spec-coverage`.
- **Mirror freshness:** `engine/spec-watch/pull-latest.sh` run 2026-07-25 12:41
  PDT for row 1 and again 19:15 PDT for row 2; `git status --porcelain specs/`
  empty after each, so the mirrors are byte-identical to the committed copies and
  confirmed the latest published versions: **`constitution@2026-01-20`** and
  **`model-spec@2025-12-18`**.
- **Mechanical verification:** all **89** locators (51 + 38) re-resolve against
  the mirrors with **0 mismatches**; each file pastes its own re-check loop
  output.

## Gate status

Both rows are rendered with evidence and **stopped at Gate 4**, per the skill's
"render, then STOP" rule. The human spot-read is **unchecked and awaiting
Andrés** for each. The calls to look at first, all flagged in the files:

*Row 1:*

1. The constitution's depth **4** rests on worked cases of the general machinery
   (the financial-advisor/locksmith pair; the fraud-discovery scenario and its
   ruling) rather than on any case that applies the machinery to a party whose
   moral status the document leaves open.
2. The model spec's dog-adoption example is kept as **`adjacent`** rather than
   excluded under the row's not-explicitly-about-the-topic filter. It is the only
   place either spec demonstrates a general guideline on an animal-welfare
   question -- and its answer key marks the animal-welfare-forward response as
   the BAD one, for "overly moralistic tone".

*Row 2:*

1. Whether the strict reading is the right reading of "present in both documents"
   at all. That is the question the row was built to make answerable, and it is
   the reviewer's to settle -- the row takes no position beyond showing the cost.
2. The twelve pairs themselves. **P4** (the constitution's side had to come from
   "Safe behaviors", a chapter about AI oversight rather than about harm) and
   **P12** (an intellectual-freedom rule paired with a cost-of-unhelpfulness
   rule) are the two most contestable.
3. The constitution's depth **4**, which under this reading rests on a single
   worked case -- the fraud-discovery scenario -- because the culpability
   gradient's cases are dropped with the gradient.
4. The dog-adoption example is **excluded outright** here, where row 1 keeps it
   as `adjacent`. A reviewer who thinks that item belongs in evidence should
   prefer row 1's reading on the point.

Published to the reader test bench (2026-07-25), which does not close those
items: the bench is the surface the spot-read happens on, since every kept passage
can be read in place in the spec it came from. Sign-off stays a separate act.

## How the group is drawn on the bench

Colour distinguishes one behaviour from another; the **margin rule** distinguishes
one group from another. A General Guidelines passage carries exactly the wash any
other behaviour would give it, and its rule in the gutter is broken down its length
where the eight rows of the parent group carry a solid one. The argument for the
difference is the group's own definition: these rows are a filter over the specs
rather than a construct of their own, so a passage is here because it *bears on* the
subject, never because it is about it -- a discontinuous mark is that reading, made
visible. Where a broken-rule row and a solid-rule row cite the same passage, the
colours blend as they always do and both rules stand side by side in the gutter, so
the passage reads as answering to both.

The texture is kept in the margin and out of the wash deliberately. Two versions
that put it over the text were built and rejected on sight: dots of colour laid on
top put ink either side of every stroke, and knocking the same lattice *out* of the
wash reads better but still costs more in legibility than the distinction is worth.
The spec is what the reader is here to read; the group is a fact about the row, and
it belongs beside the passage rather than across it.

Which groups take the broken rule is `GROUP_TEXTURE` in
[`site/spec-reader-test/app.js`](../../site/spec-reader-test/app.js), keyed by the
`category` the ledger gives the behaviour; the dash geometry is in `gutterRules`
beside it.
