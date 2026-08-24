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
   your spec markdown; optional `title`/`sourceUrl` for display sit *inside each
   version*, beside `path`/`default` -- neither doc below shows them, so copy the
   nesting from the worked manifest in `engine/stage_user_demo.py`. See
   `engine/README.md` ("User specs") and `specs/CITATION.md`.
2. Reader payload -- **run this from the repo root**:
   `python3 engine/build-spec-reader-data.py --user-manifest=specs/user/specs.json`
   The manifest path is resolved against your *current directory*, not the repo
   root. From anywhere else it silently finds nothing, prints
   `Wrote site/spec-reader/data/documents.json` and exits 0 having written a
   bundled-only payload. Pass an absolute path if you are not at the root. Check
   your spec is actually there before continuing:
   `python3 -c "import json;print([d['id'] for d in json.load(open('site/spec-reader/data/documents.json'))['documents']])"`
   Note this rewrites a **tracked** file with your spec's text inlined.
3. Behaviour: add a `set:user` entry to a copy of `data/behaviours.json`. Put it
   in `local/` -- a gitignored directory for a fork's own working files, which is
   also where your runlogs should go. (Your spec and its manifest already live in
   the gitignored `specs/user/`.) The entry needs the registry's full shape
   -- `name`, `set: "user"`, `numeric_id` (integer >= 1, per set: its display
   order and its payload `id`), `group`, `definition`, `facets`. See
   `data/schema/behaviours.schema.json` for the contract and
   `engine/stage_user_demo.py` for a complete worked entry; the shipped registry
   carries no `set:user` rows to copy from. A missing field fails the build.

   You register it **once**. Both the judging step and the build step take
   `--registry=`, and both accept this shape: `whole_doc.py` adapts a display
   entry into a judge prompt (`definition` becomes the text the judges are
   given, `facets` become clarifications). `engine/panel/behaviours.json` is the
   project's own judging registry -- you do not need to touch it.
4. Judge it -- **this is the step that spends money.** One
   (behaviour, spec, model tag) per call; tags live in
   `engine/panel/panel-config.json`; keys come from the environment
   (`key_env` per provider, e.g. `ANTHROPIC_API_KEY`).

   ```sh
   python3 engine/panel/whole_doc.py <your-slug> <your-spec-id> haiku \
     --registry=local/my-behaviours.json --runlog=local/my-run.jsonl
   ```

   It has **no dry-run** -- it calls the API immediately, so run one cell and
   read the cost before looping. One cell of a ~15 KB spec on `haiku` is well
   under a cent (measured: 5,884 in / 383 out = $0.008). Always pass
   `--runlog=`: the default is `engine/panel/runlog-v3.jsonl`, the committed
   shipped runlog. A runlog under `local/` is gitignored; one written anywhere
   else is not. It also appends
   to `engine/panel/metrics.jsonl` (gitignored).

   `run_rollout.py` is the driver for the *project's own* dataset, not yours: it
   validates `--behaviours=` against `engine/panel/behaviours.json` and judges
   `config["specs"]`, the two bundled mirrors, with no `--spec` flag. Useful only
   for a free dry-run cost estimate of a bundled behaviour.
5. Build the payload. `--panel=` takes either a panel name from
   `engine/panel/panel-config.json` or a bare model tag, which is treated as a
   one-seat panel -- so a single-judge run is just `--panel=haiku`. Its seats
   must match the judges in your runlog: a citation needs `min(2, panel_size)`
   votes, so scoring one judge against a multi-seat panel yields 0 citations.
   The builder says so when that happens, naming your runlog's tags and the
   panel's seats. Every behaviour key in the runlog must also be a registry
   slug, not just the one you pass to `--behaviours=`.

   ```sh
   python3 engine/panel/build_site_data.py --runlog=/tmp/my-run.jsonl \
     --rubric=v3w --panel=haiku --registry=local/my-behaviours.json \
     --behaviours=<your-slug>
   ```

   It prints the citation count -- if that is 0, check your panel's seats
   against the runlog's `model` values before looking anywhere else. The
   `(threshold 3, solid 5)` it also prints is builder-side and does not gate what
   renders: a single-judge run renders its 2s as defining and its 1s as related.
6. View: `python3 -m http.server 8123 --directory site` →
   `http://localhost:8123/spec-reader/` and `http://localhost:8123/llm-panel-review/`
   (panel loads the manifest's latest run by default; pin with `?data=<name>`).
   **Check the port is free first** (`lsof -i:8123`) and use any free port
   otherwise -- if another clone of this repo is already serving `site/` there,
   the URL returns 200 and renders *its* payload with nothing on the page saying
   so.

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
- Local-only artifacts must never be pushed. Gitignored: `specs/user/` (your
  spec and its manifest), `local/` (your registry copies, runlogs and scratch),
  `site/llm-panel-review/data/manifest.json` and the timestamped
  `behaviours-*.json` payloads, `engine/panel/metrics.jsonl`. A runlog or
  registry written **outside** `local/` is not ignored and lands as a
  committable file. One thing no ignore rule covers:
  `site/spec-reader/data/documents.json` is **tracked**, and
  `build-spec-reader-data.py --user-manifest=` rewrites it in place with your
  spec's text inlined -- it is build output the site serves, so it cannot be
  ignored; check it before committing. The committed `runlog-v3.jsonl` and
  `behaviours.json` fallback are deliberate, and provenance-verified.
- Behaviour identity is registry-driven: edit `data/behaviours.json`, then run
  `engine/generate_behaviour_constants.py` (its `--check` and
  `tests/test_behaviour_registry.py` fail loudly on drift).
