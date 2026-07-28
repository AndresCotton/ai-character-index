#!/usr/bin/env python3
"""Annotation knob (#3 from the design doc): optionally augment the behaviour direction
with LLM-generated text -- rephrasing, expansion, or worked examples -- then test whether
the augmented direction agrees with the Kimi-K3 judge BETTER than the base ("None") does.

Two steps:
  python3 annotate.py generate            # LLM-write variants -> annotations.json
  python3 annotate.py eval [provider]     # embed each variant, score corpus, compare to K3

Generation uses a cheap strong open model on DeepInfra (reuses DEEPINFRA_API_KEY). Eval
reuses the cached corpus embeddings (no re-embedding of the spec) and the saved K3 paragraph
scores as the reference. Nothing here touches the demo; it's a standalone experiment.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score  # corpus(), cache_path(), embed(), cosine(), load_key(), PROVIDERS

GEN_BASE = "https://api.deepinfra.com/v1/openai"
GEN_MODEL = "deepseek-ai/DeepSeek-V3.2"          # cheap, strong instruction-follower
ANNOTATIONS = HERE / "annotations.json"
VARIANTS = ("rephrase", "expand", "worked_examples")

PROMPTS = {
    "rephrase": "Rephrase the following AI-behaviour definition in different words while "
                "preserving its exact meaning and scope. Return only the rephrased definition, no preamble.",
    "expand": "Expand the following AI-behaviour definition: add the closely-related concepts, "
              "sub-cases, and vocabulary a reader would use to recognise this behaviour in a policy "
              "document, without broadening its scope. Return only the expanded definition, no preamble.",
    "worked_examples": "For the following AI-behaviour, write 3-5 short concrete worked examples of what "
                       "upholding or violating it looks like in practice. Return only the examples as a "
                       "single block of text, no preamble.",
}


def generate():
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    key = score.load_key("DEEPINFRA_API_KEY")
    from openai import OpenAI
    client = OpenAI(api_key=key, base_url=GEN_BASE)
    out = {}
    for name, b in behaviours.items():
        out[name] = {"None": b["query"]}
        for v in VARIANTS:
            msg = [{"role": "system", "content": PROMPTS[v]},
                   {"role": "user", "content": b["query"]}]
            r = client.chat.completions.create(model=GEN_MODEL, temperature=0.2, messages=msg)
            text = r.choices[0].message.content.strip()
            # augmented direction = base + augmentation (the doc: "add more text to the encoding")
            out[name][v] = b["query"] + "\n\n" + text if v != "rephrase" else text
            print(f"  {name} / {v}: {len(text)} chars")
    ANNOTATIONS.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {ANNOTATIONS.name} ({len(out)} behaviours x {1 + len(VARIANTS)} variants)")


def rankavg(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0
        i = j + 1
    return r


def auc(scores, labels):
    pos = [i for i, l in enumerate(labels) if l]
    neg = [i for i, l in enumerate(labels) if not l]
    if not pos or not neg:
        return float("nan")
    rb = rankavg(scores)
    s = sum(rb[i] + 1 for i in pos)
    return (s - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def spearman(a, b):
    ra, rb = rankavg(a), rankavg(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((x - mb) ** 2 for x in rb) ** 0.5
    return num / (da * db) if da and db else 0.0


def evaluate(provider):
    ann = json.loads(ANNOTATIONS.read_text())
    cfg = score.PROVIDERS[provider]
    model = cfg["model"]
    key = score.load_key(cfg["key"])
    from openai import OpenAI
    client = OpenAI(api_key=key, base_url=cfg["base_url"]) if cfg["base_url"] else OpenAI(api_key=key)
    units = score.corpus("paragraph")               # (loc, text)
    cache = score.corpus_embeddings(client, model, "paragraph", units)   # reuses cached vectors
    print(f"\nannotation eval [{provider}: {model}] -- AUC/Spearman vs Kimi-K3 (paragraph)\n")
    for name, variants in ann.items():
        k3 = json.loads((HERE / f"scores-{name}-Kimi-K3.json").read_text())
        kmap = {r["locator"]: r["score"] for r in k3["results"]}
        klab = [kmap.get(loc, 0.0) >= 0.5 for loc, _ in units]
        kval = [kmap.get(loc, 0.0) for loc, _ in units]
        print(name)
        for v, text in variants.items():
            qv = score.embed(client, model, [text])[0]
            s = [score.cosine(qv, cache[loc]) for loc, _ in units]
            print(f"  {v:16} AUC {auc(s, klab):.3f}   spearman {spearman(s, kval):.3f}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "generate":
        generate()
    elif cmd == "eval":
        evaluate(sys.argv[2] if len(sys.argv) > 2 else "openai")
    else:
        sys.exit("usage: annotate.py generate | eval [provider]")


if __name__ == "__main__":
    main()
