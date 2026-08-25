# AGENTS.md — working in this repo with an LLM agent

Pointer file for any agent working in this repo (Claude Code, Qwen Code, or any
other). Nothing here is Claude-specific: the procedures are plain markdown. This
file does not duplicate them — it points at the canonical copies.

## Read these first (current-state docs)

- `SYSTEM.md` — whole-repo map, system-level contracts, cross-cutting risks
- `CLOSEOUT-LIST.md` — the repo-owner's scope ruling and what is done vs open
- `<dir>/OVERVIEW.md` — per-directory current-state docs (`engine/`, `data/`,
  `research/`, `site/`, `specs/`, `.claude/skills/`, `design/`,
  `methodology/`, `.github/`, root)

## Procedures

The coverage-sweep pipeline is retired with the publish path; the coverage
ledger (`data/coverage.json`) is frozen and nothing writes it. `.claude/skills/`
records the retirement. The live procedures are the clone/fork pathway below
and the panel mechanics in `engine/panel/README.md`.

## Run it on your own specs/behaviours (the clone/fork pathway)

Everything stays local — nothing pushes back.

1. Register a user spec: put your spec markdown in `specs/user/` (gitignored, so
   it stays local) and create `specs/user/specs.json` pointing at it. Optional
   `title`/`sourceUrl` for display sit *inside each version*, beside
   `path`/`default` -- neither doc below shows them, so copy the nesting from the
   worked manifest in `engine/stage_user_demo.py`. See `engine/README.md`
   ("User specs") and `specs/CITATION.md`.
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
   -- `name`, `set: "user"`, `numeric_id` (integer >= 1, unique within your
   set; it orders the sidebar -- the payload renumbers 1..N, so it is not
   the id you see), `group`, `definition`, `facets`. See
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
   v3-era log (the SHIPPED payload's log is `engine/panel/runlog-v5.jsonl`).
   Put yours in `local/`, which is gitignored. It also appends
   to `engine/panel/metrics.jsonl` (gitignored).

   To rehearse steps 2-6 without spending, `python3 engine/stage_user_demo.py
   --out=DIR` stages a complete clone/fork site -- a synthetic user spec, a
   `set:user` behaviour and a small runlog -- into a scratch directory, leaving
   this repo untouched. Useful for seeing what the flow produces before paying
   for a real run.

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
   python3 engine/panel/build_site_data.py --runlog=local/my-run.jsonl \
     --rubric=v3w --panel=haiku --registry=local/my-behaviours.json \
     --behaviours=<your-slug>
   ```

   It prints the citation count -- if that is 0, check your panel's seats
   against the runlog's `model` values before looking anywhere else. The
   `(threshold 3, solid 5)` it also prints is builder-side and does not gate what
   renders: a single-judge run renders its 2s as defining and its 1s as related.
6. View: `python3 -m http.server 8123 --directory site` →
   `http://localhost:8123/spec-reader/`
   (loads the manifest's latest run by default; pin with `?data=<name>`).
   **Check the port is free first** (`lsof -i:8123`) and use any free port
   otherwise -- if another clone of this repo is already serving `site/` there,
   the URL returns 200 and renders *its* payload with nothing on the page saying
   so.

### Where your run lands, and where it does not

Your run stays on your machine. `manifest.json` and the timestamped
`behaviours-<ts>.json` payloads are gitignored, so a panel run cannot be pushed even
by accident, and the deployed site can only ever serve the committed fallback.

It lands on **`site/spec-reader/`**: the reader resolves the manifest's latest run
by default, so your run is what your clone shows -- your behaviour in the sidebar
alongside the bundled ones, and your registered specification as a document, with
your run's passages against it for the behaviours you judged. `site/shared/
local-mode.js` marks the page "Local specifications" so a local run is never
mistaken for the published index.

There is no supported path from a panel run into the committed payload: the
publish pipeline is retired and the coverage ledger is frozen. `.claude/skills/`
records the retirement.

## Verification (offline, no API spend)

```sh
python3 engine/panel/test_panel.py                 # panel suite (incl. hermetic smokes)
python3 engine/panel/test_verify_panel_provenance.py
python3 engine/panel/verify_panel_provenance.py    # shipped payload byte-identity
python3 -m unittest tests.test_cite tests.test_cite_user_specs \
    tests.test_custom_spec_decoupling tests.test_behaviour_registry \
    tests.test_coverage_json tests.test_reader_v5_payload
python3 engine/test_validate_data.py && python3 engine/validate_data.py
node engine/panel/test_appjs_tiers.js            # tier-band cuts (single-judge floor)
node engine/panel/test_appjs_fallthrough.js
node engine/verify-reader-test.mjs               # needs Chrome
node engine/verify-reader-features.mjs            # Tier-1 site features × bundled + user-extended (stages its own scratch site; needs Chrome + python3; run it alone)
```

## Conventions

- Data changes land via reviewed PRs against `data/`; the site is committed
  static output (no build step), deployed on merges that touch `site/**`.
- Local-only artifacts must never be pushed. Gitignored: `specs/user/` (your
  spec and its manifest), `local/` (your registry copies, runlogs and scratch),
  `site/spec-reader/data/manifest.json` and the timestamped
  `behaviours-*.json` payloads, `engine/panel/metrics.jsonl`. A registry or runlog written **outside** `local/` may not be
  ignored -- check with `git status` before committing. Two more the panel
  writes: `engine/panel/metrics.jsonl` (ignored) and, on a parse failure,
  `engine/panel/wholedoc-FAILED-*.txt` carrying raw model output (**not**
  ignored). One thing no ignore rule covers:
  `site/spec-reader/data/documents.json` is **tracked**, and
  `build-spec-reader-data.py --user-manifest=` rewrites it in place with your
  spec's text inlined -- it is build output the site serves, so it cannot be
  ignored; check it before committing. The committed runlogs (`runlog-v5.jsonl`,
  `runlog-v3.jsonl`) and the `behaviours.json` fallback are deliberate, and
  provenance-verified.
- Behaviour identity is registry-driven: edit `data/behaviours.json`, then run
  `engine/generate_behaviour_constants.py` (its `--check` and
  `tests/test_behaviour_registry.py` fail loudly on drift).
