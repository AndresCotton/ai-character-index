#!/usr/bin/env python3
"""LLM-judge per-chunk relevance scoring via DeepInfra chat (OpenAI-compatible) -- a cheap,
strong comparison column to the embeddings. Reuses the DeepInfra key already in .env.

  python3 judge.py <behaviour> [model] [--test]
      model default: moonshotai/Kimi-K2.6
      --test: score only the first batch (validate output + measure real token cost)

Writes scores-<behaviour>-<model-tag>.json (same format as score.py) so the demo shows it
as its own column, and prints real prompt/completion token usage.
"""
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score  # reuse corpus() (paragraph, TOC-filtered) + behaviours.json

BATCH = 40
PROVIDERS = {
    "deepinfra": ("https://api.deepinfra.com/v1/openai", "DEEPINFRA_API_KEY"),
    "together": ("https://api.together.xyz/v1", "TOGETHER_API_KEY"),
}
DEFAULT_PROVIDER = "together"
DEFAULT_MODEL = "moonshotai/Kimi-K2-Instruct"  # override on CLI with the exact Kimi-K3 id

RUBRIC = (
    "You score how RELEVANT each spec passage is to a target behaviour -- whether the "
    "passage states, governs, supports, or directly bears on that behaviour. Scale 0.00-1.00: "
    "1.0 = directly states or governs the behaviour; 0.7 = clearly related or reinforcing; "
    "0.4 = tangentially related; 0.15 = only adjacent concepts; 0.0 = unrelated. Judge the "
    "content, not the writing style. Return ONLY a JSON object mapping each passage number to "
    'its score, e.g. {"1": 0.8, "2": 0.0}. No prose, no explanation.'
)


def env(name):
    for line in (HERE / ".env").read_text().splitlines():
        if line.strip().startswith(name + "="):
            return line.split("=", 1)[1].strip().strip("\"'")


def tag(model):
    return model.split("/")[-1]


def judge_batch(client, model, query, batch, max_tokens=None):
    passages = "\n".join(f"[{i + 1}] {t}" for i, (loc, t) in enumerate(batch))
    user = f"Target behaviour:\n{query}\n\nPassages:\n{passages}\n\nScore all {len(batch)} passages."
    msgs = [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}]
    kw = {"model": model, "temperature": 0, "messages": msgs}
    if max_tokens:
        kw["max_tokens"] = max_tokens
    try:  # JSON mode constrains the answer; a reasoning model still thinks in its own channel
        r = client.chat.completions.create(response_format={"type": "json_object"}, **kw)
    except Exception:  # model/provider rejects response_format -- fall back to free-form + parse
        r = client.chat.completions.create(**kw)
    txt = r.choices[0].message.content or ""
    try:
        return json.loads(txt), r.usage
    except Exception:
        pass
    m = re.search(r"\{.*\}", txt, re.S)
    if m:
        try:
            return json.loads(m.group(0)), r.usage
        except Exception:
            pass
    # salvage: pull individual "N": score pairs (handles truncated/malformed output, so a
    # too-big single call reports partial coverage instead of crashing)
    pairs = re.findall(r'"(\d+)"\s*:\s*([0-9]*\.?[0-9]+)', txt)
    return {k: float(v) for k, v in pairs}, r.usage


def main():
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    name = sys.argv[1] if len(sys.argv) > 1 else None
    if name not in behaviours:
        sys.exit(f"usage: judge.py <behaviour> [model] [--test]   ({', '.join(behaviours)})")
    model, test, provider, args = DEFAULT_MODEL, False, DEFAULT_PROVIDER, list(sys.argv[2:])
    while args:
        a = args.pop(0)
        if a == "--test":
            test = True
        elif a == "--provider":
            provider = args.pop(0)
        else:
            model = a
    if provider not in PROVIDERS:
        sys.exit(f"unknown provider {provider!r} -- choices: {', '.join(PROVIDERS)}")
    base, keyname = PROVIDERS[provider]
    key = env(keyname)
    if not key:
        sys.exit(f"no {keyname} in .env -- add it to score/judge against {provider}")
    b = behaviours[name]
    query = b["query"]
    units = score.corpus()
    from openai import OpenAI
    client = OpenAI(api_key=key, base_url=base)

    batches = [units[k:k + BATCH] for k in range(0, len(units), BATCH)]
    if test:
        batches = batches[:1]
    scores, pt, ct, t0 = {}, 0, 0, time.time()
    for bi, batch in enumerate(batches, 1):
        try:
            obj, usage = judge_batch(client, model, query, batch)
        except Exception as e:
            print(f"  batch {bi} FAILED: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            continue
        for i, (loc, _) in enumerate(batch):
            v = obj.get(str(i + 1))
            if v is not None:
                scores[loc] = max(0.0, min(1.0, float(v)))
        pt += usage.prompt_tokens
        ct += usage.completion_tokens
        print(f"  batch {bi}/{len(batches)}: {len(obj)} scored  (cum {pt} in / {ct} out)", file=sys.stderr)

    results = [{"locator": loc, "score": round(scores[loc], 4), "snippet": t[:220]}
               for loc, t in units if loc in scores]
    results.sort(key=lambda r: -r["score"])
    stem = f"{name}-{tag(model)}"
    if not test:
        (HERE / f"scores-{stem}.json").write_text(json.dumps(
            {"behaviour": name, "label": b["label"], "query": query,
             "source": f"{model} per-chunk relevance judgement (0-1 scale), paragraph, via DeepInfra",
             "provider": "deepinfra", "model": model, "n_blocks": len(results), "results": results}, indent=2))
    dt = time.time() - t0
    print(f"\n{name} [{model}] {'TEST(1 batch) ' if test else ''}-- {len(results)}/"
          f"{len(batches) * BATCH if test else len(units)} scored in this run")
    print(f"tokens: {pt} in / {ct} out  ({dt:.0f}s)")
    if test:
        full = len(units)
        print(f"extrapolated to full corpus ({full} chunks, x2 behaviours): "
              f"~{round(pt/len(batches[0])*full*2/1000)}k in / ~{round(ct/len(batches[0])*full*2/1000)}k out")


if __name__ == "__main__":
    main()
