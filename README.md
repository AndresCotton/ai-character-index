# AI Character Index

A public index of **AI character**, anchored in model specs. It maps *important behaviours* → *model-spec coverage*, side by side across frontier labs, to make gaps legible: routing technical effort toward neglected areas and holding labs accountable to their own declared targets.

In the spirit of AI Lab Watch, with a neutral, METR-like framing. By Andrés Cotton.

**Status:** deployed to Cloudflare Pages (`ai-character-index.pages.dev`). Building v0 -- see [PLAN.md](PLAN.md) for the full build plan and system design.

## How it works (short version)

Data changes land through reviewed pull requests against `data/` and `research/` -- merging the PR is the "push to production" act. The public site is static output committed under `site/`, deployed to Cloudflare Pages on merges that touch it; there is no build step. `engine/spec-watch/pull-latest.sh` refreshes the mirrored lab specs (run manually; automatic re-verification of coverage claims after a spec change is planned but not built). System map: [SYSTEM.md](SYSTEM.md); the original design: [PLAN.md §1](PLAN.md).

Spec coverage enters through **coverage sweeps**: a staged pipeline with a human sign-off gate between every stage, run one behaviour at a time. The `spec-coverage-pass` route runs the coverage and publish stages on a per-behaviour branch (behaviours 2–3 were published this way); results reach the public reader when the branch merges after the fresh-context verify audit signs its gate. How to run one: [.claude/skills/README.md](.claude/skills/README.md).

## Repo map

| Folder | What it holds |
|---|---|
| [`research/`](research/) | The intellectual core: the [canonical behaviour list](research/core-behaviour-list.md) (mirrored from Notion; the repo copy lags at rows 11–13), sweep records in [`sweeps/`](research/sweeps/), superseded drafts in `archive/` |
| [`.claude/skills/`](.claude/skills/) | The coverage-sweep pipeline: versioned procedure files, one per stage, each ending at a human gate -- [how to run a sweep](.claude/skills/README.md) |
| [`specs/`](specs/) | Local mirrors of the specs the index scores against (Claude constitution, OpenAI Model Spec) |
| [`methodology/`](methodology/) | Depth rubric (anchors every published depth score), the editable site methodology copy, method-exploration write-ups |
| [`behaviours-for-adria/`](behaviours-for-adria/) | External reviewer's ten-behaviour coverage batch — feeds the reader test bench and three rows of the panel surface |
| [`data/`](data/) | Machine-readable data behind the site — rendered via engine-built payloads; writers and hand-maintained exceptions in [`data/README.md`](data/README.md) |
| [`engine/`](engine/) | The automation: `spec-cite/` (citation resolver), `panel/` (LLM panel judging), coverage/payload builders, site verifiers, `spec-watch/` (manual pulls); `notion-sync/` is a placeholder. See [`engine/README.md`](engine/README.md) |
| [`site/`](site/) | The public static site |
| [`docs/`](docs/) | Onboarding prose (the spec-coverage track) + ruling-approved skill-rescope proposals — see [`docs/OVERVIEW.md`](docs/OVERVIEW.md) |
| [`design/`](design/) | Aesthetics discussion: typography, palette, reference sites |
| `outreach/` | Communication strategy and interview guides (internal, not published; gitignored, so it exists only in local clones) |
| [`vision/`](vision/) | The original vision documents, including [features to build](vision/features%20to%20build.md) |

## Contributing

Questions, corrections, or anything you think we've got wrong: use the **contact link** on the repo's Issues page ("Contact Andrés directly"), or open a blank issue. We read everything.

## Licence and citation

Dual-licensed, by what the file is rather than where it sits:

| | Licence | Covers |
|---|---|---|
| Software | [Apache-2.0](LICENSE) | `.py`, `.js`, `.mjs`, `.html`, `.css`, `.sh`, `.yml`, plus dependency manifests |
| Written work and data | [CC BY 4.0](LICENSE-CC-BY-4.0) | `.md`, `.json`, `.jsonl`, `.txt` — coverage data, judged runlogs, methodology, docs |

Both require attribution. CC BY is the licence academic work expects for data
and written material; Apache-2.0 carries the patent grant that matters for code.

**`specs/` is not ours.** It holds verbatim copies of specifications published by
Anthropic and OpenAI, both released under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) — a public-domain
dedication that imposes no conditions and requires no attribution. We attribute
them anyway. Cite those documents to their publishers, never to this project.
CC0 covers copyright, not trademarks; nothing here is endorsed by or affiliated
with either organisation. See [NOTICE](NOTICE) for the full statement.

To cite this project, use [CITATION.cff](CITATION.cff) — GitHub renders it as a
"Cite this repository" button with BibTeX and APA output.
