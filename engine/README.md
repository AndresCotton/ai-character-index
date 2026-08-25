# engine/

The automation that keeps the index alive. Design in [PLAN.md §1.2](../PLAN.md).

## spec-watch/

`pull-latest.sh` pulls the latest published specs from the labs' GitHub repos into [`specs/`](../specs/). Run manually for now:

```sh
./engine/spec-watch/pull-latest.sh
```

Requires an authenticated `gh` CLI. Known issue: the OpenAI upstream `docs/` release archives (dated HTML snapshots, 1.7-2.6 MB each) exceed the GitHub contents API's 1 MB inline limit, so the script's fetch of them yields 0-byte files; the empty artifacts have been removed from the repo and fixing the fetch is an open closeout-list item. In Phase 3 this becomes a weekly GitHub Action that opens a PR when a spec changed, plus an issue listing which behaviours cite the changed sections and need re-verification.

## spec-cite/

`cite.py` resolves and verifies the precise spec citations defined in [`specs/CITATION.md`](../specs/CITATION.md) (`spec@version › section › ¶paragraph › sentence`). Every quote stored anywhere in the project (`data/coverage.json`, the site payloads) must be the output of `resolve` for a pinned locator:

```sh
python3 engine/spec-cite/cite.py outline model-spec              # section tree + anchors
python3 engine/spec-cite/cite.py show "constitution > Being honest"   # numbered ¶/s
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"
python3 engine/spec-cite/cite.py find model-spec "some remembered phrase"   # text → locator
```

Locators are re-resolved in CI on every PR: `.github/workflows/ci.yml` runs the `tests/` suite, which re-resolves every published locator through `cite.py`, and `tests/test_coverage_json.py` additionally byte-compares every quote in the frozen ledger. Combined with spec-watch, that is what keeps coverage claims verifiable over time.

### User specs (bring your own document)

`cite.py` also resolves locators into your own spec document, without editing the tool: drop a manifest at `specs/user/specs.json` (gitignored — the manifest and any documents stored with it stay local and unpushed):

```json
{
  "my-spec": {
    "2026-08-18": {"path": "specs/user/my-spec.md", "default": true}
  }
}
```

Every command then accepts the registered names alongside the bundled specs — `cite.py outline my-spec`, `cite.py resolve "my-spec@2026-08-18 > Some Section > ¶2 s1"`, etc. Paths resolve relative to the repo root (absolute paths also work); versions are ISO dates, as in locators. The `"default"` flag is optional when a spec has exactly one version, and at most one version per spec may carry it (two or more fail loudly at manifest load). A multi-version spec with no default still loads — the error is deferred until the spec is actually loaded without an `@version` pin, when `cite.py` exits listing the `my-spec@<version>` choices. Bundled names (`constitution`, `model-spec`) cannot be redefined — a manifest that tries, or that is malformed, fails loudly at load; an absent manifest is the normal bundled-only state. Blast radius of that loud failure: the panel pipeline imports `cite` at module-import time (via `harness.py`), so a malformed local manifest fails EVERY panel CLI and both panel test suites at startup — fix or delete the manifest (or point `SPEC_CITE_USER_SPECS` elsewhere) to recover; the bundled-spec tools fail the same way for the same reason. `SPEC_CITE_USER_SPECS=<file>` overrides the manifest location (how the test suite exercises this without touching `specs/`). This is a private citation workflow: the index's published coverage still cites only the bundled mirrors.

## panel/

The LLM panel judging pipeline: whole-spec judging calls, verdict parsing, the rollout driver, and the `site/llm-panel-review/` payload builder. Config is read lazily (`panel-config.json` at use time, injectable for tests) and the whole-doc prompts compose from the v3 rubric through named slots, so neither needs monkeypatching. See [`panel/README.md`](panel/README.md) for mechanics and reproduction; `python3 engine/panel/test_panel.py` runs its offline tests (no network, no keys). The canonical runlog that produces the shipped panel payload is committed data (`engine/panel/runlog-v5.jsonl` -- the v5 full bench on the 9-point scale, documented in [`panel/runlog-v5.md`](panel/runlog-v5.md); the v3-era `runlog-v3.jsonl` stays committed with its own record); `python3 engine/panel/verify_panel_provenance.py` proves the shipped payload rebuilds from it byte-identically (one documented allowance: the builder's build-date stamp).

## generate_behaviour_constants.py

[`data/behaviours.json`](../data/README.md) is the single behaviour registry (every behaviour in every set, keyed by slug). The derived copies of that identity regenerate from it -- never edit them by hand:

```sh
python3 engine/generate_behaviour_constants.py           # rewrite the constants in place
python3 engine/generate_behaviour_constants.py --check   # exit 1 with a diff on drift
```

Rewritten constants: `BEHAVIOURS` in `build-spec-reader-data.py`, and the `title` fields of `panel/behaviours.json` (its keys are registry slugs -- the panel runlogs are keyed by the same slugs -- and the committed key order is preserved). Only the constant blocks are touched; surrounding bytes are preserved. `display.behaviours` in `panel/panel-config.json` is curated configuration, not generated: the panel payload builder validates every entry against the registry at build time, so a renamed or unknown slug fails loudly. `tests/test_behaviour_registry.py` is the drift gate.

## site builders and checks

The reader surfaces render from generated payloads, never from hand-edited JSON:

```sh
python3 engine/build-spec-reader-data.py   # frozen data/coverage.json + specs/ -> site/spec-reader/data/documents.json
python3 engine/panel/build_site_data.py --threshold=4 --solid-threshold=6 --run-date=2026-08-17 --out=behaviours-v5-reader.json   # rebuild the reader's behaviour payload (band-boundary build of the v5 run)
node engine/verify-reader-test.mjs         # the reader: every behaviour x spec view + nav presence/resolution + the pinned payload URL (needs Chrome)
```

The reader (`site/spec-reader/`) renders the spec text from `documents.json` and its
behaviour set from the band-filtered `behaviours-v5-reader.json`, pinned by literal
filename (see `site/README.md` for why it must not resolve through the panel's
manifest). `data/coverage.json` is frozen: nothing writes it, and while the builder
still derives `documents.json`'s `behaviours` key from it, no surface renders that key.

## data validation

Every file in [`data/`](../data/) is validated against the JSON Schemas in [`data/schema/`](../data/schema/), plus the cross-file rules from [`data/README.md`](../data/README.md): no **published** coverage verdict without a citation, no coverage record pointing at a lab that `labs.json` doesn't define, no coverage record reference to a behaviour id the registry's index set doesn't define, and every `panel-cell-curation.json` cell's slug present in the registry with at most one cell per slug × lab.

```sh
python3 engine/validate_data.py          # uses jsonschema when installed, stdlib fallback otherwise
python3 engine/test_validate_data.py     # the gate's own tests: committed data passes, mutations fail
```

## notion-sync/ (Phase 3)

An empty placeholder today (`.gitkeep` only; nothing syncs yet). When built, it will pull the Notion databases behind the in-scope data files -- per PLAN.md §3, the Coverage DB feeding `data/coverage.json` -- via the official Notion API, normalize into [`data/`](../data/), and open a PR when anything changed. Merging that PR is the push-to-production step -- no unreviewed change ever reaches the site. The evals track (the "Evals by Behaviour" database) is not a sync target: eval-discovery is out of scope per the owner ruling (deliverable = model spec reader only).
