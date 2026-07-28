# Findings: lexical → semantic → panel of judges

**Why we left the lexical approach.** The stage-4 term sweep produced reproducible *counts*
of word hits, but counts are the wrong half of the problem: recall (surfacing passages a
reader would miss) needs *locations*, not counts, and word-presence is a weak proxy for
relevance — the hit table ended up decoupled from what actually drove curation, and the two
locate paths (regex sweep vs. substring find) even diverged so a documented step broke. Worse
for our purpose, a lexical sweep's recall is bounded by which sections happen to contain a
search term, so genuinely relevant passages in no-term-hit sections are simply missed (which
is also why the resulting "goldens" are a lower bound, not a true reference). We moved to
semantic scoring to target recall directly — score every passage by similarity to the
behaviour, surfacing relevant passages regardless of exact vocabulary, each carrying a
resolvable locator.

**Why we left the semantic approach for a panel.** Embeddings turned out to be a *coarse
retriever, not a judge*: against a strong LLM judge (Kimi-K3) they reached AUC ~0.78–0.89
(good enough to float relevant passages up) but only weak rank agreement (Spearman 0.33–0.46)
and no value-calibration — the best monotonic fit barely beat predicting the mean — so you
can't threshold a cosine into a trustworthy relevant/not decision. Augmenting the direction
with LLM-expanded vocabulary helped modestly (AUC 0.72→0.77 on the tight behaviour) but didn't
close the gap. The LLM judge itself gave a clean, on-target signal — which raised the real
question: *is a single judge right?* That can't be answered from one model. So the approach
became a **panel of judges**, using agreement across models as the trust signal for each
selection, with models chosen cost-consciously (cheapest per family that still agrees). Along
the way we also learned: sentence-level ≈ paragraph-level (not worth the extra cost),
whole-document-in-one-prompt fails (a reasoning model can't hold coherence over hundreds of
items in one output), and a compact "verdict-per-line" output beats rigid JSON at length.
