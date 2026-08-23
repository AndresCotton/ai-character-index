#!/usr/bin/env node
// Verify the reader test bench (site/spec-reader-test/) against its own behaviour set
// in site/spec-reader-test/data/behaviours.json and the spec text it shares with the
// published reader. Every behaviour x spec view must anchor exactly its published passage
// count, with no unresolved-anchor warnings and no console errors; with an empty behaviour
// set, both specs must render in full with nothing highlighted.
// Usage: node engine/verify-reader-test.mjs   (requires Chrome installed)

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const SITE = join(fileURLToPath(new URL("..", import.meta.url)), "site");
const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
};

const server = createServer(async (request, response) => {
  let path = normalize(decodeURIComponent(new URL(request.url, "http://x").pathname));
  if (path.endsWith("/")) path += "index.html";
  try {
    const body = await readFile(join(SITE, path));
    response.writeHead(200, { "content-type": MIME[extname(path)] || "application/octet-stream" });
    response.end(body);
  } catch {
    response.writeHead(404).end("not found");
  }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}/spec-reader-test/`;

const behaviours = JSON.parse(
  await readFile(join(SITE, "spec-reader-test/data/behaviours.json"), "utf8"),
).behaviours;
const documents = JSON.parse(
  await readFile(join(SITE, "spec-reader/data/documents.json"), "utf8"),
).documents;

/* The two payloads above are built by different scripts and can legally diverge.
 * The bench set carries no document list of its own, so the list comes from the
 * published reader -- which grows a document the moment a user registers a spec
 * (build-spec-reader-data.py --user-manifest=), while the bench behaviours are
 * rebuilt only from data/reader-test-coverage.json and still cover the bundled
 * pair. A document the bench says nothing about anchors nothing: assert that,
 * rather than dereferencing a coverage record that was never written. On the
 * committed two-document tree every document has a record, so this is a no-op. */
const coveredPassages = (behaviour, id) => behaviour.coverage[id]?.passages ?? [];

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage();
const consoleErrors = [];
page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
page.on("pageerror", error => consoleErrors.push(String(error)));

let failures = 0;

// Two citations that pin different sentences of one paragraph resolve to the same rendered
// block, and a block carries one passage marker however many citations land on it. So what
// a view must show is the number of distinct blocks the behaviour cites, not the number of
// citations: strip the sentence suffix (`¶3 s2`, `¶18 s2-s4`, `¶9 s2-4`) and count.
const blockOf = locator => locator.replace(/ s\d+(?:-s?\d+)?$/, "");
const anchorCount = passages => new Set(passages.map(passage => blockOf(passage.locator))).size;

function report(ok, label, detail) {
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${detail ? `: ${detail}` : ""}`);
}

async function readView(url) {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () => !document.querySelector("#passage-count").textContent.startsWith("Loading"),
    { timeout: 10000 },
  );
  await page.waitForTimeout(150);
  return page.evaluate(() => ({
    passages: document.querySelectorAll("[data-passage-id]").length,
    status: document.querySelector("#reader-status").textContent.trim(),
    behaviour: document.querySelector("#finding-behaviour").textContent,
    // Body text of every rendered panel, to prove the spec itself is there to read.
    panels: [...document.querySelectorAll(".document-panel")].map(panel => ({
      lab: panel.querySelector(".document-lab").textContent,
      blocks: panel.querySelectorAll(".document-body [data-block]").length,
      // Nothing may be collapsed out of view while there is no behaviour to focus on.
      hiddenBlocks: [...panel.querySelectorAll(".document-body > *")]
        .filter(child => child.hidden).length,
      collapsedSections: panel.querySelectorAll(".section-collapsed").length,
      // Computed display, not the property: a stylesheet rule that sets its own display
      // silently beats [hidden], which is how the highlight legend first leaked through.
      coverageChipHidden: getComputedStyle(panel.querySelector(".coverage-depth")).display === "none",
      focusToggleHidden: getComputedStyle(panel.querySelector(".document-focus-toggle")).display === "none",
      legendHidden: getComputedStyle(panel.querySelector(".rail-legend")).display === "none",
    })),
    emptyMenu: Boolean(document.querySelector(".behaviour-empty")),
    menuItems: document.querySelectorAll("[data-behaviour]").length,
    ticked: [...document.querySelectorAll("[data-behaviour]")]
      .filter(input => input.checked).map(input => input.dataset.behaviour),
    // A passage carries the name of every behaviour that cites it, so a selection of
    // several can be accounted for behaviour by behaviour.
    byBehaviour: [...document.querySelectorAll("[data-passage-id]")]
      .reduce((tally, anchor) => {
        anchor.dataset.behaviours.split(" · ").forEach(name => {
          tally[name] = (tally[name] || 0) + 1;
        });
        return tally;
      }, {}),
    // Marked as shared, and cited by more than one: the same passages, counted two ways.
    sharedMarked: document.querySelectorAll(".passage-overlap[data-passage-id]").length,
    sharedCited: [...document.querySelectorAll("[data-passage-id]")]
      .filter(anchor => anchor.dataset.behaviours.includes(" · ")).length,
  }));
}

async function expectView(url, expected, label) {
  const seen = await readView(url);
  const ok = seen.passages === expected.passages
    && seen.status === ""
    && seen.behaviour === expected.behaviour;
  report(ok, label, `${seen.passages}/${expected.passages} passages`
    + (seen.status ? `  status: ${seen.status}` : "")
    + (seen.behaviour !== expected.behaviour ? `  behaviour: ${seen.behaviour}` : ""));
}

if (behaviours.length === 0) {
  // The bench is empty: the point is that both specs are fully readable and untouched.
  for (const document of documents) {
    const seen = await readView(`${base}?spec=${document.id}`);
    const panel = seen.panels[0];
    report(
      seen.passages === 0
        && seen.status === ""
        && seen.emptyMenu
        && seen.menuItems === 0
        && seen.behaviour === "No behavior under test"
        && panel?.blocks > 100
        && panel.hiddenBlocks === 0
        && panel.collapsedSections === 0
        && panel.coverageChipHidden
        && panel.focusToggleHidden
        && panel.legendHidden,
      `empty bench · ${document.id}`,
      `${seen.passages} passages, ${panel?.blocks} blocks, ${panel?.hiddenBlocks} hidden,`
      + ` menu items ${seen.menuItems}, chip hidden ${panel?.coverageChipHidden}`
      + (seen.status ? `, status: ${seen.status}` : ""),
    );
  }
  const compared = await readView(`${base}?compare=1`);
  report(
    compared.panels.length === 2
      && compared.passages === 0
      && compared.panels.every(panel => panel.blocks > 100 && panel.hiddenBlocks === 0),
    "empty bench · compare",
    compared.panels.map(panel => `${panel.lab} ${panel.blocks} blocks, ${panel.hiddenBlocks} hidden`).join(", "),
  );
} else {
  for (const behaviour of behaviours) {
    let total = 0;
    for (const document of documents) {
      const passages = anchorCount(coveredPassages(behaviour, document.id));
      total += passages;
      await expectView(
        `${base}?behavior=${behaviour.slug}&spec=${document.id}`,
        { passages, behaviour: behaviour.name },
        `${behaviour.slug} · ${document.id}`,
      );
    }
    await expectView(
      `${base}?behavior=${behaviour.slug}&compare=1`,
      { passages: total, behaviour: behaviour.name },
      `${behaviour.slug} · compare`,
    );
  }

  // Several behaviours read over the same text. Each must still anchor exactly its own
  // published passages; where two of them cite one passage it is highlighted once and
  // marked as shared, rather than counted twice or overwritten by the last one drawn.
  const selections = [behaviours.slice(0, 3), behaviours];
  for (const selection of selections) {
    const slugs = selection.map(behaviour => behaviour.slug);
    for (const document of documents) {
      const seen = await readView(`${base}?behavior=${slugs.join(",")}&spec=${document.id}`);
      const short = selection.map(behaviour =>
        `${behaviour.slug} ${seen.byBehaviour[behaviour.name] || 0}/${anchorCount(coveredPassages(behaviour, document.id))}`);
      const accounted = selection.every(behaviour =>
        (seen.byBehaviour[behaviour.name] || 0) === anchorCount(coveredPassages(behaviour, document.id)));
      report(
        accounted
          && seen.status === ""
          && seen.sharedMarked === seen.sharedCited
          && seen.ticked.join(",") === slugs.join(","),
        `${slugs.length} behaviors · ${document.id}`,
        `${seen.passages} passages, ${seen.sharedMarked} shared`
        + (accounted ? "" : `  unaccounted: ${short.join(", ")}`)
        + (seen.status ? `  status: ${seen.status}` : ""),
      );
    }
  }

  // Ticking the menu must change only the highlight layer: the reader keeps its place in
  // the text, and the behaviour taken away takes its passages with it.
  const [first, second] = behaviours;
  await readView(`${base}?behavior=${first.slug},${second.slug}&spec=anthropic`);
  await page.evaluate(() => { document.querySelector(".document-scroll").scrollTop = 2400; });
  // The panel scrolls smoothly, so wait for two readings in a row that agree before
  // taking the position the toggle is supposed to leave alone.
  await page.waitForFunction(() => {
    const scroll = document.querySelector(".document-scroll");
    const settled = scroll.scrollTop > 0 && scroll.scrollTop === scroll._previousTop;
    scroll._previousTop = scroll.scrollTop;
    return settled;
  });
  const before = await page.evaluate(() => document.querySelector(".document-scroll").scrollTop);
  await page.click(`.behaviour-option:has([data-behaviour="${first.slug}"])`);
  await page.waitForTimeout(250);
  const after = await page.evaluate(() => ({
    scrollTop: document.querySelector(".document-scroll").scrollTop,
    passages: document.querySelectorAll("[data-passage-id]").length,
    behaviour: document.querySelector("#finding-behaviour").textContent,
    url: new URL(location.href).searchParams.get("behavior"),
  }));
  report(
    Math.abs(after.scrollTop - before) < 4
      && after.passages === anchorCount(second.coverage.anthropic.passages)
      && after.behaviour === second.name
      && after.url === second.slug,
    "unticking one of two · anthropic",
    `scroll ${before} → ${after.scrollTop}, ${after.passages} passages left,`
    + ` menu reads ${after.behaviour}, url ${after.url}`,
  );

  // And with the last behaviour unticked, the specification is readable in full again.
  await page.click("#clear-behaviours");
  await page.waitForTimeout(250);
  const cleared = await page.evaluate(() => ({
    passages: document.querySelectorAll("[data-passage-id]").length,
    hiddenBlocks: [...document.querySelectorAll(".document-body > *")].filter(child => child.hidden).length,
    collapsedSections: document.querySelectorAll(".section-collapsed").length,
    behaviour: document.querySelector("#finding-behaviour").textContent,
    focusToggleHidden: getComputedStyle(document.querySelector(".document-focus-toggle")).display === "none",
    url: new URL(location.href).searchParams.get("behavior"),
  }));
  report(
    cleared.passages === 0
      && cleared.hiddenBlocks === 0
      && cleared.collapsedSections === 0
      && cleared.behaviour === "No behaviors selected"
      && cleared.focusToggleHidden
      && cleared.url === null,
    "nothing ticked · anthropic",
    `${cleared.passages} passages, ${cleared.hiddenBlocks} hidden,`
    + ` ${cleared.collapsedSections} collapsed, menu reads ${cleared.behaviour}`,
  );

  // Nothing ticked is nothing to take away.
  report(
    await page.evaluate(() => document.querySelector("#download-passages").disabled),
    "export · nothing ticked",
    "download disabled",
  );

  // The export carries the reading away from the reader: every published citation of every
  // ticked behaviour, in both specifications, as the whole citation -- quote and locator and
  // role sentence -- and counted per citation rather than per highlighted block, because two
  // sentences of one paragraph are two citations even where they light one passage.
  const exported = behaviours.slice(0, 3);
  const citations = exported.flatMap(behaviour =>
    documents.flatMap(document => coveredPassages(behaviour, document.id)));
  await readView(`${base}?behavior=${exported.map(behaviour => behaviour.slug).join(",")}&spec=anthropic`);
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.click("#download-passages"),
  ]);
  const markdown = await readFile(await download.path(), "utf8");
  const missing = citations.filter(passage =>
    !markdown.includes(`\`${passage.locator}\``)
    || !markdown.includes(`> ${passage.quote.trim().split("\n")[0]}`.trimEnd())
    || !markdown.includes(passage.role));
  const written = (markdown.match(/^#### /gm) || []).length;
  const hint = (await page.textContent("#download-hint")).trim();
  const expectedHint = `${exported.length} behaviors · ${citations.length} passages, both specs`;
  report(
    missing.length === 0
      && written === citations.length
      && hint === expectedHint
      && exported.every(behaviour =>
        markdown.includes(`## ${String(behaviour.id).padStart(2, "0")} · ${behaviour.name}`)
        && markdown.includes(behaviour.definition))
      && documents.every(document =>
        markdown.includes(`### ${document.lab} · ${document.title} (${document.version})`)),
    `export · ${exported.length} behaviors`,
    `${download.suggestedFilename()}, ${written}/${citations.length} citations, menu reads ${hint}`
    + (missing.length ? `, missing ${missing.slice(0, 3).map(passage => passage.locator).join("; ")}` : ""),
  );
}

if (consoleErrors.length) {
  failures += 1;
  console.log("console errors:", consoleErrors);
}
await browser.close();
server.close();
console.log(failures ? `${failures} failures` : "All views verified.");
process.exit(failures ? 1 : 0);
