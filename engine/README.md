# engine/

The automation that keeps the index alive. Design in [PLAN.md §1.2](../PLAN.md).

## spec-watch/ (works today)

`pull-latest.sh` pulls the latest published specs from the labs' GitHub repos into [`specs/`](../specs/). Run manually for now:

```sh
./engine/spec-watch/pull-latest.sh
```

Requires an authenticated `gh` CLI. In Phase 3 this becomes a weekly GitHub Action that opens a PR when a spec changed, plus an issue listing which behaviours cite the changed sections and need re-verification.

## spec-cite/ (works today)

`cite.py` resolves and verifies the precise spec citations defined in [`specs/CITATION.md`](../specs/CITATION.md) (`spec@version › section › ¶paragraph › sentence`). Every quote stored anywhere in the project (Notion Spec Coverage DB, sweep write-ups, `data/coverage.json`) must be the output of `resolve` for a pinned locator:

```sh
python3 engine/spec-cite/cite.py outline model-spec              # section tree + anchors
python3 engine/spec-cite/cite.py show "constitution > Being honest"   # numbered ¶/s
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"
python3 engine/spec-cite/cite.py find model-spec "some remembered phrase"   # text → locator
```

In Phase 1, CI re-resolves every locator in `data/coverage.json` against `specs/`, so a spec update that moves text fails loudly instead of silently; combined with spec-watch, this is what keeps coverage claims verifiable over time.

## site builders and checks (work today)

The reader surfaces render from generated payloads, never from hand-edited JSON:

```sh
python3 engine/build-spec-reader-data.py   # data/coverage.json + specs/ -> site/spec-reader/data/documents.json
python3 engine/build-reader-test-data.py   # data/reader-test-coverage.json -> site/spec-reader-test/data/behaviours.json
node engine/verify-spec-reader.mjs         # every behaviour x spec view of the published reader (needs Chrome)
node engine/verify-reader-test.mjs         # the same for the reader test bench (needs Chrome)
```

The reader test bench ([`site/spec-reader-test/`](../site/spec-reader-test/)) is a separate
tab carrying an external reviewer's behaviour set. It shares the published reader's spec
text and nothing else, so work there cannot alter what the index publishes.

## notion-sync/ (Phase 3)

Will pull the Notion databases (Evals by Behaviour; later Behaviours and Coverage) via the official Notion API, normalize into [`data/`](../data/), and open a PR when anything changed. Merging that PR is the push-to-production step -- no unreviewed change ever reaches the site.
