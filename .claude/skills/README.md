# Running a behaviour sweep

A **sweep** is how evidence enters the index: a staged pipeline, run for one
behaviour at a time, that discovers every pre-existing eval of that behaviour,
curates and scores the credible ones, extracts what each lab's spec says, and
publishes the result -- with a human sign-off gate between every stage.

## How to run it

Open Claude Code in this repo and say:

```
sweep behaviour 1
```

(or any behaviour number from `research/core-behaviour-list.md`). The
`behaviour-sweep` skill picks it up and sequences the stages. Each stage ends by
rendering its gate checklist in chat with evidence, then **stops** -- nothing
proceeds until you review and sign.

## The stages

| # | Stage | Gate -- what you check |
|---|---|---|
| 1 | Discover | The evidence base is real and complete; spot-check 2 candidates against their sources |
| 2 | Curate | Confirm or override every disposition -- this is the editorial decision point |
| 3 | Score | Pick one eval x dimension and confirm the checklist items support the score |
| 4 | Spec coverage | Quotes re-resolve mechanically with zero mismatches; spot-read the passages |
| 5 | Publish (internal) | Notion, repo data, and prototype match the artifacts -- the public site is NOT deployed here |
| 6 | Verify, then release | Fresh-context audit passes; you sign `sweep complete`, then `pnpm deploy:site` goes public |

Stage 4 can run in parallel with 1-3. **Stage 6 must run in a session or
subagent that did not execute the sweep** -- start a new conversation and say
"verify the behaviour NN sweep".

## Where everything lands

```
research/sweeps/NN-<slug>/    the committed working record
  register.md                every candidate found, one row + disposition each
  1-dossiers.md              full dossier per candidate (kept or not)
  2-curation.md  3-scores.md  4-spec-coverage.md
  gates.md                   your dated sign-offs, corrections, accepted open items
  verify.md                  the stage-6 audit
research/sweeps/NN-<slug>.md  canonical write-up, assembled at stage 5
data/coverage.json            what the reader renders (via documents.json)
data/evals.json               the stage-5 eval survey; no renderer reads it
```

## References

- Exclusion criteria and register conventions: `behaviour-sweep/references/exclusion-criteria.md`
- Public description of the method: [the site's methodology page](../../site/methodology.html)
- Stage details: each `N-sweep-*/SKILL.md` in this directory
