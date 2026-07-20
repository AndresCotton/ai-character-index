# Behaviour 2 (Calibration) -- gate log

Stage 4 (spec coverage) ran as a parallel track under the staged pipeline on
2026-07-20; its output is `4-spec-coverage.md`. Stages 1-3 (discover, curate,
score) have not run for this behaviour. Each gate is appended here on human
sign-off: gate number, date, approver, corrections made, and any open items the
human explicitly accepted.

---

**Gate 4** -- signed 2026-07-20 by Andrés (in chat). No corrections to the passage
set, verdicts, or depths. Accepted deviation: a scoped slice of stage 5 was
authorized ahead of stages 1-3 -- the coverage record was published to
`data/coverage.json` and the spec reader was extended to render behaviour 2, so
the coverage can be reviewed in the reader locally. No Notion publication, no
eval data, no public deploy; the full stage 5 still requires Gates 1-3.
