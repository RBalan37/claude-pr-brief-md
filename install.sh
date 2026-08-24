#!/usr/bin/env bash
# Installs the pr-brief Claude Code skill, either globally (all projects) or into
# one specific project's .claude/ folder. Safe to re-run — it overwrites the
# destination's copy of the skill files, nothing else.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$SCRIPT_DIR/templates"

echo "pr-brief installer"
echo "==================="
echo

if [ ! -d "$TEMPLATES_DIR" ]; then
  echo "Error: templates/ not found next to this script ($TEMPLATES_DIR)." >&2
  exit 1
fi

read -rp "Install globally (every project) or into one project? [global/project] (default: global): " SCOPE
SCOPE=${SCOPE:-global}

read -rp "Skill name — this becomes the /command (default: pr-brief): " SKILL_NAME
SKILL_NAME=${SKILL_NAME:-pr-brief}

if [ "$SCOPE" = "project" ]; then
  read -rp "Path to the project to install into (default: current directory): " PROJECT_PATH
  PROJECT_PATH=${PROJECT_PATH:-.}
  DEST="$PROJECT_PATH/.claude/skills/$SKILL_NAME"
else
  DEST="$HOME/.claude/skills/$SKILL_NAME"
fi

mkdir -p "$DEST"
cp -r "$TEMPLATES_DIR"/. "$DEST/"

if [ "$SKILL_NAME" != "pr-brief" ]; then
  # keep the frontmatter name in sync with the folder/command name chosen above
  # (-i.bak works identically on GNU sed and macOS/BSD sed)
  sed -i.bak "s/^name: pr-brief\$/name: $SKILL_NAME/" "$DEST/SKILL.md"
  rm -f "$DEST/SKILL.md.bak"
fi

echo
echo "Installed to: $DEST"
echo "In Claude Code, invoke it with: /$SKILL_NAME <ticket-id-or-URL>"
if [ "$SCOPE" = "project" ]; then
  echo
  echo "This is inside the project's own .claude/ folder — commit it so the rest of"
  echo "the team gets the skill too when they pull."
fi
