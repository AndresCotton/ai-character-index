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

Publishes one behaviour's gate-approved stage-4 artifact into `data/coverage.json`, re-resolving every stored quote through `cite.py` first. Two artifact forms; the sidecar wins when both exist in the sweep directory:

- `4-spec-coverage.json` — structured sidecar, validated against [`data/schema/spec-coverage-sidecar.schema.json`](../data/schema/spec-coverage-sidecar.schema.json) plus cross-checks a single-file schema cannot express: `sidecar_version` must be 1 (the schema declares the field; only the publisher rejects a future value), records agree with the top-level behaviour identity and the `NN-<slug>` directory name, exactly one record per lab, the declared `citation_format` is the project convention, each `verified_against_version` equals the version pinned by the record's first locator, and a sidecar marked `provenance.reconstructed` names its source and date. Records are published verbatim — citation key order included — so a sidecar derived from `coverage.json` round-trips byte-for-byte.
- `4-spec-coverage.md` — the prose artifact, parsed by the ~4-line regex layout (behaviour 2 is the template). This is the fallback when no sidecar exists, and the only form behaviours 2–3 ship today. Its parsed records are validated against [`data/schema/coverage.schema.json`](../data/schema/coverage.schema.json) before anything is written or checked — parity with the sidecar path's schema gate.

The cite.py gate is the same on both paths: no quote is written or checked without re-resolution.

```sh
python3 engine/publish-coverage.py research/sweeps/02-calibration            # write
python3 engine/publish-coverage.py research/sweeps/02-calibration --check    # verify only
```

Behaviour 1 is a special case: `research/sweeps/01-no-sycophancy/` never had a stage-4 markdown artifact (its records were published in 2026-07, before the staged layout existed), so it ships a sidecar reconstructed from its published records in `data/coverage.json`. The sidecar's `provenance` block marks it `reconstructed` and lists what a genuine stage-4 artifact would carry that it cannot (term sweep and zero-hit probes, mirror-freshness record, authority annotations, "Considered and not kept", gate history). The schema lives in `data/schema/` but is deliberately not in `engine/validate_data.py`'s CHECKS — that tuple pairs `data/*.json` files with their schemas; sidecars validate `research/sweeps` artifacts and are enforced here at publish time instead.

Known decoupling debt: the publisher hardcodes its lab list (`LABS`: anthropic and openai, plus their markdown section headings) instead of reading `data/labs.json`, so a lab added there does not extend the publisher until `LABS` changes to match.

## panel/ (works today)

The LLM panel judging pipeline: whole-spec judging calls, verdict parsing, the rollout driver, and the `site/llm-panel-review/` payload builder. See [`panel/README.md`](panel/README.md) for mechanics and reproduction; `python3 engine/panel/test_panel.py` runs its 27 offline unit tests.

## site builders and checks (work today)

The reader surfaces render from generated payloads, never from hand-edited JSON:

```sh
python3 engine/build-spec-reader-data.py   # data/coverage.json + specs/ -> site/spec-reader/data/documents.json
python3 engine/build-reader-test-data.py   # data/reader-test-coverage.json -> site/spec-reader-test/data/behaviours.json
node engine/verify-spec-reader.mjs         # every behaviour x spec view of the published reader + nav presence + full link/fragment crawl (needs Chrome)
node engine/verify-reader-test.mjs         # the same for the reader test bench (needs Chrome)
```

The reader test bench ([`site/spec-reader-test/`](../site/spec-reader-test/)) is a separate
tab carrying an external reviewer's behaviour set. It shares the published reader's spec
text and nothing else, so work there cannot alter what the index publishes.

## data validation (works today)

Every file in [`data/`](../data/) is validated against the JSON Schemas in [`data/schema/`](../data/schema/), plus the cross-file rules from [`data/README.md`](../data/README.md): no **published** coverage verdict without a citation (the reader-test bench models an absence finding as a record with empty citations), no eval without a URL, no coverage record pointing at a lab that `labs.json` doesn't define, and no unknown behaviour IDs in `reader-test-coverage.json` (checked against its own behaviours list). Behaviour IDs in `coverage.json` and `evals.json` are unchecked until a canonical behaviours registry (`behaviours.json`, planned in PLAN.md §2) exists.

```sh
python3 engine/validate_data.py          # uses jsonschema when installed, stdlib fallback otherwise
python3 engine/test_validate_data.py     # the gate's own tests: committed data passes, mutations fail
```

## notion-sync/ (Phase 3)

Will pull the Notion databases (Evals by Behaviour; later Behaviours and Coverage) via the official Notion API, normalize into [`data/`](../data/), and open a PR when anything changed. Merging that PR is the push-to-production step -- no unreviewed change ever reaches the site.
