#!/usr/bin/env python3
"""How closely can one score column be mapped onto another?

Treats K3 (the LLM judge) as the reference and asks, per source column, using ONE fixed
function chosen once and applied across all examples:
  spearman  -- ceiling for any monotonic map (rank agreement, transform-invariant)
  pearson   -- linear agreement
  iso_rmse  -- residual (on K3's 0-1 scale) after the best monotonic map (isotonic/PAVA);
               compare to K3's own std (baseline of predicting the mean)
  auc       -- ranking quality with K3>=CUT treated as 'relevant' (threshold-free)
  shared-threshold F1 -- fit ONE threshold on pooled data, apply per-behaviour: tests
               whether a single function+threshold holds across examples or drifts.

  .venv-mc/bin/python compare.py [chunk]     # chunk: paragraph (default) | sentence
"""
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REF = "moonshotai/Kimi-K3"   # reference column
CUT = 0.5                    # K3 >= CUT counts as "relevant"


def load(chunk):
    data = {}
    for f in sorted(HERE.glob("scores-*.json")):
        d = json.loads(f.read_text())
        if d.get("chunk", "paragraph") != chunk:
            continue
        data[(d["behaviour"], d["model"])] = {r["locator"]: r["score"] for r in d["results"]}
    return data


def rankavg(x):
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        r[order[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def pearson(a, b):
    a = np.asarray(a, float) - np.mean(a)
    b = np.asarray(b, float) - np.mean(b)
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def spearman(a, b):
    return pearson(rankavg(a), rankavg(b))


def auc(scores, labels):
    labels = np.asarray(labels, int)
    pos, neg = labels == 1, labels == 0
    npos, nneg = int(pos.sum()), int(neg.sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    rb = rankavg(scores) + 1.0  # 1-based
    return float((rb[pos].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def isotonic(x, y):
    """Best monotonic-increasing fit of y on x (PAVA). Returns fitted y aligned to x order."""
    order = np.argsort(x, kind="mergesort")
    ys = np.asarray(y, float)[order]
    vals, wts = [], []
    for v in ys:
        vals.append(v)
        wts.append(1.0)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, w2 = vals.pop(), wts.pop()
            v1, w1 = vals.pop(), wts.pop()
            vals.append((v1 * w1 + v2 * w2) / (w1 + w2))
            wts.append(w1 + w2)
    fitted_sorted = np.concatenate([np.full(int(w), v) for v, w in zip(vals, wts)])
    fitted = np.empty(len(x))
    fitted[order] = fitted_sorted
    return fitted


def best_f1(scores, labels):
    labels = np.asarray(labels, int)
    thrs = np.unique(scores)
    best = (-1.0, 0.0)
    for t in thrs:
        pred = scores >= t
        tp = int((pred & (labels == 1)).sum())
        fp = int((pred & (labels == 0)).sum())
        fn = int((~pred & (labels == 1)).sum())
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        if f1 > best[0]:
            best = (f1, float(t))
    return best  # (f1, threshold)


def f1_at(scores, labels, t):
    labels = np.asarray(labels, int)
    pred = np.asarray(scores) >= t
    tp = int((pred & (labels == 1)).sum())
    fp = int((pred & (labels == 0)).sum())
    fn = int((~pred & (labels == 1)).sum())
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0


def metrics(chunk):
    """{ 'behaviour|model|chunk': {stats vs K3} } for every non-K3 source that has a K3
    reference at this chunk granularity. Consumed by the demo."""
    data = load(chunk)
    out = {}
    for (b, m), sc in data.items():
        if m == REF or (b, REF) not in data:
            continue
        locs = [l for l in sc if l in data[(b, REF)]]
        s = np.array([sc[l] for l in locs])
        k = np.array([data[(b, REF)][l] for l in locs])
        lab = (k >= CUT).astype(int)
        iso = isotonic(s, k)
        f1, thr = best_f1(s, lab)
        out[f"{b}|{m}|{chunk}"] = {
            "spearman": round(spearman(s, k), 3), "pearson": round(pearson(s, k), 3),
            "auc": round(auc(s, lab), 3), "iso_rmse": round(float(np.sqrt(((k - iso) ** 2).mean())), 3),
            "kstd": round(float(k.std()), 3), "f1": round(f1, 3), "thr": round(thr, 3),
            "nrel": int(lab.sum()), "n": int(len(lab))}
    return out


def main():
    chunk = sys.argv[1] if len(sys.argv) > 1 else "paragraph"
    data = load(chunk)
    behaviours = sorted({b for b, m in data})
    models = [m for m in {m for b, m in data} if m != REF]
    ref_present = any(m == REF for b, m in data)
    if not ref_present:
        sys.exit(f"no reference ({REF}) scores for chunk={chunk}")

    print(f"\n=== mapping each source onto {REF.split('/')[-1]} (chunk={chunk}, K3>={CUT} = relevant) ===")
    for model in sorted(models):
        rows = [b for b in behaviours if (b, model) in data and (b, REF) in data]
        if not rows:
            continue
        print(f"\n{model.split('/')[-1]}")
        pooled_s, pooled_k, pooled_b = [], [], []
        per = {}
        for b in rows:
            locs = [l for l in data[(b, model)] if l in data[(b, REF)]]
            s = np.array([data[(b, model)][l] for l in locs])
            k = np.array([data[(b, REF)][l] for l in locs])
            lab = (k >= CUT).astype(int)
            iso = isotonic(s, k)
            rmse = float(np.sqrt(((k - iso) ** 2).mean()))
            f1, thr = best_f1(s, lab)
            per[b] = dict(sp=spearman(s, k), pe=pearson(s, k), auc=auc(s, lab),
                          rmse=rmse, kstd=float(k.std()), f1=f1, thr=thr, prev=float(lab.mean()))
            pooled_s += list(s); pooled_k += list(k); pooled_b += [b] * len(s)
            print(f"  {b:22} spearman {per[b]['sp']:.3f}  auc {per[b]['auc']:.3f}  "
                  f"iso_rmse {rmse:.3f} (K3 std {per[b]['kstd']:.3f})  bestF1 {f1:.3f}@{thr:.3f}  "
                  f"[{int(lab.sum())}/{len(lab)} relevant]")
        # pooled shared threshold
        ps, pk = np.array(pooled_s), np.array(pooled_k)
        plab = (pk >= CUT).astype(int)
        _, shared_thr = best_f1(ps, plab)
        print(f"  pooled                 spearman {spearman(ps, pk):.3f}  auc {auc(ps, plab):.3f}"
              f"  shared thr {shared_thr:.3f}")
        for b in rows:
            locs = [l for l in data[(b, model)] if l in data[(b, REF)]]
            s = np.array([data[(b, model)][l] for l in locs])
            k = np.array([data[(b, REF)][l] for l in locs])
            lab = (k >= CUT).astype(int)
            print(f"    {b:20} F1 @shared({shared_thr:.3f}) = {f1_at(s, lab, shared_thr):.3f}"
                  f"   (its own best {per[b]['f1']:.3f}@{per[b]['thr']:.3f})")


if __name__ == "__main__":
    if "--emit" in sys.argv:
        allm = {}
        for ch in ("paragraph", "sentence"):
            allm.update(metrics(ch))
        (HERE / "compare.json").write_text(json.dumps(allm, indent=2))
        print(f"wrote compare.json: {len(allm)} entries")
    else:
        main()
