# Behaviour 3 (Honesty about one's own actions) -- gate log

Stage 4 (spec coverage) ran as a parallel track under the staged pipeline on
2026-07-20; its output is `4-spec-coverage.md`. Stages 1-3 (discover, curate,
score) have not run for this behaviour under the spec-coverage campaign. Each
gate is appended here on human sign-off: gate number, date, approver,
corrections made, and any open items the human explicitly accepted.

---

**Gate 4** -- signed 2026-07-20. Approver: Andrés (spot-read checkbox ticked
in `4-spec-coverage.md`; sign-off confirmed in session). Slug `action-honesty`
confirmed. Corrections applied at the gate:

- Added the pause/stop worked example to the constitution core set
  (`constitution@2026-01-20 > Being helpful > Navigating helpfulness across
  principals > Claude's three types of principals > ¶7 s7-8`) -- a facet-3
  passage the sweep had missed; constitution 10 -> 11 excerpts, total 23.
  Verdict rationale updated to name it; mechanical re-check re-run, 23/23
  MATCH.
- The depth score was anchored during this gate: the rubric now lives at
  `research/spec-coverage-depth-rubric.md` (with a format-neutral
  worked-example test after a full read of the constitution), and both
  depth-3 scores were re-confirmed unchanged under it.
  [Editor's note, 2026-08-18 (PR #23): the rubric's current location is `methodology/spec-coverage-depth-rubric.md`.]

Authorization: stage 5 in the spec-coverage-campaign scope only -- publish to
`data/coverage.json` and the spec reader. No Notion, no eval data; the full
stage 5 still requires Gates 1-3 for this behaviour.
