#!/usr/bin/env python3
"""Build report.html (the calibration-loop dossier) from the per-iteration compare
snapshots (compare-iterN.json), the prompt files, and metrics.jsonl. Re-run after
each iteration; add an entry to ITERATIONS (newest renders first).
"""
import difflib, html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent.parent / "engine" / "panel"
CONFIG = json.loads((PANEL / "panel-config.json").read_text())

JUDGE_NAME = {"sol": "GPT-5.6 Sol", "fable": "Claude Fable 5", "kimi": "Kimi-K3",
              "deepseek": "DeepSeek-V3.2"}

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


def esc(s):
    return html.escape(s, quote=True)


def word_diff(a, b):
    ta, tb = re.findall(r"\S+\s*", a), re.findall(r"\S+\s*", b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(esc("".join(ta[i1:i2])))
        if op in ("delete", "replace"):
            out.append(f"<del>{esc(''.join(ta[i1:i2]))}</del> ")
        if op in ("insert", "replace"):
            out.append(f"<ins>{esc(''.join(tb[j1:j2]))}</ins> ")
    return "".join(out)


def meter(mv, judges):
    cells = []
    for j in judges:
        v = mv.get(j)
        cls = {3: "m3", 2: "m2", 1: "m1", 0: "m0", None: "mx"}[v]
        cells.append(f'<span class="mcell {cls}" title="{JUDGE_NAME.get(j, j)}: '
                     f'{v if v is not None else "absent"}"></span>')
    return f'<span class="meter">{"".join(cells)}</span>'


def top_table(cmp_data, cellname, variant_label, k=10):
    cd = cmp_data["cells"][cellname][variant_label]
    denom = cd.get("maxv", 2) * len(cd["judges"])
    rows = []
    for r in cd["top"][:k]:
        loc_short = esc(r["locator"].split(" > ", 1)[1])
        tcls = " target" if r["target"] else ""
        chip = '<span class="chip">named core</span> ' if r["target"] else ""
        rows.append(
            f'<tr class="prow{tcls}"><td class="rk">{r["rank"]}</td>'
            f'<td class="sc">{r["score"]}/{denom} {meter(r["verdicts"], cd["judges"])}</td>'
            f'<td class="pq">{chip}<span class="loc">{loc_short}</span><br>'
            f'<span class="snip">{esc(r["snippet"])}&hellip;</span></td></tr>')
    dist = cd["dist"]
    dline = " &middot; ".join(f'{k2}&thinsp;&times;&thinsp;{dist[k2]}'
                              for k2 in sorted(dist, key=int, reverse=True) if int(k2) > 0)
    return (f'<div class="toplist"><div class="tophead"><span class="vtag">{variant_label}</span>'
            f'<span class="dist">{cd["positive"]} positive &mdash; score&times;count: {dline}</span></div>'
            f'<table class="ptable">{"".join(rows)}</table></div>')


def cost_of(vias, models=None):
    price = {t: m.get("openrouter", {}).get("price_per_mtok", m["price_per_mtok"])
             for t, m in CONFIG["models"].items()}
    tot = 0.0
    for line in (PANEL / "metrics.jsonl").read_text().splitlines():
        d = json.loads(line)
        if d.get("via") in vias and d["model"] in price and d.get("prompt_tokens") \
                and (models is None or d["model"] in models):
            i, o = price[d["model"]]
            tot += d["prompt_tokens"] / 1e6 * i + (d.get("completion_tokens") or 0) / 1e6 * o
    return tot


def scoreboard(cmp_data, old_label, new_label, verdicts_by_cell, top_band):
    """top_band: score at/above which a passage counts as the cell's top tier."""
    rows = []
    for cell in CELL_ORDER:
        cd = cmp_data["cells"].get(cell)
        if not cd or old_label not in cd or new_label not in cd:
            continue
        a, b = cd[old_label], cd[new_label]
        amax = max(int(k) for k in a["dist"]) if a["dist"] else 0
        aband = sum(v for k, v in a["dist"].items() if int(k) >= a.get("maxv", 2) * 3)
        bband = sum(v for k, v in b["dist"].items() if int(k) >= top_band)
        ta = a["targets"][0] if a["targets"] else None
        tb = b["targets"][0] if b["targets"] else None
        trk = (f'{ta["rank"]} &rarr; <strong>{tb["rank"]}</strong>' if ta and tb else "&mdash;")
        word, cls = verdicts_by_cell[cell]
        rows.append(
            f'<tr><td>{esc(CELL_TITLE[cell])}<br><span class="role">{CELL_ROLE[cell]}</span></td>'
            f'<td class="num">{aband} &rarr; <strong>{bband}</strong></td>'
            f'<td class="num">{a["positive"]} &rarr; {b["positive"]}</td>'
            f'<td class="num">{trk}</td>'
            f'<td><span class="pill {cls}">{word}</span></td></tr>')
    return "".join(rows)


ITER1 = json.loads((HERE / "compare-iter1.json").read_text())
ITER2 = json.loads((HERE / "compare-iter2.json").read_text())
P = {v: (HERE / "prompts" / f"{v}.txt").read_text() for v in ("v3w", "v4a", "v5")}
COST_ALL = cost_of({"wholedoc", "wholedoc-v4a", "wholedoc-v5"})
COST_I2 = cost_of({"wholedoc-v5"}) + cost_of({"wholedoc-v4a"}, models={"deepseek"})

V1 = {  # iteration 1 verdicts per cell
    "proportionate-risk|constitution": ("fixed", "good"),
    "proportionate-risk|model-spec": ("fixed", "good"),
    "tradeoffs|constitution": ("improved", "good"),
    "over-under-caution|constitution": ("open", "warn"),
    "helpfulness|constitution": ("held", "good"),
}
V2 = {  # iteration 2 verdicts per cell
    "proportionate-risk|constitution": ("fixed", "good"),
    "proportionate-risk|model-spec": ("fixed", "good"),
    "tradeoffs|constitution": ("fixed", "good"),
    "over-under-caution|constitution": ("fixed", "good"),
    "helpfulness|constitution": ("held", "good"),
}

det2 = "".join(
    f'<h4 class="cellh">{esc(CELL_TITLE[c])} <span class="role">({CELL_ROLE[c]})</span></h4>'
    f'<div class="beforeafter">{top_table(ITER2, c, "v4a-ds")}{top_table(ITER2, c, "v5")}</div>'
    for c in CELL_ORDER)
det1 = "".join(
    f'<h4 class="cellh">{esc(CELL_TITLE[c])} <span class="role">({CELL_ROLE[c]})</span></h4>'
    f'<div class="beforeafter">{top_table(ITER1, c, "v3w-fresh")}{top_table(ITER1, c, "v4a")}</div>'
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
.sc {{ font-family:ui-monospace,Menlo,monospace; font-size:.8rem; white-space:nowrap; width:6.6rem;
  font-variant-numeric:tabular-nums; }}
.loc {{ font-family:ui-monospace,Menlo,monospace; font-size:.72rem; color:var(--muted); }}
.snip {{ font-size:.86rem; }}
tr.target td {{ background:var(--accent-wash); }}
.chip {{ font-family:ui-monospace,Menlo,monospace; font-size:.66rem; letter-spacing:.06em; color:var(--accent);
  border:1px solid var(--accent); border-radius:2px; padding:.03rem .3rem; text-transform:uppercase; }}
.meter {{ display:inline-flex; gap:2px; margin-left:.35rem; vertical-align:middle; }}
.mcell {{ width:.55rem; height:.55rem; border:1px solid var(--muted); border-radius:1px; display:inline-block; }}
.mcell.m3 {{ background:var(--accent); border-color:var(--accent); outline:1px solid var(--accent); outline-offset:1px; }}
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
<p class="meta">Iteration dossier &mdash; whole-document judging over 374 constitution + 589 model-spec
passages per judge-call. Loop spend to date &asymp;${COST_ALL:.2f}. Latest iteration first.</p>

<div class="col">
<h2>The brief</h2>
<p>Adri&agrave;'s review of the reader-test bench: behaviours differ hugely in how much of a document
truly <em>carries</em> them, but the citation sets don't show it &mdash; proportionate risk mitigation
surfaced about as many passages as helpfulness, with no separation between the passage that carries the
construct and the many that merely touch it. The named cores: the
<em>&ldquo;probability that the action leads to harm at all&rdquo;</em> factor (constitution),
<em>&ldquo;within the defined scope of autonomy &hellip; minimize side effects&rdquo;</em> (model spec), and the
<em>&ldquo;overcautious or overcompliant&rdquo;</em> test paragraph. Tradeoffs and helpfulness read well and must
stay intact, with the initial strongest expression of tradeoffs standing above its own elaborations.</p>
<p class="note">What the review actually looked at: the deployed reader-test page shows the July
<em>hand-curated</em> sets, not panel output. Stage 4 is now the panel procedure, so the fix belongs in the
panel's fixed rubric &mdash; calibrated so the panel natively produces this salience profile for any
behaviour, with no per-behaviour tuning.</p>

<h2>What is fixed, what the user supplies</h2>
</div>
<div class="anatomy">
<div><h3>Harness skeleton (ours to calibrate, same for every behaviour)</h3><ul>
<li>The system rubric &mdash; the object under iteration below.</li>
<li>Whole-document presentation: every passage, numbered, in reading order.</li>
<li>Output contract: one <code>passage: verdict</code> line per passage
(0&ndash;2 through v4a; 0&ndash;3 from v5).</li>
<li>Aggregation: three judges, score = sum (0&ndash;6 on the 3-point scale, 0&ndash;9 on the 4-point).</li>
<li>Panel seats and display thresholds (<code>?threshold=</code>, <code>?solid=</code>, <code>?related=</code>).</li>
</ul></div>
<div><h3>User-supplied form (per behaviour, the only prompting the user does)</h3><ul>
<li><strong>Behaviour</strong> &mdash; its title.</li>
<li><strong>Definition</strong> &mdash; what the behaviour requires; passages are judged against this.</li>
<li><strong>Clarifications</strong> <span class="role">(optional)</span> &mdash; ambiguity notes.</li>
<li><strong>Scope</strong> <span class="role">(optional)</span> &mdash; the construct's edges: neighbouring
behaviours that are <em>not</em> this one.</li>
</ul></div>
</div>

<div class="col">
<h2>Iteration 2 &mdash; v4a &rarr; v5: a DEFINING tier, and a faster third judge</h2>
<p>Two changes, evaluated separately below. <strong>Rubric:</strong> the scale becomes 4-point &mdash;
<em>3 = DEFINING</em>, the document's fullest statement of the behaviour, defined relative to the document's
own maximum and explicitly allowed to be absent (&ldquo;no saliency&rdquo; is a valid answer). This is the
relative judgment a 3-level absolute scale structurally cannot express: however well core is worded, every
qualifying passage saturates at unanimous 6/6.
<strong>Panel:</strong> DeepSeek-V3.2 (open-weights, seconds per call) takes Kimi-K3's seat &mdash; K3 spent
8&ndash;18 minutes and 25&ndash;57k reasoning tokens per call. DeepSeek turned out to be a strict,
literal judge: on v4a it marked only the Definition's own dimensions (probability, severity, breadth) core
for proportionate risk, and exactly &ldquo;minimize side effects&rdquo; on the model spec &mdash; so its seat
alone already breaks ties. Iteration cost &asymp;${COST_I2:.2f} vs &asymp;$21 with K3.</p>
<p>The before/after below holds the new panel constant (v4a was re-scored with DeepSeek seated, the
<span class="vtag">v4a-ds</span> column) so the remaining movement is the rubric's. Success checks:
every named core now ranks 1 (over-/under-caution: 4, above the enumeration plateau); top bands hold 1&ndash;4
passages; tradeoffs' ordering statement is the run's only unanimous 9/9; helpfulness keeps a graded
9&ndash;8&ndash;7&ndash;6 spine rather than a wall.</p>
</div>

<h3>The exact change, v4a &rarr; v5 (struck = removed, tinted = added)</h3>
<div class="diff col">{word_diff(P["v4a"], P["v5"])}</div>

<h3>Scoreboard &mdash; top band (unanimous core 6/6 under v4a-ds; score &ge;7/9 under v5)</h3>
<div class="wrap"><table class="ledger">
<tr><th>Cell</th><th>top band</th><th>positive (&ge;1)</th><th>named-core rank</th><th>read</th></tr>
{scoreboard(ITER2, "v4a-ds", "v5", V2, 7)}
</table></div>

<h3>Before / after, per cell &mdash; same panel, rubric change only</h3>
<p class="meta col">Top 10 by score. Squares = per-judge verdicts (DeepSeek &middot; Fable &middot; Sol);
ringed = defining (3), full = core (2), half = related (1). Tinted rows are the review's named cores.</p>
{det2}

<div class="col">
<h2>Iteration 1 &mdash; v3w &rarr; v4a: core means <em>established here</em>, not <em>applied here</em></h2>
<p>Diagnosis: v3w's CORE (&ldquo;directly governs &hellip; you would cite it&rdquo;) admits every passage that
<em>applies</em> a norm, so behaviours stated once and applied everywhere saturate the top &mdash; 33 unanimous
cores for proportionate risk, a glossary definition of &ldquo;Tool&rdquo; scoring 6/6. v4a reserves CORE for
passages where the document <em>establishes</em> the behaviour, moves applications and echoes to ADJACENT, and
adds a no-quota calibration in both directions. It fixed three of the four complaint cells outright; the
over-/under-caution wall (an enumeration whose items each &ldquo;establish&rdquo; a failure mode) resisted, which
is what motivated iteration 2's relative tier. Panel: Sol &middot; Fable &middot; Kimi-K3.</p>
</div>

<h3>The exact change, v3w &rarr; v4a</h3>
<div class="diff col">{word_diff(P["v3w"], P["v4a"])}</div>

<h3>Scoreboard &mdash; unanimous 6/6 cores</h3>
<div class="wrap"><table class="ledger">
<tr><th>Cell</th><th>top band</th><th>positive (&ge;1)</th><th>named-core rank</th><th>read</th></tr>
{scoreboard(ITER1, "v3w-fresh", "v4a", V1, 6)}
</table></div>
<p class="meta col">Run-to-run noise reference: the shipped v3w run vs the fresh v3w baseline differs by
&plusmn;3 at the 6/6 tier &mdash; scoreboard movements are far outside that.</p>

<h3>Before / after, per cell</h3>
<p class="meta col">Judges: Sol &middot; Fable &middot; Kimi-K3 (3-point scale, max 6/6).</p>
{det1}

<div class="col">
<h2>Inspect in the review UI</h2>
<p>All four runs are built as data files for <code>site/llm-panel-review</code>
(<code>?data=</code> switches). For v5 data, <code>threshold=4&amp;solid=7</code> renders the defining band
solid and the core/related tail thinned. Serve locally:
<code>cd site &amp;&amp; python3 -m http.server 8000</code>, then per behaviour:</p>
<ul class="urls mono">
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v5&threshold=4&solid=7&behavior=proportionate-risk-mitigation&spec=anthropic">v5 &middot; proportionate risk &middot; constitution</a>
 &mdash; vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a-ds&behavior=proportionate-risk-mitigation&spec=anthropic">v4a same panel</a>
 &mdash; vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v3w-fresh&behavior=proportionate-risk-mitigation&spec=anthropic">v3w</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v5&threshold=4&solid=7&behavior=proportionate-risk-mitigation&spec=openai">v5 &middot; proportionate risk &middot; model spec</a>
 &mdash; vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a-ds&behavior=proportionate-risk-mitigation&spec=openai">v4a same panel</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v5&threshold=4&solid=7&behavior=how-to-approach-tradeoffs&spec=anthropic">v5 &middot; tradeoffs</a>
 &mdash; vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a-ds&behavior=how-to-approach-tradeoffs&spec=anthropic">v4a same panel</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v5&threshold=4&solid=7&behavior=avoiding-over-and-under-caution&spec=anthropic">v5 &middot; over-/under-caution</a>
 &mdash; vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a-ds&behavior=avoiding-over-and-under-caution&spec=anthropic">v4a same panel</a></li>
<li><a href="http://localhost:8000/llm-panel-review/?data=behaviours-v5&threshold=4&solid=7&behavior=helpfulness&spec=anthropic">v5 &middot; helpfulness</a>
 &mdash; vs <a href="http://localhost:8000/llm-panel-review/?data=behaviours-v4a-ds&behavior=helpfulness&spec=anthropic">v4a same panel</a></li>
</ul>
</div>
</main>
"""

(HERE / "report.html").write_text(page)
print(f"report.html written ({len(page)} chars); loop ≈ ${COST_ALL:.2f}, iteration 2 ≈ ${COST_I2:.2f}")
