#!/usr/bin/env node
// Verify the spec reader against site/spec-reader/data/documents.json:
// every behaviour x spec view must anchor exactly its published passage count,
// every expected nav link must be present, every same-site navigation link
// must resolve to a real page (and any #fragment to a real id), with no
// unresolved-anchor warnings and no console errors.
// Usage: node engine/verify-spec-reader.mjs   (requires Chrome installed)

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
const base = `http://127.0.0.1:${server.address().port}/spec-reader/`;

const payload = JSON.parse(await readFile(join(SITE, "spec-reader/data/documents.json"), "utf8"));
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage();
const consoleErrors = [];
page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
page.on("pageerror", error => consoleErrors.push(String(error)));

let failures = 0;

// Readiness predicate for the reader page: rendered once #passage-count exists
// and no longer shows the loading placeholder. Shared by the per-view checks
// and the nav/link crawl (page.waitForFunction serializes it into the page).
function readerReady() {
  const el = document.querySelector("#passage-count");
  return el && !el.textContent.startsWith("Loading");
}

async function expectView(url, expected, label) {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForFunction(readerReady, undefined, { timeout: 10000 });
  await page.waitForTimeout(150);
  const seen = await page.evaluate(() => ({
    passages: document.querySelectorAll("[data-passage-id]").length,
    status: document.querySelector("#reader-status").textContent.trim(),
    behaviour: document.querySelector("#finding-behaviour").textContent,
  }));
  const ok = seen.passages === expected.passages
    && seen.status === ""
    && seen.behaviour === expected.behaviour;
  if (!ok) failures += 1;
  console.log(
    `${ok ? "PASS" : "FAIL"}  ${label}: ${seen.passages}/${expected.passages} passages` +
    (seen.status ? `  status: ${seen.status}` : "") +
    (seen.behaviour !== expected.behaviour ? `  behaviour: ${seen.behaviour}` : ""),
  );
}

for (const behaviour of payload.behaviours) {
  let total = 0;
  for (const document of payload.documents) {
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

// Navigation anchors: the expected primary-nav links must all be present,
// every same-site link on the reader must resolve to a served page, and every
// #fragment must match an id in its target document.
await page.goto(base, { waitUntil: "networkidle" });
await page.waitForFunction(readerReady, undefined, { timeout: 10000 });
await page.waitForTimeout(150);
const expectedNav = ["../", "./", "../spec-reader-test/", "../methodology.html", "../#about"];
const navHrefs = await page.evaluate(
  () => [...document.querySelectorAll('nav[aria-label="Primary navigation"] a')].map(a => a.getAttribute("href")),
);
const missingNav = expectedNav.filter(href => !navHrefs.includes(href));
if (missingNav.length) {
  failures += 1;
  console.log(`FAIL  navigation presence: missing nav link(s): ${missingNav.join(", ")}`);
} else {
  console.log("PASS  navigation presence: all expected nav links present");
}
const linkIssues = await page.evaluate(async () => {
  const issues = [];
  const here = new URL(location.href);
  for (const anchor of document.querySelectorAll("a[href]")) {
    const href = anchor.getAttribute("href");
    let url;
    try {
      url = new URL(href, here);
    } catch {
      issues.push(`${href} -> unparsable href`);
      continue;
    }
    if (url.protocol !== "http:" && url.protocol !== "https:") continue;
    if (url.origin !== here.origin) continue; // external target, not verifiable offline
    let id = "";
    if (url.hash) {
      try {
        id = decodeURIComponent(url.hash.slice(1));
      } catch {
        issues.push(`${href} -> malformed fragment ${url.hash}`);
        continue;
      }
    }
    if (!id && url.pathname === here.pathname && url.search === here.search) continue; // self / bare "#"
    if (url.pathname === here.pathname) {
      // Same page: check the live document, since app.js renders ids dynamically.
      if (id && !document.getElementById(id) && !document.querySelector(`[name="${CSS.escape(id)}"]`)) {
        issues.push(`${href} -> no element #${id} on this page`);
      }
      continue;
    }
    const response = await fetch(url.pathname);
    if (!response.ok) {
      issues.push(`${href} -> HTTP ${response.status} for ${url.pathname}`);
      continue;
    }
    if (!id) continue;
    const target = new DOMParser().parseFromString(await response.text(), "text/html");
    if (!target.getElementById(id) && !target.querySelector(`[name="${CSS.escape(id)}"]`)) {
      issues.push(`${href} -> no element #${id} in ${url.pathname}`);
    }
  }
  return issues;
});
if (linkIssues.length) {
  failures += 1;
  console.log(`FAIL  navigation anchors: ${linkIssues.length} broken link(s)`);
  for (const issue of linkIssues) console.log(`        ${issue}`);
} else {
  console.log("PASS  navigation anchors: every same-site link resolves");
}

// This harness serves the repo's own site, which carries exactly the two bundled
// specifications. With no third document there is no choice to make, so compare must
// stay exactly as it was: no picker, and no new query parameter on a shared link.
{
  await page.goto(`${base}?compare=1`, { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const el = document.querySelector("#passage-count");
    return el && !el.textContent.startsWith("Loading");
  }, undefined, { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(500);
  const twoDoc = await page.evaluate(() => ({
    docs: document.querySelectorAll(".spec-option").length,
    panes: document.querySelectorAll(".document-panel").length,
    pickerHidden: document.querySelector("#compare-picker")?.hidden,
    compareWith: new URL(location.href).searchParams.get("compare-with"),
  }));
  if (twoDoc.docs === 2 && twoDoc.panes === 2 && twoDoc.pickerHidden === true
      && twoDoc.compareWith === null) {
    console.log("PASS  two-document compare is unchanged: no picker, no ?compare-with=");
  } else {
    failures += 1;
    console.log(`FAIL  two-document compare changed: ${JSON.stringify(twoDoc)}`);
  }
}

// The repo's own site carries no user specification, so nothing about it is local:
// no marker, and the panel stays unlinked exactly as it is today.
{
  await page.goto(base, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  const bundled = await page.evaluate(() => ({
    marked: document.body.dataset.localData === "true",
    badge: !!document.querySelector("#local-data-note")?.offsetParent,
    panelLink: !!document.querySelector('nav a[href*="llm-panel-review"]'),
  }));
  if (!bundled.marked && !bundled.badge && !bundled.panelLink) {
    console.log("PASS  bundled-only site is not marked local and does not link the panel");
  } else {
    failures += 1;
    console.log(`FAIL  bundled-only site changed: ${JSON.stringify(bundled)}`);
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
