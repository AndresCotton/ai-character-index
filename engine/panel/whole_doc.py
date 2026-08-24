#!/usr/bin/env python3
"""Arm 1 (Andres): whole spec text in ONE prompt, ALL passage verdicts in one response.

Reuses harness builders/config. The system prompts are the harness v3 template with
its {independence} slot filled by the whole-doc clause (per Andres 07-29) instead of
the passage-level one; slot contract documented in harness.py. Rubric tag "v3w"
(full output) / "v3s" (sparse). One call per (behaviour, spec, model).

  python3 whole_doc.py <behaviour[,..]> <spec[,..]> <tag[,..]> [--runlog=path] [--registry=path]
--registry= accepts EITHER registry shape (this directory's behaviours.json,
or a data/behaviours.json-shaped file), so a fork registers a behaviour once.
"""
import importlib.util, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
h = importlib.util.module_from_spec(sp); sp.loader.exec_module(h)

# Explicit composition (no str.replace): the v3 template rendered with the whole-doc
# independence clause. SYSTEM_S is the sparse variant -- report ONLY passages scoring
# > 0, so output stays short at any document size.
SYSTEM_W = h.render_system_v3(h.INDEPENDENCE_WHOLE_DOC, h.OUTPUT_FORMAT_FULL)
SYSTEM_S = h.render_system_v3(h.INDEPENDENCE_WHOLE_DOC, h.OUTPUT_FORMAT_SPARSE)
RUNLOG = HERE / "runlog-v3.jsonl"   # override with --runlog=; resume and append use the SAME file
# NOTE: this executor renders the v3 prompts and stamps rubric v3w/v3s, so its rows
# belong in the v3-family log above. The SHIPPED payload builds from runlog-v5.jsonl
# (rubric v5, produced by the calibration-loop whole-doc runs of 2026-08-17); flip
# this default only together with a v5 prompt port.

def judge_kwargs(tag, model, config):
    """Pure: per-model API params (provider quirks + config output caps)."""
    cap = config["models"][tag].get("max_output", 32768)
    bare = model.rsplit("/", 1)[-1]   # drop any OpenRouter vendor prefix before the quirk checks
    if bare.startswith("gpt-5"):
        return {"max_completion_tokens": cap, "reasoning_effort": "low"}
    if "claude" in bare or "mythos" in bare:   # anthropic: temperature deprecated
        return {"max_tokens": cap}
    return {"max_tokens": cap, "temperature": 0}


def main():
    global RUNLOG
    registry_path = None
    for a in sys.argv:
        if a.startswith("--runlog="):
            RUNLOG = Path(a.split("=", 1)[1])
        elif a.startswith("--registry="):
            registry_path = a.split("=", 1)[1]
    config = h.load_config()
    registry = h.load_registry(registry_path)
    panels = config.get("panels", {})
    for a in sys.argv[1:]:
        if a.startswith("-") and a not in ("--sparse", "--help", "-h") \
                and not a.startswith(("--runlog=", "--registry=")):
            # A space-form flag was silently dropped and its value eaten as a
            # positional, so --registry /path judged the SHIPPED definition and
            # billed for it. Reject rather than guess.
            sys.exit(f"unknown argument {a!r} -- valid: --runlog=PATH --registry=PATH "
                     "--sparse (use = , not a space)")
    positional = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(positional) < 3 or "--help" in sys.argv or "-h" in sys.argv:
        sys.exit(__doc__.strip())
    behaviours, specs, tags = (positional[0].split(","), positional[1].split(","),
                               positional[2].split(","))
    tags = [m for t in tags for m in (panels.get(t) or [t])]
    sparse = "--sparse" in sys.argv
    rubric = "v3s" if sparse else "v3w"
    h.RUNLOG = RUNLOG                      # resume must read the SAME file we append to
    done = h.done_keys(rubric)
    for behaviour in behaviours:
        qblock = h.compose_query(behaviour, "v3", registry)
        for spec in specs:
            ps = h.passages(spec)
            body = "\n".join(f"[{i+1}] (\u00a7 {sec}) {t}" for i, (_, sec, t) in enumerate(ps))
            tail = (f"Output the verdict lines for the passages scoring 2 or 1 (omissions = 0)."
                    if sparse else f"Output {len(ps)} verdict lines.")
            user = f"{qblock}\n\nPassages (the complete document, in order):\n{body}\n\n{tail}"
            for tag in tags:
                if (behaviour, spec, tag, ps[0][0]) in done:
                    print(f"skip {behaviour}/{spec}/{tag} (resumed)"); continue
                provider, model = h.resolve(tag, config)   # native route by default; openrouter only as fallback
                client = h.client_for(provider, config)
                sysmsg = SYSTEM_S if sparse else SYSTEM_W   # reason slot already rendered empty
                kwargs = dict(model=model, messages=[{"role": "system", "content": sysmsg},
                                                     {"role": "user", "content": user}])
                kwargs.update(judge_kwargs(tag, model, config))
                t0 = time.perf_counter()
                r = client.chat.completions.create(timeout=3600, **kwargs)  # K3 needs >SDK default 600s
                dt = time.perf_counter() - t0
                txt = r.choices[0].message.content or ""
                finish = getattr(r.choices[0], "finish_reason", None)
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
                        "seconds": round(dt, 2), "finish_reason": finish,
                        "prompt_tokens": getattr(u, "prompt_tokens", None),
                        "completion_tokens": getattr(u, "completion_tokens", None)}
                with h.METRICS.open("a") as f:
                    f.write(json.dumps(meta) + "\n")
                if not ok:
                    fail = HERE / f"wholedoc-FAILED-{behaviour}-{spec}-{tag}.txt"
                    fail.write_text(txt)
                    print(f"{behaviour}/{spec}/{tag}: PARSE FAILURE ({miss}/{len(ps)} unparsed, "
                          f"finish_reason={finish}) -- raw output saved to {fail.name}; "
                          f"runlog gets nothing, call is retryable (metrics still recorded)")
                    continue
                rows = [{"behaviour": behaviour, "spec": spec, "model": tag, "locator": loc,
                         "verdict": verdicts.get(i+1, 0), "relevant": int(verdicts.get(i+1, 0) == 2),
                         "parsed": (i + 1) in verdicts, "rubric": rubric,
                         "via": "wholedoc-sparse" if sparse else "wholedoc"}
                        for i, (loc, _, _) in enumerate(ps)]
                with RUNLOG.open("a") as f:
                    f.write("".join(json.dumps(row) + "\n" for row in rows))   # one buffered write: interrupt-resistant (not strictly atomic)
                print(f"{behaviour}/{spec}/{tag}: {len(ps)} verdicts ({sum(1 for x in rows if x['verdict']>0)} positive), "
                      f"{dt:.0f}s, in={meta['prompt_tokens']} out={meta['completion_tokens']}")

if __name__ == "__main__":
    main()
