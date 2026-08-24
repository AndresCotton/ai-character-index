#!/usr/bin/env node
/* Automated guard for the quote-anchoring helpers in
 * site/llm-panel-review/app.js (passageFragments + containsInOrder, extracted
 * verbatim from the real file -- not reimplemented here).
 *
 * The load-bearing case is the empty-fragment guard. A quote consisting only of
 * an admonition marker and/or cross-references normalizes to zero fragments.
 * containsInOrder must call that UNRESOLVED, because an in-order scan over an
 * empty fragment list vacuously succeeds against every block -- so returning
 * true silently anchors the passage to whatever block is checked first.
 *
 * This file exists because that guard shipped with no coverage: inverting it
 * left the tier harness, the fallthrough harness and the Playwright feature
 * walker all green, and the inverted line reached main.
 *
 * Exits 0 when every pinned behaviour holds, 1 otherwise, and prints a final
 * count line the Python driver asserts on (a harness that silently stopped
 * asserting would otherwise still exit 0).
 * Run:  node engine/panel/test_appjs_quotes.js
 * (driven from test_panel.py::TestAppJSQuotes; needs Node, no browser/keys)
 */
const fs = require("fs");
const path = require("path");

const APP_JS = path.join(__dirname, "..", "..", "site", "llm-panel-review", "app.js");
const src = fs.readFileSync(APP_JS, "utf8");
const lines = src.split("\n");

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

eval(extractFn("function normalize(value) {"));
eval(extractFn("function passageFragments(quote) {"));
eval(extractFn("function containsInOrder(haystack, fragments) {"));

let checks = 0, failures = 0;
function check(got, want, label) {
  checks += 1;
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: ${JSON.stringify(got)} (expected ${JSON.stringify(want)})`);
}

/* The guard itself, stated both ways round. An empty fragment list is the
 * vacuous-truth case: every loop over it succeeds, so the answer has to come
 * from the guard rather than from the scan. */
check(containsInOrder("any block at all", []), false,
      "no fragments is unresolved, not a match against every block");
check(containsInOrder("", []), false,
      "no fragments is unresolved even against an empty haystack");

/* A quote that really does reduce to nothing -- these are the inputs that
 * reach the guard in production, so they are pinned as fragments AND as the
 * anchoring answer, not just as one or the other. */
for (const [quote, label] of [
  ["!!! note", "an admonition marker alone"],
  ["!!! warning #SomeAnchor", "a marker plus a cross-reference"],
  ["#Anchor", "a bare cross-reference"],
  ["#One #Two", "consecutive cross-references"],
]) {
  check(passageFragments(quote), [], `${label} yields no fragments`);
  check(containsInOrder("a document block", passageFragments(quote)), false,
        `${label} does not anchor`);
}

/* The ordinary path must keep working -- a guard that rejected everything
 * would also pass the checks above. */
check(passageFragments("the quick brown fox").length, 1,
      "a plain quote is one fragment");
check(containsInOrder(normalize("the quick brown fox jumps"),
                      passageFragments("the quick brown fox")), true,
      "a plain quote matches a block containing it");
check(containsInOrder(normalize("the quick brown dog"),
                      passageFragments("the quick brown fox")), false,
      "a plain quote does not match a block lacking it");

/* Order is the contract: the fragments of a split quote must appear in
 * sequence, not merely both be present somewhere. */
const split = passageFragments("alpha #Ref omega");
check(split.length, 2, "a cross-reference splits a quote into two fragments");
check(containsInOrder(normalize("alpha then omega"), split), true,
      "split fragments match when they appear in order");
check(containsInOrder(normalize("omega then alpha"), split), false,
      "split fragments do not match when the order is reversed");
check(containsInOrder(normalize("alpha only"), split), false,
      "split fragments do not match when the second is absent");

console.log(`\n${checks} checks, ${failures} failures`);
process.exit(failures ? 1 : 0);
