#!/usr/bin/env python3
"""Together Batch API path for the Kimi-K3 LLM judge -- sentence-level relevance scoring,
cheap (batch ~50% off) and durable (Together retains batch results ~1 month).

Whole-document-in-one-call fails at sentence granularity (K3 returns malformed/truncated
JSON past ~400 scores). The viable unit is ONE request per SECTION, scoring that section's
sentences. This builds a JSONL batch (one line per behaviour x spec x section), submits it
via Together's Batch API, and maps the {index: score} responses back to sentence locators.

    python3 batch_judge.py prep   [chunk]   # build requests + manifest (default sentence)
    python3 batch_judge.py submit [chunk]   # upload + create batch, save batch id
    python3 batch_judge.py status [chunk]   # poll the saved batch
    python3 batch_judge.py fetch  [chunk]   # download output, write scores-*.json per behaviour

Together SDK (installed): files.upload(purpose="batch-api"), batches.create(
endpoint="/v1/chat/completions", input_file_id, completion_window="24h"), batches.retrieve,
files.content. Each JSONL request line is {"custom_id", "body": {chat-completion body}};
each output line is stamped with the same custom_id.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import score  # units_meta(chunk) -> (locator, spec, section, text); TOC-filtered
from judge import RUBRIC, env  # scoring system prompt + .env key reader

MODEL = "moonshotai/Kimi-K3"
TAG = MODEL.split("/")[-1]                       # "Kimi-K3"
WORK = HERE / "batch_work"
ENDPOINT = "/v1/chat/completions"
SPECS = ("constitution", "model-spec")           # same order as score.SPECS


def requests_path(chunk):
    return WORK / f"requests-{chunk}.jsonl"


def manifest_path(chunk):
    return WORK / f"manifest-{chunk}.json"


def batch_id_path(chunk):
    return WORK / f"batch-{chunk}.id"


def _user_content(query, texts):
    """Same numbered-passage format judge.judge_batch uses (system prompt = RUBRIC)."""
    passages = "\n".join(f"[{i + 1}] {t}" for i, t in enumerate(texts))
    return (f"Target behaviour:\n{query}\n\nPassages:\n{passages}\n\n"
            f"Score all {len(texts)} passages.")


def _client():
    key = env("TOGETHER_API_KEY")
    if not key:
        sys.exit("no TOGETHER_API_KEY in .env")
    from together import Together
    return Together(api_key=key)


def _sections(chunk):
    """Yield ((behaviour, spec, sec_idx), query, [(locator, text), ...]) per section.

    Sections are numbered per (behaviour, spec) in first-seen order of units_meta, so a
    custom_id 'behaviour|spec|sec_idx' is stable across prep runs.
    """
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    units = score.units_meta(chunk)              # (locator, spec, section, text)
    for name, b in behaviours.items():
        query = b["query"]
        # group this behaviour's units by spec, preserving section order
        for spec in SPECS:
            order, groups = [], {}
            for loc, sp, sec, text in units:
                if sp != spec:
                    continue
                if sec not in groups:
                    groups[sec] = []
                    order.append(sec)
                groups[sec].append((loc, text))
            for sec_idx, sec in enumerate(order):
                yield (name, spec, sec_idx), query, groups[sec]


def prep(chunk):
    WORK.mkdir(exist_ok=True)
    behaviours = json.loads((HERE / "behaviours.json").read_text())
    manifest, lines = {}, []
    n_units = 0
    for (name, spec, sec_idx), query, items in _sections(chunk):
        cid = f"{name}|{spec}|{sec_idx}"
        locators = [loc for loc, _ in items]
        texts = [t for _, t in items]
        manifest[cid] = locators
        n_units += len(locators)
        body = {
            "model": MODEL,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_tokens": 8192,
            "messages": [
                {"role": "system", "content": RUBRIC},
                {"role": "user", "content": _user_content(query, texts)},
            ],
        }
        # method/url are OpenAI-batch style; Together only requires custom_id + body, but
        # including them is harmless and keeps the file portable.
        lines.append(json.dumps({
            "custom_id": cid,
            "method": "POST",
            "url": ENDPOINT,
            "body": body,
        }))

    requests_path(chunk).write_text("\n".join(lines) + "\n")
    manifest_path(chunk).write_text(json.dumps(manifest, indent=2))
    per_beh = {}
    for cid in manifest:
        per_beh[cid.split("|")[0]] = per_beh.get(cid.split("|")[0], 0) + 1
    print(f"prep [{chunk}]: {len(lines)} requests (sections), {n_units} {chunk} units, "
          f"{len(behaviours)} behaviours x {len(SPECS)} specs")
    for name, n in per_beh.items():
        print(f"  {name}: {n} section-requests")
    print(f"wrote {requests_path(chunk)}")
    print(f"wrote {manifest_path(chunk)}")


def submit(chunk):
    rp = requests_path(chunk)
    if not rp.exists():
        sys.exit(f"{rp} missing -- run `prep {chunk}` first")
    client = _client()
    print(f"uploading {rp} ...")
    fr = client.files.upload(file=str(rp), purpose="batch-api")
    print(f"  file id: {fr.id}")
    resp = client.batches.create(
        endpoint=ENDPOINT, input_file_id=fr.id, completion_window="24h")
    job = getattr(resp, "job", resp)             # BatchCreateResponse.job is the BatchJob
    batch_id_path(chunk).write_text(job.id)
    print(f"batch id: {job.id}")
    print(f"status:   {job.status}")
    if getattr(resp, "warning", None):
        print(f"warning:  {resp.warning}")
    print(f"saved id -> {batch_id_path(chunk)}")


def status(chunk):
    bp = batch_id_path(chunk)
    if not bp.exists():
        sys.exit(f"{bp} missing -- run `submit {chunk}` first")
    bid = bp.read_text().strip()
    client = _client()
    job = client.batches.retrieve(bid)
    print(f"batch {bid}")
    print(f"  status:         {job.status}")
    print(f"  progress:       {getattr(job, 'progress', None)}")
    print(f"  input_file_id:  {job.input_file_id}")
    print(f"  output_file_id: {getattr(job, 'output_file_id', None)}")
    print(f"  error_file_id:  {getattr(job, 'error_file_id', None)}")
    if getattr(job, "error", None):
        print(f"  error:          {job.error}")
    return job


def _parse_scores(txt):
    """content string -> {index(int): score(float)}; reuse judge's salvage regex."""
    obj = None
    try:
        obj = json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt or "", re.S)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            try:
                out[int(k)] = float(v)
            except Exception:
                pass
        if out:
            return out
    # salvage truncated/malformed output
    pairs = re.findall(r'"(\d+)"\s*:\s*([0-9]*\.?[0-9]+)', txt or "")
    return {int(k): float(v) for k, v in pairs}


def _content_of(rec):
    """Pull the assistant message content out of one output JSONL record, tolerant of the
    Together output shape {custom_id, response:{body:{choices:[...]}}} or a bare body."""
    body = rec.get("response", {}).get("body") if isinstance(rec.get("response"), dict) else None
    body = body or rec.get("body") or rec.get("response") or rec
    try:
        return body["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


def fetch(chunk):
    mp = manifest_path(chunk)
    if not mp.exists():
        sys.exit(f"{mp} missing -- run `prep {chunk}` first")
    manifest = json.loads(mp.read_text())
    job = status(chunk)
    if job.status != "COMPLETED":
        sys.exit(f"batch not COMPLETED (status={job.status}) -- nothing to fetch yet")
    ofid = getattr(job, "output_file_id", None)
    if not ofid:
        sys.exit("no output_file_id on the job")

    client = _client()
    raw = client.files.content(ofid)          # together BinaryAPIResponse
    data = raw.read() if hasattr(raw, "read") else raw
    text = data.decode() if isinstance(data, (bytes, bytearray)) else str(data)
    out_path = WORK / f"output-{chunk}.jsonl"
    out_path.write_text(text)
    print(f"wrote raw output -> {out_path}")

    # custom_id -> {index: score}
    by_cid = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        cid = rec.get("custom_id")
        if cid is None:
            continue
        by_cid[cid] = _parse_scores(_content_of(rec))

    # locator text for snippets (rebuild per chunk)
    loc_text = {loc: text for loc, _, _, text in score.units_meta(chunk)}
    behaviours = json.loads((HERE / "behaviours.json").read_text())

    for name, b in behaviours.items():
        loc_score = {}
        covered = total = 0
        for cid, locators in manifest.items():
            if cid.split("|")[0] != name:
                continue
            total += len(locators)
            scores = by_cid.get(cid, {})
            for i, loc in enumerate(locators, 1):     # passages numbered from 1
                v = scores.get(i)
                if v is not None:
                    loc_score[loc] = max(0.0, min(1.0, v))
                    covered += 1
        results = [{"locator": loc, "score": round(loc_score[loc], 4),
                    "snippet": loc_text.get(loc, "")[:220]}
                   for loc in loc_score]
        results.sort(key=lambda r: -r["score"])
        out = {
            "behaviour": name, "label": b["label"], "query": b["query"],
            "source": b.get("source", ""),
            "provider": "together", "model": MODEL, "chunk": chunk,
            "n_blocks": len(results), "results": results,
        }
        fp = HERE / f"scores-{name}-{TAG}-{chunk}.json"
        fp.write_text(json.dumps(out, indent=2))
        miss = total - covered
        print(f"{name}: {covered}/{total} {chunk} units scored"
              + (f"  ({miss} MISSING)" if miss else "  (full coverage)")
              + f" -> {fp.name}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    chunk = sys.argv[2] if len(sys.argv) > 2 else "sentence"
    if chunk not in ("paragraph", "sentence"):
        sys.exit("chunk must be 'paragraph' or 'sentence'")
    fns = {"prep": prep, "submit": submit, "status": status, "fetch": fetch}
    if cmd not in fns:
        sys.exit("usage: batch_judge.py {prep|submit|status|fetch} [paragraph|sentence]")
    fns[cmd](chunk)


if __name__ == "__main__":
    main()
