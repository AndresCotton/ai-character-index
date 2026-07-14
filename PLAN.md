# AI Character Index -- Build Plan

*From concept to a living webpage, with the engine that keeps it updated. Written 2026-07-10.*

**The one-sentence architecture:** Notion is where we edit, git is where data becomes official (via a reviewed pull request -- that PR is the "push to production" button), and the site is a static page rebuilt automatically from the data in git.

```
  EDIT                      GATE                        PUBLISH
┌─────────────┐  nightly   ┌──────────────────┐  merge  ┌──────────────┐
│   Notion     │  sync      │  GitHub PR with   │ ──────► │ Site rebuilds │
│  databases   │ ─────────► │  the data diff    │         │ and deploys   │
│ (behaviours, │            │  (human reviews,  │         │ automatically │
│  evals, ...) │            │  catches errors)  │         └──────────────┘
└─────────────┘            └──────────────────┘
                                    ▲
┌─────────────┐  weekly            │
│ Lab spec     │  watch: diff       │  spec changed? PR + issue:
│ repos (OAI,  │ ─────────────────►│  "re-verify coverage claims
│ Anthropic)   │                    │   citing changed sections"
└─────────────┘
```

Everything below unpacks this: the components (§1), the data model (§2), the pages (§3), how the four "general feel" requirements map to concrete features (§4), CI/CD (§5), build phases (§6), and decisions taken vs. open (§7).

---

## 1. System design

### 1.1 The three layers

| Layer | Lives in | Role | Who touches it |
|---|---|---|---|
| **Editing** | Notion (existing databases + pages) | Where Andrés and collaborators do daily work: add evals, adjust scores, draft coverage verdicts | Humans, freely |
| **Canonical data** | `data/*.json` in this repo | The single machine-readable source of truth the site renders from. Every change is a reviewed git commit | Only the sync engine + reviewed PRs |
| **Presentation** | `site/` (static site) | Renders `data/` into the public index. Contains no data of its own | Developers |

This solves the "no manually synced duplicated files" requirement: nothing is copied by hand. Notion → `data/` is automated; `data/` → site is a build step.

### 1.2 The engine (what keeps it alive)

Four automated components, all GitHub Actions:

1. **`notion-sync`** (nightly + on-demand). Pulls the Notion databases via the API, normalizes into `data/*.json`, and -- only if something changed -- opens a PR titled `data: sync from Notion YYYY-MM-DD` with a human-readable summary of what changed ("2 evals added, behaviour 8 coverage verdict changed Anthropic: covered → partial"). **Merging that PR is the push-to-production act.** Silly errors get caught in review; nothing reaches the site unreviewed.
2. **`spec-watch`** (weekly). Runs `engine/spec-watch/pull-latest.sh` against the upstream OpenAI and Anthropic repos. If a spec changed: opens a PR with the new version, plus an issue listing which behaviours cite the changed sections ("Model Spec `#chain_of_command` changed; re-verify coverage for behaviours 4, 9, 10"). This is what makes coverage claims *stay* true, not just be true at launch.
3. **`ci`** (every PR). Validates `data/*.json` against schemas in `data/schema/` (no unknown behaviour IDs, no eval without a URL, no coverage verdict without a citation), builds the site, fails loudly. This is what makes the sync PRs safe to review quickly.
4. **`deploy`** (every merge to `main`). Rebuilds and publishes the site. PR branches get preview URLs, so a sync PR can be checked *visually* before merging.

A useful side effect: the git history of `data/` becomes a public, auditable changelog of every score we ever changed -- which is itself a credibility feature (§4).

### 1.3 Inbound channels (submissions and appeals)

v0 keeps this deliberately backend-free:

- **Submit an eval** → GitHub issue form (structured fields: name, URL, org, which behaviours/facets it targets, why it's rigorous) + an embedded no-GitHub-account fallback form (Tally/Google Form) that lands in Notion. Triaged into the "Evals by Behaviour" database; enters the site through the normal sync gate.
- **"Think we made a mistake?"** → its own issue form (which page/cell, what's wrong, evidence). Public by default: the appeal, our reasoning, and the resolution are all visible, which is the transparency requirement made concrete.
- **Well-made evals** → a `featured: true` flag in the evals data; the site renders a "Featured evals" strip. Promotion criteria published on the methodology page (per our rubric).

The **future backend** (auto-scoring submissions against the rubric) slots in cleanly later: it replaces the intake form, *not* the pipeline -- scored submissions still arrive as PRs into `data/`, so the gate and audit trail are unchanged.

### 1.4 Handling news / project parts

Each moving part has exactly one home:

| Part | Home | Reaches the public via |
|---|---|---|
| Behaviour list (canonical) | Notion "Behaviours to track" page | sync → `data/behaviours.json` + `research/core-behaviour-list.md` |
| Eval collection + scores | Notion "Evals by Behaviour" DB | sync → `data/evals.json` |
| Coverage verdicts | Notion (new "Coverage" DB, §2) | sync → `data/coverage.json` |
| Rubric + methodology | Notion "Evals Rubric" page → `data/` | Methodology page on site |
| Spec copies | `specs/` (mirrored from labs) | spec-watch keeps fresh |
| Outreach, interviews | `outreach/` + Notion "People to Talk To" | never published |
| Aesthetics discussion | `design/` | informs `site/` |
| Changelog / "what's new" | generated from `data/` git history | Changelog page on site |

---

## 2. Data model

Five small JSON files, one concern each. Schemas live in `data/schema/`; CI enforces them.

| File | One row per | Key fields |
|---|---|---|
| `behaviours.json` | behaviour (the 12) | id, name, tier, category, definition, facets[] (id, eval question, setup, metric, pass criterion), status (active/parked), parked_reason |
| `labs.json` | lab | id, name, spec title + version + date + URL, has_published_spec |
| `coverage.json` | behaviour × lab | verdict (covered / partial / not-in-spec), citations[] (locator per `specs/CITATION.md` + verbatim quote, resolvable by `engine/spec-cite/cite.py`; CI re-resolves every locator against `specs/` so a spec update that moves text fails loudly), verified_against_version, verified_date |
| `evals.json` | eval | id, name, URL, org, behaviour/facet ids[], quality (per rubric: validity, reproducibility...), featured, notes |
| `meta.json` | -- | site-wide: last sync date, data version, methodology version |

Two derived views the site computes at build time (never stored, so never stale): **evidence strength** per behaviour × lab (none / weak / strong, from eval count + quality) and the **gap list** (spec-coverage gaps and evidence gaps -- the index's headline findings).

**Notion side:** "Evals by Behaviour" already matches `evals.json`. To make the rest syncable, two additions are needed in Notion (Phase 3): a **Behaviours DB** (the structured fields of the canonical list; the prose stays on the page) and a **Coverage DB** (behaviour × lab verdicts with citation quotes). Until those exist, `behaviours.json` and `coverage.json` are hand-maintained in the repo, extracted from `research/core-behaviour-list.md` -- which already contains every verdict and citation for the two launch labs.

---

## 3. Pages and information architecture

Three options considered; **B is recommended**.

**Option A -- one page has everything.** The current mockup approach: hero, matrix, methodology, contribute, all on one scroll. Fastest to ship, but methodology depth is what makes this trustworthy, and one page can't hold "why we scored 9.4 this way" for 12 behaviours × N labs. Fine for a teaser, not for the product.

**Option B -- index-first, detail-deep (recommended).** The matrix *is* the homepage: data forward, METR-flavored, no marketing scroll before the substance. Every cell click-throughs to a behaviour page that shows its receipts. Trust is won on the behaviour pages; the homepage wins the first 10 seconds.

**Option C -- narrative-first.** Homepage tells the theory of change, matrix lives one click away. Better for cold policy audiences, but it buries the lede and our primary users (researchers, grantmakers) come *for* the data. The narrative belongs on About, one click away, not in front of the index.

### Option B page map

```
/               The Index (homepage)
/b/<slug>       One page per behaviour (12 + parked)
/methodology    Inclusion criteria, rubric, scoring, process
/contribute     Submit an eval, appeal, what makes a good eval
/changelog      Every data change, from git history
/about          Theory of change, who we are, contact
```

**Homepage -- the index:**

```
┌────────────────────────────────────────────────────────────┐
│ AI CHARACTER INDEX          [Methodology] [Contribute] [About] │
│ One line: behaviours → spec coverage → evidence quality.       │
│ Last updated <date> · data v<N>                                │
├────────────────────────────────────────────────────────────┤
│ Lens: (●) Spec coverage  ( ) Evidence strength                 │
│                                                                │
│                       Anthropic   OpenAI    GDM  Meta  xAI    │
│ HONESTY & EPISTEMICS                                           │
│  1 Sycophancy            [██]      [██]     [--]  [--] [--]   │
│  2 Calibration           [██]      [▒▒]     [--]  [--] [--]   │
│  3 Honesty re: actions   [██]      [██]     [--]  [--] [--]   │
│ INSTRUCTION & TASK FIDELITY                                    │
│  4 Instr. hierarchy      [██]      [██]     ...               │
│  ...                                                           │
│ POWER CONCENTRATION & LARGE-SCALE HARM                         │
│  7 Catastrophic risks    [██]      [██]     ...               │
│  ...                                                           │
│                                                                │
│ border = spec coverage · fill = evidence · [--] = no spec     │
│ ▸ Headline gaps: b9 complicity: no public evals anywhere;      │
│   GDM/Meta/xAI: no published behavioural spec                  │
├────────────────────────────────────────────────────────────┤
│ Featured evals ▸ · Submit an eval ▸ · Think we're wrong? ▸    │
└────────────────────────────────────────────────────────────┘
```

**Behaviour page -- where trust is won (one per behaviour):**

```
┌────────────────────────────────────────────────────────────┐
│ 9. Complicity in illegitimate power seizure     Tier 1        │
│ Definition + scope (from the canonical list)                   │
├──────────────────────────┬─────────────────────────────────┤
│ SPEC COVERAGE            │ EVIDENCE                          │
│ Anthropic: COVERED       │ Facet 9.1  no public evals  [gap] │
│  └ hard constraint 6:    │ Facet 9.2  no public evals  [gap] │
│    "never assist..."     │ Facet 9.3  no public evals  [gap] │
│    (quote + link, ver.   │ Facet 9.4  no public evals  [gap] │
│    2026-01-20)           │                                   │
│ OpenAI: COVERED          │ ⚑ Evidence gap: this is a         │
│  └ red-lines: "...       │   headline finding. Want to       │
│    persecution or mass   │   build this eval? → contribute   │
│    surveillance" (link)  │                                   │
├──────────────────────────┴─────────────────────────────────┤
│ Facets: eval question · setup · metric · pass criterion       │
│ Confound controls · measurement qualifiers                    │
│ [Think we made a mistake here? →]                             │
└────────────────────────────────────────────────────────────┘
```

**Contribute page:** three cards -- *Submit an eval* (issue form + no-account fallback; what happens next: rubric scoring, response time), *Appeal a score* (public log of past appeals + resolutions), *What we need most* (auto-generated from the gap list -- the research-handoff pipeline to MATS/SPAR, as a webpage).

Visual encoding stays as the mockup established (border = coverage, fill = evidence strength, lens toggle); agreement/consensus salience comes from tier badges. Aesthetics get decided in `design/` (fonts, palette, references) -- structure now, decisions later, per the vision doc.

---

## 4. The four "general feel" requirements → concrete features

| Requirement | Features that deliver it |
|---|---|
| **Rigorous and trustworthy** | Every verdict carries a citation (quote + spec version + date verified); no unsourced cells. Public git history of every data change. Spec-watch keeps claims fresh and flags staleness. |
| **Clarity and convergence** | Tier system front and center; the closed vocabulary (covered/partial/not-in-spec × none/weak/strong); parked behaviours listed *with reasons* so exclusion is legible too. |
| **Visitors can contribute, with clear channels** | Contribute page with three concrete routes; "what we need most" auto-generated from gaps; featured-evals promotion; appeal button on every behaviour page. |
| **Transparent criteria and mechanisms** | Methodology page publishes the inclusion criteria and rubric verbatim; changelog page; appeals and their resolutions public; the whole pipeline (this repo) is open. |

---

## 5. CI/CD (minimal, four workflows)

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | every PR | validate `data/` against schemas → build site → (preview URL via host) |
| `deploy.yml` | merge to `main` | build + publish production |
| `notion-sync.yml` | cron nightly + manual button | pull Notion → write `data/` → open PR if diff |
| `spec-watch.yml` | cron weekly | pull specs → PR + "re-verify coverage" issue if diff |

That's the whole surface. No servers, no databases to operate, nothing to be on-call for; if every automation died, the site would simply stop updating, not break.

**Stack (recommendation, revisit in `design/` if needed):** Astro + TypeScript for the site (static output, tiny JS island for the matrix interactivity), JSON Schema validation in CI, **Cloudflare Pages** for hosting (free, automatic per-PR preview URLs -- which is half of the production gate; GitHub Pages is the fallback if we'd rather stay in one vendor). Notion sync via the official Notion SDK, ~200 lines.

---

## 6. Build phases

**Phase 0 -- organize (this session).** Repo restructured, plan written, folders scaffolded. ✔

**Phase 1 -- static site with real coverage data (week 1-2).**
Hand-write `data/behaviours.json`, `labs.json`, `coverage.json` by extracting from `research/core-behaviour-list.md` (the verdicts and citations already exist there); sync `evals.json` from Notion manually once. Scaffold Astro site; render homepage matrix + behaviour pages from `data/`. Stand up `ci.yml` + `deploy.yml`; site is live (unlisted) end of phase.
*Done when: a colleague can click every Tier 1 cell and reach a cited verdict.*

**Phase 2 -- trust surface (week 2-3).**
Methodology page (criteria + rubric), contribute page, GitHub issue forms, appeal route, changelog, featured evals. Aesthetics pass using whatever has accumulated in `design/`.
*Done when: an outside researcher could submit an eval and appeal a score without asking us how.*

**Phase 3 -- the living engine (week 3-4).**
Create Behaviours + Coverage DBs in Notion; build `engine/notion-sync`; turn on `notion-sync.yml` and `spec-watch.yml`. From here on, no hand-edited data files.
*Done when: an edit in Notion appears on the site with zero manual steps except merging the PR.*

**Phase 4 -- share and iterate (month 2).**
Share MVP with the model-character community (per the vision doc); iterate on feedback; add labs beyond the initial two as "no published spec" rows (itself a finding).

**Future (explicitly out of v0 scope):** submissions backend, automated rubric scoring of incoming evals, lab-contributed evidence, policy-audience views, contradiction analysis (arXiv:2510.07686).

---

## 7. Decisions

**Taken (revisit only with reason):**
- Notion = editing layer; git = canonical data; site = pure render. The sync PR is the production gate.
- v0 scores two labs deeply (Anthropic, OpenAI -- the two specs in `specs/`); other labs appear as explicit "no published spec" rows rather than being omitted.
- Static site, no backend in v0. Submissions via issue forms + fallback form.
- Option B information architecture (index-first homepage, deep behaviour pages).

**Open (for Andrés, none block Phase 1):**
- Hosting vendor: Cloudflare Pages (recommended) vs. GitHub Pages (no per-PR previews) vs. Vercel/Netlify.
- Domain name / project public name.
- Aesthetics: everything in `design/` -- font, palette, reference sites (AI Lab Watch, METR, Epoch AI are the obvious comparables).
- Whether appeals also get a lightweight email route for people avoiding GitHub.
- When to create the Notion Behaviours/Coverage DBs (Phase 3 at the latest; earlier is fine).

---

## 8. Repo map (after this reorganization)

```
├── PLAN.md               ← this file
├── README.md             project front door + this map
├── research/             the intellectual core
│   ├── core-behaviour-list.md   (synced with Notion "Behaviours to track")
│   ├── sources/                 candidate-pool sources + scoring targets
│   └── archive/                 superseded drafts
├── specs/                mirrored lab specs (the scoring targets)
│   ├── claude-constitution/
│   └── openai-model-spec/
├── data/                 canonical machine-readable data (site renders this)
│   └── schema/           JSON schemas, enforced in CI
├── engine/               what keeps it alive
│   ├── spec-watch/       pull-latest.sh (works today)
│   ├── spec-cite/        cite.py -- resolves/verifies spec citations (works today)
│   └── notion-sync/      Notion → data/ (Phase 3)
├── site/                 the static site (Phase 1)
├── design/               aesthetics: fonts, palette, references
│   └── references/       (the v0 mockup screenshot lives here)
├── outreach/             communication strategy + interview guides (not published)
├── vision/               original vision docs, incl. "features to build.md"
└── .github/
    ├── workflows/        ci, deploy, notion-sync, spec-watch (Phases 1-3)
    └── ISSUE_TEMPLATE/   submit-eval and appeal forms (ready now)
```
