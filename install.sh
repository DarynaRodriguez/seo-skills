#!/usr/bin/env bash
# seo-skills installer for local agents.
# Copies (or symlinks) the skills into your agent's skills directory.
#
#   ./install.sh                     detect the agent, copy the skills
#   ./install.sh --link              symlink instead, so git pull updates them
#   ./install.sh --target ~/my/dir   install somewhere specific
#   ./install.sh --list              show what would be installed, change nothing

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/skills"
MODE="copy"
TARGET=""
LIST_ONLY="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --link) MODE="link"; shift ;;
    --target) TARGET="${2:-}"; shift 2 ;;
    --list) LIST_ONLY="yes"; shift ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
echo ""
echo "Next:"
echo "  1. Restart your agent so it picks up the new skills."
echo "  2. Run /seo-profile-setup for your site. Everything else reads that profile."
echo "  3. Optional: connect the Ahrefs and Peec AI MCP servers for live data."
