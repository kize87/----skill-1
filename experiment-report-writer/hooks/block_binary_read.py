#!/usr/bin/env python3
"""PreToolUse hook: block Read on .pdf / .docx / .doc files.

Why this exists
---------------
Claude Code's built-in `Read` tool returns binary documents (PDF, DOCX, DOC)
as a `document` content block. Official Anthropic Claude models support that
content type natively. Many third-party Anthropic-compatible backends
(GLM-5.1, GPT-via-proxy, OpenRouter relays, …) reject it with HTTP 400 on the
NEXT request, killing the session.

The experiment-report-writer skill bundles `scripts/read_pdf_text.py` and
`scripts/inspect_docx.py` to extract plain text instead. But the skill rule
("never use Read on binary documents") is just a SKILL.md instruction —
on a fresh session Claude often calls Read('Task 2.pdf') BEFORE it has read
the SKILL.md guidance, and the session dies.

This hook blocks the call at the tool layer so it cannot happen, regardless
of which model or which prompt the session starts with.

How to install
--------------
1. Copy this file to your project root: `<project>/.claude/hooks/block_binary_read.py`
2. Add the hook entry to `<project>/.claude/settings.json` — see
   `settings.fragment.json` next to this file for the exact JSON.
3. `chmod +x .claude/hooks/block_binary_read.py`.

For a global install, put it under `~/.claude/hooks/` and merge the JSON
fragment into `~/.claude/settings.json` instead.

Hook contract (Claude Code PreToolUse)
--------------------------------------
- stdin:  JSON describing the planned tool call ({"tool_name", "tool_input", ...}).
- stdout: nothing on allow.
- exit 0: allow the tool call to proceed.
- exit 2: block the tool call; stderr is shown to Claude as the rejection
          reason, so we put the script suggestion there.

We deliberately keep the script tiny and stdlib-only so it works on any
Python ≥3.8 the user happens to have on PATH.
"""
from __future__ import annotations

import json
import os
import sys

BLOCKED_EXTS = (".pdf", ".docx", ".doc")


def _path_from_input(tool_input: dict) -> str:
    """Pull the target path out of the Read tool's input. The Read tool uses
    `file_path`; we also tolerate `path` and `notebook_path` to be safe."""
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0  # don't block on malformed input — just let it through

    if payload.get("tool_name") != "Read":
        return 0

    path = _path_from_input(payload.get("tool_input") or {})
    if not path:
        return 0

    lowered = path.lower()
    if not lowered.endswith(BLOCKED_EXTS):
        return 0

    skill_root = os.environ.get(
        "EXPERIMENT_REPORT_SKILL",
        "experiment-report-writer",
    )
    if lowered.endswith(".pdf"):
        suggestion = (
            f"python {skill_root}/scripts/read_pdf_text.py "
            f"{json.dumps(path, ensure_ascii=False)}"
        )
    else:
        suggestion = (
            f"python {skill_root}/scripts/inspect_docx.py "
            f"{json.dumps(path, ensure_ascii=False)}"
        )

    sys.stderr.write(
        "Refusing to Read a binary document: this would emit a `document` "
        "content block, which non-Claude API backends (GLM, proxies, …) reject "
        "with HTTP 400 on the next request.\n"
        f"Use the skill's text extractor instead, e.g.:\n  {suggestion}\n"
        "If you really need the raw file (e.g. for an embedded image), copy it "
        "to a known path and reference it by path in your prose — do not pass it "
        "through the Read tool.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
