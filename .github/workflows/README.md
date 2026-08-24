# CI/CD workflows

Per PLAN.md §5. `ci.yml` (PR-time verification) and `deploy.yml` (site
publish) exist; `notion-sync.yml` and `spec-watch.yml` are still to come.

## `ci.yml` -- verify on every PR

Runs on every pull request and on pushes to `main`, with no paths filter (a
filtered required check would silently skip PRs outside its paths and block
merging). Two jobs:

- **offline** — the full no-network battery: panel + provenance suites, the
  `tests/` suite (cite goldens, sidecar/publish checks, decoupling pins),
  the data gate, builder byte-identity rebuilds, `publish-coverage.py --check`
  for every published behaviour, the registry drift gate, and the node
  app.js resolution harnesses. Stdlib python + node only; nothing to install.
- **browser** — the three Playwright walkers (spec reader, reader-test bench,
  panel feature harness × bundled + user-extended data) against an installed
  Chrome.

No secrets are needed; `contents: read` is the only permission.

## `deploy.yml` -- publish the site on merge to main

Deploys the static site in `site/` to Cloudflare Pages (project
`ai-character-index`) whenever `site/**` changes land on `main`. Can also be
run by hand from the Actions tab (`workflow_dispatch`).

### One-time setup

Two repository secrets are required
(Settings → Secrets and variables → Actions, or `gh secret set`):

| Secret | Value |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | The Cloudflare account id (`wrangler whoami` prints it). |
| `CLOUDFLARE_API_TOKEN` | A Cloudflare API token scoped to **Account → Cloudflare Pages → Edit** for this account. |

To mint the token: Cloudflare dashboard → My Profile → API Tokens → Create
Token → "Edit Cloudflare Pages" template (or a custom token with the
*Account · Cloudflare Pages · Edit* permission), scoped to this account.

The local `pnpm deploy:site` command still works for manual deploys from a
logged-in machine; it uses your interactive `wrangler login`, not these secrets.
