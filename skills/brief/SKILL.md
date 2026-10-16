---
name: brief
description: Research the market for a product idea and save a sourced market brief.
disable-model-invocation: true
argument-hint: "\"<product idea>\" [--deep]"
---

# Market brief (Phase 1 stub)

The full research workflow is built in Phase 4. For now, this skill only checks that Python
works and repeats the idea back.

## 1. Check Python

Run this command:

```
python "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" --version
```

If `python` is not found, run the same command with `python3` instead.

- If either one prints `market-copilot ...`, tell the user which command worked.
- If it prints a message that Python is too old, show that message to the user.
- If neither command is found, tell the user in plain English: "Market Copilot needs Python
  3.11 or newer. Install it from https://www.python.org/downloads/ (on Windows, check
  'Add python.exe to PATH' during install), then open a new terminal and try again." Then stop.

## 2. Repeat the idea

Tell the user: "Got your idea: $ARGUMENTS. The research workflow is coming in Phase 4."
