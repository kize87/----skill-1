# hooks/

Optional Claude Code hook that physically prevents the `document`-content-block 400 from happening on non-Claude API backends.

## What's in here

| File | Purpose |
|---|---|
| `block_binary_read.py` | PreToolUse hook script — refuses any `Read` call targeting `.pdf`, `.docx`, or `.doc`, telling Claude to use `scripts/read_pdf_text.py` or `scripts/inspect_docx.py` instead. |
| `settings.fragment.json` | The JSON fragment to merge into `.claude/settings.json` so the hook is actually invoked. |

## Why you might want it

The skill's `SKILL.md` already says "never use the `Read` tool on binary documents" — but that rule only kicks in **after** Claude has loaded the skill into context. On a fresh session Claude often calls `Read('Task 2.pdf')` as its very first tool use, before it has read SKILL.md, and the session dies with HTTP 400 because non-Claude backends (GLM, proxies, OpenRouter relays) reject the `document` content block that `Read` emits for binary files.

This hook moves the rule from "instructions Claude reads" to "tool-layer policy". It cannot be skipped.

## How to install in a project

From the project root where you actually run Claude Code (not from this skill folder):

```bash
# 1. Copy the hook script into the project's hooks directory.
mkdir -p .claude/hooks
cp <path-to>/experiment-report-writer/hooks/block_binary_read.py .claude/hooks/
chmod +x .claude/hooks/block_binary_read.py

# 2. Merge the hook entry into .claude/settings.json.
# If .claude/settings.json doesn't exist, just copy the fragment as-is:
cp <path-to>/experiment-report-writer/hooks/settings.fragment.json .claude/settings.json

# If .claude/settings.json already exists, paste the "PreToolUse" entry from
# settings.fragment.json into the existing "hooks" object (or create one).
```

## How to install globally (every Claude Code session, every project)

Same idea, in `~/.claude/`:

```bash
mkdir -p ~/.claude/hooks
cp <path-to>/experiment-report-writer/hooks/block_binary_read.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_binary_read.py
# Then edit ~/.claude/settings.json and merge the PreToolUse entry.
```

The command in the fragment uses a relative path (`.claude/hooks/...`), which matches how Claude Code resolves project-level hooks. For a global install, change the command in your `~/.claude/settings.json` to:

```
python3 ~/.claude/hooks/block_binary_read.py
```

## Verify it's working

After installing, in a Claude Code session, ask Claude to read a PDF directly. You should see a tool-call rejection that mentions `read_pdf_text.py`. If the rejection text appears in the conversation, the hook is live.

## Disable it temporarily

Comment out or delete the `PreToolUse` block in `.claude/settings.json`. The hook script itself does nothing on its own — it has to be wired up via `settings.json` to run.

## What this hook does NOT do

- It does not block files you **drag** into the Claude Code input box. Drag-and-drop bypasses tool calls; if a backend rejects `document` content blocks, drag-attached PDFs will still 400. Use file paths instead of drag-and-drop on those backends.
- It does not block reading PDFs through `Bash` (e.g. `python scripts/read_pdf_text.py`). That's the whole point — those go through stdout text and are safe.
- It does not affect `.py`, `.ipynb`, `.md`, `.csv`, `.txt`, image files, or anything else. Only `.pdf` / `.docx` / `.doc` are blocked.
