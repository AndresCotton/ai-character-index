# AI Character Index

A public, evidence-based index of **AI character**, anchored in model specs. It maps *important behaviours* → *model-spec coverage* → *strength of public evaluation evidence*, side by side across frontier labs, to make gaps legible: routing technical effort toward neglected areas and holding labs accountable to their own declared targets.

In the spirit of AI Lab Watch, with a neutral, METR-like framing. By Andrés Cotton.

**Status:** deployed to Cloudflare Pages (`ai-character-index.pages.dev`). Building v0 -- see [PLAN.md](PLAN.md) for the full build plan and system design.

## How it works (short version)

Data changes land through reviewed pull requests against `data/` and `research/` -- merging the PR is the "push to production" act. The public site is static output committed under `site/`, deployed to Cloudflare Pages on merges that touch it; there is no build step. `engine/spec-watch/pull-latest.sh` refreshes the mirrored lab specs (run manually; automatic re-verification of coverage claims after a spec change is planned but not built). System map: [SYSTEM.md](SYSTEM.md); the original design: [PLAN.md §1](PLAN.md).

Spec coverage enters through **coverage sweeps**: a staged pipeline with a human sign-off gate between every stage, run one behaviour at a time. The `spec-coverage-pass` route runs stages 4–5 on a per-behaviour branch (behaviours 2–3 were published this way); results reach the public reader when the branch merges after the stage-6 audit signs Gate 6. How to run one: [.claude/skills/README.md](.claude/skills/README.md).

## Repo map

| Folder | What it holds |
|---|---|
| [`research/`](research/) | The intellectual core: the [canonical behaviour list](research/core-behaviour-list.md) (mirrored from Notion; the repo copy lags at rows 11–13), sweep records in [`sweeps/`](research/sweeps/), superseded drafts in `archive/` |
| [`.claude/skills/`](.claude/skills/) | The coverage-sweep pipeline: versioned procedure files, one per stage, each ending at a human gate -- [how to run a sweep](.claude/skills/README.md) |
| [`specs/`](specs/) | Local mirrors of the specs the index scores against (Claude constitution, OpenAI Model Spec) |
| [`methodology/`](methodology/) | Depth rubric (anchors every published depth score), the editable site methodology copy, method-exploration write-ups |
| [`behaviours-for-adria/`](behaviours-for-adria/) | External reviewer's ten-behaviour stage-4 set — feeds the reader test bench and three rows of the panel surface |
| [`data/`](data/) | Machine-readable data behind the site — rendered via engine-built payloads; writers and hand-maintained exceptions in [`data/README.md`](data/README.md) |
| [`engine/`](engine/) | The automation: `spec-cite/` (citation resolver), `panel/` (LLM panel judging), coverage/payload builders, site verifiers, `spec-watch/` (manual pulls); `notion-sync/` is a placeholder. See [`engine/README.md`](engine/README.md) |
| [`site/`](site/) | The public static site |
| [`docs/`](docs/) | Onboarding prose (the spec-coverage track) + ruling-approved skill-rescope proposals — see [`docs/OVERVIEW.md`](docs/OVERVIEW.md) |
| [`design/`](design/) | Aesthetics discussion: typography, palette, reference sites |
| `outreach/` | Communication strategy and interview guides (internal, not published; gitignored, so it exists only in local clones) |
| [`vision/`](vision/) | The original vision documents, including [features to build](vision/features%20to%20build.md) |

## Contributing

Two channels (live on GitHub):

- **Submit an eval** you think the index should track → "Submit an eval" issue form.
- **Think we made a mistake?** → "Appeal a score" issue form. Appeals and their resolutions are public.
