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

eval(extractFn("function judgesPerCell() {"));
eval(extractFn("function maxCellScore() {"));
var state = {};

let failures = 0;

/* Scale detection: one payload can carry cells at different scales, because
 * maxVerdict is per-cell (2 on the classic rubric, 3 once a judge awards a
 * "defining"). behaviours-v5.json really does mix 6 and 9. */
function checkScale(behaviours, expectedJudges, expectedScale, label) {
  state.rawBehaviours = behaviours;
  const j = judgesPerCell(), s = maxCellScore();
  const ok = j === expectedJudges && s === expectedScale;
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: judges ${j} (want ${expectedJudges}), ` +
              `scale ${s} (want ${expectedScale})`);
}

const cell = verdicts => ({ coverage: { anthropic: { passages: verdicts.map(v => ({ verdicts: v })) } } });
checkScale([], 0, 0, "no data yet -- helpers return 0, legacy cuts fall back");
checkScale([cell([{ a: 2, b: 2, c: 2 }])], 3, 6, "3-judge classic cell is 6-scale");
checkScale([cell([{ a: 3, b: 2, c: 1 }])], 3, 9, "a single defining verdict makes the cell 9-scale");
checkScale([cell([{ a: 2, b: 2 }])], 2, 4, "2-judge classic cell is 4-scale");
checkScale([cell([{ a: 2, b: 2, c: 2 }]), cell([{ a: 3, b: 3, c: 3 }])],
           3, 9, "mixed payload takes the largest scale");

/* The legacy ?threshold= cuts. Extracted from app.js, NOT reimplemented here: an
 * earlier version of this block copied the arithmetic and kept passing after the
 * real code was regressed back to the frozen constants. */
eval(extractFn("function legacyThresholdBands(t, judges, scale) {"));

function checkLegacy(t, judges, scale, expected, label) {
  const seen = legacyThresholdBands(t, judges, scale).join("+");
  const ok = seen === expected;
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: ?threshold=${t} at j=${judges}/scale=${scale} -> ${seen} (expected ${expected})`);
}
checkLegacy(7, 3, 9, "defining", "9-scale: 7 is the defining cut");
checkLegacy(6, 3, 9, "defining+core", "9-scale: 6 is the core cut");
checkLegacy(6, 3, 6, "defining", "6-scale: 6 IS defining (the frozen constants said defining+core)");
checkLegacy(5, 2, 4, "defining", "2-judge 4-scale: 5 clamps to the defining cut");
checkLegacy(4, 2, 4, "defining", "2-judge: defCut clamps to maxCell=4");

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

/* bandReachable: which tiers a cell can put a passage in at all. The header
 * disables a tier nothing can reach, so these cuts decide whether a toggle is
 * live -- a wrong answer here either hides a working control or leaves an inert
 * one on screen. Must agree with tierBand: a band is reachable exactly when some
 * score in 0..maxCell lands in it. */
// TIERS is load-bearing for strongestBand (it must be strongest-first) and also drives
// ?tiers= serialisation and the legacy ?tier= mapping, so it is pinned here explicitly.
// `const` inside eval stays block-scoped, so it is re-declared as `var` to reach here.
eval(lines.filter(l => l.startsWith("const TIERS =")).join("\n").replace(/^const /, "var "));
eval(extractFn("function strongestBand(bands) {"));
eval(extractFn("function bandLabel(band) {"));
eval(extractFn("function achievableScores(judges, maxCell, related) {"));
eval(extractFn("function bandReachable(judges, maxCell, related) {"));

function checkReach(judges, maxCell, related, expected, label) {
  const seen = bandReachable(judges, maxCell, related);
  const ok = TIERS_ORDER.every(t => seen[t] === expected[t]);
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: j=${judges}, maxCell ${maxCell}, ` +
    `related ${related} -> ${JSON.stringify(seen)} (expected ${JSON.stringify(expected)})`);
}
const TIERS_ORDER = ["defining", "core", "related"];

// 3-point rubric (v3w): maxCell is always 2j, so defCut clamps onto coreCut and
// core is unreachable at EVERY judge count -- including the shipped 3-judge data.
checkReach(1, 2, 1, { defining: true, core: false, related: true }, "1j 3-point: core unreachable");
checkReach(2, 4, 1, { defining: true, core: false, related: true }, "2j 3-point: core unreachable");
checkReach(3, 6, 1, { defining: true, core: false, related: true }, "3j 3-point: core unreachable (shipped data)");
// 4-point rubric (v5+): defCut sits above coreCut, so all three bands are live.
checkReach(1, 3, 1, { defining: true, core: true, related: true }, "1j 4-point: all three live");
checkReach(3, 9, 1, { defining: true, core: true, related: true }, "3j 4-point: all three live");

/* A fractional ?related= weight makes the achievable set sparse, so a cut can sit in a
 * gap between two reachable scores. Deriving reachability from the cuts alone reported
 * the related band as live here; no passage can score into it. */
checkReach(2, 4, 0.5, { defining: true, core: false, related: false },
  "2j 3-point, ?related=0.5: related cut falls in a gap (achievable: 0,.5,1,2,2.5,4)");
checkReach(3, 6, 0.5, { defining: true, core: false, related: true },
  "3j 3-point, ?related=0.5: related still reachable (the gap is judge-count specific)");
checkReach(1, 2, 0, { defining: true, core: false, related: false },
  "1j ?related=0: a zeroed related vote scores 0, so the band cannot fill");

/* Cross-check over the scores a cell can ACTUALLY produce, for every shape above plus
 * fractional weights -- an integer-only sweep cannot see a cut sitting in a gap. */
for (const [judges, maxCell] of [[1, 2], [2, 4], [3, 6], [4, 8], [1, 3], [3, 9]]) {
  for (const related of [1, 0.5, 0.25, 0]) {
    const reach = bandReachable(judges, maxCell, related);
    const landed = { defining: false, core: false, related: false };
    for (const s of achievableScores(judges, maxCell, related)) {
      const b = tierBand(s, judges, maxCell, related);
      if (b) landed[b] = true;
    }
    const ok = TIERS_ORDER.every(t => reach[t] === landed[t]);
    if (!ok) failures += 1;
    console.log(`${ok ? "PASS" : "FAIL"}  reachability matches tierBand over achievable ` +
      `scores (j=${judges}, maxCell=${maxCell}, related=${related})`);
  }
}

/* strongestBand / bandLabel: the vocabulary the rail and the export print. */
function checkEq(actual, expected, label) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: ${JSON.stringify(actual)} (expected ${JSON.stringify(expected)})`);
}

// The order of TIERS IS the precedence rule. strongestBand reads it directly, and
// reordering it would silently relabel every multi-behaviour block, so pin it.
checkEq(TIERS, ["defining", "core", "related"], "TIERS is ordered strongest-first");

checkEq(strongestBand(["related", "defining"]), "defining",
  "a block that is defining for one behaviour and related to another is named by the stronger");
checkEq(strongestBand(["related", "core"]), "core", "core outranks related");
checkEq(strongestBand(["related"]), "related", "a lone related block stays related");
checkEq(strongestBand([]), null, "no bands -> null");
checkEq(strongestBand([null, undefined]), null, "only empty bands -> null");

checkEq(bandLabel("defining"), "Defining", "bandLabel capitalises the band");
checkEq(bandLabel("related"), "Related", "bandLabel capitalises related");
checkEq(bandLabel(null), "Scored", "an unbanded passage falls back to a neutral word");
checkEq(bandLabel(""), "Scored", "an empty data-band falls back too");

process.exit(failures ? 1 : 0);
