---
name: 6-sweep-verify
description: Stage 6 of a behaviour sweep -- fresh-context audit of a completed sweep: cross-surface score identity, live links, locator re-resolution, register accounting, gate-log completeness. Produces the final sign-off (Gate 6). Run in a new session or subagent that did not execute the sweep.
---

# Sweep stage 6: verify

Input: a behaviour whose Gates 1-5 are signed.
Output: `research/evals/NN-<slug>/verify.md` -- findings, discrepancies, and their
resolution.

**Independence rule:** this stage is run by a context that did not produce the sweep
-- a fresh session or a subagent given only this skill and the behaviour number. The
auditor reads the repo, Notion, and the live web; it does not read the sweeping
session's conversation. An auditor that watched the sweep shares its blind spots.

## Checks

1. **Register accounting.** Every row in `register.md` has exactly one disposition
   and a filled Used-downstream. Every curated eval appears in all four places:
   write-up, `evals.json`, Notion Evals DB, prototype `B[NN]`. Every non-curated row
   appears in the write-up's rejected/leave-out table and `evals.json`'s `rejected`.
2. **Score identity.** I/E/R scores and adherence bands are identical across the four
   surfaces. Extract mechanically (jq for the JSON, parse the write-up tables and the
   `B[NN]` object) and diff -- do not eyeball.
3. **Links.** Every URL in `evals.json` `sources` fetched live now; any status change
   since the sweep is recorded (a dead link is a finding, not a failure).
4. **Quotes.** Every locator in `coverage.json`, the write-up, and the Notion spec
   coverage rows re-resolved with `engine/spec-cite/cite.py`; stored quotes
   byte-identical to resolver output.
5. **Fact spot-audit.** Pick 3 random dossier facts tiered verified-by-us and 3
   adherence numbers; trace each to its primary source.
6. **Gate log.** Gates 1-5 signed with dates in `gates.md`; every open item accepted
   at a gate appears in the write-up's known-unknowns; the `assessment` block in
   `evals.json` claims exactly what the gate log supports.

## Discrepancies

Each discrepancy is logged in `verify.md` with the owning stage. Fixes happen in
that stage's artifact first (noted in `gates.md`), then re-propagate through publish.
Re-run the affected checks after fixes; `verify.md` keeps both the finding and its
resolution -- a clean final report that hides a fixed discrepancy is a false record.

## Gate 6 -- the sweep is done

- [ ] All six check sections ran; outputs pasted or linked in `verify.md`.
- [ ] Zero unresolved discrepancies; resolved ones documented with their fixes.
- [ ] Known-unknowns list is honest: everything NV or gate-accepted is there.
- [ ] Human signs the final line of `gates.md`: `sweep complete: <name>, <date>`.

## After Gate 6: public release

Only now does the sweep reach the public webpage (Andrés, 2026-07-14: stage 5 is
internal publication; verification precedes public release). Deploy the site
(`pnpm deploy:site`) so the verified data goes live, and record the deploy date in
`gates.md` under Gate 6.

After Gate 6, the behaviour's transparency chain is closed: every candidate found is
accounted for, every number traces to a source, every quote to a resolver call, and
every review step to a dated sign-off.
