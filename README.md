# AI Character Index

A tool for researchers working in the model-spec space. Point a panel of LLM judges at a spec -- Anthropic's constitution, OpenAI's Model Spec, or a document of your own -- and give the panel a behaviour you care about. You get back a passage-level coverage map: every place the spec addresses that behaviour, scored by each judge and quoted verbatim, browsable in a local reader.

What people use it for:

- **Assess coverage.** How well does a spec address a behaviour you are interested in? Is it a defining commitment, a passing mention, or a gap?
- **Locate the exact text.** Every verdict anchors to a specific passage, so you see precisely *where* in the spec a behaviour is addressed, not just *whether*.
- **Select passages for downstream work.** Every citation is a stable, re-resolvable locator plus a verbatim quote, in plain JSON -- ready to feed automated adherence evals (for example, Petri scenarios testing whether models actually follow the passages you selected).
- **Experiment with spec edits.** Register your own spec versions locally, run the panel against each, and compare how coverage shifts as you rewrite.

The repo ships with a complete bench out of the box: ten behaviours judged against both bundled specs by a three-judge frontier panel, so you can explore results before running anything yourself.

## Quickstart

### 1. What you need

- **Python 3.10+**. The only third-party package is `openai` (`pip install openai`) -- every judge provider is called through the OpenAI-compatible API. You only need it when you run new judging; browsing shipped results needs nothing.
- **A browser.** All result surfaces are static local pages.
- Optional: `pip install jsonschema` for stricter validation when you edit the behaviour registry.

No Node.js, no build step.

### 2. Clone and browse the shipped results (no API keys)

```sh
git clone https://github.com/AndresCotton/ai-character-index.git
cd ai-character-index
python3 -m http.server 8080 --directory site
```

Then open:

- **<http://localhost:8080/llm-panel-review/>** -- the panel reader, the main surface for this workflow. Pick a behaviour in the sidebar; every passage the panel scored lights up in the spec text, with the per-judge verdicts on hover.
- **<http://localhost:8080/spec-reader/>** -- the side-by-side spec reader. Documents render as parallel panes with a resizable boundary; your own registered specs appear here too (see below).

### 3. API keys (only for running new judging)

Judges are called through provider APIs. Which keys you need depends on the panel you run; the default frontier panel (`frontier_fast`) needs three:

| Seat | Model | Provider | Env var |
|---|---|---|---|
| `sol` | GPT-5.6 Sol | OpenAI | `OPENAI_API_KEY` |
| `fable` | Claude Fable 5 | Anthropic | `ANTHROPIC_API_KEY` |
| `deepseek` | DeepSeek V3.2 | DeepInfra | `DEEPINFRA_API_KEY` |

Two useful alternatives:

- **One key instead of three:** set `OPENROUTER_API_KEY` and any seat whose native key is absent is routed through its OpenRouter mirror automatically.
- **A two-cent test run:** the `itest` panel is a single cheap judge (DeepInfra key) for checking your setup end to end before spending on the frontier panel.

**Where keys go:** either export them in your shell, or put them in a `.env` file at `engine/panel/.env` (gitignored -- it never leaves your machine):

```sh
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPINFRA_API_KEY=...
```

`engine/panel/panel-config.json` holds env-var *names* only, never values. Keys are read from the environment first, then the `.env` file.

## Add a new behaviour

A behaviour is one entry in the registry, `data/behaviours.json`. Add yours with `"set": "user"`:

```json
"bribery-resistance": {
  "name": "Bribery resistance",
  "set": "user",
  "numeric_id": 1,
  "group": "My experiments",
  "definition": "The model should not change its behaviour in response to offers of payment, reward, or favours, and should not solicit them.",
  "facets": []
}
```

The fields:

- **key** (`bribery-resistance`) -- the behaviour's slug, its identity everywhere: run commands, log rows, build flags, the sidebar.
- **`name`** -- the title, shown to the judges and in the reader sidebar.
- **`definition`** -- the behaviour statement the judges score against, passed verbatim. Required and non-empty; this is the field that matters most, so write it the way you would brief a careful human reviewer.
- **`facets`** -- optional clarifying sentences, appended to the judge prompt as clarifications. Empty list is fine.
- **`group`** -- sidebar grouping label; anything you like.
- **`numeric_id`** -- unique within the `user` set (start at 1).
- **`set`** -- `"user"` marks it as yours, separate from the project's own lists.

The judge prompt also has an optional **scope** field ("what this behaviour is *not*"), which sharpens verdicts on behaviours that border on related ones. The registry shape cannot carry it; if you want it, add your entry to `engine/panel/behaviours.json` instead, in that file's shape (`title` / `query` / `clarifications` / `boundary` -- see the existing entries), and drop the `--registry=` flag from the run command below. Keep the `data/behaviours.json` row either way; the viewer build reads it.

### Run the panel

One command spins up the judges -- one API call per behaviour x spec x judge, each call carrying the entire spec:

```sh
python3 engine/panel/whole_doc.py bribery-resistance constitution,model-spec frontier_fast \
    --registry=data/behaviours.json --runlog=engine/panel/runlog-user.jsonl
```

- The three positional arguments are comma-separated lists: behaviours, specs, and judges (a panel name from `engine/panel/panel-config.json`, or individual model tags like `sol,fable`).
- Verdicts append to the runlog as they arrive. The run is **resume-safe**: rerun the same command after a crash or provider failure and finished cells are skipped.
- Cost: a whole-spec prompt is roughly 65k tokens, so one behaviour x both specs x the three-seat frontier panel (six calls) lands in the low single-digit dollars. Swap `frontier_fast` for `itest` to rehearse the same flow for about two cents.

### Build the viewer payload and look at the results

```sh
python3 engine/panel/build_site_data.py --runlog=engine/panel/runlog-user.jsonl \
    --rubric=v3w --panel=frontier_fast --behaviours=bribery-resistance
```

This writes a timestamped payload under `site/llm-panel-review/data/` (local to your clone, gitignored) and updates a manifest; the panel reader loads the newest run first, so just refresh the browser. Notes:

- `--rubric=v3w` is what fresh `whole_doc.py` runs stamp their rows with (the shipped bench was produced with the newer v5 rubric; the builder lists the valid values if you pass a mismatched one). The reader adapts its score tiers to whichever scale the payload carries.
- `--behaviours=` lists what appears in the sidebar; every slug must exist in the registry.
- To get back to the shipped bench, open the page with `?data=behaviours.json`; `python3 engine/panel/select_run.py` shows the run ledger and what the page will load.

### Reading the scores

Each judge scores each passage on a small relevance scale; a passage's score is the sum across the panel. The reader buckets scores into three tiers -- **defining** (the passage is squarely about the behaviour), **core**, and **related** -- with the cutoffs derived from the panel size and scale. By default the page shows defining + core; toggle the related tier on for the wider penumbra.

## Bring your own spec (and spec versions)

Register any document you want to assess -- including your own working edits of a lab's spec -- in a local manifest at `specs/user/specs.json`:

```json
{
  "my-spec": {
    "2026-08-24": {"path": "specs/user/my-spec.md", "default": true}
  }
}
```

- The document is a Markdown file with headings; the citation engine splits it into sections, paragraphs, and sentences. Check the parse with `python3 engine/spec-cite/cite.py outline my-spec` and `... show "my-spec > Some Section"`.
- Versions are ISO dates. A spec can carry several versions side by side; `"default"` marks the one used when a locator carries no `@version` pin (optional when there is exactly one version).
- Paths resolve relative to the repo root; absolute paths work too.
- **Everything under `specs/user/` is gitignored.** Your manifest and documents stay on your machine.
- The bundled names (`constitution`, `model-spec`) cannot be redefined, and a malformed manifest fails every panel command loudly at startup by design -- fix or delete the manifest to recover.

Once registered, the name works everywhere the bundled specs do:

```sh
# judge a behaviour against your spec
python3 engine/panel/whole_doc.py bribery-resistance my-spec frontier_fast \
    --registry=data/behaviours.json --runlog=engine/panel/runlog-user.jsonl

# render your spec as a pane in the readers
python3 engine/build-spec-reader-data.py
```

The second command regenerates the shared document payload (again local to your clone) so both reader surfaces display your spec's full text alongside the bundled ones.

**Iterating on edits:** save each revision as a new dated version in the manifest, run the panel against each version, and compare the coverage maps. Locators pin the version (`my-spec@2026-08-24 > ...`), so citations into older drafts keep resolving as your document evolves.

## Selecting passages for downstream work

Every citation the tool produces is a **locator** in the grammar defined in [`specs/CITATION.md`](specs/CITATION.md):

```
spec@version > section > ¶paragraph sentence
```

`engine/spec-cite/cite.py` is the resolver, and the contract is byte-exact: a locator always resolves to the same text or fails loudly.

```sh
python3 engine/spec-cite/cite.py outline model-spec                              # section tree
python3 engine/spec-cite/cite.py show "constitution > Being honest"              # numbered ¶/sentences
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"
python3 engine/spec-cite/cite.py find model-spec "some remembered phrase"        # text -> locator
```

The panel payloads under `site/llm-panel-review/data/` are plain JSON: each citation carries its locator, the exact quote, and the per-judge verdicts behind the score. So the selection workflow is: browse in the reader, decide which tiers or passages you care about, then script over the payload to pull the locator + quote pairs into your eval pipeline -- for example, as the target passages of automated model-spec-adherence evals in Petri. Because locators re-resolve exactly, your selection stays a stable reference rather than a copy-paste that drifts.

## Sanity checks

All offline, no keys:

```sh
python3 engine/panel/test_panel.py               # unit tests for the judging pipeline
python3 engine/panel/verify_panel_provenance.py  # shipped payload rebuilds from its committed runlog
python3 engine/validate_data.py                  # schema-check data/, incl. your registry edits
```

## Where things live

| Path | What it is |
|---|---|
| [`engine/panel/`](engine/panel/) | The judging pipeline: config, prompts, run scripts, payload builder ([README](engine/panel/README.md)) |
| [`engine/spec-cite/cite.py`](engine/spec-cite/cite.py) | The citation resolver behind every quote |
| [`specs/`](specs/) | Bundled spec mirrors and the locator grammar ([`CITATION.md`](specs/CITATION.md)); `specs/user/` is your local manifest |
| [`data/behaviours.json`](data/behaviours.json) | The behaviour registry -- where your behaviours go |
| [`site/`](site/) | The local reader surfaces |

The remaining directories (`research/`, `methodology/`, `docs/`, `design/`, and friends) are the project's own editorial records and maintenance; none of them are needed to use the tool.

## Questions

Something broken, unclear, or wrong: open an issue -- or use the contact link on the Issues page to reach Andrés directly. We read everything.
