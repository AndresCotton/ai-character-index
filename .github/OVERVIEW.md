# .github — one production deploy workflow + two public intake forms

> As-is snapshot of origin/main @ 4fe2dac (2026-08-18); the documentation set itself is added by this PR. Describes what exists now, not what should exist.

## Purpose
`.github/` holds the repo's only CI/CD automation — a Cloudflare Pages deploy fired by merges to `main` — plus the two GitHub issue forms that are the project's public inbound channels (eval submissions, appeals).

## Contents
| Path | What it is |
|---|---|
| `workflows/deploy.yml` | The only workflow. Deploys committed `site/` to Cloudflare Pages project `ai-character-index` on pushes to `main` filtered to `site/**`, plus `workflow_dispatch` |
| `workflows/README.md` | Operator docs: required secrets setup; states `ci.yml` / `notion-sync.yml` / `spec-watch.yml` are "still to come" |
| `ISSUE_TEMPLATE/submit-eval.yml` | Issue form (label `eval-submission`): eval name/URL/org, 12-behaviour dropdown, rigor rationale |
| `ISSUE_TEMPLATE/appeal.yml` | Issue form (label `appeal`): where (page/cell), what's wrong, evidence |
| `ISSUE_TEMPLATE/config.yml` | Blank issues enabled; mailto contact link (andrescotton@gmail.com) |

## Relationships
- `deploy.yml` triggers: `push` to `main` (paths: `site/**`, `.github/workflows/deploy.yml`) and manual `workflow_dispatch`. Concurrency group `deploy-production` with `cancel-in-progress: false`; `permissions: contents: read`; job environment `production`. Steps: checkout → `pnpm/action-setup@v4` → `actions/setup-node@v4` (Node 22, pnpm cache) → `cloudflare/wrangler-action@v3` (wrangler pinned 4.110.0) running `pages deploy site --project-name ai-character-index --branch main`. Secrets consumed: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
- The deploy has no build step: `site/` is committed static output, and the paths filter watches `site/**` only, so `data/**` or `engine/**` changes trigger nothing until they are baked into `site/`.
- Its local twin is `pnpm deploy:site` from root `package.json`, documented in `workflows/README.md` as the interactive-`wrangler login` route to the same project.
- The issue forms implement PLAN.md §1.3's inbound channels and are linked from `README.md` "Contributing". `submit-eval.yml`'s behaviour dropdown mirrors `research/core-behaviour-list.md`.

## Dependency map
```mermaid
graph LR
  PR[merge to main] -->|paths site/**| DW[deploy.yml]
  WD[workflow_dispatch] --> DW
  DW -->|secrets CLOUDFLARE_API_TOKEN / ACCOUNT_ID| CF[Cloudflare Pages: ai-character-index]
  DW -->|deploys committed dir| SITE[site/]
  SE[submit-eval.yml] -->|label eval-submission| GH[GitHub Issues]
  AP[appeal.yml] -->|label appeal| GH
```

## As-is observations
- PLAN.md §5 promises four workflows (`ci.yml`, `deploy.yml`, `notion-sync.yml`, `spec-watch.yml`); only `deploy.yml` exists on main (`git ls-tree origin/main .github/workflows/` shows just `deploy.yml` + `README.md`). `workflows/README.md` itself says the other three are "still to come".
- A `ci.yml` does exist on the unmerged branch `ci/fast-suite` ("ci: run the fast suite on every PR") — it is not an ancestor of `origin/main`.
- `engine/notion-sync/` contains only `.gitkeep`: the Notion sync engine promised by PLAN.md §1.2/§6 Phase 3 has no code.
- `engine/spec-watch/pull-latest.sh` exists and is used, but manually — sweep records log it being run (`research/sweeps/*/4-spec-coverage.md`, `behaviours-for-adria/*/4-spec-coverage.md`), and `docs/onboarding-spec-coverage.md` lists it as the "Mirror refresher". No workflow invokes it.
- `data/schema/` holds only `.gitkeep`, so the `ci.yml` promise to "validate `data/*.json` against schemas in `data/schema/`" (PLAN.md §2/§5, `engine/README.md`) has no schemas to run against on main either.
- With no `ci.yml` on main there is no PR-time validation and no per-PR preview deploy; production deploys fire only post-merge.
