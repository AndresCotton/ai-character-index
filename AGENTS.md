# AGENTS.md — working in this repo with an LLM agent

Pointer file for any agent working in this repo (Claude Code, Qwen Code, or any
other). Nothing here is Claude-specific: the procedures are plain markdown. This
file does not duplicate them — it points at the canonical copies.

## Read these first (current-state docs)

- `SYSTEM.md` — whole-repo map, system-level contracts, cross-cutting risks
- `CLOSEOUT-LIST.md` — the repo-owner's scope ruling and what is done vs open
- `<dir>/OVERVIEW.md` — per-directory current-state docs (`engine/`, `data/`,
  `research/`, `site/`, `specs/`, `.claude/skills/`, `design/`, `docs/`,
  `methodology/`, `behaviours-for-adria/`, `.github/`, root)
- `docs/onboarding-spec-coverage.md` — human onboarding for the coverage pipeline

## Procedures (agent-executable)

- `.claude/skills/README.md` — entry point: how to run a coverage sweep, gate table
- `.claude/skills/sweep-coverage/SKILL.md` — LLM-panel spec coverage (the coverage stage)
- `.claude/skills/sweep-publish/SKILL.md`, `sweep-verify/SKILL.md` — publish/verify
- `.claude/skills/spec-coverage-pass/SKILL.md` — the one-behaviour campaign wrapper

The `.claude/skills/` path is a Claude Code / Qwen Code convention; agents that
use other conventions can read the same files directly.

## Run it on your own specs/behaviours (the clone/fork pathway)

Everything stays local — nothing pushes back.

1. Register a user spec: create `specs/user/specs.json` (gitignored) pointing at
   your spec markdown; optional `title`/`sourceUrl` for display. See
   `engine/README.md` ("User specs") and `specs/CITATION.md`.
2. Reader payload: `python3 engine/build-spec-reader-data.py --user-manifest=specs/user/specs.json`
3. Behaviour: add a `set:user` entry to a local copy of `data/behaviours.json`.
   The entry needs the registry's full shape -- `name`, `set: "user"`,
   `numeric_id` (integer >= 1, per set: its display order and its payload `id`),
   `group`, `definition`, `facets`. See `data/schema/behaviours.schema.json` for
   the contract and `engine/stage_user_demo.py` for a complete worked entry; the
   shipped registry carries no `set:user` rows to copy from. A missing field
   fails the build.
4. Judge it -- **this is the step that spends money.** Judging produces a
   *runlog*, which step 5 turns into a payload; without it there is nothing to
   build. Model tags live in `engine/panel/panel-config.json`; keys come from
   the environment (`key_env` per provider, e.g. `ANTHROPIC_API_KEY`).

   Your own behaviour against your own spec means `whole_doc.py`, one cell at a
   time -- one (behaviour, spec, model tag) per call:

   ```sh
   python3 engine/panel/whole_doc.py <your-slug> <your-spec-id> haiku \
     --runlog=my-run.jsonl
   ```

   Two things it does not do. It has **no dry-run** -- it calls the API the
   moment you run it, so start with a single cell and read the cost before
   looping. And its default runlog is `engine/panel/runlog-v3.jsonl`, the
   committed shipped runlog, so **always pass `--runlog=`**; the file you name
   is not gitignored, so keep it outside the repo or add it to `.gitignore`
   yourself.

   `run_rollout.py` is the driver for the *project's own* dataset, not for
   yours: it is dry-run by default and prints a cost estimate, but it validates
   `--behaviours=` against `engine/panel/behaviours.json` (the bundled panel set,
   not `data/behaviours.json` and not your registry) and it judges
   `config["specs"]` -- the two bundled mirrors. It has no `--registry` and no
   `--spec` flag, so it cannot judge a `set:user` behaviour or a user spec. Use
   it to see the shape of a plan and a cost estimate:

   ```sh
   python3 engine/panel/run_rollout.py --panel=cheap --behaviours=helpfulness \
     --runlog=/tmp/plan.jsonl        # dry-run; --go would spend
   ```

5. Build the payload from your runlog:

   ```sh
   python3 engine/panel/build_site_data.py --runlog=my-run.jsonl \
     --rubric=v3w --panel=cheap --registry=<your behaviours.json> \
     --behaviours=<your-slug>
   ```

   See `engine/panel/README.md` ("Behaviour metadata is registry-driven").
6. View: `python3 -m http.server 8123 --directory site` →
   `http://localhost:8123/spec-reader/` and `http://localhost:8123/llm-panel-review/`
   (panel loads the manifest's latest run by default; pin with `?data=<name>`).

### Where your run lands, and where it does not

Your run stays on your machine. `manifest.json` and the timestamped
`behaviours-<ts>.json` payloads are gitignored, so a panel run cannot be pushed even
by accident, and the deployed site can only ever serve the committed fallback.

It lands on **`site/llm-panel-review/`** and nowhere else. That surface is the
project's own calibration bench: unlisted, `noindex`, and linked from nothing in
`site/`. Once a user specification is registered, every surface marks itself "Local
specifications", and the reader and the bench grow an "LLM panel review" nav link to
the panel, so it is reachable from a local clone and invisible on the published site
(`site/shared/local-mode.js`).

The spec reader will **not** show your behaviours. It renders published coverage from
`data/coverage.json` -- the index's own behaviours, each one gated through
`publish-coverage.py`, locator re-resolution and the sweep gates. A panel run is
ungated by construction, so it is deliberately not folded in. Your specification does
appear in the reader as a document, with no passages against it.

There is no supported path from a panel run to published coverage. Publishing means
running the sweep pipeline for a behaviour and passing its gates; that is what
`.claude/skills/` documents.

## Verification (offline, no API spend)

```sh
python3 engine/panel/test_panel.py                 # panel suite (incl. hermetic smokes)
python3 engine/panel/test_verify_panel_provenance.py
python3 engine/panel/verify_panel_provenance.py    # shipped payload byte-identity
python3 -m unittest tests.test_cite tests.test_cite_user_specs \
    tests.test_custom_spec_decoupling tests.test_behaviour_registry \
    tests.test_coverage_json tests.test_publish_check tests.test_sidecar
python3 engine/test_validate_data.py && python3 engine/validate_data.py
node engine/panel/test_appjs_tiers.js            # tier-band cuts (single-judge floor)
node engine/panel/test_appjs_fallthrough.js
node engine/verify-spec-reader.mjs && node engine/verify-reader-test.mjs  # needs Chrome
node engine/verify-panel-features.mjs            # Tier-1 site features × bundled + user-extended (stages its own scratch site; needs Chrome + python3)
```

## Conventions

- Data changes land via reviewed PRs against `data/`; the site is committed
  static output (no build step), deployed on merges that touch `site/**`.
- Local-only artifacts must never be pushed: `specs/user/`, your runlogs,
  timestamped payloads + `manifest.json`, builder smoke scratch. Only some of
  these are gitignored -- `specs/user/`, `site/llm-panel-review/data/manifest.json`
  and the timestamped `behaviours-*.json` payloads are. **Runlogs are not**: a
  runlog you write lands as a committable untracked file, so keep it outside the
  repo or ignore it yourself. `site/spec-reader/data/documents.json` is tracked
  and is rewritten in place by `build-spec-reader-data.py --user-manifest=`, with
  your spec's text inlined -- check it before committing. The committed
  `runlog-v3.jsonl` and `behaviours.json` fallback are deliberate, and
  provenance-verified.
- Behaviour identity is registry-driven: edit `data/behaviours.json`, then run
  `engine/generate_behaviour_constants.py` (its `--check` and
  `tests/test_behaviour_registry.py` fail loudly on drift).
