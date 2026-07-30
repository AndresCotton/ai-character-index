# engine/panel

Pipeline that produces the LLM-panel relevance data for `site/llm-panel-review/`.

Credentials: `panel-config.json` holds env-var NAMES only; keys live in the
environment or a gitignored `.env` in this directory.

## Pieces
- `panel-config.json` -- providers, model tags, panels, rubric, display behaviours.
- `harness.py` -- batched judging (40 passages/prompt) + shared prompt builders
  (rubrics v1 binary / v2 ternary+scope / v3 ternary+form-fields).
- `whole_doc.py` -- whole-document judging (entire spec in one prompt, all verdicts
  in one response; rubric tag `v3w`). This mode produced the shipped data, winning
  an empirical dense-vs-sparse comparison.
- `batch_panel.py` -- provider Batch-API path (OpenAI + Anthropic) for the batched mode.
- `select_strata.py` + `smoke-*.txt` -- stratified validation sample (pinned).
- `build_site_data.py` -- runlog -> `site/llm-panel-review/data/behaviours.json`.

## The procedure
The end-to-end stage-4 procedure (dry run, execution, failure substitutions,
Gate 4 checks) is `.claude/skills/4-sweep-spec-coverage/SKILL.md`. This README
covers only the mechanics of the individual scripts.

## Reproducing the shipped data
1. Verdicts: `python3 whole_doc.py <behaviour> <spec> sol,fable,kimi` per cell
   (runlog is append-only + resume-safe; rerunning skips banked cells).
2. Site data: `python3 build_site_data.py --runlog=<runlog> --rubric=v3w --panel=frontier`.
The runlog behind the shipped data lives on the experiment branch
(`experiment/panel-judges`, `experiments/panel-judges/runlog-v3.jsonl`).
