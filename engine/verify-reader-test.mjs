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

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage();
const consoleErrors = [];
page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
page.on("pageerror", error => consoleErrors.push(String(error)));

let failures = 0;

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
      const passages = behaviour.coverage[document.id].passages.length;
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
}

if (consoleErrors.length) {
  failures += 1;
  console.log("console errors:", consoleErrors);
}
await browser.close();
server.close();
console.log(failures ? `${failures} failures` : "All views verified.");
process.exit(failures ? 1 : 0);
