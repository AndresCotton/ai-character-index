#!/bin/bash
# Pulls the latest published model specs into specs/.
# Run from anywhere; paths resolve relative to this script's location.
# Requires: gh (authenticated), base64.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SPECS="$ROOT/specs"

# -- OpenAI model spec --
DEST="$SPECS/openai-model-spec"
mkdir -p "$DEST/docs"

for f in model_spec.md CHANGELOG.md README.md; do
  gh api "repos/openai/model_spec/contents/$f" --jq '.content' | base64 -d > "$DEST/$f"
done

gh api repos/openai/model_spec/contents/docs/version-manifest.json --jq '.content' | base64 -d > "$DEST/docs/version-manifest.json"
gh api repos/openai/model_spec/contents/docs/index.html --jq '.content' | base64 -d > "$DEST/docs/index.html"

versions=$(gh api repos/openai/model_spec/contents/docs --jq '[.[].name | select(test("^[0-9]{4}-[0-9]{2}-[0-9]{2}\\.html$"))] | .[]')
for f in $versions; do
  gh api "repos/openai/model_spec/contents/docs/$f" --jq '.content' | base64 -d > "$DEST/docs/$f"
done

echo "[$(date)] OpenAI model spec updated."

# -- Anthropic Claude constitution --
DEST="$SPECS/claude-constitution"
mkdir -p "$DEST"

files=$(gh api repos/anthropics/claude-constitution/contents/ --jq '[.[].name | select(test("\\.(md|txt)$"))] | .[]')
for f in $files; do
  gh api "repos/anthropics/claude-constitution/contents/$f" --jq '.content' | base64 -d > "$DEST/$f"
done

echo "[$(date)] Claude constitution updated."
