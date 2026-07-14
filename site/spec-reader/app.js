const GROUPS = [
  {
    name: "Honesty & epistemics",
    behaviours: [
      [1, "No sycophancy", true],
      [2, "Calibration"],
      [3, "Honesty about one’s own actions"],
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

const state = {
  payload: null,
  selectedSpec: "anthropic",
  comparing: false,
  embedded: false,
  passageIndex: 0,
  anchors: [],
  documentFocus: { anthropic: true, openai: true },
};

const elements = {
  behaviourList: document.querySelector("#behaviour-list"),
  compareToggle: document.querySelector("#compare-toggle"),
  documentReader: document.querySelector("#document-reader"),
  findingDefinition: document.querySelector("#finding-definition"),
  mode: document.querySelector("#mode"),
  nextPassage: document.querySelector("#next-passage"),
  passageCount: document.querySelector("#passage-count"),
  previousPassage: document.querySelector("#previous-passage"),
  readerStatus: document.querySelector("#reader-status"),
  sourceLink: document.querySelector("#source-link"),
  template: document.querySelector("#document-template"),
};

const initialParams = new URLSearchParams(location.search);
state.embedded = initialParams.get("embedded") === "1";
document.body.classList.toggle("embedded", state.embedded);

function syncURL() {
  const params = new URLSearchParams(location.search);
  params.set("behavior", state.payload?.behaviour?.slug || "no-sycophancy");
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

function renderBehaviourList() {
  elements.behaviourList.innerHTML = GROUPS.map(group => `
    <section class="behaviour-group">
      <h2>${group.name}</h2>
      <ul>
        ${group.behaviours.map(([number, name, mapped]) => `
          <li>
            <button
              class="behaviour-button ${mapped ? "mapped active" : ""}"
              type="button"
              ${mapped ? 'aria-current="true"' : "disabled"}
              title="${mapped ? "Show mapped passages" : "Passage mapping pending"}"
            >
              <span class="number">${String(number).padStart(2, "0")}</span>
              <span class="name">${name}</span>
              <i class="status-dot ${mapped ? "mapped" : "pending"}" aria-hidden="true"></i>
            </button>
          </li>
        `).join("")}
      </ul>
    </section>
  `).join("");
}

function escapeHTML(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function inlineMarkdown(source) {
  let value = source
    .replace(/\[\^[^\]]+\]/g, "")
    .replace(/\{#[^}]+\}/g, "");
  value = escapeHTML(value);
  value = value.replace(
    /\[([^\]]+)\]\((https?:\/\/[^)\s]+|#[^)\s]+)\)/g,
    '<a href="$2">$1</a>',
  );
  value = value
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>")
    .replace(/(?<!_)_([^_\n]+)_(?!_)/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  return value;
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

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const output = [];
  let blockNumber = 0;
  const blockAttr = () => `data-block="${++blockNumber}"`;

  for (let index = 0; index < lines.length;) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    const heading = headingDetails(line);
    if (heading) {
      const id = heading.id ? ` id="${escapeHTML(heading.id)}"` : "";
      output.push(`<h${heading.level} ${blockAttr()}${id}>${inlineMarkdown(heading.text)}</h${heading.level}>`);
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
      output.push(`<pre class="code-block" ${blockAttr()} data-language="${escapeHTML(language)}">${escapeHTML(content.join("\n"))}</pre>`);
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
          <div class="admonition-label">${inlineMarkdown(admonition[2] || admonition[1])}</div>
          ${renderMarkdown(content.join("\n"))}
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
      output.push(`<blockquote ${blockAttr()}>${renderMarkdown(content.join("\n"))}</blockquote>`);
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
        items.push(`<li ${blockAttr()}>${inlineMarkdown(item[2])}</li>`);
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
    output.push(`<p ${blockAttr()}>${inlineMarkdown(paragraph.join(" "))}</p>`);
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

function findPassageBlock(body, passage) {
  const needle = normalize(passage.quote);
  const blocks = [...body.querySelectorAll("[data-block]")];
  const exact = blocks.find(block => normalize(block.textContent).includes(needle));
  if (exact) return exact;

  // Published Markdown sometimes renders cross-references as "?" while the
  // citation ledger stores the resolved anchor. The opening clause remains a
  // stable, version-pinned fallback for those otherwise identical passages.
  const opening = needle.split(" ").slice(0, 18).join(" ");
  return blocks.find(block => normalize(block.textContent).includes(opening));
}

function annotatePassages(panel, document) {
  const body = panel.querySelector(".document-body");
  const missing = [];

  document.coverage.passages.forEach((passage, index) => {
    const block = findPassageBlock(body, passage);
    if (!block) {
      missing.push(passage.locator);
      return;
    }

    block.classList.add("passage");
    block.classList.toggle("adjacent", passage.adjacent);
    block.dataset.passageId = passage.id;
    block.dataset.documentId = document.id;
    block.dataset.passageNumber = String(index + 1);
    block.dataset.role = passage.role;
    block.insertAdjacentHTML(
      "afterbegin",
      `<span class="passage-label">${passage.adjacent ? "Adjacent · " : ""}${escapeHTML(passage.role)}</span>`,
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

function renderDocument(document) {
  const panel = elements.template.content.firstElementChild.cloneNode(true);
  panel.dataset.documentId = document.id;
  panel.querySelector(".document-lab").textContent = document.lab;
  panel.querySelector(".document-title").textContent = document.title;
  panel.querySelector(".document-version").textContent = `Version ${document.version}`;
  panel.querySelector(".coverage-depth").textContent = `Coverage depth ${document.coverage.depth} / 4`;
  panel.querySelector(".document-body").innerHTML = renderMarkdown(document.markdown);

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
  panel._missingPassages = missing;
  return panel;
}

function visibleDocuments() {
  if (state.comparing) return state.payload.documents;
  return [state.payload.documents.find(document => document.id === state.selectedSpec)];
}

function rebuildReader() {
  const documents = visibleDocuments();
  elements.documentReader.classList.toggle("compare", state.comparing);
  elements.documentReader.replaceChildren(...documents.map(renderDocument));
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

window.addEventListener("resize", () => requestAnimationFrame(updateRails));

async function initialize() {
  renderBehaviourList();
  try {
    const response = await fetch("./data/documents.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.payload = await response.json();
    const params = initialParams;
    const requestedSpec = params.get("spec");
    if (state.payload.documents.some(document => document.id === requestedSpec)) {
      state.selectedSpec = requestedSpec;
    }
    state.comparing = params.get("compare") === "1";
    elements.compareToggle.setAttribute("aria-pressed", String(state.comparing));
    elements.findingDefinition.textContent = state.payload.behaviour.definition;
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
