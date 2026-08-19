#!/usr/bin/env node
// Tier-1 feature harness for the site surfaces, driven against TWO data
// states: the bundled payloads that ship in the repo, and a user-extended
// staging built by engine/stage_user_demo.py (synthetic user spec + set:user
// behaviour, staged into a scratch copy of site/ -- the repo itself is
// restored untouched). Covers the panel's URL/DOM-state features and the
// reader's user-data path; interactive-only features (resizer drags, focus
// toggles, scroll behaviour) stay manual (Tier 2). The bench surface is
// covered by verify-reader-test.mjs and is not repeated here.
//
// Usage:  node engine/verify-panel-features.mjs   (needs Chrome + python3)
// Exits 0 when every check passes, 1 otherwise.

import { spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { readFile as readFileAsync } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const ENGINE = join(fileURLToPath(new URL("..", import.meta.url)), "engine");
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
               ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
               ".md": "text/markdown", ".txt": "text/plain" };

// --- Stage the user-extended site into a scratch dir -------------------------
const scratch = mkdtempSync(join(tmpdir(), "panel-features-"));
const staged = spawnSync("python3", [join(ENGINE, "stage_user_demo.py"), "--out", scratch],
                         { encoding: "utf8" });
if (staged.status !== 0) {
  console.error("staging failed:\n" + staged.stdout + staged.stderr);
  process.exit(2);
}
const stageInfo = JSON.parse(staged.stdout);
const SITE = stageInfo.site;
const USER = stageInfo.userBehaviour;          // acme-transparency
const USER_SPEC = stageInfo.userSpec;          // acme-spec
const PAYLOAD = stageInfo.payload;             // behaviours-<ts>.json
const userDocs = JSON.parse(readFileSync(join(SITE, "spec-reader/data/documents.json"), "utf8"));
const userPayload = JSON.parse(readFileSync(join(SITE, "llm-panel-review/data", PAYLOAD), "utf8"));

// --- Serve the staged site ----------------------------------------------------
const server = createServer(async (req, res) => {
  let path = normalize(decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (path.endsWith("/")) path += "index.html";
  try {
    const body = await readFileAsync(join(SITE, path));
    res.writeHead(200, { "content-type": MIME[extname(path)] || "application/octet-stream" });
    res.end(body);
  } catch { res.writeHead(404).end("not found"); }
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const panelBase = `http://127.0.0.1:${server.address().port}/llm-panel-review/`;
const readerBase = `http://127.0.0.1:${server.address().port}/spec-reader/`;

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage();
let pageErrors = [];
page.on("console", m => { if (m.type() === "error") pageErrors.push(m.text()); });
page.on("pageerror", e => pageErrors.push(String(e)));

let failures = 0;
const check = (ok, label, detail = "") => {
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${detail ? ` -- ${detail}` : ""}`);
};
const ready = () => {
  const el = document.querySelector("#passage-count");
  return el && !el.textContent.startsWith("Loading");
};
async function load(base, query) {
  pageErrors = [];
  await page.goto(base + query, { waitUntil: "networkidle" });
  await page.waitForFunction(ready, undefined, { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(250);
}
const sidebar = () => page.evaluate(() =>
  document.querySelector("#behaviour-list")?.textContent || "");
const cards = () => page.evaluate(() =>
  document.querySelectorAll(".passage").length);

const panelUrl = q => load(panelBase, q);

// =============================================================================
console.log("== Panel: payload resolution (bundled vs user-extended) ==");
await panelUrl("");
check((await sidebar()).includes("Acme transparency"),
  "default load resolves manifest latest = the user-extended run");
check(pageErrors.length === 0, "default load: no console errors", pageErrors.join("; "));

await panelUrl("?data=behaviours");
{
  const sb = await sidebar();
  check(!sb.includes("Acme transparency"), "?data=behaviours pin loads the shipped fallback");
}
await panelUrl(`?data=${PAYLOAD.replace(/\.json$/, "")}`);
check((await sidebar()).includes("Acme transparency"),
  "?data=<staged run> pin loads the user-extended run");
await panelUrl("?data=manifest.json");
check(pageErrors.length === 0 && (await sidebar()).includes("Acme transparency"),
  "?data=manifest.json is refused as a pin and degrades to manifest latest (no error)",
  pageErrors.join("; "));

// =============================================================================
console.log("== Panel: sidebar + behaviour selection ==");
await panelUrl("");
{
  const sb = await sidebar();
  check(sb.includes("Behaviours under test"),
    "group header present (B2: user behaviour shares the bundled group spelling)",
    sb.replace(/\s+/g, " ").slice(0, 100));
  check(sb.includes("Helpfulness"), "bundled behaviour present in the user-extended payload");
}
await panelUrl(`?behavior=${USER}&spec=${USER_SPEC}&tiers=defining,core,related`);
{
  const finding = await page.evaluate(() => ({
    name: document.querySelector("#finding-behaviour")?.textContent.trim(),
    def: document.querySelector("#finding-definition")?.textContent.trim() || "",
  }));
  check(finding.name === "Acme transparency", "?behavior= selects the user behaviour", finding.name);
  check(finding.def.includes("disclose compute usage"), "user behaviour definition renders");
}
await panelUrl("?behavior=no-such-behaviour");
check(pageErrors.length === 0 && (await page.evaluate(() =>
  document.querySelector("#finding-behaviour")?.textContent.trim().length > 0)),
  "unknown ?behavior= degrades to a real behaviour without errors",
  pageErrors.join("; "));

// =============================================================================
console.log("== Panel: tier bands (incl. the single-judge floor, B1) ==");
const acmeAll = q => panelUrl(`?behavior=${USER}&spec=${USER_SPEC}${q}`);
await acmeAll("");                       // default bands: defining + core
{
  const n = await cards();
  check(n === 1, "default bands: lone core vote renders, lone related vote waits in the related band", `${n} cards`);
}
await acmeAll("&tiers=defining,core,related");
{
  const n = await cards();
  check(n === 2, "all bands on: the single judge's related vote is reachable (B1)", `${n} cards`);
  const role = await page.evaluate(() =>
    [...document.querySelectorAll(".passage")].some(p => /score 2\/2/.test(p.textContent)));
  check(role, "passage card carries the recomputed score text (score 2/2)");
  const countText = await page.evaluate(() =>
    document.querySelector("#passage-count").textContent.trim());
  check(/of 2 passages/.test(countText), "passage counter total tracks the rendered anchors", countText);
}
await acmeAll("&tiers=none");
check((await cards()) === 0, "?tiers=none hides every band");
await acmeAll("&tiers=defining,core,related&related=0");
check((await cards()) === 1, "?related=0 zeroes the lone related vote (weight tuning survives B1)");

// =============================================================================
console.log("== Panel: document view, source link, compare, embedded ==");
await panelUrl(`?behavior=${USER}&spec=${USER_SPEC}&tiers=defining,core,related`);
{
  const href = await page.evaluate(() =>
    document.querySelector("#source-link")?.getAttribute("href") || "");
  check(href === "https://acme.example.com/spec",
    "source link carries the user spec's sourceUrl", href);
  const bodyText = await page.evaluate(() =>
    document.querySelector("#document-reader")?.textContent || "");
  check(bodyText.includes("disclose compute usage"), "user spec text renders behind the cards");
}
await panelUrl(`?behavior=${USER}&spec=no-such-spec`);
check(pageErrors.length === 0, "unknown ?spec= degrades to the default document without errors",
  pageErrors.join("; "));
await panelUrl(`?compare=1`);
{
  const out = await page.evaluate(() => ({
    panels: document.querySelectorAll(".document-panel").length,
    comparing: document.querySelector("#document-reader")?.classList.contains("compare"),
    toggle: document.querySelector("#compare-toggle")?.getAttribute("aria-pressed"),
    link: document.querySelector("#source-link")?.textContent.trim(),
  }));
  // Pins CURRENT behaviour (C7): compare is a two-pane view of the first two
  // documents; the 3rd (user) document is not reachable here by design today.
  check(out.panels === 2 && out.comparing, "?compare=1 renders the two-pane compare view",
    `${out.panels} panels`);
  check(out.toggle === "true", "compare toggle reflects ?compare=1");
  check(out.link === "Sources ↗", "source link switches to 'Sources ↗' in compare view", out.link);
}
await panelUrl("?embedded=1");
check(await page.evaluate(() => document.body.classList.contains("embedded")),
  "?embedded=1 sets the embedded body class");

// =============================================================================
console.log("== Panel: toolbar controls ==");
await panelUrl(`?behavior=${USER}&spec=${USER_SPEC}&tiers=defining,core,related`);
{
  const enabled = await page.evaluate(() =>
    !document.querySelector("#download-passages").disabled);
  check(enabled, "export-passages button enabled with a behaviour selected");
  const prevNext = await page.evaluate(() => ({
    prev: !document.querySelector("#previous-passage").disabled,
    next: !document.querySelector("#next-passage").disabled,
  }));
  check(prevNext.prev && prevNext.next, "prev/next passage buttons enabled with anchors present");
}
await panelUrl(`?behavior=${USER}&spec=${USER_SPEC}&tiers=defining,core,related`);
await page.click("#clear-behaviours");
await page.waitForTimeout(250);
check((await cards()) === 0, "clear-behaviours empties the view");
await page.click("#select-all-behaviours");
await page.waitForTimeout(250);
check((await cards()) > 0, "select-all-behaviours restores the view");
await panelUrl("?behavior=helpfulness");
{
  const before = await page.evaluate(() => document.body.dataset.palette);
  await page.click("#mode");
  await page.waitForTimeout(150);
  const after = await page.evaluate(() => document.body.dataset.palette);
  check(before !== after && ["daylight", "umber"].includes(after),
    "mode button toggles the palette", `${before} -> ${after}`);
}

// =============================================================================
console.log("== Reader: user-extended documents ==");
await load(readerBase, `?spec=${USER_SPEC}`);
{
  const out = await page.evaluate(() => ({
    body: document.querySelector("#document-reader")?.textContent || "",
    passages: document.querySelectorAll("[data-passage-id]").length,
    options: [...document.querySelectorAll(".spec-option")].map(o => o.dataset.spec),
  }));
  // Pins CURRENT behaviour (C12): the reader's spec options are hardcoded in
  // index.html to the two bundled specs; a user spec is reachable only via
  // ?spec= (checked next). If the options ever become documents.json-driven,
  // this tripwire fires and the check should flip to expecting the user spec.
  check(out.options.join(",") === "anthropic,openai",
    "reader spec options enumerate the bundled specs (user spec is URL-only today)",
    out.options.join(","));
  check(out.body.includes("disclose compute usage"), "user spec body renders in the reader");
  check(out.passages === 0, "user spec view shows 0 published passages (graceful empty state)");
  check(pageErrors.length === 0, "reader user-spec view: no console errors", pageErrors.join("; "));
}
{
  // Bundled regression: a published view still anchors exactly its passages.
  const b = userDocs.behaviours.find(x => x.slug === "no-sycophancy");
  const expected = b.coverage.anthropic.passages.length;
  await load(readerBase, "?behavior=no-sycophancy&spec=anthropic");
  const seen = await page.evaluate(() =>
    document.querySelectorAll("[data-passage-id]").length);
  check(seen === expected, "bundled view unregressed by the user-extended documents.json",
    `${seen}/${expected} passages`);
}

// =============================================================================
await browser.close();
server.close();
rmSync(scratch, { recursive: true, force: true });
console.log(failures ? `${failures} FAILURES` : "ALL FEATURE CHECKS PASSED.");
process.exit(failures ? 1 : 0);
