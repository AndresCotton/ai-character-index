/* Local mode: says so when a surface is showing a run of your own.
 *
 * A user registers their own specifications through specs/user/specs.json, and
 * build-spec-reader-data.py folds them into documents.json marked `lab: "User"`. That
 * marker is the whole signal -- nothing else needs to be built or stamped, and a site
 * with only the two bundled mirrors is untouched by this file.
 *
 * Two things follow from it:
 *
 *  - The page says the data is local. Production and a local clone are otherwise
 *    pixel-identical, and payload resolution deliberately falls through to the shipped
 *    data rather than failing, so without this a reader has no way to tell which one
 *    they are looking at.
 *
 *  - The panel becomes reachable. site/llm-panel-review/ is unlisted and noindexed:
 *    nothing in site/ links to it, which is right for the project's own calibration
 *    bench but wrong once it is also where YOUR run lands. The link appears only when
 *    there is a local run to look at, so the public site keeps its shape.
 *
 * Shared by all three surfaces rather than copied into each: the three app.js files
 * already carry three copies of too much, and new behaviour should not add a fourth.
 */
const PANEL_HREF = "llm-panel-review";

const onPanel = () => location.pathname.includes(`/${PANEL_HREF}/`);
let DOCUMENTS_URL_HINT = "documents.json";   // for the diagnostic below

/* The panel already sits in its own nav, marked as the current page. A second link to
 * it under another name would just be two names for where you already are, so the link
 * is only ever added to the surfaces a reader arrives on. */
/* The link says what the page it lands on is called. "Local analysis" describes the
 * job better, but the page is still titled "LLM panel review", and a link that names
 * its destination something else is a broken contract -- the rename, if it happens,
 * moves both together. */
function addPanelLink(nav) {
  if (!nav || onPanel() || nav.querySelector(`a[href*="${PANEL_HREF}"]`)) return;
  const link = document.createElement("a");
  link.href = `../${PANEL_HREF}/`;
  link.textContent = "LLM panel review";
  link.dataset.localOnly = "true";
  /* Before the palette button, so the nav keeps its shape: links, then the control. */
  const mode = nav.querySelector("#mode");
  if (mode) nav.insertBefore(link, mode);
  else nav.append(link);
}

/* A status marker, not a destination: it goes in the header beside the wordmark, not
 * into the navigation list, where anything traversing the links -- a screen reader
 * included -- would read it as one.
 *
 * It names WHAT is local rather than announcing that something is. "Local data" reads
 * as offline or stale; the fact is that this page is showing specifications registered
 * on this machine. The tooltip carries the consequence, and is treated as an extra:
 * it does not exist on a touch device. */
function addNote(header, nav) {
  if (!header || document.getElementById("local-data-note")) return;
  const note = document.createElement("span");
  note.id = "local-data-note";
  note.className = "local-data-note";
  note.textContent = "Local specifications";
  note.title = "Specifications registered on this machine are included here. "
    + "Runs you make stay local -- they are never published to the index.";
  if (nav) header.insertBefore(note, nav);
  else header.append(note);
}

/* documents.json is the one file every surface loads, so it is the one place the
 * answer can come from.
 *
 * "No user specification" and "could not tell" are different answers and must not look
 * the same. The first is the ordinary bundled case and is silent. The second -- a parse
 * error, a 404 from a moved path, a blocked request -- would leave a page that IS local
 * showing nothing, which is exactly the ambiguity this file exists to remove, so it
 * says so on the console. */
export async function initLocalMode() {
  let documents = [];
  try {
    /* Only the reader holds documents.json; the bench and the panel both read it
     * from there. "/spec-reader-test/" does not contain "/spec-reader/", so the
     * bench correctly takes the sibling path. */
    const url = location.pathname.includes("/spec-reader/")
      ? "./data/documents.json"
      : "../spec-reader/data/documents.json";
    DOCUMENTS_URL_HINT = url;
    documents = (await (await fetch(url)).json()).documents || [];
  } catch (error) {
    console.warn(`local-mode: could not read ${DOCUMENTS_URL_HINT} (${error.message}); `
      + "a local run would not be marked.");
    return;
  }
  if (!documents.some(document_ => document_.lab === "User")) return;

  document.body.dataset.localData = "true";
  const nav = document.querySelector("nav");
  addNote(document.querySelector(".site-header") || nav?.parentElement, nav);
  addPanelLink(nav);
}

initLocalMode();
