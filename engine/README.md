# engine/

The automation that keeps the index alive. Design in [PLAN.md §1.2](../PLAN.md).

## spec-watch/ (works today)

`pull-latest.sh` pulls the latest published specs from the labs' GitHub repos into [`specs/`](../specs/). Run manually for now:

```sh
./engine/spec-watch/pull-latest.sh
```

Requires an authenticated `gh` CLI. Known issue: the OpenAI upstream `docs/` release archives (dated HTML snapshots, 1.7-2.6 MB each) exceed the GitHub contents API's 1 MB inline limit, so the script's fetch of them yields 0-byte files; the empty artifacts have been removed from the repo and fixing the fetch is an open closeout-list item. In Phase 3 this becomes a weekly GitHub Action that opens a PR when a spec changed, plus an issue listing which behaviours cite the changed sections and need re-verification.

## spec-cite/ (works today)

`cite.py` resolves and verifies the precise spec citations defined in [`specs/CITATION.md`](../specs/CITATION.md) (`spec@version › section › ¶paragraph › sentence`). Every quote stored anywhere in the project (Notion Spec Coverage DB, sweep write-ups, `data/coverage.json`) must be the output of `resolve` for a pinned locator:

```sh
python3 engine/spec-cite/cite.py outline model-spec              # section tree + anchors
python3 engine/spec-cite/cite.py show "constitution > Being honest"   # numbered ¶/s
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"
python3 engine/spec-cite/cite.py find model-spec "some remembered phrase"   # text → locator
```

No CI re-resolves locators today (the only workflow is `.github/workflows/deploy.yml`). Re-resolution happens when `engine/publish-coverage.py` runs — it verifies every quote through `cite.py` before writing `data/coverage.json` — and a PR-time locator check is on the closeout list. Combined with spec-watch, that is what keeps coverage claims verifiable over time.

## publish-coverage.py (works today)

Publishes one behaviour's gate-approved stage-4 artifact (`research/sweeps/NN-<slug>/4-spec-coverage.md`) into `data/coverage.json`, re-resolving every stored quote through `cite.py` first:

```sh
python3 engine/publish-coverage.py research/sweeps/02-calibration            # write
python3 engine/publish-coverage.py research/sweeps/02-calibration --check    # verify only
```

## panel/ (works today)

The LLM panel judging pipeline: whole-spec judging calls, verdict parsing, the rollout driver, and the `site/llm-panel-review/` payload builder. See [`panel/README.md`](panel/README.md) for mechanics and reproduction; `python3 engine/panel/test_panel.py` runs its 27 offline unit tests.

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
