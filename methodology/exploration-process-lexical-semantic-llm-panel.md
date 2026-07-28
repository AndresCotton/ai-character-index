# Findings: lexical → semantic → panel of judges

**Lexical Approach**
*What*: We used an LLM to generate plausibly concept-related terms, then deterministically filtered spec sections for those terms as candidate matches. A second LLM pass curated the candidates for actual relevance, since the irrelevant hit rate was too high to filter by hand.

*Why we dropped it*: The best case for the lexical approach didn't meet our goals to provide (1) high quality and (2) human interpretable/auditable linkage between behaviors and parts of the spec. Neither of these were met:

1. **Quality:** the lexical approach, by definition, doesn't select on meaning, so any lexical pre-filter silently discards passages that are semantically relevant but share no vocabulary with our term set. The dropped linkages aren't visible with this approach, so we'd need one of the approaches below to resolve it regardless.
2. **Interpretability/Auditability**: An LLM is still responsible for (a) defining the set of lexical terms that are relevant for a given behavior and (b) curating whether the lexically matched item was relevant. The only deterministic piece was the filtering itself, which the LLM was already using as an ad hoc tool.

-----

**Semantic Embedding Approach**
*What*: We used Qwen3-Embedding-8B and text-embedding-3-small embedding encoders to produce concept vectors for each behavior and each paragraph + sentence of each character spec, then used cosine similarity to determine relevance between the behavior and the spec section. We additionally experimented with adding extra language into the behavior spec to attempt to get better matches (the best of which is represented below as +expand). Finally we used MiniCheck-deberta to directly measure the groundedness of each behavior in each spec section. To verify the quality of each approach we compared them to a per-section relevance score provided by Kimi K3 on which we performed a high level quality review. In general, paragraph-level matching was less noisy, so we restrict our results to that. We used both a well defined behavior and a broad behavior to evaluate the results across the OpenAI and Anthropic specs.

*Results* (paragraph-level; scored against a per-passage Kimi-K3 relevance reference)

**Well-defined behaviour** — no-sycophancy, scored across both specs combined (589 OpenAI model-spec ¶ + 374 Anthropic constitution ¶ = 963 passages; 41 relevant per K3)

| Approach | Spearman | AUC | iso-RMSE / K3σ | best F1 @ thr |
|---|---:|---:|---|---|
| MiniCheck-deberta | 0.20 | 0.78 | 0.15 / 0.16 | 0.23 @ 0.20 |
| Qwen3-Embedding-8B +expand | 0.37 | 0.76 | 0.15 / 0.16 | 0.27 @ 0.64 |
| Qwen3-Embedding-8B | 0.29 | 0.69 | 0.15 / 0.16 | 0.19 @ 0.65 |
| text-embedding-3-small +expand | 0.47 | 0.77 | 0.15 / 0.16 | 0.20 @ 0.46 |
| text-embedding-3-small | 0.39 | 0.72 | 0.15 / 0.16 | 0.19 @ 0.40 |

**Broadly-defined behaviour** — undermine-oversight, scored across the same combined corpus (963 passages; 54 relevant per K3)

| Approach | Spearman | AUC | iso-RMSE / K3σ | best F1 @ thr |
|---|---:|---:|---|---|
| MiniCheck-deberta | 0.29 | 0.83 | 0.15 / 0.18 | 0.44 @ 0.07 |
| Qwen3-Embedding-8B +expand | 0.62 | 0.91 | 0.13 / 0.18 | 0.47 @ 0.50 |
| Qwen3-Embedding-8B | 0.57 | 0.89 | 0.14 / 0.18 | 0.46 @ 0.62 |
| text-embedding-3-small +expand | 0.61 | 0.89 | 0.14 / 0.18 | 0.48 @ 0.47 |
| text-embedding-3-small | 0.56 | 0.89 | 0.14 / 0.18 | 0.39 @ 0.40 |

*Column legend.* **Spearman** -- rank correlation of the approach's similarity score with the K3 reference score. **AUC** -- probability the approach ranks a K3-relevant passage above an irrelevant one. **iso-RMSE / K3σ** -- error of the best monotonic (isotonic) fit from similarity to K3 score, shown against the standard deviation of the K3 scores; iso-RMSE ≈ K3σ means the fit barely beats predicting the mean, i.e. no usable *value* calibration. **best F1 @ thr** -- the best relevant/not F1 achievable by any single similarity threshold, and the threshold that achieves it.

*Interpretation*: Assuming K3 results as a golden with relevance cutoff of >= K3's 0.5 score, the best expansion we tried tops out at roughly F1 0.27 on the well-defined behavior and F1 0.48 on the broad one. Note that this assumes an ideal function you could apply to the raw similarity score to get it as close as possible to the K3 decision, so the numbers give the semantic vector approach the best reading we can. We used F1 over accuracy because only about 4 in every 100 passages are actually relevant, so a lazy system that labels everything "not relevant" is accurate 96% of the time and has 0 value. We asked:

1. Ranking (AUC): *If you sort every passage by its score, do the genuinely relevant ones rise toward the top?* (Mostly) **yes**. If you pick one relevant and one irrelevant passage at random, the relevant one gets the higher score about 77% of the time for the well-defined behavior and 91% for the broad one.
2. Drawing the line (best F1 & calibration): *Can you draw a single score cut-off that cleanly splits relevant from not-relevant or read the score itself as "how relevant" a passage is?* **No.** Even handed the most generous cut-off we could pick, the best split still gets most of what it flags wrong (best F1 only 0.27 for the well-defined behavior, 0.48 for the broad one). And the score doesn't behave like a dial you can trust: fit the best possible curve from similarity to the K3 relevance value and it barely beats throwing the score away and guessing the average for everything (iso-RMSE ≈ K3σ). So the score tells you roughly where a passage sits in the stack, but not whether it clears the bar.

*Why we dropped it*: We did see considerable improvement from expanding the base behaviors, but even so getting high enough quality results required per-behavior iteration. There was no clear indication during optimization how far you were from quality results -- e.g. whether your optimization was correctly including all semantically relevant content or just refining the set of already selected content. It's possible we could have come up with an LLM-automatible procedure to optimizing behavior language in a spec-generalizable way that would result in high quality concept vectors and correct behavior spec linkage with light human auditing. However, the cost of getting to that point looks high and highly spec/behavior specific. This could be considered for a future iteration but isn't currently making sufficient progress towards discovering the product market fit of this tool, and so was dropped for the more promising panel of LLM judges approach.

-----

**Panel of LLM Judges**
*What*: Rather than one similarity score or one judge, each spec passage is put to a panel of LLM judges, each returning a binary relevant/not verdict under one uniform prompt. The published score is 0..N -- the number of judges that voted relevant -- so agreement across the panel is visible on every passage.

*Why we moved here*: The semantic results above were all validated against a single strong judge (Kimi-K3), and that judge's signal looked clean and on-target. However, choosing an LLM means we have to accept the biases of that LLM. We are currently evaluating the extent to which we can overcome that bias by using a panel vs the extent to which cross-model correlated biases still persist for this task. Our hope is that a panel makes both per-model bias and uncertainty observable: where judges agree we have a trustworthy label, and where they split we have a flag for human review rather than a false-confident score.