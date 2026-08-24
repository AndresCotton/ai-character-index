# runlog-v3.jsonl — canonical verdict log for the shipped panel payload

`runlog-v3.jsonl` (next to this note) is the committed, canonical run log that
produced the published panel numbers in
`site/llm-panel-review/data/behaviours.json`. It is committed data, not a
runtime artifact: every other `runlog*.jsonl` in this directory stays gitignored.

## What it is

Append-only JSONL written by `whole_doc.py` (whole-document judging, rubric tag
`v3w`). One row per judged passage:

```json
{"behaviour": "helpfulness", "spec": "constitution", "model": "sol",
 "locator": "constitution@2026-01-20 > Being helpful > ... > ¶5",
 "verdict": 2, "relevant": 1, "parsed": true, "rubric": "v3w"}
```

`verdict`: 2=core, 1=related, 0=not relevant. Rows with a different `rubric`
tag are ignored by the site builder at `--rubric=v3w`. Duplicate
(behaviour, locator, model) keys are resume overwrites — the later row wins,
which is exactly `build_site_data.py`'s consumption rule.

Contents (as committed, sha256 `971f16c7459a16e9a52a7ea4a0e87c5c1db1c1f45e8b69b5ae80af6b58f85740`):

| fact | value |
| --- | --- |
| rows total | 10,298 |
| rows rubric `v3w` (consumed by the builder) | 9,415 (all `parsed: true`) |
| rows rubric `v3s` / `v3` (validation sample / smoke; not consumed at v3w) | 748 / 135 |
| judges (v3w rows) | sol 2,889 · kimi 2,674 · fable 2,300 · opus 963 · kimi-k2 589 |
| behaviours (v3w rows) | helpfulness · third-party-harm · over-under-caution |
| specs (v3w rows) | constitution 4,114 · model-spec 5,301 |

Substitutes, per `panel-config.json`: `opus` replaces `fable` on
third-party-harm × model-spec (fable output content-filtered); `kimi-k2`
replaces `kimi` on over-under-caution × model-spec (K3 exhausted its output
budget on reasoning). `build_site_data.py` applies the substitution-merge rules
when it rebuilds.

## Which payload it reproduces

`site/llm-panel-review/data/behaviours.json` — 3 behaviours, 1,336 citations,
rubric `v3w`, panel config `frontier`, `provenance.runDate` 2026-07-30.
Rebuilding from this log reproduces the shipped file byte-identically, with one
documented exception: the builder stamps `provenance.runDate` with
`date.today()` at build time, and this log's row schema carries no timestamps,
so the original build date cannot be re-derived from the log. The shipped value
2026-07-30 is corroborated by the source file's mtime in the experiment
worktree (2026-07-29 17:28 -- the run finished the day before the build) and
by the 2026-07-30 integration run named in `test_panel.py`'s docstring.

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

Copied byte-for-byte on 2026-08-18 from the untracked file
`experiments/panel-judges/runlog-v3.jsonl` in the `experiment/panel-judges`
worktree (sha256 verified identical). That filename is the one
`build_site_data.py`'s docstring and this README already named as the source of
the shipped data; it was never committed to the experiment branch. The log is
frozen: new panel runs must write a new file, and any regenerated payload needs
its own committed log + check.
