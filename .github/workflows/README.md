# CI/CD workflows

Per PLAN.md §5. Only `deploy.yml` exists so far; the others (`ci.yml`,
`notion-sync.yml`, `spec-watch.yml`) are still to come.

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
