# Running a coverage sweep

A **coverage sweep** is how spec coverage enters the index: a staged pipeline,
run for one behaviour at a time, that grades what each lab's spec says about
the behaviour with the LLM panel, publishes the gate-approved coverage to the
repo data layer and the spec reader, and audits the publication -- with a
human sign-off gate between every stage.

## How to run it

Open this repo in an agent that reads these skill files (Claude Code, Qwen Code, or any agent you point at `.claude/skills/` — the files are plain markdown and agent-neutral; see root `AGENTS.md`) and say:

```
do the spec coverage for behaviour N
```

(or any behaviour number from `research/core-behaviour-list.md`). The
`spec-coverage-pass` skill runs one behaviour through the coverage and publish
stages -- extraction, coverage gate, publish, publish gate -- on a
`sweep/NN-<slug>` branch with a commit at every step. The verify audit then
runs in a fresh context, and the branch's PR merges only after you sign the
verify gate. Each stage ends by rendering its gate checklist in chat with
evidence, then **stops** -- nothing proceeds until you review and sign.

## The stages

| Stage | Gate -- what you check |
|---|---|
| Coverage (`sweep-coverage/`): the LLM panel grades every spec passage | Quotes re-resolve mechanically with zero mismatches; spot-read the passages |
| Publish (`sweep-publish/`): gate-approved coverage enters the data layer | `data/coverage.json` + the reader payload match the gate-approved artifact -- nothing deploys publicly here |
| Verify (`sweep-verify/`): fresh-context audit of the publication | The audit passes; you sign `sweep complete`, then the merge deploys the site |

**The verify stage must run in a session or subagent that did not execute the
sweep** -- start a new conversation and say "verify the behaviour NN sweep".

The gate records for the 02/03 sweeps were signed under an earlier numbering
(Gate 4/5/6); an edit note at the top of each maps those numbers to the stage
names above.

## Gate protocol (applies at every gate)

1. The stage skill finishes its artifact and renders its gate checklist in
   chat -- each item with pointed evidence (command output, links into the
   artifact), never bare checkmarks.
2. **STOP.** Do not start the next stage. The human reviews the artifact
   against the checklist; the checklist tells them what to spot-check, not
   just what to accept.
3. Corrections loop within the stage; re-render the checklist after fixes.
4. On approval, append to `gates.md`: the gate's name, date, approver,
   corrections made, and any open items the human explicitly accepted.
5. An open item accepted at a gate stays on the record in `gates.md` under
   that gate -- accepted never means dropped.
6. The next stage's work must not begin, even speculatively, before the
   current gate is signed.

## Where everything lands

```
research/sweeps/NN-<slug>/   the committed working record
  spec-coverage.md           excerpt sets, verdict, depth (a parsing contract)
  gates.md                   your dated sign-offs, corrections, accepted open items
  verify.md                  the verify audit
data/coverage.json            what the reader renders (via documents.json)
```

## References

- Shared fixed locations and spec versions: `references/locations.md`
- Public description of the method: [the site's methodology page](../../site/methodology.html)
- Stage details: each stage's `SKILL.md` in this directory
