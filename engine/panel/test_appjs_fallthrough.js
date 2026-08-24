#!/usr/bin/env node
/* Automated guard for the three-tier payload resolution that
 * site/llm-panel-review/app.js implements:  ?data= pin -> manifest "latest" ->
 * shipped behaviours.json.  app.js runs DOM code at module scope, so it cannot be
 * imported directly; instead the resolution functions (dataUrl, payloadName,
 * loadBehaviours) are extracted verbatim from the real file and loadBehaviours is
 * driven against a stubbed loadJSON, exactly as the browser's fetch would resolve it.
 *
 * Exits 0 when every tier falls through as documented, 1 otherwise.
 * Run:  node engine/panel/test_appjs_fallthrough.js
 * (driven from test_panel.py::TestAppJSResolution; needs Node, no browser/keys)
 */
const fs = require("fs");
const path = require("path");

const APP_JS = path.join(__dirname, "..", "..", "site", "llm-panel-review", "app.js");
const src = fs.readFileSync(APP_JS, "utf8");
const lines = src.split("\n");

/* Extract a top-level function by brace depth (template-literal ${} braces balance,
 * so depth counting lands on the function's own closing brace). */
function extractFn(header) {
  const start = lines.findIndex(l => l.startsWith(header));
  if (start < 0) throw new Error(`not found in app.js: ${header}`);
  let depth = 0, began = false;
  for (let i = start; i < lines.length; i++) {
    for (const ch of lines[i]) {
      if (ch === "{") { depth++; began = true; }
      else if (ch === "}") { depth--; }
    }
    if (began && depth === 0) return lines.slice(start, i + 1).join("\n");
  }
  throw new Error(`unbalanced braces in app.js for: ${header}`);
}

const consts = lines.filter(l =>
  l.startsWith("const MANIFEST_URL") ||
  l.startsWith("const FALLBACK_DATA_URL") ||
  l.startsWith("const FALLBACK_DATA_NAME") ||
  l.startsWith("const DATA_NAME")).join("\n");

let runner, readSource;
eval(consts + "\n" +
  "let fetchMap = {};\n" +
  "const state = {};\n" +
  "let location;\n" +   // browser global, injected per-scenario below
  "async function loadJSON(url) {\n" +
  "  if (url in fetchMap) return fetchMap[url];\n" +
  "  throw new Error(\"HTTP 404 for \" + url);\n" +
  "}\n" +
  extractFn("function dataName(name)") + "\n" +
  extractFn("function dataUrl(name)") + "\n" +
  extractFn("function payloadName(name)") + "\n" +
  extractFn("async function loadBehaviours()") + "\n" +
  "runner = async (search, map) => { fetchMap = map; location = { search }; state.payloadSource = undefined; return loadBehaviours(); };\n" +
  "readSource = () => state.payloadSource;");

const PIN = { behaviours: ["PIN"] };
const LATEST = { behaviours: ["LATEST"] };
const FALLBACK = { behaviours: ["FALLBACK"] };

let failures = 0;
function check(label, actual, expected) {
  const got = JSON.stringify(actual);
  const want = JSON.stringify(expected);
  if (got === want) console.log(`PASS  ${label}: ${got}`);
  else { failures++; console.log(`FAIL  ${label}: got ${got}, expected ${want}`); }
}

/* payloadSource with undefined keys dropped, so a served pin and a fallen-through one
   are compared on the same shape. */
const source = () => JSON.parse(JSON.stringify(readSource() ?? null));

const realWarn = console.warn; console.warn = () => {};   // silence expected fall-through warnings

(async () => {
  // Tier 1: a resolvable pin wins over latest and the shipped default.
  let r = await runner("?data=behaviours-pin", {
    "./data/behaviours-pin.json": PIN,
    "./data/manifest.json": { latest: "behaviours-latest" },
    "./data/behaviours-latest.json": LATEST,
    "./data/behaviours.json": FALLBACK });
  check("tier 1: pin resolves", r.behaviours, ["PIN"]);
  // The sidebar run block reads payloadSource; a served pin reports no `requested`,
  // because there is nothing the viewer asked for and did not get.
  check("tier 1: source recorded", source(), { origin: "pin", name: "behaviours-pin.json" });

  // Tier 2: a stale/absent pin falls through to the manifest's latest run.
  r = await runner("?data=behaviours-missing", {
    "./data/manifest.json": { latest: "behaviours-latest" },
    "./data/behaviours-latest.json": LATEST,
    "./data/behaviours.json": FALLBACK });
  check("tier 2: manifest latest", r.behaviours, ["LATEST"]);
  check("tier 2: fall-through names what was asked for", source(),
    { origin: "latest", name: "behaviours-latest.json",
      requested: { name: "behaviours-missing", refused: false } });

  // Tier 3: stale pin + no manifest (fresh clone) falls through to the shipped default.
  r = await runner("?data=behaviours-missing", {
    "./data/behaviours.json": FALLBACK });
  check("tier 3: shipped default", r.behaviours, ["FALLBACK"]);
  check("tier 3: fall-through to shipped names what was asked for", source(),
    { origin: "fallback", name: "behaviours.json",
      requested: { name: "behaviours-missing", refused: false } });

  // Manifest exclusion: ?data=manifest.json must never load the run ledger -- the pin
  // tier refuses it and the chain falls through to the next source (latest here).
  r = await runner("?data=manifest.json", {
    "./data/manifest.json": { latest: "behaviours-latest" },
    "./data/behaviours-latest.json": LATEST,
    "./data/behaviours.json": FALLBACK });
  check("refused pin is recorded as refused, not merely unavailable", (await (async () => {
    await runner("?data=manifest.json", {
      "./data/manifest.json": { latest: "behaviours-latest" },
      "./data/behaviours-latest.json": LATEST,
      "./data/behaviours.json": FALLBACK });
    return source().requested;
  })()), { name: "manifest.json", refused: true });

  check("pin=manifest.json falls through, ledger not loaded", r.behaviours, ["LATEST"]);

  // A self-referential manifest ("latest": "manifest.json") must not load the ledger.
  r = await runner("", {
    "./data/manifest.json": { latest: "manifest.json" },
    "./data/behaviours.json": FALLBACK });
  check("latest=manifest.json refused", r.behaviours, ["FALLBACK"]);

  console.warn = realWarn;
  if (failures) {
    console.log(`app.js three-tier fallthrough: ${failures} FAILURE(S)`);
    process.exit(1);
  }
  console.log("app.js three-tier fallthrough: PASS " +
    "(pin -> manifest latest -> shipped default; manifest never loadable as a payload)");
})().catch(error => {
  console.warn = realWarn;
  console.log(`app.js three-tier fallthrough: ERROR ${error.message}`);
  process.exit(1);
});
