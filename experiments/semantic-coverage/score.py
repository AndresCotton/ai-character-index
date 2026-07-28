#!/usr/bin/env python3
"""Semantic coverage demo -- score every spec block by similarity to a behaviour.

Reuses cite.py's segmentation + locators, so each scored unit is a resolvable locator
(spec@version > section > paragraph). The embedding model is a config knob:

    python3 score.py <behaviour> [provider]   # provider: openai (default) | deepinfra

Set the relevant key in the environment or a .env file next to this script:
    OPENAI_API_KEY=sk-...
    DEEPINFRA_API_KEY=...

Writes scores-<behaviour>-<provider>.json + viewer-<behaviour>-<provider>.html (a slider).
Block embeddings are cached to disk per model, so a second behaviour reuses the corpus
embedding and only the query is re-embedded.
"""
import html
import json
import math
import os
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "engine" / "spec-cite"))
import cite  # noqa: E402

# Both providers speak the OpenAI embeddings API -- only base_url / model / key differ.
PROVIDERS = {
    "openai": {"base_url": None,
               "model": "text-embedding-3-small", "key": "OPENAI_API_KEY"},
    "deepinfra": {"base_url": "https://api.deepinfra.com/v1/openai",
                  "model": "Qwen/Qwen3-Embedding-8B", "key": "DEEPINFRA_API_KEY"},
}
DEFAULT_PROVIDER = "openai"
SPECS = ("constitution", "model-spec")


def cache_path(model, chunk):
    tag = model.replace('/', '_')
    return HERE / (f"cache-{tag}.pkl" if chunk == "paragraph" else f"cache-{tag}-{chunk}.pkl")


def load_key(name):
    key = os.environ.get(name)
    if not key and (HERE / ".env").exists():
        for line in (HERE / ".env").read_text().splitlines():
            if line.strip().startswith(name + "="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    return key


def units_meta(chunk="paragraph"):
    """(locator, spec, section, text) for every scorable chunk of both specs.

    Skips table-of-contents blocks: the constitution's H1 span is a list of section
    titles, so any block whose text is exactly a section heading is navigation, not
    content. ¶ numbering is preserved so locators stay stable. chunk='sentence' splits
    each kept paragraph via cite.split_sentences, locator '... > ¶i > sj'.
    """
    out = []
    for spec in SPECS:
        version, sections, lines = cite.load_spec(spec, None)
        titles = {cite.normalize(sec.path_str.split(" > ")[-1]) for sec in sections}
        for sec in sections:
            ref = f"#{sec.anchor}" if (spec == "model-spec" and sec.anchor) else sec.path_str
            for i, raw in enumerate(cite.segment_blocks(lines, sec.start, sec.end), 1):
                text = cite.normalize(raw)
                if not text.strip() or text in titles:
                    continue
                base = f"{spec}@{version} > {ref} > ¶{i}"
                if chunk == "sentence":
                    for j, sent in enumerate(cite.split_sentences(text), 1):
                        s = sent.strip()
                        if s:
                            out.append((f"{base} > s{j}", spec, sec.path_str, s))
                else:
                    out.append((base, spec, sec.path_str, text))
    return out


def corpus(chunk="paragraph"):
    """(locator, text) for every scorable chunk -- the embedding units."""
    return [(loc, text) for loc, _, _, text in units_meta(chunk)]


def embed(client, model, texts):
    vecs = []
    for k in range(0, len(texts), 128):
        resp = client.embeddings.create(model=model, input=texts[k:k + 128])
        vecs.extend(d.embedding for d in resp.data)
    return vecs


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def corpus_embeddings(client, model, chunk, units):
    cache_file = cache_path(model, chunk)
    cache = pickle.loads(cache_file.read_bytes()) if cache_file.exists() else {}
    missing = [(loc, txt) for loc, txt in units if loc not in cache]
    if missing:
        print(f"embedding {len(missing)} new blocks (cache had {len(cache)})...", file=sys.stderr)
        for (loc, _), v in zip(missing, embed(client, model, [t for _, t in missing])):
            cache[loc] = v
        cache_file.write_bytes(pickle.dumps(cache))
    return cache


VIEWER = """<!doctype html><meta charset=utf-8><title>semantic coverage</title>
<style>body{font:14px system-ui;margin:2rem;max-width:62rem}
.row{padding:.45rem 0;border-top:1px solid #eee}.loc{color:#06c;font-family:monospace}
.score{display:inline-block;width:3.5rem;font-weight:600}small{color:#444}</style>
<h2>__LABEL__</h2>
<p>score threshold <input id=t type=range min=0 max=1 step=.01 value=.3 oninput="render()">
<b id=tv>0.30</b> &mdash; showing <b id=n></b> of __N__ blocks</p>
<div id=out></div>
<script>
var R=__DATA__;
function esc(s){return String(s).replace(/</g,'&lt;');}
function render(){
 var th=+document.getElementById('t').value;
 document.getElementById('tv').textContent=th.toFixed(2);
 var hits=R.filter(function(r){return r.score>=th;});
 document.getElementById('n').textContent=hits.length;
 document.getElementById('out').innerHTML=hits.map(function(r){
  return '<div class=row><span class=score>'+r.score.toFixed(3)+'</span> '+
   '<span class=loc>'+esc(r.locator)+'</span><br><small>'+esc(r.snippet)+'</small></div>';
 }).join('');
}
render();
</script>"""


def main():
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    name = sys.argv[1] if len(sys.argv) > 1 else None
    provider = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROVIDER
    chunk = sys.argv[3] if len(sys.argv) > 3 else "paragraph"
    if name not in behaviours:
        sys.exit(f"usage: score.py <behaviour> [provider] [chunk]   behaviours: {', '.join(behaviours)}")
    if provider not in PROVIDERS:
        sys.exit(f"unknown provider {provider!r} -- choices: {', '.join(PROVIDERS)}")
    if chunk not in ("paragraph", "sentence"):
        sys.exit("chunk must be 'paragraph' or 'sentence'")
    label, query = behaviours[name]["label"], behaviours[name]["query"]
    source = behaviours[name].get("source", "")
    cfg = PROVIDERS[provider]
    model = cfg["model"]

    key = load_key(cfg["key"])
    if not key:
        sys.exit(f"no {cfg['key']} -- set the env var, or put {cfg['key']}=... in a "
                 ".env next to score.py")
    from openai import OpenAI
    client = OpenAI(api_key=key, base_url=cfg["base_url"]) if cfg["base_url"] else OpenAI(api_key=key)

    units = corpus(chunk)
    cache = corpus_embeddings(client, model, chunk, units)
    qvec = embed(client, model, [query])[0]

    results = [{"locator": loc, "score": round(cosine(qvec, cache[loc]), 4),
                "snippet": text[:220]} for loc, text in units]
    results.sort(key=lambda r: -r["score"])

    stem = f"{name}-{provider}" + ("" if chunk == "paragraph" else f"-{chunk}")
    (HERE / f"scores-{stem}.json").write_text(json.dumps(
        {"behaviour": name, "label": label, "query": query, "source": source,
         "provider": provider, "model": model, "chunk": chunk,
         "n_blocks": len(results), "results": results}, indent=2))
    (HERE / f"viewer-{stem}.html").write_text(
        VIEWER.replace("__LABEL__", html.escape(f"{label}  [{model}, {chunk}]"))
              .replace("__N__", str(len(results)))
              .replace("__DATA__", json.dumps(results)))

    print(f"\n{label}  [{provider}: {model}, {chunk}]")
    print(f"{len(results)} chunks scored -> scores-{stem}.json, viewer-{stem}.html")
    print("top 12:")
    for r in results[:12]:
        print(f"  {r['score']:.3f}  {r['locator']}")


if __name__ == "__main__":
    main()
