#!/usr/bin/env python3
"""Head-to-head: per-section SCORING (compact 0-1 per line) vs listwise RANKING (permutation),
for selecting the spec passages relevant to a behaviour. Both operate per section (bounded output),
then we compare each to the K3 paragraph reference (rank agreement / recall) and report cost +
robustness (parse failures). Uses the compact line format -- robust at length (see PANEL_PLAN.md).

  python3 headtohead.py test [provider] [model]                      # 2-section validation
  python3 headtohead.py run  <behaviour> <spec> [provider] [model]   # writes -score / -rank columns
  python3 headtohead.py eval <behaviour>                             # saved score/rank vs K3 paragraph

Real run is meant for K3 on Together (credit-blocked until the cap is raised); DeepInfra is fine to
validate the harness. Ranking is intra-section only (the sliding-window calibration limit) -- the eval
surfaces that vs. scoring's globally-comparable values.
"""
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score
import judge

DEF_PROVIDER = "deepinfra"
DEF_MODEL = "Qwen/Qwen2.5-72B-Instruct"   # cheap, non-reasoning -> clean line output for validation

SCORE_SYS = ("Rate how RELEVANT each passage is to the target behaviour, 0.0 (unrelated) to 1.0 "
             "(directly states or governs it). Output EXACTLY one number per line, one line per "
             "passage, in the given order -- nothing else, no labels, no prose.")
RANK_SYS = ("Rank the passages by RELEVANCE to the target behaviour, most relevant first. Output the "
            "passage numbers as: [x] > [y] > [z] > ... using EVERY number exactly once -- nothing else.")


def client_for(provider):
    base, keyname = judge.PROVIDERS[provider]
    from openai import OpenAI
    return OpenAI(api_key=judge.env(keyname), base_url=base)


def call(client, model, sys_p, user):
    r = client.chat.completions.create(model=model, temperature=0, max_tokens=16384,
                                       messages=[{"role": "system", "content": sys_p},
                                                 {"role": "user", "content": user}])
    return r.choices[0].message.content or "", r.usage


def sections_of(spec, chunk="paragraph"):
    secs, cur = [], None
    for loc, sp, sec, txt in score.units_meta(chunk):
        if sp != spec:
            continue
        if sec != cur:
            secs.append((sec, [])); cur = sec
        secs[-1][1].append((loc, txt))
    return secs


def score_section(client, model, query, passages):
    body = "\n".join(f"[{i+1}] {t}" for i, (_, t) in enumerate(passages))
    txt, u = call(client, model, SCORE_SYS,
                  f"Behaviour:\n{query}\n\nPassages:\n{body}\n\nOutput exactly {len(passages)} lines.")
    nums = []
    for line in txt.splitlines():
        m = re.search(r'\d+(?:\.\d+)?|\.\d+', line)
        if m:
            nums.append(max(0.0, min(1.0, float(m.group(0)))))
    ok = len(nums) == len(passages)
    vals = {passages[i][0]: nums[i] for i in range(min(len(nums), len(passages)))}
    return vals, u, ok


def rank_section(client, model, query, passages):
    body = "\n".join(f"[{i+1}] {t}" for i, (_, t) in enumerate(passages))
    txt, u = call(client, model, RANK_SYS,
                  f"Behaviour:\n{query}\n\nPassages:\n{body}\n\nRank all {len(passages)}.")
    n = len(passages)
    seen, perm = set(), []
    for x in (int(m) for m in re.findall(r'\[(\d+)\]', txt)):
        if 1 <= x <= n and x not in seen:
            seen.add(x); perm.append(x)
    ok = len(perm) == n
    vals = {passages[i][0]: 0.0 for i in range(n)}
    for r, idx in enumerate(perm):
        vals[passages[idx - 1][0]] = (n - r) / n   # rank -> [1/n .. 1], intra-section
    return vals, u, ok


def cost(pin, pout):  # Kimi-K3 list rates (the intended run); DeepInfra will differ
    return pin * 3 / 1e6 + pout * 15 / 1e6


def run(beh, spec, provider, model):
    query = json.loads((HERE / "behaviours.json").read_text())[beh]["query"]
    text = {loc: t for loc, _, _, t in score.units_meta("paragraph")}
    client = client_for(provider)
    secs = sections_of(spec)
    S, R, pin, pout, badS, badR, t0 = {}, {}, 0, 0, 0, 0, time.time()
    for i, (_, passages) in enumerate(secs, 1):
        sv, u1, ok1 = score_section(client, model, query, passages); S.update(sv); pin += u1.prompt_tokens; pout += u1.completion_tokens; badS += (not ok1)
        rv, u2, ok2 = rank_section(client, model, query, passages); R.update(rv); pin += u2.prompt_tokens; pout += u2.completion_tokens; badR += (not ok2)
        print(f"  section {i}/{len(secs)}  ({len(passages)} passages)", file=sys.stderr)
    tag = model.split("/")[-1]
    for kind, vals in (("score", S), ("rank", R)):
        results = [{"locator": loc, "score": round(vals[loc], 4), "snippet": text[loc][:220]} for loc in text if loc in vals]
        results.sort(key=lambda r: -r["score"])
        (HERE / f"scores-{beh}-{tag}-{kind}.json").write_text(json.dumps(
            {"behaviour": beh, "label": beh, "query": query,
             "source": f"{model} per-section {'relevance score' if kind=='score' else 'listwise rank'} (head-to-head)",
             "provider": provider, "model": f"{tag}-{kind}", "chunk": "paragraph",
             "n_blocks": len(results), "results": results}, indent=2))
    print(f"\n{beh}/{spec} [{model}] -- score bad {badS}/{len(secs)}, rank bad {badR}/{len(secs)}; "
          f"{pin} in / {pout} out (~${cost(pin,pout):.2f} at K3 rates); {time.time()-t0:.0f}s")


def _spear_auc(vals, ref):
    locs = [l for l in vals if l in ref]
    a = [vals[l] for l in locs]; k = [ref[l] for l in locs]; lab = [x >= 0.5 for x in k]
    import granularity as g  # reuse spearman
    sp = g.spearman(a, k)
    pos = [i for i in range(len(lab)) if lab[i]]; neg = [i for i in range(len(lab)) if not lab[i]]
    if not pos or not neg:
        return sp, float("nan"), len(locs)
    rb = g.rankavg(a); auc = (sum(rb[i] + 1 for i in pos) - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    return sp, auc, len(locs)


def evaluate(beh):
    k3 = {r["locator"]: r["score"] for r in json.loads((HERE / f"scores-{beh}-Kimi-K3.json").read_text())["results"]}
    print(f"\n{beh} -- vs K3 paragraph:")
    for f in sorted(HERE.glob(f"scores-{beh}-*-score.json")) + sorted(HERE.glob(f"scores-{beh}-*-rank.json")):
        d = json.loads(f.read_text()); vals = {r["locator"]: r["score"] for r in d["results"]}
        sp, auc, n = _spear_auc(vals, k3)
        print(f"  {d['model']:32} spearman {sp:.3f}  auc {auc:.3f}  (n={n})")


def whole(beh, spec, provider, model):
    """Whole document in one prompt: 1 compact-score call + 1 rank call over ALL passages."""
    query = json.loads((HERE / "behaviours.json").read_text())[beh]["query"]
    passages = [p for _, plist in sections_of(spec) for p in plist]
    text = {loc: t for loc, _, _, t in score.units_meta("paragraph")}
    client = client_for(provider)
    print(f"whole-doc {beh}/{spec}: {len(passages)} passages -> 1 score + 1 rank prompt [{model}]", file=sys.stderr)
    t0 = time.time()
    sv, u1, ok1 = score_section(client, model, query, passages)
    rv, u2, ok2 = rank_section(client, model, query, passages)
    tag = model.split("/")[-1]
    for kind, vals in (("whole-score", sv), ("whole-rank", rv)):
        results = [{"locator": loc, "score": round(vals[loc], 4), "snippet": text[loc][:220]} for loc in text if loc in vals]
        results.sort(key=lambda r: -r["score"])
        (HERE / f"scores-{beh}-{tag}-{kind}.json").write_text(json.dumps(
            {"behaviour": beh, "label": beh, "query": query,
             "source": f"{model} whole-document {'score' if 'score' in kind else 'listwise rank'} ({len(passages)} passages, one prompt)",
             "provider": provider, "model": f"{tag}-{kind}", "chunk": "paragraph",
             "n_blocks": len(results), "results": results}, indent=2))
    pin, pout = u1.prompt_tokens + u2.prompt_tokens, u1.completion_tokens + u2.completion_tokens
    print(f"\nwhole-doc [{model}] {beh}/{spec}: {len(passages)} passages")
    print(f"  score: ok={ok1} ({len(sv)}/{len(passages)})   rank: ok={ok2} ({sum(1 for v in rv.values() if v>0)}/{len(passages)})")
    print(f"  tokens {pin} in / {pout} out (~${cost(pin,pout):.2f}); {time.time()-t0:.0f}s")


def test(provider, model):
    beh = "no-sycophancy"
    query = json.loads((HERE / "behaviours.json").read_text())[beh]["query"]
    passages = sections_of("model-spec")[0][1][:8]  # a small real section
    client = client_for(provider)
    print(f"validate [{provider}: {model}] on {len(passages)} passages\n")
    sv, u1, ok1 = score_section(client, model, query, passages)
    print(f"SCORE  ok={ok1}  got {len(sv)}/{len(passages)}  sample:", [round(v, 2) for v in list(sv.values())[:8]])
    rv, u2, ok2 = rank_section(client, model, query, passages)
    print(f"RANK   ok={ok2}  perm mapped {sum(1 for v in rv.values() if v>0)}/{len(passages)}  sample:", [round(v, 2) for v in list(rv.values())[:8]])
    print(f"\ntokens: score {u1.prompt_tokens}/{u1.completion_tokens}, rank {u2.prompt_tokens}/{u2.completion_tokens}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "test":
        test(sys.argv[2] if len(sys.argv) > 2 else DEF_PROVIDER, sys.argv[3] if len(sys.argv) > 3 else DEF_MODEL)
    elif cmd == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else DEF_PROVIDER, sys.argv[5] if len(sys.argv) > 5 else DEF_MODEL)
    elif cmd == "whole":
        whole(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "together",
              sys.argv[5] if len(sys.argv) > 5 else "moonshotai/Kimi-K3")
    elif cmd == "eval":
        evaluate(sys.argv[2])
    else:
        sys.exit("usage: headtohead.py test|run|eval ...")


if __name__ == "__main__":
    main()
