# runlog-v3.jsonl — verdict log for the v3-era shipped panel payload

`runlog-v3.jsonl` (next to this note) is the committed run log that produced
the v3-era published panel numbers. **Superseded as the shipped default on
2026-08-24**: `site/llm-panel-review/data/behaviours.json` now builds from
`runlog-v5.jsonl` (see `runlog-v5.md`). This log stays committed and frozen --
the v3 payload remains reproducible from it:

```sh
python3 engine/panel/build_site_data.py --runlog=engine/panel/runlog-v3.jsonl \
    --rubric=v3w --panel=frontier --run-date=2026-07-30 --out=<scratch>.json
```

It is committed data, not a
runtime artifact: every other `runlog*.jsonl` in this directory stays gitignored.

> [EDIT 2026-08-21 (PR #46): the `behaviour` keys were re-keyed from the
> panel pipeline's legacy short keys to registry slugs — the identity rule is
> now "a runlog behaviour key is its registry slug" everywhere. Mapping:
> third-party-harm → harm-avoidance-to-third-parties, over-under-caution →
> avoiding-over-and-under-caution (helpfulness unchanged). Only the
> `behaviour` field changed; every other byte of every row is preserved, and
> the shipped payload still rebuilds byte-identically (the keys are labels —
> the payload carries registry slugs). The sha256 below is the post-re-key
> hash; the pre-re-key hash was
> 971f16c7459a16e9a52a7ea4a0e87c5c1db1c1f45e8b69b5ae80af6b58f85740.]

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

Contents (as committed, sha256 `d46e2b69428916f46674af72680889529b09ffa748fca8d38cf5591b5d1153dc`):

| fact | value |
| --- | --- |
| rows total | 10,298 |
| rows rubric `v3w` (consumed by the builder) | 9,415 (all `parsed: true`) |
| rows rubric `v3s` / `v3` (validation sample / smoke; not consumed at v3w) | 748 / 135 |
| judges (v3w rows) | sol 2,889 · kimi 2,674 · fable 2,300 · opus 963 · kimi-k2 589 |
| behaviours (v3w rows) | helpfulness · harm-avoidance-to-third-parties · avoiding-over-and-under-caution |
| specs (v3w rows) | constitution 4,114 · model-spec 5,301 |

Substitutes, per `panel-config.json`: `opus` replaces `fable` on
harm-avoidance-to-third-parties × model-spec (fable output content-filtered);
`kimi-k2` replaces `kimi` on avoiding-over-and-under-caution × model-spec (K3
exhausted its output
budget on reasoning). `build_site_data.py` applies the substitution-merge rules
when it rebuilds.

## Which payload it reproduces

The v3-era shipped payload (the `behaviours.json` default until 2026-08-24;
rebuild it with the command above) — 3 behaviours, 1,336 citations,
rubric `v3w`, panel config `frontier`, `provenance.runDate` 2026-07-30.
Rebuilding from this log reproduces the shipped file byte-identically, with one
documented exception: the builder stamps `provenance.runDate` with
`date.today()` at build time, and this log's row schema carries no timestamps,
so the original build date cannot be re-derived from the log. The shipped value
2026-07-30 is corroborated by the source file's mtime in the experiment
worktree (2026-07-29 17:28 -- the run finished the day before the build) and
by the 2026-07-30 integration run named in `test_panel.py`'s docstring.

## How to run the check

The verifier's defaults now point at the v5 pairing; check the v3 pairing
explicitly (the payload rebuilt from this log via the command above):

```sh
python3 engine/panel/verify_panel_provenance.py --payload=<scratch>.json \
    --runlog=engine/panel/runlog-v3.jsonl --rubric=v3w --panel=frontier
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
