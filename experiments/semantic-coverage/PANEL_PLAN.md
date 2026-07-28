# Multi-agent (judge-panel) testing plan

Goal: find the most **reliable + cost-effective** way to select the spec passages relevant
to a behaviour, using a **panel of LLM judges**, and decide the right **model(s) + granularity +
context**. Core signal = **agreement across judges** (not any single "golden" model).

## What we already have (DO NOT re-run)
- K3 **paragraph** relevance, both behaviours, both specs (complete).
- K3 **sentence**, both behaviours, **~50% partial** (`partial-Kimi-K3-sentence-*.json`) -- credit-limited.
- Embedding cosine (2 models × paragraph+sentence) + `+expand` variants; MiniCheck-deberta (paragraph).
- Findings so far: embeddings are a coarse retriever, not a judge proxy (AUC ~0.8, weak rank agreement);
  **expand** annotation helps modestly; sentence≈paragraph in ordering (Pearson ~0.88) but noisier on the
  relevant set (F1 0.63-0.79), so sentence isn't clearly worth its cost on its own.

## The three things to test (in priority order)

### 1. Full-document context, per-section output  ← TOP PRIORITY
The whole-doc attempt that failed asked for *all* scores in one response (~1500) → truncated JSON.
Fix: put the **whole document in the prompt as context**, but ask the model to score **only the
passages of one section per call** (bounded output → reliable JSON), and mark which passages to score.
- Compares directly against the existing section-only K3 (same passages, added context).
- Answers Andrés's calibration point: does seeing the rest of the doc change/steady the scores?
- Cost: one call per section (~117/behaviour), input now includes the doc each call → input-heavy.
  Estimate first from a couple of sections before committing.

### 2. Judge panel across models (quality-vs-cost curve)
Run the SAME section-level judging with a range of models and measure agreement + degradation:
- **K3** (have, reference) · **Qwen3-235B-Instruct** · **Qwen3-32B** · **DeepSeek-V3.2** · a small one
  (e.g. Qwen3-8B) to find where quality falls off. All on Together/DeepInfra batch.
- Metrics: pairwise Spearman + "relevant-set" F1 between judges; **per-passage agreement** (variance/
  fraction of judges above threshold) as a confidence score surfaced in the demo.
- Deliverable: cheapest model whose agreement with the panel is acceptable → the recommended judge.

### 3. Granularity confirm (cheap, mostly done)
Use the existing partial sentence data (`granularity.py`) -- already shows sentence≈paragraph in order,
noisier on the set. Only extend if #1/#2 suggest sentence+context behaves differently.

## Reuse / cost discipline
- Reuse `judge.py` (takes a model arg) for real-time and `batch_judge.py` (Together batch, ~50% off) for scale.
- Together has a credit cap that killed the sentence batch twice -- **raise the cap / prefund** before batch runs;
  estimate cost from a 2-3 request probe first (K3 output is ~650 tokens/section, so output at $15/M dominates).
- Persist every judge as `scores-<behaviour>-<model>-<chunk>.json` so it drops into the demo as a column,
  and add a panel-agreement analysis (like `compare.py`, but across judges).

## Open questions to answer with the above
- Does full-doc context materially change the selection vs section-only? (calibration)
- How small a model can we use before agreement with the panel degrades? (cost)
- Is the right product a single judge, or a panel with an agreement-gated selection? (methodology)
