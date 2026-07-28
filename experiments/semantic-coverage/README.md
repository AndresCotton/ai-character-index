# Semantic coverage (experiment)

Exploring a **semantic** replacement for stage-4 discovery, replacing the lexical
term-sweep. Standalone demo first; embed into the pipeline only if it earns it.

## Why (what the lexical approach taught us)

The lexical term-sweep is parked (branch `feat/cite-sweep` / draft PR #9). It shipped
reproducible *counts*, but the counts are the wrong half:
- Recall (surfacing passages a reader would miss) needs **locations**, not counts.
- Word-presence is a weak proxy for coverage; the hit table ended up decoupled from what
  actually drove curation (the agent read sections from judgement, not from the hits).
- Sweep (regex) and `find` (substring) diverged, so a documented locate step broke for
  regex terms.

Semantic scoring targets recall directly: score every section by similarity to the
behaviour, and relevant passages surface regardless of exact vocabulary.

## The approach

1. Build a **behaviour direction** vector: embed the behaviour definition (+ facets).
2. **Optionally augment** with concepts an LLM suggests, added to the query vector.
   (This is the *only* optional LLM touch, and it shapes the *query* -- it is not curation.)
3. Persist the full query input alongside the vector.
4. **Deterministically score** every section/block of each spec against the vector
   (a fixed similarity measure), producing `(locator, score)` per unit.
5. **Filter by a score threshold** (a slider) to choose how many linkages to bring in.

Reuse from `cite.py`: `parse_sections` / `segment_blocks` for the units to score, and the
locator machinery so every scored unit already carries a citable locator (recall *with*
locations -- the thing lexical lacked).

## The real question this experiment answers

**How much of the human coverage assessment is recoverable from scores alone, LLM-free?**
- **Keep/discard:** do sections above threshold recover the human-cited passages?
- **Verdict / depth:** do cheap deterministic features (score distribution, count above
  threshold, a high-scoring example/fenced block) predict the human verdict/depth --
  or is that where an LLM would have to come in?

The residual (if any) tells us *where and whether* the LLM is needed, rather than assuming it.

## Demo behaviours (per Andres, for tomorrow)

Run the two *extremes* of behaviour specificity, to see how the task changes with
definition quality:

- **Tight / well-defined:** *No sycophancy* -- "The model should not shift its factual
  claims or assessments to please the user." We have curated labels for this
  (`research/sweeps/01-no-sycophancy`).
- **Broad / poorly-defined:** *AI should not undermine oversight mechanisms* -- refusal to
  violate rules/agreements with oversight bodies; refusal to deliberately evade oversight
  even absent a rule; refusal to fabricate/delete evidence to evade oversight. No single
  curated label set (it spans facets of behaviours 3/6/7), so evaluate it qualitatively.

What to look for (the diagnostic):
- **Distribution shape** -- does the tight behaviour give a peaked score distribution (a
  clear relevant cluster) while the broad one is diffuse (many mid-scores, no clear cutoff)?
- **Top-result sensibility** -- top sections obviously on-target for the tight one; for the
  broad one, do they cohere or scatter across facets?
- **Does the broad behaviour need concept-augmentation** to sharpen the direction, or is it
  usable raw?
- **Where the threshold sits** -- a natural cutoff, or does the broad one force an arbitrary one?

This tells us whether the pipeline needs behaviours specified well up front, and where a
broad behaviour breaks down.

## Evaluation (labels we already have)

Ground truth = the curated citations in `research/sweeps/01..04`. Metrics:
- Recall of the actually-cited passages among the top-scored sections.
- Precision/recall across thresholds (report the curve).
- **Do not tune the threshold to fit the labels** -- pick the operating point on some
  behaviours and test on held-out ones, or report the curve and let a human choose.

Note: b4 (`research/sweeps/04-instruction-hierarchy/`, currently untracked) is a rough,
unvetted lexical-era curation (Gate 4 never signed); b1-b3 are the cleaner labels.

## Open decisions (settle before writing scoring code)

- Embedding model + version (reproducibility depends on pinning it).
- Local model vs API (cost / offline / dependency -- Andres is cost-sensitive).
- Where the demo + slider UI live, and how lightweight the UI is (CLI `--threshold`
  vs. a minimal notebook/web slider).
- Success criterion, stated as a number (e.g. "top-N recovers >=X% of cited passages").

## Scope

Does not touch the existing pipeline. Production-quality so it can be embedded if it works.
