# panel-judges

Panel of LLM judges over spec passages. Per passage, each model votes **relevant / not**;
the published score is **0..N = how many models voted relevant**. See `FINDINGS.md` for why
we're here (lexical → semantic → panel) and `docs/matts-personal-notes.md` `[LADDER]` for the
experiment ladder + log.

## Pipeline
```
python3 harness.py <behaviour> <spec> <tag[,tag,...]> [--reason]   # judge -> runlog.jsonl
python3 aggregate.py [behaviour]                                    # runlog -> scores-*.json + agreement
```
- **Durable:** every verdict is appended to `runlog.jsonl` as it arrives; nothing is held only
  in memory.
- **Resumable:** re-running skips any `(behaviour, spec, model, locator)` already in the runlog.
- **Uniform:** one system+user prompt + "verdict per line" for every model, via each provider's
  OpenAI-compatible endpoint (`PROVIDERS` / `MODELS` in `harness.py`).
- `--reason` also logs the raw model output to `reasons.jsonl` (calibration/debug only).

`aggregate.py` writes `scores-<behaviour>-<model>.json` and `scores-<behaviour>-panel.json` in
the same shape the semantic-coverage demo (`build_demo.py`, parked branch) renders, so we can
visualise the panel in real context.

## Setup
- Keys in `.env` (gitignored): `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPINFRA_API_KEY`,
  `TOGETHER_API_KEY`, `GEMINI_API_KEY` (only the ones you use).
- Populate `behaviours.json` from `behaviours-for-adria`.

## Ladder (this dir = R0 onward; prior phase parked in `experiment/semantic-coverage`, PR #15)
R1 format smoke test · R2 approach sound (2 behaviours × models) · R3 cheapest model/family ·
R4 full run (10 behaviours) → publish.
