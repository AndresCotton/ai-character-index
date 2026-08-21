#!/bin/bash
# Pulls the latest published model specs into specs/ -- but only after
# verifying upstream still matches the versions pinned in cite.py's registry.
# If upstream has moved on, this script aborts WITHOUT touching specs/: an
# in-place overwrite would silently invalidate every locator in
# data/coverage.json and every published artifact. Updating a spec is a
# deliberate act: bump the registry in engine/spec-cite/cite.py and re-sweep
# the affected behaviour (see specs/OVERVIEW.md).
#
# Run from anywhere; paths resolve relative to this script's location.
# Requires: gh (authenticated), base64, python3.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SPECS="$ROOT/specs"

fail() { echo "pull-latest: ABORT -- $*" >&2; exit 1; }

# The version pins live in cite.py's registry (the single source of truth);
# importing cite.py is side-effect free (pinned by the panel import probe).
registry_version() {
  (cd "$ROOT" && python3 -c "
import sys
sys.path.insert(0, 'engine/spec-cite')
import cite
print(cite.BUNDLED_DEFAULT_VERSION['$1'])")
}

registry_path() {
  (cd "$ROOT" && python3 -c "
import sys
sys.path.insert(0, 'engine/spec-cite')
import cite
print(cite.BUNDLED_SPECS[('$1', '$2')])")
}

# ---- Checks first (read-only); nothing under specs/ is touched until both pass.

MODEL_PIN="$(registry_version model-spec)"
upstream_model=$(gh api repos/openai/model_spec/contents/docs/version-manifest.json \
  --jq '.content' | base64 -d \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['latest_version'])") \
  || fail "could not read upstream model-spec version manifest"
[ "$upstream_model" = "$MODEL_PIN" ] || fail "upstream model-spec is at $upstream_model but the registry pins $MODEL_PIN (engine/spec-cite/cite.py). Bump the registry and re-sweep deliberately; not pulling."

CONSTITUTION_PIN="$(registry_version constitution)"
pinned_path="$(registry_path constitution "$CONSTITUTION_PIN")" \
  || fail "registry_path lookup failed for constitution/$CONSTITUTION_PIN"
pinned_file="$(basename "$pinned_path")"
upstream_constitutions=$(gh api repos/anthropics/claude-constitution/contents/ \
  --jq '[.[].name | select(test("constitution\\.md$"))] | .[]')
echo "$upstream_constitutions" | grep -Fqx "$pinned_file" \
  || fail "upstream no longer carries $pinned_file (registry pin: $CONSTITUTION_PIN); not pulling."
newest=$(echo "$upstream_constitutions" | sort | tail -1)
[ "$newest" = "$pinned_file" ] || fail "upstream carries a newer constitution ($newest) than the registry pin ($pinned_file). Bump the registry and re-sweep deliberately; not pulling."

echo "pull-latest: upstream matches the registry pins (model-spec $MODEL_PIN, constitution $CONSTITUTION_PIN). Pulling."

# ---- OpenAI model spec ----
# The dated release archives (docs/<date>.html) are deliberately not fetched:
# nothing in the repo consumes them, and they exceed the contents API's 1 MB
# inline limit (they used to arrive as 0-byte files). The version manifest is
# read above as the version signal, not stored.
DEST="$SPECS/openai-model-spec"
mkdir -p "$DEST"

for f in model_spec.md CHANGELOG.md README.md; do
  gh api "repos/openai/model_spec/contents/$f" --jq '.content' | base64 -d > "$DEST/$f"
done

echo "[$(date)] OpenAI model spec updated."

# ---- Anthropic Claude constitution ----
DEST="$SPECS/claude-constitution"
mkdir -p "$DEST"

files=$(gh api repos/anthropics/claude-constitution/contents/ --jq '[.[].name | select(test("\\.(md|txt)$"))] | .[]')
for f in $files; do
  gh api "repos/anthropics/claude-constitution/contents/$f" --jq '.content' | base64 -d > "$DEST/$f"
done

echo "[$(date)] Claude constitution updated."
