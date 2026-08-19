# Running a coverage sweep

A **coverage sweep** is how spec coverage enters the index: a staged pipeline,
run for one behaviour at a time, that grades what each lab's spec says about
the behaviour with the LLM panel, publishes the gate-approved coverage to the
repo data layer and the spec reader, and audits the publication -- with a
human sign-off gate between every stage.

Stage numbering starts at 4: numbers 4/5/6 are kept for continuity with the
signed gate records in `research/sweeps/02-calibration/` and
`03-action-honesty/`.

## How to run it

Open Claude Code in this repo and say:

```
do the spec coverage for behaviour N
```

(or any behaviour number from `research/core-behaviour-list.md`). The
`spec-coverage-pass` skill runs one behaviour through stages 4-5 -- stage 4,
Gate 4, publish, verify, Gate 5 -- on a `sweep/NN-<slug>` branch with a
commit at every step. The stage-6 audit then runs in a fresh context, and the
branch's PR merges only after you sign Gate 6. Each stage ends by rendering
its gate checklist in chat with evidence, then **stops** -- nothing proceeds
until you review and sign.

## The stages

| # | Stage | Gate -- what you check |
|---|---|---|
| 4 | Spec coverage (LLM panel) | Quotes re-resolve mechanically with zero mismatches; spot-read the passages |
| 5 | Publish | `data/coverage.json` + the reader payload match the gate-approved artifact -- nothing deploys publicly here |
| 6 | Verify | Fresh-context audit passes; you sign `sweep complete`, then the merge deploys the site |

**Stage 6 must run in a session or subagent that did not execute the sweep**
-- start a new conversation and say "verify the behaviour NN sweep".

## Gate protocol (applies at every gate)

1. The stage skill finishes its artifact and renders its gate checklist in
   chat -- each item with pointed evidence (command output, links into the
   artifact), never bare checkmarks.
2. **STOP.** Do not start the next stage. The human reviews the artifact
   against the checklist; the checklist tells them what to spot-check, not
   just what to accept.
3. Corrections loop within the stage; re-render the checklist after fixes.
4. On approval, append to `gates.md`: gate number, date, approver,
   corrections made, and any open items the human explicitly accepted.
5. An open item accepted at a gate stays on the record in `gates.md` under
   that gate -- accepted never means dropped.
6. Gate N+1 work must not begin, even speculatively, before gate N is signed.

## Where everything lands

```
research/sweeps/NN-<slug>/   the committed working record
  4-spec-coverage.md         excerpt sets, verdict, depth (a parsing contract)
  gates.md                   your dated sign-offs, corrections, accepted open items
  verify.md                  the stage-6 audit
data/coverage.json            what the reader renders (via documents.json)
```

## References

- Shared fixed locations and spec versions: `references/locations.md`
- Public description of the method: [the site's methodology page](../../site/methodology.html)
- Stage details: each `N-sweep-*/SKILL.md` in this directory
