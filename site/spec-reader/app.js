const GROUPS = [
  {
    name: "Honesty & epistemics",
    behaviours: [
      [1, "No sycophancy"],
      [2, "Calibration"],
      [3, "Honesty about one's own actions"],
    ],
  },
  {
    name: "Instruction & task fidelity",
    behaviours: [
      [4, "Instruction-hierarchy conformance"],
      [5, "Handling disagreements with user instructions"],
      [6, "Reward hacking"],
    ],
  },
  {
    name: "Power concentration & large-scale harm",
    behaviours: [
      [7, "Catastrophic risks"],
      [8, "Even-handedness"],
      [9, "Complicity in illegitimate power seizure"],
      [10, "Secret loyalties"],
    ],
  },
  {
    name: "Interaction with others",
    behaviours: [
      [11, "Cooperative stance"],
      [12, "Avoiding hateful and spiteful dispositions"],
      [13, "Caution in high-stakes scenarios"],
    ],
  },
];

/* Depth anchors per the coverage depth rubric (methodology.html#coverage). */
const DEPTH_ANCHORS = ["absent", "named", "discussed", "prescribed", "demonstrated"];

const state = {
  payload: null,
  selectedBehaviour: null,
  selectedSpec: "anthropic",
  comparing: false,
  embedded: false,
  passageIndex: 0,
  anchors: [],
  documentFocus: { anthropic: true, openai: true },
  sidebarWidth: 292,
  compareFirst: 50,
  compareWidths: [],
};

const elements = {
  appShell: document.querySelector(".app-shell"),
  behaviourList: document.querySelector("#behaviour-list"),
  compareToggle: document.querySelector("#compare-toggle"),
  documentReader: document.querySelector("#document-reader"),
  findingBehaviour: document.querySelector("#finding-behaviour"),
  findingDefinition: document.querySelector("#finding-definition"),
  mode: document.querySelector("#mode"),
  nextPassage: document.querySelector("#next-passage"),
  passageCount: document.querySelector("#passage-count"),
  previousPassage: document.querySelector("#previous-passage"),
  readerStatus: document.querySelector("#reader-status"),
  sidebarResizer: document.querySelector("#sidebar-resizer"),
  sourceLink: document.querySelector("#source-link"),
  specSwitcher: document.querySelector(".spec-switcher"),
  template: document.querySelector("#document-template"),
};

const initialParams = new URLSearchParams(location.search);
state.embedded = initialParams.get("embedded") === "1";
document.body.classList.toggle("embedded", state.embedded);

function activeBehaviour() {
  const behaviours = state.payload?.behaviours || [];
  return behaviours.find(behaviour => behaviour.slug === state.selectedBehaviour) || behaviours[0];
}

function syncURL() {
  const params = new URLSearchParams(location.search);
  params.set("behavior", activeBehaviour()?.slug || "no-sycophancy");
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

/* Compare layout generalizes to N documents: the two-document case keeps the
 * persisted --compare-first split exactly as before; with three-plus documents
 * the panes take weighted shares (state.compareWidths, equal on entry, not
 * persisted) and each boundary resizer moves its own boundary. */
function comparePaneCount() {
  return state.comparing ? state.payload.documents.length : 0;
}

function applyCompareLayout() {
  const n = comparePaneCount();
  if (n <= 2) return;   // two-pane layout stays CSS-var driven (setCompareFirst)
  if (state.compareWidths.length !== n) state.compareWidths = Array.from({ length: n }, () => 100 / n);
  const cols = [];
  state.compareWidths.forEach((w, i) => {
    cols.push(`minmax(0, ${w}fr)`);
    if (i < n - 1) cols.push("9px");
  });
  elements.documentReader.style.gridTemplateColumns = cols.join(" ");
  elements.documentReader.querySelectorAll(".document-resizer").forEach((resizer, i) => {
    const w = state.compareWidths[i];
    resizer.setAttribute("aria-valuemin", "10");
    resizer.setAttribute("aria-valuemax", "90");
    resizer.setAttribute("aria-valuenow", String(Math.round(w)));
    resizer.setAttribute("aria-valuetext", `Specification ${i + 1} ${Math.round(w)} percent wide`);
  });
  requestAnimationFrame(updateRails);
}

function moveCompareBoundary(index, delta) {
  const widths = state.compareWidths;
  const min = 10;
  const left = widths[index], right = widths[index + 1];
  const d = clamp(delta, min - left, right - min);
  widths[index] = left + d;
  widths[index + 1] = right - d;
  applyCompareLayout();
}

function setCompareBoundaryTo(index, pct) {
  const widths = state.compareWidths;
  const min = 10;
  const cumBefore = widths.slice(0, index).reduce((a, b) => a + b, 0);
  const target = clamp(pct - cumBefore, min, widths[index] + widths[index + 1] - min);
  moveCompareBoundary(index, target - widths[index]);
}

function createDocumentResizer(index = 0) {
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
    if (comparePaneCount() <= 2) {
      startColumnDrag(
        event,
        resizer,
        clientX => setCompareFirst(((clientX - bounds.left) / bounds.width) * 100),
        () => setCompareFirst(state.compareFirst, true),
      );
    } else {
      startColumnDrag(
        event,
        resizer,
        clientX => setCompareBoundaryTo(index, ((clientX - bounds.left) / bounds.width) * 100),
        () => applyCompareLayout(),
      );
    }
  });
  resizer.addEventListener("keydown", event => {
    const step = event.shiftKey ? 10 : 2;
    if (comparePaneCount() <= 2) {
      let next = state.compareFirst;
      if (event.key === "ArrowLeft") next -= step;
      else if (event.key === "ArrowRight") next += step;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = 100;
      else return;
      event.preventDefault();
      setCompareFirst(next, true);
    } else {
      let delta;
      if (event.key === "ArrowLeft") delta = -step;
      else if (event.key === "ArrowRight") delta = step;
      else if (event.key === "Home") delta = -Infinity;
      else if (event.key === "End") delta = Infinity;
      else return;
      event.preventDefault();
      moveCompareBoundary(index, delta);
    }
  });
  return resizer;
}

setupSidebarResizer();

function renderBehaviourList() {
  const byNumber = new Map((state.payload?.behaviours || []).map(behaviour => [behaviour.id, behaviour]));
  const activeSlug = activeBehaviour()?.slug;
  elements.behaviourList.innerHTML = GROUPS.map(group => `
    <section class="behaviour-group">
      <h2>${group.name}</h2>
      <ul>
        ${group.behaviours.map(([number, name]) => {
          const behaviour = byNumber.get(number);
          const active = behaviour && behaviour.slug === activeSlug;
          return `
          <li>
            <button
              class="behaviour-button ${behaviour ? "mapped" : ""}${active ? " active" : ""}"
              type="button"
              ${behaviour ? `data-behaviour="${behaviour.slug}"` : "disabled"}
              ${active ? 'aria-current="true"' : ""}
              title="${behaviour ? "Show mapped passages" : "Passage mapping pending"}"
            >
              <span class="number">${String(number).padStart(2, "0")}</span>
              <span class="name">${name}</span>
              <i class="status-dot ${behaviour ? "mapped" : "pending"}" aria-hidden="true"></i>
            </button>
          </li>
        `;}).join("")}
      </ul>
    </section>
  `).join("");
  elements.behaviourList.querySelectorAll("[data-behaviour]").forEach(button => {
    button.addEventListener("click", () => selectBehaviour(button.dataset.behaviour));
  });
}

function updateFindingBar() {
  const behaviour = activeBehaviour();
  if (!behaviour) return;
  elements.findingBehaviour.textContent = behaviour.name;
  elements.findingDefinition.textContent = behaviour.definition;
}

function selectBehaviour(slug) {
  if (slug === activeBehaviour()?.slug) return;
  state.selectedBehaviour = slug;
  updateFindingBar();
  renderBehaviourList();
  syncURL();
  rebuildReader();
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

function findPassageBlocks(body, passage) {
  const needle = normalize(passage.quote);
  const blocks = [...body.querySelectorAll("[data-block]")];
  const exact = blocks.find(block => normalize(block.textContent).includes(needle));
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

  // Published Markdown sometimes renders cross-references as "?" while the
  // citation ledger stores the resolved anchor. The opening clause remains a
  // stable, version-pinned fallback for those otherwise identical passages.
  const opening = needle.split(" ").slice(0, 18).join(" ");
  const fallback = blocks.find(block => normalize(block.textContent).includes(opening));
  return fallback ? { anchor: fallback, continuation: [] } : null;
}

function annotatePassages(panel, document) {
  const body = panel.querySelector(".document-body");
  const missing = [];

  document.coverage.passages.forEach((passage, index) => {
    const found = findPassageBlocks(body, passage);
    if (!found) {
      missing.push(passage.locator);
      return;
    }
    const block = found.anchor;
    found.continuation.forEach(extra => {
      extra.classList.add("passage", "passage-continuation");
      extra.classList.toggle("adjacent", passage.adjacent);
    });

    block.classList.add("passage");
    block.classList.toggle("adjacent", passage.adjacent);
    block.dataset.passageId = passage.id;
    block.dataset.documentId = document.id;
    block.dataset.passageNumber = String(index + 1);
    block.dataset.role = passage.role;
    block.insertAdjacentHTML(
      "afterbegin",
      `<span class="passage-label">${passage.adjacent ? "Related · " : ""}${escapeHTML(passage.role)}</span>`,
    );

    if (passage.exampleBlock) {
      let continuation = block.nextElementSibling;
      while (continuation && !continuation.classList.contains("code-block")) {
        if (/^H[1-6]$/.test(continuation.tagName)) break;
        continuation = continuation.nextElementSibling;
      }
      if (continuation?.classList.contains("code-block")) {
        continuation.classList.add("passage", "passage-continuation");
        continuation.classList.toggle("adjacent", passage.adjacent);
      }
    }
  });

  return missing;
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

function updateSectionVisibility(panel) {
  const focused = state.documentFocus[panel.dataset.documentId];
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

function setPanelFocus(panel, focused) {
  state.documentFocus[panel.dataset.documentId] = focused;
  (panel._sectionInfos || []).forEach(info => {
    info.collapsed = focused ? !info.hasPassage : false;
  });
  updateSectionVisibility(panel);
  requestAnimationFrame(updateRails);
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
    info.hasPassage = children.some(child => {
      if (!(child._sectionAncestors || []).includes(info)) return false;
      return child.matches(".passage") || Boolean(child.querySelector(".passage"));
    });
    info.heading.classList.toggle("section-has-passage", info.hasPassage);
    info.button.addEventListener("click", () => {
      info.collapsed = !info.collapsed;
      updateSectionVisibility(panel);
      requestAnimationFrame(updateRails);
    });
  });

  panel._sectionInfos = infos;
  panel.querySelector(".document-focus-toggle").addEventListener("click", () => {
    setPanelFocus(panel, !state.documentFocus[panel.dataset.documentId]);
  });
  setPanelFocus(panel, state.documentFocus[panel.dataset.documentId]);
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

function renderDocument(document) {
  const panel = elements.template.content.firstElementChild.cloneNode(true);
  const markdownContext = {
    headings: buildHeadingIndex(document.markdown),
    idPrefix: document.id,
    usedHeadingIds: new Map(),
  };
  panel.dataset.documentId = document.id;
  panel.querySelector(".document-lab").textContent = document.lab;
  panel.querySelector(".document-title").textContent = document.title;
  panel.querySelector(".document-version").textContent = `Version ${document.version}`;
  panel.querySelector(".coverage-depth").textContent =
    `Coverage depth ${document.coverage.depth} / 4 · ${DEPTH_ANCHORS[document.coverage.depth] ?? ""}`;
  panel.querySelector(".document-body").innerHTML = renderMarkdown(document.markdown, markdownContext);

  const missing = annotatePassages(panel, document);
  if (document.coverage.passages.length === 0) {
    panel.querySelector(".document-body").insertAdjacentHTML(
      "afterbegin",
      `<div class="zero-coverage" role="note">
        <strong>No mapped passages in this specification.</strong>
        <span>Absence of coverage is an index finding, not missing data.</span>
      </div>`,
    );
  }
  setupSectionFocus(panel);
  setupInternalLinks(panel);
  panel._missingPassages = missing;
  return panel;
}

function visibleDocuments() {
  const behaviour = activeBehaviour();
  const withCoverage = state.payload.documents.map(document => ({
    ...document,
    coverage: behaviour.coverage[document.id],
  }));
  if (state.comparing) return withCoverage;
  return [withCoverage.find(document => document.id === state.selectedSpec)];
}

function rebuildReader() {
  const documents = visibleDocuments();
  elements.documentReader.classList.toggle("compare", state.comparing);
  const panels = documents.map(renderDocument);
  const children = state.comparing
    ? panels.flatMap((panel, i) => (i < panels.length - 1 ? [panel, createDocumentResizer(i)] : [panel]))
    : panels;
  elements.documentReader.replaceChildren(...children);
  if (state.comparing && panels.length > 2) applyCompareLayout();
  else {
    elements.documentReader.style.gridTemplateColumns = "";
    if (state.comparing) setCompareFirst(state.compareFirst);
  }
  state.passageIndex = 0;

  const selected = state.payload.documents.find(document => document.id === state.selectedSpec);
  elements.sourceLink.href = selected.sourceUrl;
  elements.sourceLink.textContent = state.comparing ? "Sources ↗" : "Original ↗";

  document.querySelectorAll(".spec-option").forEach(option => {
    option.classList.toggle("active", option.dataset.spec === state.selectedSpec);
    option.setAttribute("aria-pressed", String(option.dataset.spec === state.selectedSpec));
  });

  const missing = [...elements.documentReader.querySelectorAll(".document-panel")]
    .flatMap(panel => panel._missingPassages || []);
  elements.readerStatus.classList.toggle("visible", missing.length > 0);
  elements.readerStatus.textContent = missing.length
    ? `${missing.length} cached passage ${missing.length === 1 ? "anchor could" : "anchors could"} not be resolved against this document version.`
    : "";

  requestAnimationFrame(() => {
    collectAnchors();
    updateRails();
    focusPassage(0, false);
    revealHashTarget();
  });
}

function collectAnchors() {
  state.anchors = [...elements.documentReader.querySelectorAll("[data-passage-id]")];
  elements.previousPassage.disabled = state.anchors.length === 0;
  elements.nextPassage.disabled = state.anchors.length === 0;

  if (!state.anchors.length) {
    elements.passageCount.textContent = state.comparing
      ? "No passages in either spec"
      : "No passages in this spec";
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
      const mark = document.createElement("button");
      mark.type = "button";
      mark.className = `rail-mark${anchor.classList.contains("adjacent") ? " adjacent" : ""}`;
      mark.dataset.forPassage = anchor.dataset.passageId;
      mark.style.top = `${Math.min(98, (anchor.offsetTop / body.scrollHeight) * 100)}%`;
      mark.style.height = `max(5px, ${(anchor.offsetHeight / body.scrollHeight) * 100}%)`;
      mark.setAttribute(
        "aria-label",
        `${anchor.classList.contains("adjacent") ? "Related" : "Core"} passage ${localIndex + 1}: ${anchor.dataset.role}`,
      );
      mark.title = anchor.dataset.role;
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

elements.compareToggle.addEventListener("click", () => {
  state.comparing = !state.comparing;
  elements.compareToggle.setAttribute("aria-pressed", String(state.comparing));
  syncURL();
  rebuildReader();
});

elements.previousPassage.addEventListener("click", () => focusPassage(state.passageIndex - 1));
elements.nextPassage.addEventListener("click", () => focusPassage(state.passageIndex + 1));

document.addEventListener("keydown", event => {
  if (event.target.matches("input, textarea, select")) return;
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

/* Spec options follow documents.json rather than a hardcoded pair (C12), so a
 * user-registered spec gets its own switcher button the moment it is folded in. */
function renderSpecOptions() {
  const options = state.payload.documents.map(doc => {
    const option = document.createElement("button");
    option.className = "spec-option";
    option.dataset.spec = doc.id;
    option.type = "button";
    const name = document.createElement("span");
    name.textContent = doc.lab;
    const detail = document.createElement("small");
    const version = (doc.version || "").replaceAll("-", ".");
    detail.textContent = version ? `${doc.title} · ${version}` : doc.title;
    option.append(name, detail);
    option.addEventListener("click", () => {
      state.selectedSpec = doc.id;
      if (state.comparing) {
        state.comparing = false;
        elements.compareToggle.setAttribute("aria-pressed", "false");
      }
      syncURL();
      rebuildReader();
    });
    return option;
  });
  elements.specSwitcher.replaceChildren(...options);
}

async function initialize() {
  renderBehaviourList();
  try {
    const response = await fetch("./data/documents.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.payload = await response.json();
    renderSpecOptions();
    const params = initialParams;
    const requestedBehaviour = params.get("behavior");
    if (state.payload.behaviours.some(behaviour => behaviour.slug === requestedBehaviour)) {
      state.selectedBehaviour = requestedBehaviour;
    }
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
    elements.readerStatus.textContent = "The cached spec documents could not be loaded. Serve this directory over HTTP and reload.";
    elements.passageCount.textContent = "Documents unavailable";
    console.error(error);
  }
}

initialize();
