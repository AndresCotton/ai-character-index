# AI Character Index

A public, evidence-based index of **AI character**, anchored in model specs. It maps *important behaviours* → *model-spec coverage* → *strength of public evaluation evidence*, side by side across frontier labs, to make gaps legible: routing technical effort toward neglected areas and holding labs accountable to their own declared targets.

In the spirit of AI Lab Watch, with a neutral, METR-like framing. By Andrés Cotton.

**Status:** pre-launch. Building v0 -- see [PLAN.md](PLAN.md) for the full build plan and system design.

## How it works (short version)

Notion is where we edit. A sync engine turns Notion changes into a reviewed pull request against `data/` -- merging that PR is the "push to production" step. The public site is a static page rebuilt automatically from `data/` on every merge. A weekly watcher pulls the labs' published specs and flags any coverage claims that need re-verification. Details in [PLAN.md §1](PLAN.md).

## Repo map

| Folder | What it holds |
|---|---|
| [`research/`](research/) | The intellectual core: the [canonical behaviour list](research/core-behaviour-list.md) (synced with Notion), its [sources](research/sources/), superseded drafts in `archive/` |
| [`specs/`](specs/) | Local mirrors of the specs the index scores against (Claude constitution, OpenAI Model Spec) |
| [`data/`](data/) | Canonical machine-readable data the site renders from; schemas in `data/schema/` |
| [`engine/`](engine/) | The automation that keeps the index alive: `spec-watch/` (works today), `notion-sync/` (Phase 3) |
| [`site/`](site/) | The public static site (Phase 1) |
| [`design/`](design/) | Aesthetics discussion: typography, palette, reference sites |
| `outreach/` | Communication strategy and interview guides (internal, not published) |
| [`vision/`](vision/) | The original vision documents, including [features to build](vision/features%20to%20build.md) |

## Contributing

Two channels (live once the repo is on GitHub; also linked from the site when it launches):

- **Submit an eval** you think the index should track → "Submit an eval" issue form.
- **Think we made a mistake?** → "Appeal a score" issue form. Appeals and their resolutions are public.
