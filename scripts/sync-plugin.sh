#!/usr/bin/env bash
# Copy the canonical skills into the plugin directory so the marketplace entry
# ships a self-contained plugin. Run this after changing anything in skills/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/plugins/seo-skills"

rm -rf "$DEST/skills" "$DEST/profiles" "$DEST/seo_tools" "$DEST/agents"
mkdir -p "$DEST/skills" "$DEST/profiles"
cp -R "$ROOT/skills/." "$DEST/skills/"
cp -R "$ROOT/profiles/." "$DEST/profiles/"
cp "$ROOT/PRINCIPLES.md" "$DEST/PRINCIPLES.md"
cp "$ROOT/README.md" "$DEST/README.md"
# All of docs/, plus the two root files the README links to. Shipping the README
# without them left four broken relative links inside the installed plugin.
mkdir -p "$DEST/docs"
cp "$ROOT"/docs/*.md "$DEST/docs/"
cp "$ROOT/LICENSE" "$DEST/LICENSE"
cp "$ROOT/CONTRIBUTING.md" "$DEST/CONTRIBUTING.md"
# AGENTS.md is the file every agent reads on entering a repo, so it belongs in
# an installed plugin as much as in the source tree.
cp "$ROOT/AGENTS.md" "$DEST/AGENTS.md"

# Subagents live at the plugin root, which is where Claude Code looks for them.
# /site-audit fans out to these, so a plugin without them ships a skill that
# cannot run.
mkdir -p "$DEST/agents"
cp "$ROOT"/agents/*.md "$DEST/agents/"

# The skills call the execution layer, so an installed plugin has to carry it.
# Without this the plugin ships instructions to run a module that is not there.
mkdir -p "$DEST/seo_tools"
cp "$ROOT"/seo_tools/*.py "$DEST/seo_tools/"
cp "$ROOT/seo.py" "$DEST/seo.py"
find "$DEST/seo_tools" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "synced $(find "$DEST/skills" -name SKILL.md | wc -l | tr -d ' ') skills, $(find "$DEST/agents" -name '*.md' | wc -l | tr -d ' ') agents and $(find "$DEST/seo_tools" -name '*.py' | wc -l | tr -d ' ') tool modules into plugins/seo-skills"
