/*
 * Reader test -- a standalone copy of the published spec reader (site/spec-reader/),
 * kept separate so an external reviewer's behaviour set can be published, revised and
 * withdrawn without touching the index's own reader.
 *
 * Differences from the original: the behaviour menu is built from whatever set has
 * been published to this bench (rather than the index's fixed thirteen); the reader
 * degrades to plain reading -- both specs in full, nothing highlighted -- when that set
 * is empty; and the menu is a checklist rather than a single choice, so any number of
 * behaviours can be read over the same text at once. Each behaviour carries its own
 * colour, a core passage is that colour at full strength and a related one the same
 * colour washed out, and a passage cited by more than one selected behaviour blends
 * their colours and shows one gutter rule per behaviour. Colour distinguishes the
 * behaviours; the margin rule's texture distinguishes the groups -- see GROUP_TEXTURE
 * below. The spec text itself is shared with the published reader, so both surfaces
 * always render the same document versions.
 */

const DOCUMENTS_URL = "../spec-reader/data/documents.json";
const BEHAVIOURS_URL = "./data/behaviours.json";

/* Shown for a document when no behaviour is under test. */
const NO_COVERAGE = { verdict: null, depth: null, note: "", verifiedDate: "", passages: [] };

/* Depth anchors per the coverage depth rubric (../methodology.html#coverage). */
const DEPTH_ANCHORS = ["absent", "named", "discussed", "prescribed", "demonstrated"];

/* Behaviour colours live in the stylesheet, one --hue-N per slot and one set per
 * surface, so a palette switch repaints every highlight without re-annotating. */
const HUE_SLOTS = 12;

/* Colour separates the behaviours; texture separates the groups they belong to. A group
 * whose rows are defined by a filter over the specs -- passages that bear on the subject
 * without ever naming it -- carries a broken margin rule where the others carry a solid
 * one, so the indirectness of the reading is legible beside the passage. The texture is
 * kept in the margin and out of the wash on purpose: anything laid over the text itself,
 * added or knocked out, costs more in legibility than the distinction is worth. Groups not
 * listed here take the solid rule. Keyed by the `category` the ledger gives the behaviour. */
const GROUP_TEXTURE = { "General Guidelines": "stipple" };

function behaviourTexture(behaviour) {
  return GROUP_TEXTURE[behaviour.category] || "wash";
}

const state = {
  payload: null,
  selectedSlugs: [],
  selectedSpec: "anthropic",
  comparing: false,
  embedded: false,
  passageIndex: 0,
  anchors: [],
  documentFocus: { anthropic: false, openai: false },
  sidebarWidth: 292,
  compareFirst: 50,
};

const elements = {
  appShell: document.querySelector(".app-shell"),
  behaviourCount: document.querySelector("#behaviour-count"),
  behaviourList: document.querySelector("#behaviour-list"),
  behaviourToolbar: document.querySelector("#behaviour-toolbar"),
  clearBehaviours: document.querySelector("#clear-behaviours"),
  compareToggle: document.querySelector("#compare-toggle"),
  documentReader: document.querySelector("#document-reader"),
  downloadHint: document.querySelector("#download-hint"),
  downloadPassages: document.querySelector("#download-passages"),
  findingBehaviour: document.querySelector("#finding-behaviour"),
  findingDefinition: document.querySelector("#finding-definition"),
  mode: document.querySelector("#mode"),
  nextPassage: document.querySelector("#next-passage"),
  passageCount: document.querySelector("#passage-count"),
  previousPassage: document.querySelector("#previous-passage"),
  readerStatus: document.querySelector("#reader-status"),
  selectAllBehaviours: document.querySelector("#select-all-behaviours"),
  sidebarResizer: document.querySelector("#sidebar-resizer"),
  sourceLink: document.querySelector("#source-link"),
  template: document.querySelector("#document-template"),
};

const initialParams = new URLSearchParams(location.search);
state.embedded = initialParams.get("embedded") === "1";
document.body.classList.toggle("embedded", state.embedded);

function benchBehaviours() {
  return state.payload?.behaviours || [];
}

/* The ticked behaviours, always in menu order: the order decides which colour a passage
 * blend starts from and the order of the rules in a shared passage's gutter. */
function selectedBehaviours() {
  return benchBehaviours().filter(behaviour => state.selectedSlugs.includes(behaviour.slug));
}

function highlightsActive() {
  return selectedBehaviours().length > 0;
}

/* A behaviour's colour is fixed by its place in the published set, not by what else is
 * ticked, so a passage keeps the same colour as the selection changes around it. */
function behaviourHue(behaviour) {
  const index = benchBehaviours().indexOf(behaviour);
  return `var(--hue-${(Math.max(0, index) % HUE_SLOTS) + 1})`;
}

function syncURL() {
  const params = new URLSearchParams(location.search);
  if (state.selectedSlugs.length) params.set("behavior", state.selectedSlugs.join(","));
  else params.delete("behavior");
  params.set("spec", state.selectedSpec);
  if (state.comparing) params.set("compare", "1");
  else params.delete("compare");
  if (state.embedded) params.set("embedded", "1");
  else params.delete("embedded");
  history.replaceState(null, "", `${location.pathname}?${params}${location.hash}`);
  if (state.embedded) {
    window.parent.postMessage(
      {
        type: "aci-spec-reader-state",
        spec: state.selectedSpec,
        comparing: state.comparing,
      },
      location.origin,
    );
  }
}

function setPalette(palette) {
  const selected = ["daylight", "umber"].includes(palette) ? palette : "daylight";
  document.body.dataset.palette = selected;
  const night = selected === "umber";
  elements.mode.textContent = night ? "☼" : "☾";
  elements.mode.title = night ? "Back to daylight" : "Switch to umber";
  elements.mode.setAttribute(
    "aria-label",
    night ? "Switch to the daylight surface" : "Switch to the umber night surface",
  );
  try { localStorage.setItem("aci-palette", selected); } catch (error) {}
}

elements.mode.addEventListener("click", () => {
  setPalette(document.body.dataset.palette === "umber" ? "daylight" : "umber");
});

const paletteParam = new URLSearchParams(location.search).get("palette");
let savedPalette = null;
try { savedPalette = localStorage.getItem("aci-palette"); } catch (error) {}
setPalette(paletteParam || savedPalette || "daylight");

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function savedNumber(key, fallback) {
  try {
    const value = Number(localStorage.getItem(key));
    return Number.isFinite(value) && value > 0 ? value : fallback;
  } catch (error) {
    return fallback;
  }
}

function saveNumber(key, value) {
  try { localStorage.setItem(key, String(value)); } catch (error) {}
}

function setSidebarWidth(width, persist = false) {
  const desktop = window.matchMedia("(min-width: 901px)").matches;
  const maximum = desktop
    ? Math.max(200, Math.min(480, elements.appShell.clientWidth - 420))
    : 480;
  state.sidebarWidth = Math.round(clamp(width, 200, maximum));
  elements.appShell.style.setProperty("--sidebar-width", `${state.sidebarWidth}px`);
  elements.sidebarResizer.setAttribute("aria-valuenow", String(state.sidebarWidth));
  elements.sidebarResizer.setAttribute("aria-valuemax", String(maximum));
  elements.sidebarResizer.setAttribute("aria-valuetext", `${state.sidebarWidth} pixels wide`);
  if (persist) saveNumber("aci-sidebar-width", state.sidebarWidth);
}

function setCompareFirst(percent, persist = false) {
  const width = elements.documentReader.clientWidth;
  const minimum = width > 0 ? Math.min(40, (260 / width) * 100) : 20;
  const maximum = 100 - minimum - (width > 0 ? (9 / width) * 100 : 0);
  state.compareFirst = Math.round(clamp(percent, minimum, maximum) * 10) / 10;
  elements.documentReader.style.setProperty("--compare-first", `${state.compareFirst}%`);
  const resizer = elements.documentReader.querySelector(".document-resizer");
  if (resizer) {
    resizer.setAttribute("aria-valuemin", String(Math.ceil(minimum)));
    resizer.setAttribute("aria-valuemax", String(Math.floor(maximum)));
    resizer.setAttribute("aria-valuenow", String(Math.round(state.compareFirst)));
    resizer.setAttribute("aria-valuetext", `First specification ${Math.round(state.compareFirst)} percent wide`);
  }
  if (persist) saveNumber("aci-compare-first", state.compareFirst);
  requestAnimationFrame(updateRails);
}

function startColumnDrag(event, resizer, update, finish) {
  if (event.button !== 0) return;
  event.preventDefault();
  resizer.setPointerCapture(event.pointerId);
  resizer.classList.add("dragging");
  document.body.classList.add("resizing-columns");

  const move = moveEvent => update(moveEvent.clientX);
  const end = () => {
    resizer.classList.remove("dragging");
    document.body.classList.remove("resizing-columns");
    resizer.removeEventListener("pointermove", move);
    resizer.removeEventListener("pointerup", end);
    resizer.removeEventListener("pointercancel", end);
    finish();
  };
  resizer.addEventListener("pointermove", move);
  resizer.addEventListener("pointerup", end);
  resizer.addEventListener("pointercancel", end);
}

function setupSidebarResizer() {
  state.sidebarWidth = savedNumber("aci-sidebar-width", state.sidebarWidth);
  setSidebarWidth(state.sidebarWidth);
  elements.sidebarResizer.addEventListener("pointerdown", event => {
    const shellLeft = elements.appShell.getBoundingClientRect().left;
    startColumnDrag(
      event,
      elements.sidebarResizer,
      clientX => setSidebarWidth(clientX - shellLeft),
      () => setSidebarWidth(state.sidebarWidth, true),
    );
  });
  elements.sidebarResizer.addEventListener("keydown", event => {
    const step = event.shiftKey ? 40 : 16;
    let next = state.sidebarWidth;
    if (event.key === "ArrowLeft") next -= step;
    else if (event.key === "ArrowRight") next += step;
    else if (event.key === "Home") next = 200;
    else if (event.key === "End") next = 480;
    else return;
    event.preventDefault();
    setSidebarWidth(next, true);
  });
}

function createDocumentResizer() {
  const resizer = document.createElement("div");
  resizer.className = "column-resizer document-resizer";
  resizer.role = "separator";
  resizer.tabIndex = 0;
  resizer.setAttribute("aria-label", "Resize specification panels");
  resizer.setAttribute("aria-orientation", "vertical");
  resizer.setAttribute("aria-valuemin", "0");
  resizer.setAttribute("aria-valuemax", "100");
  resizer.addEventListener("pointerdown", event => {
    const bounds = elements.documentReader.getBoundingClientRect();
    startColumnDrag(
      event,
      resizer,
      clientX => setCompareFirst(((clientX - bounds.left) / bounds.width) * 100),
      () => setCompareFirst(state.compareFirst, true),
    );
  });
  resizer.addEventListener("keydown", event => {
    const step = event.shiftKey ? 10 : 2;
    let next = state.compareFirst;
    if (event.key === "ArrowLeft") next -= step;
    else if (event.key === "ArrowRight") next += step;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = 100;
    else return;
    event.preventDefault();
    setCompareFirst(next, true);
  });
  return resizer;
}

setupSidebarResizer();

function behaviourGroups() {
  const groups = new Map();
  (state.payload?.behaviours || []).forEach(behaviour => {
    const name = behaviour.category || "Behaviors under test";
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(behaviour);
  });
  return [...groups].map(([name, behaviours]) => ({
    name,
    behaviours,
    texture: GROUP_TEXTURE[name] || "wash",
  }));
}

function renderBehaviourList() {
  const groups = behaviourGroups();
  const empty = groups.length === 0;
  document.body.classList.toggle("no-behaviours", empty);
  elements.behaviourToolbar.hidden = empty;

  if (empty) {
    elements.behaviourList.innerHTML = `
      <div class="behaviour-empty">
        <strong>No behaviors under test yet.</strong>
        <p>Both specifications are shown here in full, with no passages highlighted.
        Behaviors appear in this menu once their passage mappings are published to this bench.</p>
      </div>`;
    updateExportControl();
    return;
  }

  const selected = new Set(state.selectedSlugs);
  elements.behaviourList.innerHTML = groups.map(group => `
    <section class="behaviour-group texture-${group.texture}">
      <h2>${escapeHTML(group.name)}</h2>
      <ul>
        ${group.behaviours.map(behaviour => {
          const checked = selected.has(behaviour.slug);
          const texture = behaviourTexture(behaviour);
          return `
          <li>
            <label class="behaviour-option${checked ? " checked" : ""} texture-${texture}" style="--bh: ${behaviourHue(behaviour)}">
              <input
                class="behaviour-check"
                type="checkbox"
                data-behaviour="${escapeHTML(behaviour.slug)}"
                ${checked ? "checked" : ""}
              >
              <span class="behaviour-box" aria-hidden="true"></span>
              <span class="number">${String(behaviour.id).padStart(2, "0")}</span>
              <span class="name">${escapeHTML(behaviour.name)}</span>
            </label>
          </li>
        `;}).join("")}
      </ul>
    </section>
  `).join("");
  elements.behaviourList.querySelectorAll(".behaviour-check").forEach(input => {
    input.addEventListener("change", () => toggleBehaviour(input.dataset.behaviour, input.checked));
  });
  updateBehaviourCount();
}

function updateBehaviourCount() {
  const total = benchBehaviours().length;
  updateExportControl();
  if (!total) return;
  const chosen = state.selectedSlugs.length;
  elements.behaviourCount.textContent = `${chosen} of ${total} selected`;
  elements.selectAllBehaviours.disabled = chosen === total;
  elements.clearBehaviours.disabled = chosen === 0;
}

/* ---------- taking the reading away ---------- */

/* What the export is for: the passages a behaviour rests on, read away from the reader --
 * pasted into a review, diffed against a later spec version, or annotated by hand. So it
 * carries the whole citation and not just the quote: the definition the passage was read
 * against, the locator that pins it to a section of a pinned spec version, and the role
 * sentence saying why it was picked. Both specifications are written out whichever one is
 * open, because a behaviour's coverage is the pair -- and a spec that maps nothing to it
 * is a finding of the index, so it is named and stated rather than left out. */

function paddedNumber(behaviour) {
  return String(behaviour.id).padStart(2, "0");
}

function selectedPassageTotal() {
  return selectedBehaviours().reduce((total, behaviour) => total
    + (state.payload?.documents || []).reduce(
      (count, doc) => count + (behaviour.coverage?.[doc.id]?.passages.length || 0), 0), 0);
}

function updateExportControl() {
  const behaviours = selectedBehaviours();
  const bench = benchBehaviours().length;
  elements.downloadPassages.disabled = behaviours.length === 0;
  if (!bench) {
    elements.downloadHint.textContent = "";
    return;
  }
  if (!behaviours.length) {
    elements.downloadHint.textContent = "Tick a behavior to export its passages.";
    return;
  }
  const passages = selectedPassageTotal();
  elements.downloadHint.textContent =
    `${behaviours.length} ${behaviours.length === 1 ? "behavior" : "behaviors"}`
    + ` · ${passages} ${passages === 1 ? "passage" : "passages"}, both specs`;
}

/* The reader's own date, not UTC: an export made in the evening is dated the day it was
   made, and the file names of a day's exports sort together. */
function today() {
  const now = new Date();
  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
  ].join("-");
}

/* A quote can run to several lines; every one of them has to carry the marker, or the
 * markdown closes the quotation early and the rest of the passage reads as commentary. */
function blockquote(value) {
  return value
    .trim()
    .split("\n")
    .map(line => `> ${line}`.trimEnd())
    .join("\n");
}

function coverageSummary(coverage) {
  const parts = [];
  if (coverage.verdict) parts.push(`Verdict: ${coverage.verdict}`);
  if (Number.isFinite(coverage.depth)) {
    parts.push(`coverage depth ${coverage.depth} / 4 (${DEPTH_ANCHORS[coverage.depth] || "--"})`);
  }
  if (coverage.verifiedDate) parts.push(`verified ${coverage.verifiedDate}`);
  return parts.join(" · ");
}

function passagesMarkdown() {
  const behaviours = selectedBehaviours();
  const documents = state.payload?.documents || [];
  const lines = [
    "# Reader test -- specification passages",
    "",
    `Exported from the AI Character Index reader test bench on ${today()}.`,
    "",
    `Behaviors: ${behaviours.map(behaviour => `${paddedNumber(behaviour)} ${behaviour.name}`).join(", ")}.`,
    "",
    `Specifications read: ${documents.map(doc => `${doc.lab} · ${doc.title} (${doc.version})`).join("; ")}.`,
    "",
    "Each passage is quoted verbatim from the specification version named above; the locator"
    + " pins it to the section it was read in, and the role sentence records why it was cited.",
  ];

  behaviours.forEach(behaviour => {
    lines.push("", "---", "", `## ${paddedNumber(behaviour)} · ${behaviour.name}`);
    if (behaviour.category) lines.push("", `*${behaviour.category}*`);
    lines.push("", `**Definition.** ${behaviour.definition}`);

    documents.forEach(doc => {
      const coverage = behaviour.coverage?.[doc.id] || NO_COVERAGE;
      lines.push("", `### ${doc.lab} · ${doc.title} (${doc.version})`);
      const summary = coverageSummary(coverage);
      if (summary) lines.push("", summary);
      lines.push("", `Source: ${doc.sourceUrl}`);
      if (coverage.note) lines.push("", `**Coverage note.** ${coverage.note}`);
      if (!coverage.passages.length) {
        lines.push(
          "",
          "No mapped passages in this specification."
          + " Absence of coverage is an index finding, not missing data.",
        );
        return;
      }
      coverage.passages.forEach((passage, index) => {
        lines.push(
          "",
          `#### ${index + 1}. ${passage.adjacent ? "Related" : "Core"} passage`,
          "",
          `\`${passage.locator}\``,
          "",
          blockquote(passage.quote),
          "",
          `**Why this passage.** ${passage.role}`,
        );
      });
    });
  });

  return `${lines.join("\n")}\n`;
}

function exportFilename() {
  const behaviours = selectedBehaviours();
  const subject = behaviours.length === 1
    ? behaviours[0].slug
    : `${behaviours.length}-behaviors`;
  return `reader-test-${subject}-passages-${today()}.md`;
}

function downloadPassages() {
  if (!selectedBehaviours().length) return;
  const blob = new Blob([passagesMarkdown()], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = exportFilename();
  document.body.append(link);
  link.click();
  link.remove();
  // Held open until the browser has taken the blob, then released.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

elements.downloadPassages.addEventListener("click", downloadPassages);

function behaviourChip(behaviour) {
  return `<span class="behaviour-chip" style="--bh: ${behaviourHue(behaviour)}">${escapeHTML(behaviour.name)}</span>`;
}

function updateFindingBar(overlaps = null) {
  const behaviours = selectedBehaviours();
  if (!behaviours.length) {
    const bench = benchBehaviours().length;
    elements.findingBehaviour.textContent = bench ? "No behaviors selected" : "No behavior under test";
    elements.findingDefinition.textContent = bench
      ? "Both specifications are shown in full. Tick a behavior in the menu to highlight the passages that bear on it."
      : "Reading both specifications in full -- nothing is highlighted until a behavior is published to this bench.";
    return;
  }

  elements.findingBehaviour.innerHTML = behaviours.map(behaviourChip).join("");
  if (behaviours.length === 1) {
    elements.findingDefinition.textContent = behaviours[0].definition;
    return;
  }
  const shared = overlaps === null
    ? ""
    : ` · ${overlaps} ${overlaps === 1 ? "passage is" : "passages are"} cited by more than one`;
  elements.findingDefinition.textContent = `${behaviours.length} behaviors read over the same text${shared}.`;
}

/* Ticking or unticking never re-renders the specification, only its highlight layer, so
 * the reader keeps its place in the text while a behaviour is added or taken away. */
function setSelection(slugs) {
  const order = benchBehaviours().map(behaviour => behaviour.slug);
  const chosen = new Set(slugs);
  state.selectedSlugs = order.filter(slug => chosen.has(slug));

  elements.behaviourList.querySelectorAll(".behaviour-check").forEach(input => {
    const on = chosen.has(input.dataset.behaviour);
    input.checked = on;
    input.closest(".behaviour-option").classList.toggle("checked", on);
  });
  updateBehaviourCount();
  syncURL();
  applyHighlights();
}

function toggleBehaviour(slug, checked) {
  const next = new Set(state.selectedSlugs);
  if (checked) next.add(slug);
  else next.delete(slug);
  setSelection([...next]);
}

function escapeHTML(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function plainHeadingTitle(source) {
  return source
    .replace(/\[\^([^\]]+)\]/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_`]/g, "")
    .replace(/<[^>]+>/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function generatedHeadingAnchor(source) {
  return plainHeadingTitle(source)
    .toLocaleLowerCase()
    .trim()
    .replace(/\s+/g, "-");
}

function buildHeadingIndex(markdown) {
  const headings = new Map();
  markdown.replace(/\r\n/g, "\n").split("\n").forEach(line => {
    const heading = headingDetails(line);
    if (!heading) return;
    const anchor = heading.id || generatedHeadingAnchor(heading.text);
    if (anchor && !headings.has(anchor)) {
      headings.set(anchor, plainHeadingTitle(heading.text));
    }
  });
  return headings;
}

function scopedAnchor(prefix, anchor) {
  return `${prefix}--${anchor}`;
}

function applyInlineFormatting(value) {
  return value
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>")
    .replace(/(?<!_)_([^_\n]+)_(?!_)/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function inlineMarkdown(source, context) {
  let value = source
    .replace(/\[\^[^\]]+\]/g, "")
    .replace(/\{#[^}]+\}/g, "");
  value = escapeHTML(value);
  const renderedLinks = [];
  value = value.replace(
    /\[([^\]]+)\]\((https?:\/\/[^)\s]+|#[^)\s]+)\)/g,
    (match, label, href) => {
      let renderedLink;
      if (!href.startsWith("#")) {
        renderedLink = `<a href="${href}">${applyInlineFormatting(label)}</a>`;
      } else {
        const target = href.slice(1);
        const title = context?.headings.get(target);
        const placeholder = /^\s*\?\s*$/.test(label);
        const renderedLabel = placeholder && title
          ? escapeHTML(title)
          : applyInlineFormatting(label);
        const renderedHref = context
          ? `#${scopedAnchor(context.idPrefix, target)}`
          : href;
        const ariaLabel = placeholder && title
          ? ` aria-label="See section: ${escapeHTML(title)}"`
          : "";
        renderedLink = `<a href="${escapeHTML(renderedHref)}"${ariaLabel}>${renderedLabel}</a>`;
      }

      const token = `\uE000${renderedLinks.length}\uE001`;
      renderedLinks.push(renderedLink);
      return token;
    },
  );
  value = applyInlineFormatting(value);
  return value.replace(/\uE000(\d+)\uE001/g, (match, index) => renderedLinks[Number(index)]);
}

function renderCodeBlock(source, context) {
  return escapeHTML(source).replace(
    /\[([^\]]+)\]\(#([^)\s]+)\)/g,
    (match, label, target) => {
      const title = context?.headings.get(target);
      const placeholder = /^\s*\?\s*$/.test(label);
      const renderedLabel = placeholder && title ? escapeHTML(title) : label;
      const renderedHref = context
        ? `#${scopedAnchor(context.idPrefix, target)}`
        : `#${target}`;
      const ariaLabel = placeholder && title
        ? ` aria-label="See section: ${escapeHTML(title)}"`
        : "";
      return `<a href="${escapeHTML(renderedHref)}"${ariaLabel}>${renderedLabel}</a>`;
    },
  );
}

function headingDetails(line) {
  const match = line.match(/^(#{1,6})\s+(.+)$/);
  if (!match) return null;
  const attrs = match[2].match(/\{#([^\s}]+)[^}]*\}\s*$/);
  return {
    level: match[1].length,
    text: match[2].replace(/\s*\{#[^}]+\}\s*$/, ""),
    id: attrs?.[1] || "",
  };
}

function isSpecialLine(lines, index) {
  const line = lines[index];
  return (
    !line.trim()
    || headingDetails(line)
    || /^(~~~|```)/.test(line)
    || /^!!!\s/.test(line)
    || /^>\s?/.test(line)
    || /^\s*([-*+]|\d+\.)\s+/.test(line)
    || /^\s*\|/.test(line)
    || /^-{3,}\s*$/.test(line)
  );
}

function renderMarkdown(markdown, context) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const output = [];
  let blockNumber = 0;
  const blockAttr = () => `data-block="${++blockNumber}"`;
  const usedHeadingIds = context?.usedHeadingIds || new Map();

  for (let index = 0; index < lines.length;) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    const heading = headingDetails(line);
    if (heading) {
      const anchor = heading.id || generatedHeadingAnchor(heading.text);
      const occurrence = (usedHeadingIds.get(anchor) || 0) + 1;
      usedHeadingIds.set(anchor, occurrence);
      const uniqueAnchor = occurrence === 1 ? anchor : `${anchor}--${occurrence}`;
      const id = anchor
        ? ` id="${escapeHTML(scopedAnchor(context.idPrefix, uniqueAnchor))}"`
        : "";
      output.push(`<h${heading.level} ${blockAttr()}${id}>${inlineMarkdown(heading.text, context)}</h${heading.level}>`);
      index += 1;
      continue;
    }

    const fence = line.match(/^(~~~|```)(.*)$/);
    if (fence) {
      const marker = fence[1];
      const language = fence[2].trim();
      const content = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith(marker)) {
        content.push(lines[index]);
        index += 1;
      }
      index += 1;
      output.push(`<pre class="code-block" ${blockAttr()} data-language="${escapeHTML(language)}">${renderCodeBlock(content.join("\n"), context)}</pre>`);
      continue;
    }

    const admonition = line.match(/^!!!\s+(\w+)(?:\s+"([^"]+)")?/);
    if (admonition) {
      const content = [];
      index += 1;
      while (index < lines.length && (!lines[index].trim() || /^\s{4}/.test(lines[index]))) {
        content.push(lines[index].replace(/^\s{4}/, ""));
        index += 1;
      }
      output.push(`
        <aside class="admonition" ${blockAttr()}>
          <div class="admonition-label">${inlineMarkdown(admonition[2] || admonition[1], context)}</div>
          ${renderMarkdown(content.join("\n"), context)}
        </aside>
      `);
      continue;
    }

    if (/^>\s?/.test(line)) {
      const content = [];
      while (index < lines.length && (/^>\s?/.test(lines[index]) || !lines[index].trim())) {
        content.push(lines[index].replace(/^>\s?/, ""));
        index += 1;
      }
      output.push(`<blockquote ${blockAttr()}>${renderMarkdown(content.join("\n"), context)}</blockquote>`);
      continue;
    }

    const listMatch = line.match(/^\s*([-*+]|\d+\.)\s+(.+)$/);
    if (listMatch) {
      const ordered = /\d+\./.test(listMatch[1]);
      const tag = ordered ? "ol" : "ul";
      const items = [];
      while (index < lines.length) {
        const item = lines[index].match(/^\s*([-*+]|\d+\.)\s+(.+)$/);
        if (!item || /\d+\./.test(item[1]) !== ordered) break;
        items.push(`<li ${blockAttr()}>${inlineMarkdown(item[2], context)}</li>`);
        index += 1;
      }
      output.push(`<${tag}>${items.join("")}</${tag}>`);
      continue;
    }

    if (/^\s*\|/.test(line)) {
      const tableLines = [];
      while (index < lines.length && /^\s*\|/.test(lines[index])) {
        tableLines.push(lines[index]);
        index += 1;
      }
      output.push(`<pre class="raw-table" ${blockAttr()}>${escapeHTML(tableLines.join("\n"))}</pre>`);
      continue;
    }

    if (/^-{3,}\s*$/.test(line)) {
      output.push("<hr>");
      index += 1;
      continue;
    }

    const paragraph = [line.trim()];
    index += 1;
    while (index < lines.length && !isSpecialLine(lines, index)) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    output.push(`<p ${blockAttr()}>${inlineMarkdown(paragraph.join(" "), context)}</p>`);
  }

  return output.join("\n");
}

function normalize(value) {
  return value
    .normalize("NFKD")
    .toLocaleLowerCase()
    .replace(/&(?:amp|quot|#39);/g, " ")
    .replace(/[*_`[\]{}()<>]/g, " ")
    .replace(/[’‘“”"'—–-]/g, " ")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/* Two places where resolver output and rendered text legitimately differ, so the
 * quote has to be matched in pieces rather than as one literal run:
 *
 *   - an admonition opens "!!! meta "Commentary"" in the source and in the
 *     resolver's output, while the reader renders the label alone;
 *   - a cross-reference is written "[?](#letter_and_spirit)" in the source and
 *     resolved to "#letter_and_spirit", while the reader renders the title of
 *     the section it points at.
 *
 * Dropping the marker and splitting on the references leaves fragments that are
 * identical on both sides and must appear, in order, inside one block. A quote
 * with neither feature yields a single fragment, i.e. the whole normalized quote. */
function passageFragments(quote) {
  return quote
    .replace(/^!!!\s+\w+\s*/, "")
    .split(/#[A-Za-z0-9_]+/)
    .map(normalize)
    .filter(Boolean);
}

function containsInOrder(haystack, fragments) {
  let cursor = 0;
  for (const fragment of fragments) {
    const at = haystack.indexOf(fragment, cursor);
    if (at < 0) return false;
    cursor = at + fragment.length;
  }
  return true;
}

function findPassageBlocks(body, passage) {
  const needle = normalize(passage.quote);
  const fragments = passageFragments(passage.quote);
  const blocks = [...body.querySelectorAll("[data-block]")];
  const exact = blocks.find(block => containsInOrder(normalize(block.textContent), fragments));
  if (exact) return { anchor: exact, continuation: [] };

  // A whole-block citation can flatten a labelled list cluster (a bold intro
  // plus its nested items) into one resolver line, while the reader renders
  // each item as its own block. Match the needle across a run of consecutive
  // blocks, anchoring the first and highlighting the rest as continuation.
  const texts = blocks.map(block => normalize(block.textContent));
  for (let start = 0; start < blocks.length; start += 1) {
    if (!texts[start] || !needle.startsWith(texts[start])) continue;
    let combined = texts[start];
    const run = [blocks[start]];
    for (let next = start + 1; next < blocks.length && combined.length < needle.length; next += 1) {
      combined = `${combined} ${texts[next]}`;
      if (!needle.startsWith(combined) && !combined.startsWith(needle)) break;
      run.push(blocks[next]);
    }
    if (combined.startsWith(needle) && run.length > 1) {
      return { anchor: run[0], continuation: run.slice(1) };
    }
  }

  // Last resort for a passage the two paths above both miss: the opening clause
  // of its first fragment is the longest run of the quote that no rendering
  // difference can reach, and stays stable for a pinned spec version.
  const opening = (fragments[0] || needle).split(" ").slice(0, 18).join(" ");
  const fallback = blocks.find(block => normalize(block.textContent).includes(opening));
  return fallback ? { anchor: fallback, continuation: [] } : null;
}

/* The example a passage introduces is rendered as its own code block, which the citation
 * does not quote; it is highlighted as continuation of the passage that announces it. */
function followingExampleBlock(block) {
  let next = block.nextElementSibling;
  while (next && !next.classList.contains("code-block")) {
    if (/^H[1-6]$/.test(next.tagName)) return null;
    next = next.nextElementSibling;
  }
  return next?.classList.contains("code-block") ? next : null;
}

/* One wash per behaviour on the block, blended left to right where several land on the
 * same passage. Core carries the colour at full strength, related the same colour thinned;
 * the alphas are palette variables so daylight and umber can weigh the tint differently. */
function tintGradient(marks, strong) {
  const suffix = strong ? "-strong" : "";
  const colors = marks.map(mark =>
    `rgb(${mark.hue} / var(--tint-${mark.adjacent ? "related" : "core"}${suffix}))`);
  if (colors.length === 1) return `linear-gradient(${colors[0]}, ${colors[0]})`;
  const step = 100 / (colors.length - 1);
  return `linear-gradient(100deg, ${colors.map((color, index) => `${color} ${Math.round(index * step)}%`).join(", ")})`;
}

/* The margin rules: one per behaviour, side by side, so a shared passage is legible as
 * two or three behaviours at a glance rather than as one indeterminate blend. One layer
 * per behaviour rather than one gradient across all of them, because a stippled group's
 * rule is broken down its length -- the same reading as its dotted wash, at rule width. */
function gutterRules(marks) {
  const bar = marks.length > 4 ? 1 : 2;
  const pitch = bar + 1;
  const dash = bar > 1 ? 3 : 2;
  const layers = [];
  const sizes = [];
  const positions = [];
  marks.forEach((mark, index) => {
    const color = `rgb(${mark.hue} / var(--rule-${mark.adjacent ? "related" : "core"}))`;
    layers.push(mark.texture === "stipple"
      ? `repeating-linear-gradient(to bottom, ${color} 0 ${dash}px, transparent ${dash}px ${dash * 2}px)`
      : `linear-gradient(${color}, ${color})`);
    sizes.push(`${bar}px 100%`);
    positions.push(`${index * pitch}px 0`);
  });
  return {
    image: layers.join(", "),
    size: sizes.join(", "),
    position: positions.join(", "),
    width: marks.length * pitch - 1,
  };
}

/* The same reading, banded down the height of a 4px rail mark. */
function railTint(marks) {
  const colors = marks.map(mark =>
    `rgb(${mark.hue} / var(--rule-${mark.adjacent ? "related" : "core"}))`);
  if (colors.length === 1) return `linear-gradient(${colors[0]}, ${colors[0]})`;
  const step = 100 / colors.length;
  return `linear-gradient(to bottom, ${colors
    .map((color, index) => `${color} ${index * step}% ${(index + 1) * step}%`)
    .join(", ")})`;
}

/* The strip above an anchored passage. It names the behaviours that cite the passage and
 * nothing else: the role sentences are the reason a passage was picked, not part of reading
 * it, and set above every highlight they crowded the specification off the page. They move
 * behind the question mark at the right of the strip, one per anchored passage.
 *
 * Every element here is inline, because a block is whatever the markdown made it -- often a
 * <p>, where insertAdjacentHTML would drop a <div> straight back out again. */
function passageLabels(marks, passageId) {
  const naming = marks.filter(mark => mark.anchored.length);
  const chips = naming.map(mark => `
    <span class="passage-label" style="--bh: ${mark.hue}">
      <span class="passage-label-behaviour">${escapeHTML(mark.behaviour.name)}</span>
    </span>
  `).join("");
  // One reason needs no name: the strip above it already carries the only behaviour there is.
  const pairs = naming.flatMap(mark => mark.anchored.map(passage => ({ mark, passage })));
  const reasons = pairs.map(({ mark, passage }) => `
    <span class="passage-reason" style="--bh: ${mark.hue}">
      ${pairs.length > 1
        ? `<span class="passage-reason-behaviour">${escapeHTML(mark.behaviour.name)}</span>`
        : ""}
      <span class="passage-reason-role">${passage.adjacent ? "Related · " : ""}${
        applyInlineFormatting(escapeHTML(passage.role))}</span>
    </span>
  `).join("");
  const panelId = `${passageId}-why`;
  return `
    <span class="passage-head">
      ${chips}
      <button type="button" class="passage-why" aria-expanded="false" aria-controls="${panelId}"
        aria-label="Why was this passage selected?" data-tip="Why was this passage selected?">?</button>
    </span>
    <span class="passage-rationale" id="${panelId}" role="note" hidden>${reasons}</span>
  `;
}

/* Opening a rationale changes the height of the block it sits in, so the rail marks -- which
 * are positioned from block offsets -- have to be measured again once it has laid out. */
function setupPassageDisclosure(panel) {
  panel.querySelector(".document-body").addEventListener("click", event => {
    const button = event.target.closest(".passage-why");
    if (!button) return;
    const panelEl = panel.querySelector(`#${CSS.escape(button.getAttribute("aria-controls"))}`);
    if (!panelEl) return;
    const open = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!open));
    panelEl.hidden = open;
    requestAnimationFrame(updateRails);
  });
}

/* Strip every trace of the previous selection, so the next one can be laid over text that
 * reads exactly as the specification does -- passage matching runs against textContent. */
function clearHighlights(panel) {
  const body = panel.querySelector(".document-body");
  body.querySelectorAll(".passage-head, .passage-rationale").forEach(part => part.remove());
  body.querySelectorAll(":scope > .zero-coverage").forEach(note => note.remove());
  body.querySelectorAll(".passage").forEach(block => {
    block.classList.remove("passage", "passage-continuation", "adjacent", "passage-overlap", "current");
    ["passageId", "documentId", "passageNumber", "role", "behaviours"]
      .forEach(key => { delete block.dataset[key]; });
    ["--tint", "--tint-strong", "--gutter", "--gutter-size", "--gutter-pos",
      "--gutter-width", "--bh-primary"]
      .forEach(property => block.style.removeProperty(property));
    delete block._railTint;
  });
}

function annotatePassages(panel, doc) {
  const body = panel.querySelector(".document-body");
  const missing = [];
  const contributions = new Map();
  const record = (block, behaviour, passage, anchored) => {
    if (!contributions.has(block)) contributions.set(block, []);
    contributions.get(block).push({ behaviour, passage, anchored });
  };

  // Collected for every ticked behaviour before anything is painted: the labels this pass
  // inserts would otherwise sit inside the text the next behaviour's quote is matched against.
  selectedBehaviours().forEach(behaviour => {
    const coverage = behaviour.coverage?.[doc.id] || NO_COVERAGE;
    coverage.passages.forEach(passage => {
      const found = findPassageBlocks(body, passage);
      if (!found) {
        missing.push(passage.locator);
        return;
      }
      record(found.anchor, behaviour, passage, true);
      found.continuation.forEach(extra => record(extra, behaviour, passage, false));
      if (passage.exampleBlock) {
        const example = followingExampleBlock(found.anchor);
        if (example) record(example, behaviour, passage, false);
      }
    });
  });

  const behaviours = selectedBehaviours();
  const blocks = [...body.querySelectorAll("[data-block]")].filter(block => contributions.has(block));
  let overlaps = 0;
  let number = 0;

  blocks.forEach(block => {
    const items = contributions.get(block);
    const marks = behaviours
      .map(behaviour => {
        const own = items.filter(item => item.behaviour === behaviour);
        if (!own.length) return null;
        return {
          behaviour,
          hue: behaviourHue(behaviour),
          texture: behaviourTexture(behaviour),
          adjacent: own.every(item => item.passage.adjacent),
          anchored: own.filter(item => item.anchored).map(item => item.passage),
        };
      })
      .filter(Boolean);

    const anchored = marks.some(mark => mark.anchored.length);
    const gutter = gutterRules(marks);
    if (marks.length > 1) overlaps += 1;

    block.classList.add("passage");
    block.classList.toggle("adjacent", marks.every(mark => mark.adjacent));
    block.classList.toggle("passage-continuation", !anchored);
    block.classList.toggle("passage-overlap", marks.length > 1);
    block.style.setProperty("--tint", tintGradient(marks, false));
    block.style.setProperty("--tint-strong", tintGradient(marks, true));
    block.style.setProperty("--gutter", gutter.image);
    block.style.setProperty("--gutter-size", gutter.size);
    block.style.setProperty("--gutter-pos", gutter.position);
    block.style.setProperty("--gutter-width", `${gutter.width}px`);
    block.style.setProperty("--bh-primary", marks[0].hue);
    if (!anchored) return;

    number += 1;
    block.dataset.passageId = `${doc.id}-passage-${number}`;
    block.dataset.documentId = doc.id;
    block.dataset.passageNumber = String(number);
    block.dataset.behaviours = marks.map(mark => mark.behaviour.name).join(" · ");
    block.dataset.role = marks
      .flatMap(mark => mark.anchored.map(passage => passage.role))
      .join(" · ");
    block._railTint = railTint(marks);
    block.insertAdjacentHTML("afterbegin", passageLabels(marks, block.dataset.passageId));
  });

  return { missing, overlaps };
}

function addContentsSection(body) {
  const children = [...body.children];
  const titleIndex = children.findIndex(child => child.tagName === "H1");
  const firstSectionIndex = children.findIndex((child, index) => index > titleIndex && child.tagName === "H2");
  if (titleIndex < 0 || firstSectionIndex < 0) return;

  const opening = children.slice(titleIndex + 1, firstSectionIndex);
  const linkedRows = opening.filter(child => child.matches("p") && child.querySelector(":scope > a"));
  if (opening.length < 8 || linkedRows.length / opening.length < .7) return;

  const heading = document.createElement("h2");
  heading.dataset.block = "contents";
  heading.dataset.syntheticSection = "true";
  heading.textContent = "Document contents";
  body.insertBefore(heading, opening[0]);
}

function panelFocused(panel) {
  return highlightsActive() && Boolean(state.documentFocus[panel.dataset.documentId]);
}

function updateSectionVisibility(panel) {
  const focused = panelFocused(panel);
  const infos = panel._sectionInfos || [];

  infos.forEach(info => {
    info.heading.classList.toggle("section-collapsed", info.collapsed);
    info.button.setAttribute("aria-expanded", String(!info.collapsed));
  });

  [...panel.querySelector(".document-body").children].forEach(child => {
    const ancestors = child._sectionAncestors || [];
    child.hidden = ancestors.some(info => info.collapsed);
  });

  const toggle = panel.querySelector(".document-focus-toggle");
  toggle.textContent = focused ? "Expand all" : "Focus highlights";
  toggle.setAttribute("aria-pressed", String(!focused));
}

/* Focus mode is re-applied whenever the selection changes, so the sections a document
 * opens on follow the behaviours currently ticked. With focus off, sections the reader
 * collapsed by hand are left alone -- unless nothing is highlighted at all, when the
 * toggle is hidden and everything has to be readable again. */
function applyPanelFocus(panel, { expandAll = false } = {}) {
  const focused = panelFocused(panel);
  const infos = panel._sectionInfos || [];
  if (focused) infos.forEach(info => { info.collapsed = !info.hasPassage; });
  else if (expandAll || !highlightsActive()) infos.forEach(info => { info.collapsed = false; });
  updateSectionVisibility(panel);
  requestAnimationFrame(updateRails);
}

/* Which sections carry a highlight changes with every tick of the menu. */
function refreshSectionPassages(panel) {
  const children = [...panel.querySelector(".document-body").children];
  (panel._sectionInfos || []).forEach(info => {
    info.hasPassage = children.some(child => {
      if (!(child._sectionAncestors || []).includes(info)) return false;
      return child.matches(".passage") || Boolean(child.querySelector(".passage"));
    });
    info.heading.classList.toggle("section-has-passage", info.hasPassage);
  });
  applyPanelFocus(panel);
}

function setupSectionFocus(panel) {
  const body = panel.querySelector(".document-body");
  addContentsSection(body);
  const children = [...body.children];
  const stack = [];
  const infos = [];

  children.forEach(child => {
    const headingMatch = child.tagName.match(/^H([2-5])$/);
    if (headingMatch) {
      const level = Number(headingMatch[1]);
      while (stack.length && stack.at(-1).level >= level) stack.pop();

      const title = child.textContent.trim();
      const button = document.createElement("button");
      button.className = "section-heading-button";
      button.type = "button";
      button.innerHTML = `<span class="section-title">${child.innerHTML}</span><span class="section-chevron" aria-hidden="true">▾</span>`;
      button.setAttribute("aria-label", `${title}: toggle section`);
      child.replaceChildren(button);
      child.classList.add("section-heading");

      const info = {
        heading: child,
        button,
        level,
        title,
        ancestors: [...stack],
        hasPassage: false,
        collapsed: false,
      };
      child._sectionAncestors = [...stack];
      infos.push(info);
      stack.push(info);
      return;
    }
    child._sectionAncestors = [...stack];
  });

  infos.forEach(info => {
    info.button.addEventListener("click", () => {
      info.collapsed = !info.collapsed;
      updateSectionVisibility(panel);
      requestAnimationFrame(updateRails);
    });
  });

  panel._sectionInfos = infos;
  panel.querySelector(".document-focus-toggle").addEventListener("click", () => {
    const next = !panelFocused(panel);
    state.documentFocus[panel.dataset.documentId] = next;
    applyPanelFocus(panel, { expandAll: !next });
  });
}

function revealInternalTarget(panel, heading, shouldUpdateHash = true) {
  const body = panel.querySelector(".document-body");
  let sectionChild = heading;
  while (sectionChild.parentElement && sectionChild.parentElement !== body) {
    sectionChild = sectionChild.parentElement;
  }
  (sectionChild._sectionAncestors || []).forEach(info => { info.collapsed = false; });
  updateSectionVisibility(panel);

  const scroll = panel.querySelector(".document-scroll");
  const top = heading.getBoundingClientRect().top
    - scroll.getBoundingClientRect().top
    + scroll.scrollTop
    - 32;
  heading.setAttribute("tabindex", "-1");
  heading.focus({ preventScroll: true });
  scroll.scrollTo({
    top: Math.max(0, top),
    behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
  });

  if (shouldUpdateHash) {
    history.replaceState(null, "", `${location.pathname}${location.search}#${heading.id}`);
  }
  requestAnimationFrame(updateRails);
}

function setupInternalLinks(panel) {
  panel.querySelector(".document-body").addEventListener("click", event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;
    const id = link.getAttribute("href").slice(1);
    const heading = panel.querySelector(`#${CSS.escape(id)}`);
    if (!heading) return;
    event.preventDefault();
    revealInternalTarget(panel, heading);
  });
}

function revealHashTarget() {
  const id = decodeURIComponent(location.hash.slice(1));
  if (!id) return;
  const heading = elements.documentReader.querySelector(`#${CSS.escape(id)}`);
  const panel = heading?.closest(".document-panel");
  if (heading && panel) revealInternalTarget(panel, heading, false);
}

function renderDocument(doc) {
  const panel = elements.template.content.firstElementChild.cloneNode(true);
  const markdownContext = {
    headings: buildHeadingIndex(doc.markdown),
    idPrefix: doc.id,
    usedHeadingIds: new Map(),
  };
  panel.dataset.documentId = doc.id;
  panel.querySelector(".document-lab").textContent = doc.lab;
  panel.querySelector(".document-title").textContent = doc.title;
  panel.querySelector(".document-version").textContent = `Version ${doc.version}`;
  panel.querySelector(".document-body").innerHTML = renderMarkdown(doc.markdown, markdownContext);
  setupSectionFocus(panel);
  setupInternalLinks(panel);
  setupPassageDisclosure(panel);
  return panel;
}

/* The coverage line reads one behaviour's depth verdict; over several it reads the range,
 * because a set of behaviours has no single depth and averaging them would invent one. */
function coverageDepthLine(doc) {
  const depths = selectedBehaviours()
    .map(behaviour => behaviour.coverage?.[doc.id]?.depth)
    .filter(depth => Number.isFinite(depth));
  if (!depths.length) return "";
  const low = Math.min(...depths);
  const high = Math.max(...depths);
  if (low === high) {
    return `Coverage depth ${low} / 4 · ${DEPTH_ANCHORS[low] ?? ""}`
      + (depths.length > 1 ? ` · all ${depths.length}` : "");
  }
  return `Coverage depth ${low}–${high} / 4 · ${depths.length} behaviors`;
}

function updatePanelMeta(panel, doc) {
  const tracking = highlightsActive();
  const depth = panel.querySelector(".coverage-depth");
  depth.textContent = tracking ? coverageDepthLine(doc) : "";
  depth.hidden = !tracking;
  panel.querySelector(".rail-legend").hidden = !tracking;
  panel.querySelector(".document-focus-toggle").hidden = !tracking;

  // Counted from the published set, not from what resolved: a passage that failed to
  // anchor is an unresolved-anchor warning, not an absence of coverage.
  const published = selectedBehaviours()
    .reduce((total, behaviour) => total + (behaviour.coverage?.[doc.id]?.passages.length || 0), 0);
  if (tracking && published === 0) {
    const several = selectedBehaviours().length > 1;
    panel.querySelector(".document-body").insertAdjacentHTML(
      "afterbegin",
      `<div class="zero-coverage" role="note">
        <strong>${several
          ? "None of the selected behaviors map to a passage in this specification."
          : "No mapped passages in this specification."}</strong>
        <span>Absence of coverage is an index finding, not missing data.</span>
      </div>`,
    );
  }
}

/* Lay the current selection over documents that are already rendered. Nothing here
 * touches the specification text, so ticking a behaviour cannot move the reader. */
function applyHighlights() {
  const previous = state.anchors[state.passageIndex] || null;
  const panels = [...elements.documentReader.querySelectorAll(".document-panel")];
  const missing = [];
  let overlaps = 0;

  panels.forEach(panel => {
    const doc = state.payload.documents.find(item => item.id === panel.dataset.documentId);
    clearHighlights(panel);
    const annotated = annotatePassages(panel, doc);
    missing.push(...annotated.missing);
    overlaps += annotated.overlaps;
    updatePanelMeta(panel, doc);
    refreshSectionPassages(panel);
  });

  elements.readerStatus.classList.toggle("visible", missing.length > 0);
  elements.readerStatus.textContent = missing.length
    ? `${missing.length} cached passage ${missing.length === 1 ? "anchor could" : "anchors could"} not be resolved against this document version.`
    : "";
  updateFindingBar(overlaps);

  requestAnimationFrame(() => {
    collectAnchors();
    updateRails();
    // Hold the reader's place: the passage it was on keeps the cursor if it survived
    // the change of selection, and nothing scrolls if it did not.
    const index = previous ? state.anchors.indexOf(previous) : -1;
    focusPassage(Math.max(0, index), false);
  });
}

function visibleDocuments() {
  if (state.comparing) return state.payload.documents;
  return [state.payload.documents.find(doc => doc.id === state.selectedSpec)];
}

function rebuildReader() {
  elements.documentReader.classList.toggle("compare", state.comparing);
  const panels = visibleDocuments().map(renderDocument);
  const children = state.comparing
    ? [panels[0], createDocumentResizer(), panels[1]]
    : panels;
  elements.documentReader.replaceChildren(...children);
  if (state.comparing) setCompareFirst(state.compareFirst);
  state.passageIndex = 0;
  state.anchors = [];

  const selected = state.payload.documents.find(doc => doc.id === state.selectedSpec);
  elements.sourceLink.href = selected.sourceUrl;
  elements.sourceLink.textContent = state.comparing ? "Sources ↗" : "Original ↗";

  document.querySelectorAll(".spec-option").forEach(option => {
    option.classList.toggle("active", option.dataset.spec === state.selectedSpec);
    option.setAttribute("aria-pressed", String(option.dataset.spec === state.selectedSpec));
  });

  applyHighlights();
  requestAnimationFrame(revealHashTarget);
}

function collectAnchors() {
  state.anchors = [...elements.documentReader.querySelectorAll("[data-passage-id]")];
  elements.previousPassage.disabled = state.anchors.length === 0;
  elements.nextPassage.disabled = state.anchors.length === 0;

  if (!state.anchors.length) {
    if (!benchBehaviours().length) elements.passageCount.textContent = "No behaviors under test";
    else if (!highlightsActive()) elements.passageCount.textContent = "No behaviors selected";
    else if (state.comparing) elements.passageCount.textContent = "No passages in either spec";
    else elements.passageCount.textContent = "No passages in this spec";
  }
}

function updatePassageCount() {
  const total = state.anchors.length;
  if (!total) return;
  const current = state.anchors[state.passageIndex];
  const panel = current.closest(".document-panel");
  const lab = panel.querySelector(".document-lab").textContent;
  elements.passageCount.textContent = state.comparing
    ? `${lab} · ${state.passageIndex + 1} of ${total}`
    : `${state.passageIndex + 1} of ${total} passages`;
}

function updateRails() {
  document.querySelectorAll(".document-panel").forEach(panel => {
    const body = panel.querySelector(".document-body");
    const rail = panel.querySelector(".passage-rail");
    const anchors = [...panel.querySelectorAll("[data-passage-id]")];
    rail.replaceChildren(...anchors.map((anchor, localIndex) => {
      const overlap = anchor.classList.contains("passage-overlap");
      const mark = document.createElement("button");
      mark.type = "button";
      mark.className = "rail-mark"
        + (anchor.classList.contains("adjacent") ? " adjacent" : "")
        + (overlap ? " overlap" : "");
      mark.dataset.forPassage = anchor.dataset.passageId;
      mark.style.setProperty("--rail", anchor._railTint || "");
      mark.style.top = `${Math.min(98, (anchor.offsetTop / body.scrollHeight) * 100)}%`;
      mark.style.height = `max(5px, ${(anchor.offsetHeight / body.scrollHeight) * 100}%)`;
      mark.setAttribute(
        "aria-label",
        `${overlap ? "Shared" : anchor.classList.contains("adjacent") ? "Related" : "Core"}`
        + ` passage ${localIndex + 1}, ${anchor.dataset.behaviours}: ${anchor.dataset.role}`,
      );
      mark.title = `${anchor.dataset.behaviours} · ${anchor.dataset.role}`;
      mark.addEventListener("click", () => focusPassage(state.anchors.indexOf(anchor)));
      return mark;
    }));
  });
}

function focusPassage(index, shouldScroll = true) {
  if (!state.anchors.length) return;
  state.passageIndex = (index + state.anchors.length) % state.anchors.length;
  document.querySelectorAll(".passage.current, .rail-mark.current").forEach(item => item.classList.remove("current"));

  const anchor = state.anchors[state.passageIndex];
  const body = anchor.closest(".document-body");
  let sectionChild = anchor;
  while (sectionChild.parentElement && sectionChild.parentElement !== body) {
    sectionChild = sectionChild.parentElement;
  }
  const panel = anchor.closest(".document-panel");
  (sectionChild._sectionAncestors || []).forEach(info => { info.collapsed = false; });
  updateSectionVisibility(panel);
  anchor.classList.add("current");
  document
    .querySelector(`.rail-mark[data-for-passage="${CSS.escape(anchor.dataset.passageId)}"]`)
    ?.classList.add("current");

  if (shouldScroll) {
    anchor.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  updatePassageCount();
}

document.querySelectorAll(".spec-option").forEach(option => {
  option.addEventListener("click", () => {
    state.selectedSpec = option.dataset.spec;
    if (state.comparing) {
      state.comparing = false;
      elements.compareToggle.setAttribute("aria-pressed", "false");
    }
    syncURL();
    rebuildReader();
  });
});

elements.selectAllBehaviours.addEventListener("click", () => {
  setSelection(benchBehaviours().map(behaviour => behaviour.slug));
});
elements.clearBehaviours.addEventListener("click", () => setSelection([]));

elements.compareToggle.addEventListener("click", () => {
  state.comparing = !state.comparing;
  elements.compareToggle.setAttribute("aria-pressed", String(state.comparing));
  syncURL();
  rebuildReader();
});

elements.previousPassage.addEventListener("click", () => focusPassage(state.passageIndex - 1));
elements.nextPassage.addEventListener("click", () => focusPassage(state.passageIndex + 1));

document.addEventListener("keydown", event => {
  // Text entry keeps its keys; a checkbox in the behaviour menu does not, so j and k
  // still walk the passages while the reader is ticking behaviours from the keyboard.
  if (event.target.matches("textarea, select, input:not([type=checkbox])")) return;
  if (event.key === "Escape" && state.embedded) {
    window.parent.postMessage({ type: "aci-spec-reader-close" }, location.origin);
    return;
  }
  if (event.key === "j") focusPassage(state.passageIndex + 1);
  if (event.key === "k") focusPassage(state.passageIndex - 1);
});

window.addEventListener("resize", () => {
  setSidebarWidth(state.sidebarWidth);
  if (state.comparing) setCompareFirst(state.compareFirst);
  requestAnimationFrame(updateRails);
});

async function loadJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);
  return response.json();
}

async function initialize() {
  renderBehaviourList();
  try {
    const [documents, behaviours] = await Promise.all([
      loadJSON(DOCUMENTS_URL),
      loadJSON(BEHAVIOURS_URL),
    ]);
    state.payload = {
      documents: documents.documents,
      behaviours: behaviours.behaviours || [],
    };
    const bench = state.payload.behaviours;
    state.documentFocus = { anthropic: bench.length > 0, openai: bench.length > 0 };
    const params = initialParams;
    // ?behavior= takes one slug or a comma-separated list; with none given the reader
    // opens on the first behaviour of the set, as the single-choice menu used to.
    const requested = (params.get("behavior") || "")
      .split(",")
      .map(slug => slug.trim())
      .filter(slug => bench.some(behaviour => behaviour.slug === slug));
    if (requested.length) state.selectedSlugs = requested;
    else if (!params.has("behavior") && bench.length) state.selectedSlugs = [bench[0].slug];

    const requestedSpec = params.get("spec");
    if (state.payload.documents.some(document => document.id === requestedSpec)) {
      state.selectedSpec = requestedSpec;
    }
    state.comparing = params.get("compare") === "1";
    state.compareFirst = savedNumber("aci-compare-first", state.compareFirst);
    elements.compareToggle.setAttribute("aria-pressed", String(state.comparing));
    updateFindingBar();
    renderBehaviourList();
    syncURL();
    rebuildReader();
  } catch (error) {
    elements.readerStatus.classList.add("visible");
    elements.readerStatus.textContent = "The cached spec documents or this bench's behavior set could not be loaded. Serve this directory over HTTP and reload.";
    elements.passageCount.textContent = "Documents unavailable";
    console.error(error);
  }
}

initialize();
