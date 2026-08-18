# tests/

Regression tests for the spec-coverage tooling.

## Running

```sh
python3 -m unittest discover -s tests        # the whole fast suite (~20s)
python3 -m unittest discover -s tests -v     # verbose
```

The suite is the fast gate: run it before committing any change to
`engine/`. It does not replace the slow end-to-end check, which needs
Node deps (`pnpm install`) and Chrome:

```sh
node engine/verify-spec-reader.mjs           # every behaviour x spec view + nav presence + full link/fragment crawl
```

## What is covered

One test file per subject under test:

- `test_cite.py` -- everything pinning `cite.py`. Golden-master snapshots
  diffed against `tests/golden/`: the full corpus (`outline`/`show`/
  `resolve` for **every** section of both pinned specs, catching drift even
  in sections no published citation touches) and `find` for a fixed query
  set (the `match_normalize` folding and sentence-span arithmetic the
  corpus commands never exercise). Plus unit tests for the pure functions
  (`normalize`, `match_normalize`, `split_sentences`, `parse_locator`) and
  the corpus-wide invariant that every published quote stays findable
  under folding.
- `test_publish_check.py` -- runs `publish-coverage.py --check` for every
  sweep directory holding a stage-4 artifact (`4-spec-coverage.md` or its
  structured sidecar `4-spec-coverage.json`): re-resolves every published
  quote byte-for-byte and diffs the artifact against `data/coverage.json`.
- `test_sidecar.py` -- pins the structured sidecar path of
  `publish-coverage.py`: committed sidecars validate against
  `data/schema/spec-coverage-sidecar.schema.json` (both validator backends)
  with complete reconstruction provenance; corrupted quotes still fail at
  the cite.py re-resolution gate; schema violations and missing
  reconstruction provenance fail loudly at publish time.
- `test_coverage_json.py` -- re-resolves **every** locator in
  `data/coverage.json` against `cite.py`, whether or not the behaviour has
  any artifact. Resolution is in-process (one spec load per spec), so this
  stays near-instant as behaviours accumulate.

To run one class during a tight edit loop (the goldens take ~20s; the unit
tests are instant):

```sh
python3 -m unittest tests.test_cite.MatchNormalizeTest -v
```

## Regenerating the golden snapshots

```sh
python3 tests/dump_goldens.py --write            # all goldens
python3 tests/dump_goldens.py --write corpus     # or one family: corpus | find
```

Do this only after an **intentional** change: a spec mirror update
(spec-watch) or a deliberate change to `cite.py`'s behaviour. Then review
the git diff of `tests/golden/` before committing -- the diff *is* the
record of what changed. Never regenerate just to turn a red test green:
a red snapshot means cite.py's output moved, and that is a finding.

## Adding tests

Every change to the pipeline lands with its test in this directory. Pin
outputs (golden files) for behaviour that must stay byte-stable; write
plain unit tests for logic with edge cases. Keep the suite dependency-free
and fast enough that nobody hesitates to run it.
