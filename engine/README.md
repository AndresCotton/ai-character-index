# engine/

The automation that keeps the index alive. Design in [PLAN.md §1.2](../PLAN.md).

## spec-watch/ (works today)

`pull-latest.sh` pulls the latest published specs from the labs' GitHub repos into [`specs/`](../specs/). Run manually for now:

```sh
./engine/spec-watch/pull-latest.sh
```

Requires an authenticated `gh` CLI. In Phase 3 this becomes a weekly GitHub Action that opens a PR when a spec changed, plus an issue listing which behaviours cite the changed sections and need re-verification.

## notion-sync/ (Phase 3)

Will pull the Notion databases (Evals by Behaviour; later Behaviours and Coverage) via the official Notion API, normalize into [`data/`](../data/), and open a PR when anything changed. Merging that PR is the push-to-production step -- no unreviewed change ever reaches the site.
