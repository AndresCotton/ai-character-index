# Archived: the cross-spec "strict reading" judgment (general-welfare-impacts-strict)

Preserved here when `behaviours-for-adria/` was retired (2026-08-24) because
this file is the only place a genuine cross-spec comparison judgment exists in
the repository, and it is not recoverable from any committed panel runlog
(`engine/panel/runlog-v5.jsonl` has no rows for the
`general-welfare-impacts-strict` slug).

## What it is

`4-spec-coverage.md` is a stage-4 spec-coverage sweep (2026-07-25, Claude Code
Opus 5 under the then-current sweep skill) of one behaviour — *General welfare
impacts, strict reading: only what both specs share* — against the Claude
constitution (`constitution@2026-01-20`) and the OpenAI Model Spec
(`model-spec@2025-12-18`).

Its analytical result: applying the strict filter (keep a passage only if the
rule it states is also stated, in substance, by the other specification) cuts
the two specs' excerpt sets **asymmetrically** — the constitution drops from 29
passages to 16, while the model spec goes 22 → 22 (four out, four in). The
asymmetry is the finding: the constitution's welfare-relevant general
guidelines are far less mirrored by the model spec than the reverse. The file
organizes the surviving evidence as twelve paired rules (P1–P12) and logs
every dropped passage rather than silently omitting it.

## Provenance

- Sweep date: 2026-07-25; run by Claude Code (Opus 5) under
  `.claude/skills/4-sweep-spec-coverage` (the sweep skill as it then was).
- Quotes are exact `engine/spec-cite/cite.py resolve` output against the spec
  mirrors pinned above; they were independently re-resolved at the sweep's
  Gate 4. The mirrors themselves remain committed under `specs/`, so every
  locator in this file still resolves.
- Originally committed at
  `behaviours-for-adria/general-guidelines/02-general-welfare-impacts-strict/4-spec-coverage.md`;
  copied here byte-for-byte before that tree was deleted.

## What it establishes / does not establish

- Establishes: where the two specifications genuinely share welfare-relevant
  general guidelines, and how lopsided that overlap is (16 vs 22 surviving
  passages under a symmetric filter).
- Does not establish: anything about model behaviour (this is a spec-coverage
  judgment, not an adherence measurement), and nothing about the v5 panel run
  (which judges a different set of behaviours and never judged this one).
