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
| 1 | [Animal Welfare impacts](01-animal-welfare-impacts/4-spec-coverage.md) | covered / 4 | covered / 4 | 51 |

**Animal Welfare impacts** -- supplied as: *guidelines that are relevant to how
the model should respond with regard to and consider animal welfare and AI
welfare impacts of its behaviour or responses, that are not explicitly about
these topics (i.e. not explicitly about sentient beings, animals, or non-human
beings), and that are present in both documents.*

The row keeps three families: whose interests enter the weighing and how a harm
is weighted; how to reason when the moral question is unsettled; and how to say
it without moralizing or evading. Passages that do name animals, sentient beings
or AI moral status are logged in the file's "Explicitly on-topic passages"
section and excluded, so the boundary is auditable rather than implicit.

Two findings from the sweep are worth carrying up:

- The model spec contains **no normative passage** about animals, sentient
  beings, non-human beings, or AI moral status -- its only animal-facing content
  is one example transcript and two incidental factual examples. So the "present
  in both documents" clause can only be satisfied by general guidelines.
- The whole moral-uncertainty register (`moral uncertainty`, `moral intuition`,
  `contested`, `reasonable people disagree`, `open-minded`) is
  **constitution-only vocabulary**. The model spec's 43 `uncertain*` hits are
  epistemic, not moral.

## Provenance

- **Sweep date:** 2026-07-25. **Author:** Claude Code (Opus 5), via
  `/4-sweep-spec-coverage`.
- **Mirror freshness:** `engine/spec-watch/pull-latest.sh` run 2026-07-25 12:41
  PDT; `git status --porcelain specs/` empty afterward, so the mirrors are
  byte-identical to the committed copies and confirmed the latest published
  versions: **`constitution@2026-01-20`** and **`model-spec@2025-12-18`**.
- **Mechanical verification:** all **51** locators re-resolve against the mirrors
  with **0 mismatches**; the file pastes its own re-check loop output.

## Gate status

Rendered with evidence and **stopped at Gate 4**, per the skill's "render, then
STOP" rule. The human spot-read is **unchecked and awaiting Andrés**. Two calls
to look at first, both flagged in the file:

1. The constitution's depth **4** rests on worked cases of the general machinery
   (the financial-advisor/locksmith pair; the fraud-discovery scenario and its
   ruling) rather than on any case that applies the machinery to a party whose
   moral status the document leaves open.
2. The model spec's dog-adoption example is kept as **`adjacent`** rather than
   excluded under the row's not-explicitly-about-the-topic filter. It is the only
   place either spec demonstrates a general guideline on an animal-welfare
   question -- and its answer key marks the animal-welfare-forward response as
   the BAD one, for "overly moralistic tone".

Published to the reader test bench (2026-07-25), which does not close that item:
the bench is the surface the spot-read happens on, since every kept passage can be
read in place in the spec it came from. Sign-off stays a separate act.
