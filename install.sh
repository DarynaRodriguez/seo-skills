#!/usr/bin/env bash
# seo-skills installer for local agents.
# Copies (or symlinks) the skills into your agent's skills directory.
#
#   ./install.sh                     detect the agent, copy the skills
#   ./install.sh --link              symlink instead, so git pull updates them
#   ./install.sh --target ~/my/dir   install somewhere specific
#   ./install.sh --list              show what would be installed, change nothing
#   ./install.sh --skills-only       skip the execution layer (not recommended)
#
# The skills call a small standard-library tool layer. It is installed alongside
# them by default, because a skill that tells you to run a command you do not
# have is worse than no skill.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/skills"
MODE="copy"
TARGET=""
LIST_ONLY="no"
WITH_TOOLS="yes"

while [ $# -gt 0 ]; do
  case "$1" in
    --link) MODE="link"; shift ;;
    --target) TARGET="${2:-}"; shift 2 ;;
    --list) LIST_ONLY="yes"; shift ;;
    --skills-only) WITH_TOOLS="no"; shift ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
done

if [ ! -d "$SRC" ]; then
  echo "no skills/ directory found next to install.sh. Run this from the cloned repo."
  exit 1
fi

COUNT="$(find "$SRC" -name SKILL.md | wc -l | tr -d ' ')"

if [ "$LIST_ONLY" = "yes" ]; then
  echo "$COUNT skills in $SRC:"
  for d in "$SRC"/*/; do echo "  /$(basename "$d")"; done
  exit 0
fi

# Detect the agent when no target was given.
if [ -z "$TARGET" ]; then
  CANDIDATES=""
  [ -d "$HOME/.claude" ] && CANDIDATES="$CANDIDATES $HOME/.claude/skills"
  [ -d "$HOME/.codex" ] && CANDIDATES="$CANDIDATES $HOME/.codex/skills"
  [ -d "$HOME/.config/openclaw" ] && CANDIDATES="$CANDIDATES $HOME/.config/openclaw/skills"

  set -- $CANDIDATES
  if [ $# -eq 0 ]; then
    echo "No agent directory found (~/.claude, ~/.codex, ~/.config/openclaw)."
    echo "Pass one explicitly:  ./install.sh --target ~/.claude/skills"
    exit 1
  fi
  TARGET="$1"
  if [ $# -gt 1 ]; then
    echo "Found more than one agent. Installing into $TARGET."
    echo "Others: ${*:2}. Re-run with --target for those."
  fi
fi

mkdir -p "$TARGET"

INSTALLED=0
SKIPPED=0
for d in "$SRC"/*/; do
  name="$(basename "$d")"
  dest="$TARGET/$name"

  if [ -e "$dest" ] && [ ! -L "$dest" ] && [ "$MODE" = "copy" ]; then
    if ! diff -rq "$d" "$dest" >/dev/null 2>&1; then
      echo "  changed: $name (replacing, previous version at $dest.bak)"
      rm -rf "$dest.bak"
      mv "$dest" "$dest.bak"
    else
      SKIPPED=$((SKIPPED + 1))
      continue
    fi
  fi

  rm -rf "$dest"
  if [ "$MODE" = "link" ]; then
    ln -s "$d" "$dest"
  else
    cp -R "$d" "$dest"
  fi
  INSTALLED=$((INSTALLED + 1))
done

echo ""
echo "seo-skills installed into $TARGET"
echo "  $INSTALLED written, $SKIPPED already current, $COUNT total"
[ "$MODE" = "link" ] && echo "  symlinked, so 'git pull' in $ROOT updates them in place"

# The execution layer. Kept out of the skills directory itself so an agent that
# treats every subdirectory as a skill does not trip over a Python package.
TOOLS_DEST=""
if [ "$WITH_TOOLS" = "yes" ]; then
  if [ "$(basename "$TARGET")" = "skills" ]; then
    TOOLS_DEST="$(dirname "$TARGET")/seo-skills-tools"
  else
    TOOLS_DEST="$TARGET/seo-skills-tools"
  fi
  mkdir -p "$TOOLS_DEST"
  rm -rf "$TOOLS_DEST/seo_tools"
  if [ "$MODE" = "link" ]; then
    ln -s "$ROOT/seo_tools" "$TOOLS_DEST/seo_tools"
    ln -sf "$ROOT/seo.py" "$TOOLS_DEST/seo.py"
  else
    cp -R "$ROOT/seo_tools" "$TOOLS_DEST/seo_tools"
    cp "$ROOT/seo.py" "$TOOLS_DEST/seo.py"
    find "$TOOLS_DEST" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  fi
  echo "  tools written to $TOOLS_DEST"
fi

# Subagents. /site-audit fans out to these, so they install alongside the skills.
AGENTS_DEST=""
if [ -d "$ROOT/agents" ]; then
  if [ "$(basename "$TARGET")" = "skills" ]; then
    AGENTS_DEST="$(dirname "$TARGET")/agents"
  else
    AGENTS_DEST="$TARGET/../agents"
  fi
  mkdir -p "$AGENTS_DEST"
  for a in "$ROOT"/agents/*.md; do
    [ -e "$a" ] || continue
    if [ "$MODE" = "link" ]; then
      ln -sf "$a" "$AGENTS_DEST/$(basename "$a")"
    else
      cp "$a" "$AGENTS_DEST/$(basename "$a")"
    fi
  done
  echo "  $(ls "$AGENTS_DEST"/*.md 2>/dev/null | wc -l | tr -d ' ') agents written to $AGENTS_DEST"
fi

echo ""
echo "Next:"
echo "  1. Restart your agent so it picks up the new skills."
if [ -n "$TOOLS_DEST" ]; then
  echo "  2. Check the tools run on this machine:"
  echo "       python \"$TOOLS_DEST/seo.py\" doctor"
  echo "  3. Run /seo-profile-setup for your site. Everything else reads that profile."
  echo "  4. Optional: connect the Ahrefs and Peec AI MCP servers for live data."
  echo ""
  echo "The skills refer to 'python -m seo_tools <command>', which works from the"
  echo "repo root. From anywhere else use the full path above, which is equivalent:"
  echo "  python \"$TOOLS_DEST/seo.py\" page https://example.com"
else
  echo "  2. Run /seo-profile-setup for your site. Everything else reads that profile."
  echo "  3. Optional: connect the Ahrefs and Peec AI MCP servers for live data."
  echo ""
  echo "You passed --skills-only, so the tool layer is NOT installed. Skills that"
  echo "measure things will tell you to run commands you do not have."
fi
