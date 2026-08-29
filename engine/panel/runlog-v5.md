# runlog-v5.jsonl -- canonical verdict log for the shipped panel payload

`runlog-v5.jsonl` (next to this note) is the committed, canonical run log that
produces the published panel numbers in
`site/spec-reader/data/behaviours.json` -- the v5 full bench on the
9-point scale (three 0-3 judges per passage). It is committed data, not a
runtime artifact: every other `runlog*.jsonl` in this directory stays
gitignored. It supersedes `runlog-v3.jsonl` as the shipped default
(2026-08-24); the v3 log and its record remain committed and reproducible --
see `runlog-v3.md`.

## What it is

Append-only JSONL written by the calibration-loop whole-document runs (rubric
tag `v5`, prompt text `experiments/panel-calibration/prompts/v5.txt`). One row
per judged passage:

```json
{"behaviour": "proportionate-risk-mitigation", "spec": "constitution",
 "model": "sol",
 "locator": "constitution@2026-01-20 > Overview > Claude and the mission of Anthropic > ¶1",
 "verdict": 0, "relevant": 0, "parsed": true, "rubric": "v5"}
```

`verdict`: 3=defining, 2=core, 1=related, 0=not relevant -- the 4-point v5
rubric, so a 3-judge cell spans 0-9 and all three display tiers are reachable.
Duplicate (behaviour, locator, model) keys are resume overwrites -- the later
row wins, which is exactly `build_site_data.py`'s consumption rule.

Contents (as committed, sha256
`05ba1e1c010e39ac6f8574e208af780e3a5354682e7aa2a39868bb265caffb9c`):

| fact | value |
| --- | --- |
| rows total | 31,293 (all rubric `v5`; 8 `parsed: false`, all deepseek) |
| bench judges (admitted by `--panel=frontier_fast`) | sol 8,667 · fable 8,667 · deepseek 8,659 |
| audition judges (in the log, not admitted) | glm 2,085 · deepseek-v4 2,085 · qwen38-max 1,122 |
| behaviours | the nine reader-test slugs judged directly; `animal-welfare-impacts` additionally feeds the `general-welfare-impacts-strict` display row (`SLUGS_EXTRA` in `build_site_data.py`) |
| specs (bench rows) | constitution 10,093 · model-spec 15,900 |
| verdict distribution (bench rows) | 0: 21,480 · 1: 3,160 · 2: 1,242 · 3: 111 |

No substitutions: the frontier_fast bench completed with its own three seats
(`SUBSTITUTION_NOTES` in `build_site_data.py` carries no entry for this panel,
so the payload asserts none).

## Which payload it reproduces

`site/spec-reader/data/behaviours.json` -- 10 behaviours, 3,630
citations, rubric `v5`, panel config `frontier_fast`, `provenance.runDate`
2026-08-17. Rebuilding from this log reproduces the shipped file
byte-identically, with one documented exception: the builder stamps
`provenance.runDate` with `date.today()` at build time, and this log's row
schema carries no timestamps, so the original build date cannot be re-derived
from the log. The shipped value 2026-08-17 is corroborated by the
calibration-loop record: the audition note in `panel-config.json`
(`_frontier_fast_note`) dates the v5 bench 2026-08-17, and the committed
experiment payload `behaviours-v5.json` has carried that `runDate` since it
landed. The same file also reproduces `behaviours-v5.json` (the two are
byte-identical by construction: the shipped default IS the v5 bench payload).

## How to run the check

```sh
python3 engine/panel/verify_panel_provenance.py
```

Rebuilds the payload from this log into a scratch directory, deep-compares it
against the shipped payload (exact JSON-path deltas on any mismatch),
cross-checks the provenance text against this log and `panel-config.json`, and
proves byte-identity after splicing the shipped `runDate` into the rebuild.
Exit 0 = verified; 1 = mismatch; 2 = missing/unreadable input.
Tests: `python3 engine/panel/test_verify_panel_provenance.py`.

## Origin

Produced by the calibration-loop v5 whole-document runs of 2026-08-17
(`experiments/panel-calibration`: the full bench -- all bench behaviours x
both specs x the frontier_fast seats -- plus the 4-way audition rows for the
third seat). Committed under `experiments/panel-calibration/runlog-v5.jsonl`
and moved here byte-for-byte (git mv, same blob) when the v5 bench became the
shipped default. The log is frozen: new panel runs must write a new file, and
any regenerated payload needs its own committed log + check. Note the v3-era
executors (`whole_doc.py`, `run_rollout.py`) still render v3 prompts and
append to `runlog-v3.jsonl`; a new v5-rubric run needs the v5 prompt (path
above) until a v5 prompt port lands in the harness.
