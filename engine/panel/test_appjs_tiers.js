#!/usr/bin/env node
/* Automated guard for the tier-band cuts that site/llm-panel-review/app.js
 * applies to panel-scored passages (tierBand, extracted verbatim from the real
 * file). Pins BOTH regimes:
 *
 *  - multi-judge cells keep the consensus floor: related needs score >= j+1
 *    (at least two judges behind it), core >= 2j, defining >= 2j+1 clamped to
 *    the cell's max (unanimous core counts as defining on 3-point data);
 *  - single-judge cells (the clone/fork cheap-run case) render the sole
 *    judge's related vote at its own weight instead of hiding it under the
 *    multi-judge floor; zeroing the related weight (?related=0) hides them.
 *
 * Exits 0 when every pinned cut holds, 1 otherwise.
 * Run:  node engine/panel/test_appjs_tiers.js
 * (driven from test_panel.py::TestAppJSTiers; needs Node, no browser/keys)
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

eval(extractFn("function tierBand(score, judges, maxCell, related) {"));

let failures = 0;
function check(score, judges, maxCell, related, expected, label) {
  const seen = tierBand(score, judges, maxCell, related);
  const ok = seen === expected;
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: score ${score}, j=${judges}, ` +
    `maxCell ${maxCell}, related ${related} -> ${seen} (expected ${expected})`);
}

/* Multi-judge regime: the consensus floor is unchanged. */
// 3 judges, 3-point cell (maxCell 6): unanimous core clamps to defining.
check(6, 3, 6, 1, "defining", "3j unanimous core = defining (clamp)");
check(5, 3, 6, 1, "related",   "3j two-core-plus-related = related");
check(4, 3, 6, 1, "related",   "3j two cores = related");
check(3, 3, 6, 1, null,        "3j three lone related votes below floor = hidden");
check(2, 3, 6, 1, null,        "3j lone related pair below floor = hidden");
// 2 judges, 3-point cell (maxCell 4): unanimous core clamps to defining.
check(4, 2, 4, 1, "defining", "2j unanimous core = defining (clamp)");
check(3, 2, 4, 1, "related",  "2j core+related = related");
check(2, 2, 4, 1, null,       "2j lone core below floor = hidden");

/* Single-judge regime (the fix): the sole verdict is the whole evidence. */
check(1, 1, 2, 1, "related", "1j lone related vote renders as related");
check(2, 1, 2, 1, "defining", "1j lone core = unanimous-core clamp = defining (core band empty, as with 3j)");
check(0, 1, 2, 1, null,      "1j unrelated vote hidden");
// 4-point single-judge cell: a 3-vote reaches defining, a 2-vote core, a 1-vote related.
check(3, 1, 3, 1, "defining", "1j 4-point 3-vote = defining");
check(2, 1, 3, 1, "core",     "1j 4-point 2-vote = core");
check(1, 1, 3, 1, "related",  "1j 4-point 1-vote = related");
// Related-weight tuning still applies to single-judge cells. A zeroed weight
// scores the vote 0 at tally time, so it stays hidden (cut falls back to 1).
check(0.5, 1, 2, 0.5, "related", "1j half-weight related vote renders at its weight");
check(0, 1, 2, 0, null,          "1j ?related=0: lone related vote scores 0 and hides");
check(2, 1, 2, 0, "defining",    "1j ?related=0 still shows core votes (unanimous-core clamp)");
// The multi-judge floor never uses the single-judge rule.
check(1, 2, 4, 1, null, "2j lone related still hidden (floor applies)");

process.exit(failures ? 1 : 0);
