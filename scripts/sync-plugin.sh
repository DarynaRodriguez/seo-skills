#!/usr/bin/env bash
# Copy the canonical skills into the plugin directory so the marketplace entry
# ships a self-contained plugin. Run this after changing anything in skills/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/plugins/seo-skills"

rm -rf "$DEST/skills" "$DEST/profiles"
mkdir -p "$DEST/skills" "$DEST/profiles"
cp -R "$ROOT/skills/." "$DEST/skills/"
cp -R "$ROOT/profiles/." "$DEST/profiles/"
cp "$ROOT/PRINCIPLES.md" "$DEST/PRINCIPLES.md"
cp "$ROOT/README.md" "$DEST/README.md"
mkdir -p "$DEST/docs"
cp "$ROOT/docs/data-sources.md" "$DEST/docs/data-sources.md"

echo "synced $(find "$DEST/skills" -name SKILL.md | wc -l | tr -d ' ') skills into plugins/seo-skills"
