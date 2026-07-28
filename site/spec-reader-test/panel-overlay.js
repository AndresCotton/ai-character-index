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
let threshold = 0.5;   // default: majority agreement -- drag left to see contested 1-of-N calls

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

let tooltip = null;
function showTip(block, hit) {
  hideTip();
  tooltip = document.createElement("div");
  const rows = Object.entries(hit.votes)
    .map(([m, v]) => `<tr><td>${m}</td><td>${v ? "✓ relevant" : "✗ not"}</td></tr>`).join("");
  tooltip.innerHTML =
    `<strong>${hit.nRelevant}/${hit.nVoters} models</strong> (${Math.round(hit.pct * 100)}%)` +
    `<table>${rows}</table><small>${hit.locator}</small>`;
  tooltip.style.cssText =
    "position:absolute;z-index:50;background:var(--surface,#fff);border:1px solid #8886;" +
    "border-radius:6px;padding:.5em .7em;font-size:.78rem;max-width:22em;box-shadow:0 4px 14px #0003;";
  tooltip.querySelectorAll("td").forEach(td => td.style.padding = "0 .5em 0 0");
  document.body.appendChild(tooltip);
  const r = block.getBoundingClientRect();
  tooltip.style.left = `${Math.max(8, r.left + window.scrollX)}px`;
  tooltip.style.top = `${r.bottom + window.scrollY + 4}px`;
}
function hideTip() { tooltip?.remove(); tooltip = null; }

function apply() {
  if (!PANEL) return;
  let shown = 0, total = 0;
  document.querySelectorAll(".document-panel").forEach(panel => {
    const docId = DOC_SLUG[panel.dataset.documentId] || panel.dataset.documentId
      || (norm(panel.querySelector(".document-lab")?.textContent).includes("anthropic") ? "anthropic" : "openai");
    const hits = passagesFor(docId);
    const index = new Map(hits.map(h => [norm(h.quote), h]));
    panel.querySelectorAll("[data-block]").forEach(block => {
      block.querySelector(":scope > .panel-chip")?.remove();   // before matching: chip text pollutes textContent
      block.classList.remove("panel-hit");
      block.style.outline = "";
      block.onmouseenter = null; block.onmouseleave = null;
      const hit = index.get(norm(block.textContent));
      if (!hit) return;
      total += 1;
      if (hit.pct < threshold) return;
      shown += 1;
      block.classList.add("panel-hit");
      block.style.outline = `2px solid hsl(${120 * hit.pct} 70% 45% / .55)`;
      block.style.outlineOffset = "2px";
      const chip = document.createElement("span");
      chip.className = "panel-chip";
      chip.textContent = `${hit.nRelevant}/${hit.nVoters}`;
      chip.style.cssText =
        "float:right;font-size:.7rem;padding:0 .45em;border-radius:1em;margin-left:.5em;" +
        `background:hsl(${120 * hit.pct} 70% 45% / .18);border:1px solid hsl(${120 * hit.pct} 70% 35% / .5);`;
      block.prepend(chip);
      block.onmouseenter = () => showTip(block, hit);
      block.onmouseleave = hideTip;
    });
    if (hits.length) {
      console.info(`[panel-overlay] ${docId}: matched ${index.size ? total : 0} blocks`
        + ` from ${hits.length} flagged passages (ticked behaviours)`);
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
  });
  const count = document.getElementById("panel-count");
  if (count) count.textContent = `${shown}/${total} passages shown`;
}

const observer = new MutationObserver(muts => {
  if (muts.some(m => [...m.addedNodes].some(n => n.nodeType === 1))) apply();
});
const reader = document.getElementById("document-reader");
if (reader) observer.observe(reader, { childList: true, subtree: false });
document.getElementById("behaviour-list")?.addEventListener("change", () => setTimeout(apply, 50));
["select-all-behaviours", "clear-behaviours"].forEach(id =>
  document.getElementById(id)?.addEventListener("click", () => setTimeout(apply, 50)));

loadPanel();
