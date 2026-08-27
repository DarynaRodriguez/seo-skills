#!/usr/bin/env bash
# Copy the canonical skills into the plugin directory so the marketplace entry
# ships a self-contained plugin. Run this after changing anything in skills/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/plugins/seo-skills"

rm -rf "$DEST/skills" "$DEST/profiles" "$DEST/seo_tools"
mkdir -p "$DEST/skills" "$DEST/profiles"
cp -R "$ROOT/skills/." "$DEST/skills/"
cp -R "$ROOT/profiles/." "$DEST/profiles/"
cp "$ROOT/PRINCIPLES.md" "$DEST/PRINCIPLES.md"
cp "$ROOT/README.md" "$DEST/README.md"
mkdir -p "$DEST/docs"
cp "$ROOT/docs/data-sources.md" "$DEST/docs/data-sources.md"
cp "$ROOT/docs/execution-layer.md" "$DEST/docs/execution-layer.md"

# The skills call the execution layer, so an installed plugin has to carry it.
# Without this the plugin ships instructions to run a module that is not there.
mkdir -p "$DEST/seo_tools"
cp "$ROOT"/seo_tools/*.py "$DEST/seo_tools/"
cp "$ROOT/seo.py" "$DEST/seo.py"
find "$DEST/seo_tools" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "synced $(find "$DEST/skills" -name SKILL.md | wc -l | tr -d ' ') skills and $(find "$DEST/seo_tools" -name '*.py' | wc -l | tr -d ' ') tool modules into plugins/seo-skills"
