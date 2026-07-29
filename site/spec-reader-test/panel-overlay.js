/* Panel-of-judges overlay (branch-only; not for main).
 *
 * Layers model-vote data over the reader without touching its annotation engine:
 * loads data/panel.json, matches each flagged passage to a rendered [data-block]
 * by normalized text, then adds (a) a per-block agreement chip, (b) a hover
 * tooltip listing each model's vote, and (c) a slider that filters highlights
 * by % of models voting relevant (voter counts differ per passage, so the
 * threshold is a percentage, not a count).
 *
 * Re-applies via MutationObserver whenever the reader re-renders.
 */

const DOC_SLUG = { anthropic: "anthropic", openai: "openai" };
let PANEL = null;
let SLUG_ORDER = [];   // sidebar order -> same hue slots the app assigns
let threshold = 0.5;   // default: majority agreement -- drag left to see contested 1-of-N calls

/* Same hue the app gives this behaviour's curated tint (index into --hue-1..12). */
function hueFor(slug) {
  const i = Math.max(0, SLUG_ORDER.indexOf(slug));
  return `var(--hue-${(i % 12) + 1})`;
}
/* Agreement is encoded in the outline STYLE (hue now belongs to the behaviour):
 * solid = unanimous, dashed = majority, dotted = below majority. */
const strokeFor = pct => pct >= 1 ? "solid" : pct >= 0.5 ? "dashed" : "dotted";

/* Panel quotes are source markdown; rendered blocks are its text. Strip markdown
 * syntax from both sides so they compare equal. */
const norm = s => (s || "")
  .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")   // [text](url) -> text
  .replace(/[*_`~#>]/g, "")
  .replace(/\s+/g, " ").trim().toLowerCase();

async function loadPanel() {
  try {
    const res = await fetch("./data/panel.json", { cache: "no-store" });
    if (!res.ok) return;
    PANEL = await res.json();
    try {
      const b = await fetch("./data/behaviours.json", { cache: "no-store" }).then(r => r.json());
      SLUG_ORDER = b.behaviours.map(x => x.slug);
    } catch { /* hue fallback: slot 1 */ }
    buildSlider();
    apply();
  } catch { /* no panel data -- overlay stays dormant */ }
}

function selectedSlugs() {
  return [...document.querySelectorAll("#behaviour-list input:checked")]
    .map(i => i.dataset.behaviour).filter(Boolean);
}

/* One entry per rendered document panel: docId -> flagged passages of ticked behaviours. */
function passagesFor(docId) {
  if (!PANEL) return [];
  const slugs = selectedSlugs();
  const out = [];
  for (const slug of Object.keys(PANEL)) {
    if (!slugs.includes(slug)) continue;   // overlay strictly follows the sidebar selection
    for (const row of PANEL[slug]?.[docId] || []) out.push({ slug, ...row });
  }
  return out;
}

function buildSlider() {
  if (document.getElementById("panel-slider")) return;
  const bar = document.querySelector(".finding-bar");
  if (!bar) return;
  const wrap = document.createElement("div");
  wrap.id = "panel-slider";
  wrap.innerHTML = `
    <label>Model agreement ≥ <output id="panel-thr">50%</output></label>
    <input type="range" min="0" max="100" step="5" value="50" aria-label="Minimum model agreement">
    <span id="panel-count"></span>`;
  wrap.style.cssText = "display:flex;gap:.6em;align-items:center;font-size:.85em;padding:.2em .8em;";
  bar.after(wrap);
  wrap.querySelector("input").addEventListener("input", e => {
    threshold = Number(e.target.value) / 100;
    wrap.querySelector("#panel-thr").textContent = `${e.target.value}%`;
    apply();
  });
}

const shortName = slug => slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())
  .replace("Avoidance To", "to").replace(" On Contested Questions", "");

let tooltip = null;
function showTip(block, hitList) {
  hideTip();
  tooltip = document.createElement("div");
  tooltip.innerHTML = hitList.map(hit => {
    const rows = Object.entries(hit.votes)
      .map(([m, v]) => `<tr><td>${m}</td><td>${v ? "✓ relevant" : "✗ not"}</td></tr>`).join("");
    return `<div style="margin-bottom:.4em"><strong>${shortName(hit.slug)}: `
      + `${hit.nRelevant}/${hit.nVoters} models</strong> (${Math.round(hit.pct * 100)}%)`
      + `<table>${rows}</table></div>`;
  }).join("") + `<small>${hitList[0].locator}</small>`;
  tooltip.style.cssText =
    "position:absolute;z-index:50;background:var(--surface,#fff);border:1px solid #8886;" +
    "border-radius:6px;padding:.5em .7em;font-size:.78rem;max-width:22em;box-shadow:0 4px 14px #0003;";
  tooltip.querySelectorAll("td").forEach(td => td.style.padding = "0 .5em 0 0");
  document.body.appendChild(tooltip);
  // Anchor to the right of the chip tokens (top-right of the block); flip left if cramped.
  const anchor = block.querySelector(".panel-chip") || block;
  const r = anchor.getBoundingClientRect();
  const w = tooltip.offsetWidth;
  let x = r.right + window.scrollX + 10;
  if (r.right + 10 + w > window.innerWidth - 8) x = Math.max(8, r.left + window.scrollX - w - 10);
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${Math.max(8, r.top + window.scrollY - 4)}px`;
}
function hideTip() { tooltip?.remove(); tooltip = null; }

/* Block text for matching: the app injects .passage-head labels and .passage-rationale
 * spans INSIDE curated-passage blocks, and we prepend .panel-chip -- all of which pollute
 * textContent and break the quote match. Strip them on a clone before normalizing. */
function matchText(block) {
  const clone = block.cloneNode(true);
  clone.querySelectorAll(".panel-chip, .passage-head, .passage-rationale, .passage-why")
    .forEach(el => el.remove());
  return norm(clone.textContent);
}

function apply() {
  if (!PANEL) return;
  let shown = 0, total = 0;
  document.querySelectorAll(".document-panel").forEach(panel => {
    try {
    const docId = DOC_SLUG[panel.dataset.documentId] || panel.dataset.documentId
      || (norm(panel.querySelector(".document-lab")?.textContent).includes("anthropic") ? "anthropic" : "openai");
    const hits = passagesFor(docId);
    const index = new Map();   // normText -> ALL hits (multiple ticked behaviours can flag one block)
    hits.forEach(h => {
      const k = norm(h.quote);
      if (!index.has(k)) index.set(k, []);
      index.get(k).push(h);
    });
    panel.querySelectorAll("[data-block]").forEach(block => {
      block.querySelectorAll(":scope > .panel-chip").forEach(c => c.remove());
      block.classList.remove("panel-hit");
      block.style.outline = "";
      block.onmouseenter = null; block.onmouseleave = null;
      const all = index.get(matchText(block));
      if (!all) return;
      total += 1;
      const visible = all.filter(h => h.pct >= threshold);
      if (!visible.length) return;
      shown += 1;
      const lead = visible.reduce((a, b) => (b.pct > a.pct ? b : a));
      block.classList.add("panel-hit");
      // Behaviour's own hue (matches its curated tint); agreement lives in the stroke style.
      block.style.outline = `2px ${strokeFor(lead.pct)} rgb(${hueFor(lead.slug)} / .8)`;
      block.style.outlineOffset = "2px";
      block.dataset.panelLead = lead.slug;
      block.dataset.panelPct = lead.pct;
      visible.forEach(hit => {
        const chip = document.createElement("span");
        chip.className = "panel-chip";
        chip.textContent = `${shortName(hit.slug)} ${hit.nRelevant}/${hit.nVoters}`;
        chip.style.cssText =
          "float:right;clear:right;font-size:.68rem;padding:0 .45em;border-radius:1em;margin-left:.5em;" +
          `background:rgb(${hueFor(hit.slug)} / .15);border:1px ${strokeFor(hit.pct)} rgb(${hueFor(hit.slug)} / .6);`;
        block.prepend(chip);
      });
      block.onmouseenter = () => showTip(block, visible);
      block.onmouseleave = hideTip;
    });
    paintRail(panel);
    console.info(`[panel-overlay] ${docId}: selected=[${selectedSlugs()}] hits=${hits.length}`
      + ` painted=${panel.querySelectorAll(".panel-hit").length} thr=${threshold}`);
    if (hits.length) {
      // Rows with no curated passages render fully collapsed, hiding our outlines --
      // expand the document once so panel hits are visible.
      const painted = [...panel.querySelectorAll(".panel-hit")];
      if (painted.length && painted.every(b => b.offsetParent === null)) {
        const toggle = panel.querySelector(".document-focus-toggle");
        if (toggle?.getAttribute("aria-pressed") === "false") toggle.click();
      }
      // The app's zero-coverage note reads as "no data" -- point at the overlay instead.
      panel.querySelectorAll(".zero-coverage").forEach(note => {
        note.textContent = "No curated passage mapping for this row -- highlights below are "
          + "model-panel votes (demo). Use the agreement slider to filter.";
      });
    }
    } catch (e) { console.error("[panel-overlay] apply failed for a panel:", e); }
  });
  const count = document.getElementById("panel-count");
  if (count) count.textContent = `${shown}/${total} passages shown`;
}

/* Hollow rail marks for panel hits, so they're findable from the scroll bar. The app
 * rebuilds the rail with replaceChildren() on every relayout, wiping ours -- a per-rail
 * observer re-adds them (guarded so our own insertions don't loop). */
function paintRail(panel) {
  const rail = panel.querySelector(".passage-rail");
  const body = panel.querySelector(".document-body");
  if (!rail || !body || !body.scrollHeight) return;
  rail.querySelectorAll(".panel-rail-mark").forEach(m => m.remove());
  panel.querySelectorAll(".panel-hit").forEach(block => {
    const mark = document.createElement("span");
    mark.className = "panel-rail-mark";
    mark.title = `panel: ${block.dataset.panelLead}`;
    mark.style.cssText =
      "position:absolute;left:0;right:0;border-radius:2px;cursor:pointer;background:transparent;" +
      `border:1.5px ${strokeFor(Number(block.dataset.panelPct))} rgb(${hueFor(block.dataset.panelLead)} / .9);` +
      `top:${Math.min(98, (block.offsetTop / body.scrollHeight) * 100)}%;` +
      `height:max(5px,${(block.offsetHeight / body.scrollHeight) * 100}%);`;
    mark.onclick = () => block.scrollIntoView({ block: "center", behavior: "smooth" });
    rail.appendChild(mark);
  });
}

const railObserver = new MutationObserver(muts => {
  for (const m of muts) {
    const rail = m.target;
    // re-add only if the app wiped us (avoid reacting to our own inserts)
    if (rail.classList?.contains("passage-rail") && !rail.querySelector(".panel-rail-mark")) {
      const panel = rail.closest(".document-panel");
      if (panel?.querySelector(".panel-hit")) requestAnimationFrame(() => paintRail(panel));
    }
  }
});
function watchRails() {
  document.querySelectorAll(".passage-rail").forEach(r =>
    railObserver.observe(r, { childList: true }));
}

const observer = new MutationObserver(muts => {
  if (muts.some(m => [...m.addedNodes].some(n => n.nodeType === 1))) { watchRails(); apply(); }
});
const reader = document.getElementById("document-reader");
if (reader) observer.observe(reader, { childList: true, subtree: false });
document.getElementById("behaviour-list")?.addEventListener("change", () => setTimeout(apply, 50));
["select-all-behaviours", "clear-behaviours"].forEach(id =>
  document.getElementById(id)?.addEventListener("click", () => setTimeout(apply, 50)));

loadPanel();
