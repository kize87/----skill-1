#!/usr/bin/env bash
# install.sh — deploy experiment-report-writer (skill + hook) into a target project.
#
# Usage:
#   bash <path-to-skill>/install.sh <target-project-dir>
#
# Example:
#   bash ~/Documents/课/实验报告skill-1/experiment-report-writer/install.sh \
#        ~/Documents/课/机器学习/实验/Task\ 3
#
# What it does:
#   1. Copies the skill folder (this directory) into <target>/experiment-report-writer.
#   2. Installs the PreToolUse hook into <target>/.claude/hooks/.
#   3. Writes <target>/.claude/settings.json (or merges the PreToolUse entry if a
#      settings.json already exists there) so Claude Code wires up the hook.
#
# What it explicitly does NOT do:
#   - It does not touch ~/.claude/. Only the project under <target>/.claude/.
#   - It does not copy any settings.local.json from the source — that file is a
#     per-session permission cache, not skill content.

set -euo pipefail

# ---------- args ----------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  echo "Usage: bash $0 <target-project-dir>" >&2
  exit 1
fi

TARGET="$1"
if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: target directory does not exist: $TARGET" >&2
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"

# Resolve this script's directory — that is the skill source.
SKILL_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="$(basename "$SKILL_SRC")"

if [[ ! -f "$SKILL_SRC/SKILL.md" ]]; then
  echo "ERROR: $SKILL_SRC does not look like the skill folder (no SKILL.md)" >&2
  exit 1
fi

echo "Skill source : $SKILL_SRC"
echo "Target       : $TARGET"
echo

# ---------- (1) copy the skill --------------------------------------------------

DEST_SKILL="$TARGET/$SKILL_NAME"
if [[ -d "$DEST_SKILL" ]]; then
  echo "[1/3] Updating existing skill copy at $DEST_SKILL"
fi
echo "[1/3] Copying skill to $DEST_SKILL"
mkdir -p "$DEST_SKILL"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
        --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' \
        "$SKILL_SRC/" "$DEST_SKILL/"
else
  # Fallback when rsync is unavailable: cp + manual prune.
  rm -rf "$DEST_SKILL"
  cp -R "$SKILL_SRC" "$DEST_SKILL"
  find "$DEST_SKILL" -type d \( -name '__pycache__' -o -name '.pytest_cache' \) \
       -prune -exec rm -rf {} + 2>/dev/null || true
  find "$DEST_SKILL" -type f -name '*.pyc' -delete 2>/dev/null || true
fi

# ---------- (2) install the hook ------------------------------------------------

HOOK_DIR="$TARGET/.claude/hooks"
mkdir -p "$HOOK_DIR"
cp "$SKILL_SRC/hooks/block_binary_read.py" "$HOOK_DIR/"
chmod +x "$HOOK_DIR/block_binary_read.py"
echo "[2/3] Installed hook at $HOOK_DIR/block_binary_read.py"

# ---------- (3) wire up settings.json ------------------------------------------

SETTINGS="$TARGET/.claude/settings.json"
FRAGMENT="$SKILL_SRC/hooks/settings.fragment.json"

if [[ ! -f "$SETTINGS" ]]; then
  cp "$FRAGMENT" "$SETTINGS"
  echo "[3/3] Created $SETTINGS from fragment"
else
  if grep -q "block_binary_read.py" "$SETTINGS"; then
    echo "[3/3] $SETTINGS already references block_binary_read.py — no change"
  else
    if command -v python3 >/dev/null 2>&1; then
      BACKUP="$SETTINGS.bak.$(date +%s 2>/dev/null || echo backup)"
      cp "$SETTINGS" "$BACKUP"
      python3 - "$SETTINGS" "$FRAGMENT" <<'PY'
import json, sys, pathlib
settings_path = pathlib.Path(sys.argv[1])
fragment_path = pathlib.Path(sys.argv[2])
settings = json.loads(settings_path.read_text() or "{}")
fragment = json.loads(fragment_path.read_text())

settings.setdefault("hooks", {})
pre = settings["hooks"].setdefault("PreToolUse", [])
frag_entries = fragment.get("hooks", {}).get("PreToolUse", [])
for new_entry in frag_entries:
    matcher = new_entry.get("matcher")
    target = next((e for e in pre if e.get("matcher") == matcher), None)
    if target is None:
        pre.append(new_entry)
        continue
    target.setdefault("hooks", [])
    for h in new_entry.get("hooks", []):
        if h not in target["hooks"]:
            target["hooks"].append(h)

settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
PY
      echo "[3/3] Merged PreToolUse entry into $SETTINGS (backup: $BACKUP)"
    else
      echo "[3/3] WARNING: $SETTINGS exists and python3 is unavailable for safe merging." >&2
      echo "      Open it and add the PreToolUse block from $FRAGMENT manually." >&2
    fi
  fi
fi

# ---------- environment sanity report ------------------------------------------

echo
echo "Environment check:"

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  ✓ $label"
  else
    echo "  ✗ $label  (missing — install when you actually need it)"
  fi
}

check "python3" command -v python3
check "pdftotext (poppler) — fastest PDF reader" command -v pdftotext
check "LibreOffice (soffice) — for .doc → .docx conversion" command -v soffice
if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import pdfminer" >/dev/null 2>&1; then
    echo "  ✓ pdfminer.six (PDF reader fallback)"
  else
    echo "  ✗ pdfminer.six  (pip install pdfminer.six — recommended fallback)"
  fi
  if python3 -c "import docx" >/dev/null 2>&1; then
    echo "  ✓ python-docx (used by build_report.py)"
  else
    echo "  ✗ python-docx  (pip install python-docx — needed when building DOCX)"
  fi
  if python3 -c "import sklearn,pandas,matplotlib" >/dev/null 2>&1; then
    echo "  ✓ sklearn + pandas + matplotlib"
  else
    echo "  ✗ sklearn / pandas / matplotlib (needed for ML-style reports)"
  fi
fi

echo
echo "Done. To use the skill in this project:"
echo "  cd \"$TARGET\""
echo "  # open Claude Code here and ask it to write the report."
echo
echo "The hook will refuse Read on .pdf / .docx / .doc and steer Claude to:"
echo "  python $SKILL_NAME/scripts/read_pdf_text.py <file>"
echo "  python $SKILL_NAME/scripts/inspect_docx.py <file>"
