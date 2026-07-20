#!/usr/bin/env node
// Verify the spec reader against site/spec-reader/data/documents.json:
// every behaviour x spec view must anchor exactly its published passage count,
// with no unresolved-anchor warnings and no console errors.
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

async function expectView(url, expected, label) {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () => !document.querySelector("#passage-count").textContent.startsWith("Loading"),
    { timeout: 10000 },
  );
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

if (consoleErrors.length) {
  failures += 1;
  console.log("console errors:", consoleErrors);
}
await browser.close();
server.close();
console.log(failures ? `${failures} failures` : "All views verified.");
process.exit(failures ? 1 : 0);
