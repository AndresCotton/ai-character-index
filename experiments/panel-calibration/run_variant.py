#!/usr/bin/env python3
"""Calibration-loop runner: whole-document panel call with a VARIANT system prompt.

Mirrors engine/panel/whole_doc.py (full, non-sparse output mode) but takes the system
prompt from prompts/<variant>.txt and tags run-log rows rubric=<variant>, so iteration
runs never collide with production v3w rows and build_site_data.py can select them
with --rubric=<variant>.

  python3 run_variant.py <behaviour[,..]> <spec[,..]> <tag[,..]> <variant> [--runlog=path]

Default runlog: runlog-<variant>.jsonl beside this script (append + resume, like prod).
"""
import importlib.util, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent.parent / "engine" / "panel"
sp = importlib.util.spec_from_file_location("h", PANEL / "harness.py")
h = importlib.util.module_from_spec(sp); sp.loader.exec_module(h)
sw = importlib.util.spec_from_file_location("w", PANEL / "whole_doc.py")
w = importlib.util.module_from_spec(sw); sw.loader.exec_module(w)


def main():
    behaviours, specs, tags, variant = (sys.argv[1].split(","), sys.argv[2].split(","),
                                        sys.argv[3].split(","), sys.argv[4])
    tags = [m for t in tags for m in (h.PANELS.get(t) or [t])]
    sysmsg = (HERE / "prompts" / f"{variant}.txt").read_text()
    runlog = HERE / f"runlog-{variant}.jsonl"
    for a in sys.argv:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
    h.RUNLOG = runlog
    done = h.done_keys(variant)
    for behaviour in behaviours:
        qblock = h.compose_query(behaviour, "v3")
        for spec in specs:
            ps = h.passages(spec)
            body = "\n".join(f"[{i+1}] (§ {sec}) {t}" for i, (_, sec, t) in enumerate(ps))
            user = (f"{qblock}\n\nPassages (the complete document, in order):\n{body}\n\n"
                    f"Output {len(ps)} verdict lines.")
            for tag in tags:
                if (behaviour, spec, tag, ps[0][0]) in done:
                    print(f"skip {behaviour}/{spec}/{tag} (resumed)"); continue
                provider, model = h.resolve(tag)
                client = h.client_for(provider)
                kwargs = dict(model=model, messages=[{"role": "system", "content": sysmsg},
                                                     {"role": "user", "content": user}])
                kwargs.update(w.judge_kwargs(tag, model, h.CONFIG))
                t0 = time.perf_counter()
                r = client.chat.completions.create(timeout=3600, **kwargs)
                dt = time.perf_counter() - t0
                txt = r.choices[0].message.content or ""
                finish = getattr(r.choices[0], "finish_reason", None)
                verdicts = h.parse_verdicts(txt, len(ps))
                miss = sum(1 for i in range(len(ps)) if (i + 1) not in verdicts)
                ok = miss / len(ps) < 0.02
                u = getattr(r, "usage", None)
                meta = {"behaviour": behaviour, "spec": spec, "model": tag, "model_id": model,
                        "n": len(ps), "via": f"wholedoc-{variant}", "seconds": round(dt, 2),
                        "finish_reason": finish,
                        "prompt_tokens": getattr(u, "prompt_tokens", None),
                        "completion_tokens": getattr(u, "completion_tokens", None)}
                with h.METRICS.open("a") as f:
                    f.write(json.dumps(meta) + "\n")
                if not ok:
                    fail = HERE / f"FAILED-{variant}-{behaviour}-{spec}-{tag}.txt"
                    fail.write_text(txt)
                    print(f"{behaviour}/{spec}/{tag}: PARSE FAILURE ({miss}/{len(ps)} unparsed, "
                          f"finish_reason={finish}) -- raw saved to {fail.name}; retryable")
                    continue
                rows = [{"behaviour": behaviour, "spec": spec, "model": tag, "locator": loc,
                         "verdict": verdicts.get(i+1, 0), "relevant": int(verdicts.get(i+1, 0) == 2),
                         "parsed": (i + 1) in verdicts, "rubric": variant,
                         "via": f"wholedoc-{variant}"}
                        for i, (loc, _, _) in enumerate(ps)]
                with runlog.open("a") as f:
                    f.write("".join(json.dumps(row) + "\n" for row in rows))
                print(f"{behaviour}/{spec}/{tag}: {len(ps)} verdicts "
                      f"({sum(1 for x in rows if x['verdict']>0)} positive), {dt:.0f}s, "
                      f"in={meta['prompt_tokens']} out={meta['completion_tokens']}")


if __name__ == "__main__":
    main()
