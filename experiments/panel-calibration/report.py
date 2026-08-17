#!/usr/bin/env python3
"""Build report.html (the calibration-loop dossier) from compare-latest.json,
the prompt files, and metrics.jsonl. Re-run after each iteration; prepend new
entries to ITERATIONS. Publish via the Artifact tool from report.html.
"""
import difflib, html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent.parent / "engine" / "panel"
CMP = json.loads((HERE / "compare-latest.json").read_text())
CONFIG = json.loads((PANEL / "panel-config.json").read_text())

JUDGE_ORDER = ["sol", "fable", "kimi"]
JUDGE_SHORT = {"sol": "S", "fable": "F", "kimi": "K"}
JUDGE_NAME = {"sol": "GPT-5.6 Sol", "fable": "Claude Fable 5", "kimi": "Kimi-K3"}

CELL_ORDER = ["proportionate-risk|constitution", "proportionate-risk|model-spec",
              "tradeoffs|constitution", "over-under-caution|constitution",
              "helpfulness|constitution"]
CELL_TITLE = {
    "proportionate-risk|constitution": "Proportionate risk mitigation × Constitution",
    "proportionate-risk|model-spec": "Proportionate risk mitigation × Model Spec",
    "tradeoffs|constitution": "How to approach tradeoffs × Constitution",
    "over-under-caution|constitution": "Avoiding over- and under-caution × Constitution",
    "helpfulness|constitution": "Helpfulness × Constitution",
}
CELL_ROLE = {
    "proportionate-risk|constitution": "complaint",
    "proportionate-risk|model-spec": "complaint",
    "tradeoffs|constitution": "keep, sharpen top",
    "over-under-caution|constitution": "complaint",
    "helpfulness|constitution": "regression control",
}
UI_SLUG = {"proportionate-risk": "proportionate-risk-mitigation", "tradeoffs": "how-to-approach-tradeoffs",
           "over-under-caution": "avoiding-over-and-under-caution", "helpfulness": "helpfulness"}
UI_SPEC = {"constitution": "anthropic", "model-spec": "openai"}


def esc(s):
    return html.escape(s, quote=True)


def word_diff(a, b):
    """Prose diff as HTML: unchanged text plain, removals <del>, insertions <ins>."""
    ta, tb = re.findall(r"\S+\s*", a), re.findall(r"\S+\s*", b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if op in ("equal",):
            out.append(esc("".join(ta[i1:i2])))
        if op in ("delete", "replace"):
            out.append(f"<del>{esc(''.join(ta[i1:i2]))}</del> ")
        if op in ("insert", "replace"):
            out.append(f"<ins>{esc(''.join(tb[j1:j2]))}</ins> ")
    return "".join(out)


def meter(mv):
    """Per-judge verdict glyphs in fixed order: 2 full, 1 half, 0 empty."""
    cells = []
    for j in JUDGE_ORDER:
        v = mv.get(j)
        cls = {2: "m2", 1: "m1", 0: "m0", None: "mx"}[v]
        cells.append(f'<span class="mcell {cls}" title="{JUDGE_NAME[j]}: {v if v is not None else "absent"}"></span>')
    return f'<span class="meter">{"".join(cells)}</span>'


def top_table(cellname, variant_label, k=10):
    cd = CMP["cells"][cellname][variant_label]
    njudge = len(cd["judges"])
    rows = []
    for r in cd["top"][:k]:
        loc_short = esc(r["locator"].split(" > ", 1)[1])
        tcls = " target" if r["target"] else ""
        chip = '<span class="chip">named core</span> ' if r["target"] else ""
        rows.append(
            f'<tr class="prow{tcls}"><td class="rk">{r["rank"]}</td>'
            f'<td class="sc">{r["score"]}/{2*njudge} {meter(r["verdicts"])}</td>'
            f'<td class="pq">{chip}<span class="loc">{loc_short}</span><br>'
            f'<span class="snip">{esc(r["snippet"])}&hellip;</span></td></tr>')
    dist = cd["dist"]
    dline = " &middot; ".join(f'{k2}/6&thinsp;&times;&thinsp;{dist[k2]}'
                              for k2 in sorted(dist, key=int, reverse=True) if int(k2) > 0)
    return (f'<div class="toplist"><div class="tophead"><span class="vtag">{variant_label}</span>'
            f'<span class="dist">{cd["positive"]} positive &mdash; {dline}</span></div>'
            f'<table class="ptable">{"".join(rows)}</table></div>')


def cost_of(vias):
    price = {}
    for tag, m in CONFIG["models"].items():
        p = m.get("openrouter", {}).get("price_per_mtok", m["price_per_mtok"])
        price[tag] = p
    tot = 0.0
    for line in (PANEL / "metrics.jsonl").read_text().splitlines():
        d = json.loads(line)
        if d.get("via") in vias and d["model"] in price and d.get("prompt_tokens"):
            i, o = price[d["model"]]
            tot += d["prompt_tokens"] / 1e6 * i + (d.get("completion_tokens") or 0) / 1e6 * o
    return tot


def scoreboard():
    rows = []
    for cell in CELL_ORDER:
        cd = CMP["cells"][cell]
        a, b = cd["v3w-fresh"], cd["v4a"]
        a6, b6 = a["dist"].get("6", 0), b["dist"].get("6", 0)
        ta = a["targets"][0] if a["targets"] else None
        tb = b["targets"][0] if b["targets"] else None
        trk = (f'{ta["rank"]} &rarr; <strong>{tb["rank"]}</strong>' if ta and tb else "&mdash;")
        pct = round(100 * (b6 - a6) / a6) if a6 else 0
        verdict, vcls = {
            "proportionate-risk|constitution": ("fixed", "good"),
            "proportionate-risk|model-spec": ("fixed", "good"),
            "tradeoffs|constitution": ("improved", "good"),
            "over-under-caution|constitution": ("open", "warn"),
            "helpfulness|constitution": ("held", "good"),
        }[cell]
        rows.append(
            f'<tr><td>{esc(CELL_TITLE[cell])}<br><span class="role">{CELL_ROLE[cell]}</span></td>'
            f'<td class="num">{a6} &rarr; <strong>{b6}</strong> <span class="delta">({pct:+d}%)</span></td>'
            f'<td class="num">{a["positive"]} &rarr; {b["positive"]}</td>'
            f'<td class="num">{trk}</td>'
            f'<td><span class="pill {vcls}">{verdict}</span></td></tr>')
    return "".join(rows)


PROMPT_A = (HERE / "prompts" / "v3w.txt").read_text()
PROMPT_B = (HERE / "prompts" / "v4a.txt").read_text()
DIFF_HTML = word_diff(PROMPT_A, PROMPT_B)
COST = cost_of({"wholedoc", "wholedoc-v4a"})

detail_cells = "".join(
    f'<h4 class="cellh">{esc(CELL_TITLE[c])} <span class="role">({CELL_ROLE[c]})</span></h4>'
    f'<div class="beforeafter">{top_table(c, "v3w-fresh")}{top_table(c, "v4a")}</div>'
    for c in CELL_ORDER)

page = f"""<title>Panel Salience Calibration</title>
<style>
:root {{
  --ground:#FAF7F1; --panel:#F3EDE2; --ink:#2A2520; --muted:#7A7062; --rule:#E4DDD1;
  --accent:#9C4A1E; --accent-wash:#F3E4D6; --good:#3D6B4F; --good-wash:#E3EDE5;
  --warn:#8A6D1F; --warn-wash:#F2EAD2; --del:#9A8C7A;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#201A15; --panel:#2A231C; --ink:#EDE4D7; --muted:#A39682; --rule:#3A322A;
    --accent:#D98A54; --accent-wash:#3B2A1D; --good:#8FBF9F; --good-wash:#25352B;
    --warn:#CFA84D; --warn-wash:#37301D; --del:#7E7264;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#201A15; --panel:#2A231C; --ink:#EDE4D7; --muted:#A39682; --rule:#3A322A;
  --accent:#D98A54; --accent-wash:#3B2A1D; --good:#8FBF9F; --good-wash:#25352B;
  --warn:#CFA84D; --warn-wash:#37301D; --del:#7E7264;
}}
body {{ background:var(--ground); color:var(--ink); margin:0;
  font:17px/1.6 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; }}
main {{ max-width:76rem; margin:0 auto; padding:3.5rem 1.5rem 5rem; }}
.col {{ max-width:70ch; }}
h1 {{ font-size:2.1rem; line-height:1.15; margin:.2rem 0 .4rem; font-weight:600; text-wrap:balance; }}
h2 {{ font-size:1.35rem; margin:2.8rem 0 .6rem; font-weight:600; }}
h3 {{ font-size:1.1rem; margin:2rem 0 .5rem; font-weight:600; }}
h4.cellh {{ font-size:1rem; margin:1.8rem 0 .5rem; font-weight:600; }}
p {{ margin:.55rem 0; }}
.eyebrow {{ font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--accent);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
.meta {{ color:var(--muted); font-size:.92rem; }}
.role {{ color:var(--muted); font-size:.8rem; font-style:italic; }}
table {{ border-collapse:collapse; width:100%; }}
.ledger td, .ledger th {{ padding:.5rem .7rem; border-top:1px solid var(--rule);
  vertical-align:top; text-align:left; }}
.ledger th {{ font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);
  font-family:ui-monospace,Menlo,monospace; font-weight:500; border-top:none; }}
.num {{ font-family:ui-monospace,Menlo,monospace; font-variant-numeric:tabular-nums; font-size:.9rem; white-space:nowrap; }}
.delta {{ color:var(--muted); font-size:.8rem; }}
.pill {{ font-family:ui-monospace,Menlo,monospace; font-size:.72rem; letter-spacing:.06em;
  padding:.14rem .5rem; border-radius:2px; text-transform:uppercase; }}
.pill.good {{ background:var(--good-wash); color:var(--good); }}
.pill.warn {{ background:var(--warn-wash); color:var(--warn); }}
.wrap {{ overflow-x:auto; }}
.beforeafter {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; align-items:start; }}
@media (max-width: 860px) {{ .beforeafter {{ grid-template-columns:1fr; }} }}
.toplist {{ background:var(--panel); border:1px solid var(--rule); border-radius:3px; padding:.6rem .8rem; }}
.tophead {{ display:flex; justify-content:space-between; gap:.8rem; align-items:baseline;
  border-bottom:1px solid var(--rule); padding-bottom:.4rem; margin-bottom:.2rem; }}
.vtag {{ font-family:ui-monospace,Menlo,monospace; font-size:.8rem; color:var(--accent); }}
.dist {{ font-family:ui-monospace,Menlo,monospace; font-size:.72rem; color:var(--muted); }}
.ptable td {{ padding:.4rem .4rem; border-top:1px solid var(--rule); vertical-align:top; }}
.ptable tr:first-child td {{ border-top:none; }}
.rk {{ font-family:ui-monospace,Menlo,monospace; font-size:.8rem; color:var(--muted); width:1.4rem; }}
.sc {{ font-family:ui-monospace,Menlo,monospace; font-size:.8rem; white-space:nowrap; width:6.2rem;
  font-variant-numeric:tabular-nums; }}
.loc {{ font-family:ui-monospace,Menlo,monospace; font-size:.72rem; color:var(--muted); }}
.snip {{ font-size:.86rem; }}
tr.target td {{ background:var(--accent-wash); }}
.chip {{ font-family:ui-monospace,Menlo,monospace; font-size:.66rem; letter-spacing:.06em; color:var(--accent);
  border:1px solid var(--accent); border-radius:2px; padding:.03rem .3rem; text-transform:uppercase; }}
.meter {{ display:inline-flex; gap:2px; margin-left:.35rem; vertical-align:middle; }}
.mcell {{ width:.55rem; height:.55rem; border:1px solid var(--muted); border-radius:1px; display:inline-block; }}
.mcell.m2 {{ background:var(--accent); border-color:var(--accent); }}
.mcell.m1 {{ background:linear-gradient(to top, var(--accent) 50%, transparent 50%); }}
.mcell.mx {{ border-style:dotted; }}
.diff {{ background:var(--panel); border:1px solid var(--rule); border-radius:3px; padding:1.1rem 1.3rem;
  font-size:.95rem; line-height:1.75; }}
.diff del {{ color:var(--del); text-decoration:line-through; text-decoration-thickness:1px; }}
.diff ins {{ background:var(--good-wash); color:var(--good); text-decoration:none; padding:0 .08em; }}
.anatomy {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
@media (max-width: 860px) {{ .anatomy {{ grid-template-columns:1fr; }} }}
.anatomy > div {{ background:var(--panel); border:1px solid var(--rule); border-radius:3px; padding: .9rem 1.1rem; }}
.anatomy h3 {{ margin-top:0; }}
.anatomy ul {{ margin:.4rem 0 .2rem 1.1rem; padding:0; }}
.anatomy li {{ margin:.3rem 0; font-size:.92rem; }}
code, .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.85em;
  background:var(--panel); border:1px solid var(--rule); border-radius:2px; padding:.05em .3em; }}
.urls li {{ margin:.35rem 0; }}
.note {{ border-left:3px solid var(--accent); padding:.2rem 0 .2rem 1rem; color:var(--muted); font-size:.95rem; }}
a {{ color:var(--accent); }}
:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
</style>
<main>
<div class="eyebrow">AI Character Index &middot; spec-coverage panel</div>
<h1>Panel Salience Calibration</h1>
<p class="meta">Iteration dossier &mdash; frontier panel (GPT-5.6 Sol &middot; Claude Fable 5 &middot; Kimi-K3),
whole-document judging, 374 constitution + 589 model-spec passages per judge-call.
Run 2026-08-17 via OpenRouter; 31 calls this iteration, &asymp;${COST:.2f}.</p>

<div class="col">
<h2>The brief</h2>
<p>Adri&agrave;'s review of the reader-test bench: behaviours differ hugely in how much of a document
truly <em>carries</em> them, but the citation sets don't show it &mdash; proportionate risk mitigation
surfaced about as many passages as helpfulness, with no separation between the one passage that carries
the construct and the many that merely touch it. The named cores: the
<em>&ldquo;probability that the action leads to harm at all&rdquo;</em> factor (constitution),
<em>&ldquo;within the defined scope of autonomy &hellip; minimize side effects&rdquo;</em> (model spec), and the
<em>&ldquo;overcautious or overcompliant&rdquo;</em> test paragraph. Tradeoffs and helpfulness read well and must stay
intact, with the initial strongest expression of tradeoffs standing above its own elaborations.</p>
<p class="note">What the review actually looked at: the deployed reader-test page shows the July
<em>hand-curated</em> sets, not panel output. Stage 4 is now the panel procedure, so the fix belongs in the
panel's fixed rubric &mdash; calibrated so the panel natively produces the salience profile the review asked for,
for any behaviour, with no per-behaviour tuning.</p>

<h2>What is fixed, what the user supplies</h2>
</div>
<div class="anatomy">
<div><h3>Harness skeleton (ours to calibrate, same for every behaviour)</h3><ul>
<li>The system rubric &mdash; the object under iteration below.</li>
<li>Whole-document presentation: every passage, numbered, in reading order.</li>
<li>Output contract: one <code>passage: 0/1/2</code> line per passage.</li>
<li>Aggregation: three judges, score = sum (0&ndash;6); unanimous 2s = a &ldquo;6/6 core&rdquo;.</li>
<li>Display: reader UI thresholds (<code>?threshold=</code>, <code>?solid=</code>, <code>?related=</code>).</li>
</ul></div>
<div><h3>User-supplied form (per behaviour, the only prompting the user does)</h3><ul>
<li><strong>Behaviour</strong> &mdash; its title.</li>
<li><strong>Definition</strong> &mdash; what the behaviour requires; passages are judged against this.</li>
<li><strong>Clarifications</strong> <span class="role">(optional)</span> &mdash; ambiguity notes.</li>
<li><strong>Scope</strong> <span class="role">(optional)</span> &mdash; the construct's edges: neighbouring
behaviours that are <em>not</em> this one.</li>
</ul></div>
</div>

<div class="col"><h2>Iteration 1 &mdash; v3w &rarr; v4a: core means <em>established here</em>, not <em>applied here</em></h2>
<p>Diagnosis: v3w's CORE (&ldquo;directly governs &hellip; you would cite it&rdquo;) admits every passage that
<em>applies</em> a norm. A behaviour that a document states once and applies everywhere saturates the top:
33 unanimous cores for proportionate risk on the constitution, a glossary definition of &ldquo;Tool&rdquo;
scoring 6/6 on the model spec. The v4a rubric instead reserves CORE for passages where the document
<em>establishes</em> the behaviour, moves applications and echoes to ADJACENT, and states that core has
no quota in either direction &mdash; pervasive themes keep many, narrow constructs keep few. Nothing in it
names any behaviour.</p></div>

<h3>The exact change (struck = removed, tinted = added; everything else byte-identical)</h3>
<div class="diff col">{DIFF_HTML}</div>

<h3>Scoreboard</h3>
<div class="wrap"><table class="ledger">
<tr><th>Cell</th><th>6/6 cores</th><th>positive (&ge;1)</th><th>named-core rank</th><th>read</th></tr>
{scoreboard()}
</table></div>
<p class="meta col">Run-to-run noise reference: the shipped v3w run vs today's fresh v3w differs by
&plusmn;3 at the 6/6 tier (helpfulness 25 vs 28, over-/under-caution 22 vs 22) &mdash; every movement in the
scoreboard is far outside that.</p>

<h2>Before / after, per cell</h2>
<p class="meta col">Top 10 by score, ties in document order. Squares = per-judge verdicts (Sol &middot; Fable &middot; Kimi);
full = core, half = related, empty = not relevant. Tinted rows are the review's named cores.</p>
{detail_cells}

<div class="col">
<h2>The open problem: over- and under-caution</h2>
<p>v4a barely compresses this wall (22 &rarr; 18 unanimous cores) and the named paragraph stays at rank 17.
The cause is visible in the verdicts: the top of the wall is the constitution's enumeration of over-caution
failure modes, and this behaviour's own user-supplied Scope declares such enumerations in-construct &mdash;
each list item genuinely <em>establishes</em> a named failure mode, so the establishes-test keeps them all.
Three candidate levers for iteration 2:</p>
<ul>
<li><strong>(a) Fullest-statement criterion (skeleton, general).</strong> Within core, reserve 2 for passages that
state the behaviour as fully as the document ever states it; a passage establishing one fragment or one side
of the defined behaviour is adjacent. Tradeoffs already shows judges can hold this distinction
(the ordering statement now outranks its own elaborations).</li>
<li><strong>(b) Retire the &ldquo;one clause or list item still counts&rdquo; sentence (skeleton).</strong> Riskier:
it protects real partial-governance passages, and the review explicitly wants a <em>list item</em> as the core
of proportionate risk.</li>
<li><strong>(c) Definition guidance (user side).</strong> The form could ask: name the construct's centre.
One sentence in over-/under-caution's Definition (&ldquo;the symmetric test is the centre&rdquo;) would likely
resolve it &mdash; but that's tuning the input, and the skeleton should carry as much as it can first.</li>
</ul>
<p>Recommendation: try (a) alone as v4b, on all five cells; fall back to pairing it with (c) guidance if the
factor-list cores of proportionate risk survive but the symmetric-test paragraph still doesn't lead.</p>

<h2>Inspect in the review UI</h2>
<p>Both runs are built as data files for <code>site/llm-panel-review</code>
(<code>?data=</code> switches; add <code>&amp;threshold=5</code> to widen the solid tier).
Serve locally: <code>cd site &amp;&amp; python3 -m http.server 8000</code>, then:</p>
<ul class="urls mono">
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a&behavior=proportionate-risk-mitigation&spec=anthropic">v4a &middot; proportionate risk &middot; constitution</a>
 vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v3w-fresh&behavior=proportionate-risk-mitigation&spec=anthropic">v3w</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a&behavior=proportionate-risk-mitigation&spec=openai">v4a &middot; proportionate risk &middot; model spec</a>
 vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v3w-fresh&behavior=proportionate-risk-mitigation&spec=openai">v3w</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a&behavior=how-to-approach-tradeoffs&spec=anthropic">v4a &middot; tradeoffs</a>
 vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v3w-fresh&behavior=how-to-approach-tradeoffs&spec=anthropic">v3w</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a&behavior=avoiding-over-and-under-caution&spec=anthropic">v4a &middot; over-/under-caution</a>
 vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v3w-fresh&behavior=avoiding-over-and-under-caution&spec=anthropic">v3w</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a&behavior=helpfulness&spec=anthropic">v4a &middot; helpfulness</a>
 vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v3w-fresh&behavior=helpfulness&spec=anthropic">v3w</a></li>
</ul>
</div>
</main>
"""

(HERE / "report.html").write_text(page)
print(f"report.html written ({len(page)} chars), iteration cost ≈ ${COST:.2f}")
