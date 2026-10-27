---
name: view
description: Open the Market Copilot viewer on the saved market briefs in this folder.
disable-model-invocation: true
argument-hint: "[folder of briefs, default market-briefs]"
# Pre-approved for the turn that runs this skill, like the brief skill. Each rule allows one of
# the plugin's own commands, not Python in general. Every command below is written exactly the
# way these rules spell it.
allowed-tools:
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" --version)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" --version)
  - Bash(python -m streamlit version)
  - Bash(python3 -m streamlit version)
  - Bash(python -m streamlit run "${CLAUDE_PLUGIN_ROOT}/app.py" *)
  - Bash(python3 -m streamlit run "${CLAUDE_PLUGIN_ROOT}/app.py" *)
---

# Market brief viewer

You open the viewer, a local web page that shows the user's saved briefs with colored badges
and lets them change market-size numbers. Follow these steps in order. Run each command exactly
as written here, one command per call: no `cd`, no `&&`, no pipes. That keeps them
pre-approved. Never install anything yourself.

## 1. Pick the folder

The folder of briefs is `market-briefs` (in the user's current folder). If the user gave a
folder, use it instead: $ARGUMENTS

## 2. Check Python

Run:

```
python "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" --version
```

If `python` is not found, run the same command with `python3` instead.

- If one prints `market-copilot ...`, use that same command (`python` or `python3`) for every
  later step.
- If it prints a message that Python is too old, show that message to the user and stop.
- If neither command works, tell the user: "Market Copilot needs Python 3.11 or newer. Install
  it from https://www.python.org/downloads/ (on Windows, check 'Add python.exe to PATH' during
  install), then open a new terminal and try again." Then stop.

## 3. Check Streamlit

The viewer needs Streamlit (making briefs doesn't). Run:

```
python -m streamlit version
```

If it prints `Streamlit, version ...`, go on. If it says `No module named streamlit`, do not
install it. Tell the user:

> The viewer needs Streamlit, a free Python package. Install it with
> `python -m pip install streamlit` (use `python3` if that is the command that works for you),
> then run /market-copilot:view again. Your briefs are also saved as brief.md files you can
> read without it.

Then stop.

## 4. Start the viewer

Streamlit keeps running until it is stopped, so run this command **in the background** (Bash
with `run_in_background: true`), never in the foreground:

```
python -m streamlit run "${CLAUDE_PLUGIN_ROOT}/app.py" --server.headless=true --server.address=localhost --browser.gatherUsageStats=false --client.toolbarMode=minimal -- "market-briefs"
```

Replace `market-briefs` with the folder from step 1 if the user gave one.

- `--server.headless=true` stops Streamlit from asking for an email address on its first run
  and from opening a browser by itself.
- `--server.address=localhost` keeps the viewer on this computer, so nobody else on the
  network can open it, and stops Streamlit from looking up the computer's public address
  online.
- `--browser.gatherUsageStats=false` turns off Streamlit's usage statistics, so the viewer
  sends nothing anywhere.
- `--client.toolbarMode=minimal` hides Streamlit's Deploy button, which this viewer doesn't use.

## 5. Tell the user the address

Read the background command's output file. Once it shows a line starting with `URL:`, tell
the user:

1. "The viewer is running at <that URL>. Open that address in your browser."
   (It is usually http://localhost:8501; Streamlit picks the next port if that one is busy.)
2. "Pick a brief in the sidebar. Change a base value under Market size inputs to recompute
   TAM, SAM, and SOM. Your changes are marked Your edit, last until you refresh the page, and
   never change your saved files. To save the brief with your numbers, click Prepare Markdown
   download, then Save brief.md."
3. "To stop the viewer, run /tasks and stop it there. It also stops when you exit Claude
   Code."

If the output shows an error instead, show the user the last few lines of it and stop.
