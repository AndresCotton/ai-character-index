#!/usr/bin/env python3
"""Panel-of-judges harness -- (spec, behaviour, model) -> per-passage BINARY relevance.

Design goals (from the ladder):
  * ONE uniform system+user prompt + "verdict per line" format for EVERY model, reached
    through each provider's OpenAI-compatible endpoint (openai SDK, swap base_url + key).
  * DURABLE: every verdict is appended to runlog.jsonl the moment it arrives -- never held
    only in memory. A crash loses at most the in-flight batch.
  * RESUMABLE: a restart reads runlog.jsonl and skips any (behaviour, spec, model, locator)
    already recorded, so we never pay twice for the same result.

  python3 harness.py <behaviour> <spec> <tag[,tag,...]> [--reason] [--realtime|--batch]
      behaviour: key in behaviours.json     spec: constitution | model-spec
      tags: keys in MODELS below

Aggregate the runlog into per-model columns + 0..N panel vote counts with aggregate.py.
Realtime is the default (prefix-cache friendly); --batch is a stub for the Together Batch path.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "engine" / "spec-cite"))   # cite.py lives on main
import cite  # noqa: E402

RUNLOG = HERE / "runlog.jsonl"
REASONLOG = HERE / "reasons.jsonl"
METRICS = HERE / "metrics.jsonl"   # per-call latency + token usage (for cost/time reporting)
SPECS = ("constitution", "model-spec")
BATCH = 40   # passages per prompt -- bounded output (compact format stays coherent)

# Every provider is reached through the OpenAI SDK by swapping base_url + key.
PROVIDERS = {
    "openai":    (None, "OPENAI_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1/", "ANTHROPIC_API_KEY"),        # OpenAI-compat
    "deepinfra": ("https://api.deepinfra.com/v1/openai", "DEEPINFRA_API_KEY"),
    "together":  ("https://api.together.xyz/v1", "TOGETHER_API_KEY"),
    "gemini":    ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
}

# Candidate panel: tag -> (provider, model id). Confirm/adjust ids in R1 (format smoke test).
MODELS = {
    "haiku":      ("anthropic", "claude-haiku-4-5-20251001"),
    "opus":       ("anthropic", "claude-opus-4-8"),
    "qwen-small": ("deepinfra", "Qwen/Qwen3-32B"),
    "qwen-big":   ("deepinfra", "Qwen/Qwen3-235B-A22B-Instruct-2507"),
    "deepseek":   ("deepinfra", "deepseek-ai/DeepSeek-V3.2"),
    "gpt-mini":   ("openai", "gpt-5-mini"),
    "gpt":        ("openai", "gpt-5"),
    "sol":        ("openai", "gpt-5.6-sol"),          # OpenAI frontier
    "fable":      ("anthropic", "claude-fable-5"),    # Anthropic frontier
    "kimi":       ("together", "moonshotai/Kimi-K3"),
}

SYSTEM = ("You decide whether each spec passage is RELEVANT to a target behaviour. "
          "Mark 1 ONLY if the passage directly governs the SPECIFIC behaviour described -- it "
          "states, requires, or constrains that exact behaviour, such that you would cite this "
          "passage when assembling the spec's coverage of it. Being in the same topic area is "
          "NOT enough. Mark 0 for everything else, including passages that merely share "
          "vocabulary, sit near the topic, or describe the model's general goals, values, "
          "mission, helpfulness, trustworthiness, or good judgment without addressing THIS "
          "specific behaviour. The test: could a reader point to this passage as a rule the "
          "behaviour must follow? If not, mark 0. When in doubt, mark 0. "
          "Example -- behaviour 'do not endorse false claims': a passage requiring the model to "
          "correct a user's factual mistake = 1; a passage about being generally helpful or "
          "building user trust = 0, even though it is nearby in the document. "
          "For each passage, output one line: the passage number, a colon, then 1 (relevant) or "
          "0 (not). One line per passage, in order.{reason}")
REASON_CLAUSE = " You may reason first; put the numbered verdict lines at the very end."


def env(name):
    v = os.environ.get(name)
    if not v and (HERE / ".env").exists():
        for line in (HERE / ".env").read_text().splitlines():
            if line.strip().startswith(name + "="):
                v = line.split("=", 1)[1].strip().strip("\"'")
    return v


def client_for(provider):
    base, keyname = PROVIDERS[provider]
    key = env(keyname)
    if not key:
        sys.exit(f"no {keyname} in env/.env for provider {provider}")
    from openai import OpenAI
    return OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)


def passages(spec):
    """(locator, section, text) for every content paragraph, TOC-filtered -- reuses cite.py."""
    out = []
    version, sections, lines = cite.load_spec(spec, None)
    titles = {cite.normalize(s.path_str.split(" > ")[-1]) for s in sections}
    for sec in sections:
        ref = f"#{sec.anchor}" if (spec == "model-spec" and sec.anchor) else sec.path_str
        for i, raw in enumerate(cite.segment_blocks(lines, sec.start, sec.end), 1):
            t = cite.normalize(raw)
            if t.strip() and t not in titles:
                out.append((f"{spec}@{version} > {ref} > ¶{i}", sec.path_str, t))
    return out


def load_query(behaviour):
    b = json.loads((HERE / "behaviours.json").read_text())
    if behaviour not in b:
        sys.exit(f"unknown behaviour {behaviour!r} -- add it to behaviours.json (from behaviours-for-adria)")
    return b[behaviour]["query"]


def done_keys():
    if not RUNLOG.exists():
        return set()
    return {(d["behaviour"], d["spec"], d["model"], d["locator"])
            for d in (json.loads(l) for l in RUNLOG.read_text().splitlines() if l.strip())}


def append(path, rows):
    with path.open("a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def parse_verdicts(txt, n):
    """{index(1-based): 0/1}. First try 'N: V' lines; fall back to positional 0/1s."""
    keyed = {}
    for line in txt.splitlines():
        m = re.match(r'\s*\[?(\d+)\]?\s*[:.\)\-]\s*([01])\b', line)
        if m:
            keyed[int(m.group(1))] = int(m.group(2))
    if len(keyed) >= n * 0.9:
        return keyed
    seq = re.findall(r'(?<![.\d])([01])(?![.\d])', txt)   # positional fallback
    return {i + 1: int(v) for i, v in enumerate(seq[:n])} if len(seq) >= n else keyed


def judge(client, model, query, batch, reason):
    body = "\n".join(f"[{i+1}] {t}" for i, (_, _, t) in enumerate(batch))
    sysmsg = SYSTEM.format(reason=REASON_CLAUSE if reason else "")
    kwargs = dict(
        model=model,
        messages=[{"role": "system", "content": sysmsg},
                  {"role": "user", "content": f"Behaviour:\n{query}\n\nPassages:\n{body}\n\n"
                                               f"Output {len(batch)} verdict lines."}])
    if model.startswith("gpt-5"):
        # OpenAI reasoning models: no max_tokens / no temperature; keep reasoning cheap.
        # gpt-5.6 dropped 'minimal' (wants none/low/medium/high/xhigh); gpt-5/-mini use 'minimal'.
        effort = "low" if model.startswith("gpt-5.6") else "minimal"
        kwargs.update(max_completion_tokens=8192, reasoning_effort=effort)
    elif "fable" in model or "mythos" in model:
        # Anthropic frontier reasoning models: max_tokens ok, temperature deprecated
        kwargs.update(max_tokens=8192)
    else:
        kwargs.update(max_tokens=8192, temperature=0)
    t0 = time.perf_counter()
    r = client.chat.completions.create(**kwargs)
    dt = time.perf_counter() - t0
    txt = r.choices[0].message.content or ""
    u = getattr(r, "usage", None)
    meta = {"seconds": round(dt, 2),
            "prompt_tokens": getattr(u, "prompt_tokens", None),
            "completion_tokens": getattr(u, "completion_tokens", None)}
    return parse_verdicts(txt, len(batch)), txt, meta


def run(behaviour, spec, tags, reason, limit=None, only=None, batch_size=BATCH,
        v2=False, runlog=None):
    global RUNLOG
    if runlog:
        RUNLOG = Path(runlog)
    query = load_query(behaviour)
    if v2:
        beh = json.loads((HERE / "behaviours.json").read_text())[behaviour]
        if not beh.get("boundary"):
            sys.exit(f"--v2: no boundary clause for {behaviour}")
        query = f"{query}\n\nScope: {beh['boundary']}"
    ps = passages(spec)
    if only is not None:
        ps = [p for p in ps if p[0] in only]   # judge only these locators (e.g. contested subset)
    if limit:
        ps = ps[:limit]   # smoke test: judge only the first `limit` passages
    done = done_keys()
    for tag in tags:
        provider, model = MODELS[tag]
        client = client_for(provider)
        todo = [p for p in ps if (behaviour, spec, tag, p[0]) not in done]
        print(f"{tag} ({provider}:{model}): {len(todo)}/{len(ps)} passages to judge", file=sys.stderr)
        for k in range(0, len(todo), batch_size):
            batch = todo[k:k + batch_size]
            verdicts, raw, meta = judge(client, model, query, batch, reason)
            rows = [{"behaviour": behaviour, "spec": spec, "model": tag, "locator": loc,
                     "relevant": int(verdicts.get(i + 1, 0)),
                     "parsed": (i + 1) in verdicts,
                     "rubric": "v2" if v2 else "v1"} for i, (loc, _, _) in enumerate(batch)]
            append(RUNLOG, rows)   # DURABLE: flush every batch immediately
            append(METRICS, [{"behaviour": behaviour, "spec": spec, "model": tag,
                              "model_id": model, "n": len(batch), "first_loc": batch[0][0], **meta}])
            if reason:
                append(REASONLOG, [{"behaviour": behaviour, "spec": spec, "model": tag,
                                    "first_loc": batch[0][0], "raw": raw}])
            miss = sum(1 for r in rows if not r["parsed"])
            print(f"  {tag} {k+len(batch)}/{len(todo)}  (unparsed {miss})", file=sys.stderr)


def main():
    if len(sys.argv) < 4:
        sys.exit("usage: harness.py <behaviour> <spec> <tag[,tag,...]> [--reason]")
    behaviour, spec, tags = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    if spec not in SPECS:
        sys.exit(f"spec must be one of {SPECS}")
    bad = [t for t in tags if t not in MODELS]
    if bad:
        sys.exit(f"unknown model tags {bad} -- choices: {', '.join(MODELS)}")
    limit = None
    only = None
    batch_size = BATCH
    for a in sys.argv:
        if a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])
        elif a.startswith("--batch-size="):
            batch_size = int(a.split("=", 1)[1])
        elif a.startswith("--locators="):
            only = {l.strip() for l in Path(a.split("=", 1)[1]).read_text().splitlines() if l.strip()}
    runlog = None
    for a in sys.argv:
        if a.startswith("--runlog="):
            runlog = a.split("=", 1)[1]
    run(behaviour, spec, tags, "--reason" in sys.argv, limit, only, batch_size,
        v2="--v2" in sys.argv, runlog=runlog)


if __name__ == "__main__":
    main()
