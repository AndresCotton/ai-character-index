#!/usr/bin/env python3
"""Arm 1 (Andres): whole spec text in ONE prompt, ALL passage verdicts in one response.

Reuses harness builders/config. SYSTEM = v3 minus the passage-independence sentence
(removed per Andres 07-29); rubric tag "v3w". One call per (behaviour, spec, model).

  python3 whole_doc.py <behaviour[,..]> <spec[,..]> <tag[,..]>
"""
import importlib.util, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
h = importlib.util.module_from_spec(sp); sp.loader.exec_module(h)

INDEP = ("Grade every passage independently, on its own text (the \u00a7 section path is "
         "context only), on a 3-point scale. ")
SYSTEM_W = h.SYSTEM_V3.replace(INDEP,
    "You are given the ENTIRE document, split into numbered passages in reading order; "
    "use the full document and its structure as context when grading each passage, on a "
    "3-point scale. ")
assert SYSTEM_W != h.SYSTEM_V3, "independence sentence not found -- check text"
# Sparse variant: report ONLY passages scoring > 0 (output stays short at any document size)
OUT_FULL = ("For each passage, output one line: the passage number, a colon, then 2, 1, or 0. "
            "One line per passage, in order.")
OUT_SPARSE = ("Output ONLY the passages that score 2 or 1, one line each: the passage number, a "
              "colon, then the score, in document order. Do NOT list passages that score 0 -- "
              "every passage you omit is recorded as 0. Output no other text.")
SYSTEM_S = SYSTEM_W.replace(OUT_FULL, OUT_SPARSE)
assert SYSTEM_S != SYSTEM_W, "output-format sentence not found -- check text"
RUNLOG = HERE / "runlog-v3.jsonl"

def main():
    behaviours, specs, tags = (sys.argv[1].split(","), sys.argv[2].split(","), sys.argv[3].split(","))
    tags = [m for t in tags for m in (h.PANELS.get(t) or [t])]
    sparse = "--sparse" in sys.argv
    rubric = "v3s" if sparse else "v3w"
    h.RUNLOG = RUNLOG                      # resume must read the SAME file we append to
    done = h.done_keys(rubric)
    for behaviour in behaviours:
        qblock = h.compose_query(behaviour, "v3")
        for spec in specs:
            ps = h.passages(spec)
            body = "\n".join(f"[{i+1}] (\u00a7 {sec}) {t}" for i, (_, sec, t) in enumerate(ps))
            tail = (f"Output the verdict lines for the passages scoring 2 or 1 (omissions = 0)."
                    if sparse else f"Output {len(ps)} verdict lines.")
            user = f"{qblock}\n\nPassages (the complete document, in order):\n{body}\n\n{tail}"
            for tag in tags:
                if (behaviour, spec, tag, ps[0][0]) in done:
                    print(f"skip {behaviour}/{spec}/{tag} (resumed)"); continue
                provider, model = h.MODELS[tag]
                client = h.client_for(provider)
                sysmsg = (SYSTEM_S if sparse else SYSTEM_W).format(reason="")
                kwargs = dict(model=model, messages=[{"role": "system", "content": sysmsg},
                                                     {"role": "user", "content": user}])
                if model.startswith("gpt-5"):
                    kwargs.update(max_completion_tokens=32768, reasoning_effort="low")
                elif "claude" in model or "mythos" in model:   # anthropic models: temperature deprecated
                    kwargs.update(max_tokens=32768)
                else:
                    kwargs.update(max_tokens=65536, temperature=0)   # kimi reasons in-content
                t0 = time.perf_counter()
                r = client.chat.completions.create(timeout=3600, **kwargs)  # K3 needs >SDK default 600s
                dt = time.perf_counter() - t0
                txt = r.choices[0].message.content or ""
                if sparse:
                    keyed = {}
                    for line in txt.splitlines():
                        m = __import__("re").match(r'\s*\[?(\d+)\]?\s*[:.\)\-]\s*([12])\b', line)
                        if m and 1 <= int(m.group(1)) <= len(ps):
                            keyed[int(m.group(1))] = int(m.group(2))
                    verdicts = {i + 1: keyed.get(i + 1, 0) for i in range(len(ps))}
                    ok = bool(keyed)                     # integrity: at least one positive line
                    miss = 0 if ok else len(ps)
                else:
                    verdicts = h.parse_verdicts(txt, len(ps))
                    miss = sum(1 for i in range(len(ps)) if (i + 1) not in verdicts)
                    ok = miss / len(ps) < 0.02           # gate: >=98% of lines must parse
                u = getattr(r, "usage", None)
                meta = {"behaviour": behaviour, "spec": spec, "model": tag, "model_id": model,
                        "n": len(ps), "via": "wholedoc-sparse" if sparse else "wholedoc",
                        "seconds": round(dt, 2),
                        "prompt_tokens": getattr(u, "prompt_tokens", None),
                        "completion_tokens": getattr(u, "completion_tokens", None)}
                with h.METRICS.open("a") as f:
                    f.write(json.dumps(meta) + "\n")
                if not ok:
                    fail = HERE / f"wholedoc-FAILED-{behaviour}-{spec}-{tag}.txt"
                    fail.write_text(txt)
                    print(f"{behaviour}/{spec}/{tag}: PARSE FAILURE ({miss}/{len(ps)} unparsed) -- "
                          f"raw output saved to {fail.name}; NOTHING logged, call is retryable")
                    continue
                rows = [{"behaviour": behaviour, "spec": spec, "model": tag, "locator": loc,
                         "verdict": verdicts.get(i+1, 0), "relevant": int(verdicts.get(i+1, 0) == 2),
                         "parsed": (i + 1) in verdicts, "rubric": rubric,
                         "via": "wholedoc-sparse" if sparse else "wholedoc"}
                        for i, (loc, _, _) in enumerate(ps)]
                with RUNLOG.open("a") as f:
                    for row in rows: f.write(json.dumps(row) + "\n")
                print(f"{behaviour}/{spec}/{tag}: {len(ps)} verdicts ({sum(1 for x in rows if x['verdict']>0)} positive), "
                      f"{dt:.0f}s, in={meta['prompt_tokens']} out={meta['completion_tokens']}")

if __name__ == "__main__":
    main()
