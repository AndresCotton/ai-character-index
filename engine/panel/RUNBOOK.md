# Runbook: producing panel coverage data

How to score behaviours against the specs with the LLM panel, from a standing start.
Anyone with repo access and API keys can follow this end to end; no prior context on the pipeline is assumed.

## One-time setup
1. Put API keys in `engine/panel/.env` (gitignored). The variable names are listed in
   `panel-config.json` under `providers`. You need OPENAI_API_KEY, ANTHROPIC_API_KEY,
   and TOGETHER_API_KEY for the default frontier panel.

## Adding or editing a behaviour
2. Add an entry to `engine/panel/behaviours.json`. Required: `label` and `query`
   (the definition, exactly as supplied). Optional: `title` (display name if the label
   carries annotations), `clarifications`, `boundary` (the scope text; rendered as the
   Scope field). Blank optional fields render as "none provided" and the rubric tells
   judges to infer nothing from that.
3. If the behaviour should appear on the site, add its site slug to `SLUGS` in
   `build_site_data.py` and to `display.behaviours` in `panel-config.json`.

## Producing the data
4. Dry run first. This prints every API call the run would make, what resume will
   skip, and a cost estimate. It sends nothing:
       python3 run_rollout.py --runlog=<runlog path>
5. Execute: add `--go`. Interrupting is safe; rerunning skips completed cells.
6. Watch for PARSE FAILURE lines. Known failure modes and fixes:
   - finish_reason content_filter (seen with Fable on harm-dense cells): run the
     substitute judge, e.g. `python3 whole_doc.py <behaviour> <spec> opus`
   - finish_reason length (seen with K3: it spends the whole output budget reasoning):
     run `python3 whole_doc.py <behaviour> <spec> kimi-k2`
   The builder prefers the primary judge when both exist, so substitutes are safe to
   run and are replaced automatically if the primary later succeeds.
7. Build the site data:
       python3 build_site_data.py --runlog=<runlog> --rubric=v3w --panel=frontier
8. Check the output line for citation counts, then load the site locally
   (`cd site && python3 -m http.server`) and spot check a few "?" popups.

## What the numbers mean
Each judge grades every passage 2 (core), 1 (related), or 0. A passage's score is the
sum across judges. The site's display threshold is a URL parameter; the data always
carries every passage that scored at least 1, plus each judge's raw verdict.
