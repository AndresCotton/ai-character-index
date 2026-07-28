#!/usr/bin/env python3
"""Live smoke test: can we actually get an embedding from each provider?

Reads keys from the .env next to this file and does one tiny embedding call per
provider, reporting model, vector dimension, and a latency figure. No secrets printed.
"""
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def env(name):
    for line in (HERE / ".env").read_text().splitlines():
        if line.strip().startswith(name + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return None


PROVIDERS = [
    ("OpenAI", None, "text-embedding-3-small", "OPENAI_API_KEY"),
    ("DeepInfra", "https://api.deepinfra.com/v1/openai", "Qwen/Qwen3-Embedding-8B", "DEEPINFRA_API_KEY"),
]

from openai import OpenAI

for label, base_url, model, keyname in PROVIDERS:
    key = env(keyname)
    if not key:
        print(f"{label:10} SKIP -- no {keyname} in .env")
        continue
    try:
        client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
        t0 = time.time()
        resp = client.embeddings.create(model=model, input=["oversight mechanisms and factual honesty"])
        dt = time.time() - t0
        dim = len(resp.data[0].embedding)
        print(f"{label:10} OK   model={model} dim={dim} {dt*1000:.0f}ms")
    except Exception as e:
        print(f"{label:10} FAIL model={model} -- {type(e).__name__}: {str(e)[:160]}")
