---
name: brief
description: Research the market for a product idea and save a sourced market brief.
disable-model-invocation: true
argument-hint: "\"<product idea>\" [--deep]"
# Pre-approved for the turn that runs this skill, so a first-time user isn't flooded with
# permission prompts. Each rule allows one of the plugin's own scripts, not Python in general.
# Every command below is written exactly the way these rules spell it.
allowed-tools:
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" *)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/copilot/sources.py" fetch *)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/copilot/sources.py" fetch *)
  - WebSearch
  - WebFetch
  - Edit(market-briefs/**)
---

# Market brief

You research the market for the user's product idea and save a sourced brief that prepares
them for customer interviews. Code decides what is verified, not you. Follow these steps in
order.

Ground rules for the whole run:

- **No invented facts.** Every competitor, price, and market figure must come from a page you
  read with `sources.py fetch`, with an exact quote in the ledger. If you didn't read it, it is
  an assumption.
- **Never say a claim is verified.** `check.py` decides that.
- **Never state a market size.** You propose assumptions; `check.py` does the math.
- **Never say demand is validated.** The brief prepares the user for interviews.
- **Run each command exactly as written here**, one command per call: no `cd`, no `&&`, no
  `mkdir`, no pipes. That keeps them pre-approved.
- **Keep the user posted** with one short line per step, like "Searching for competitors..."
  or "Reading 9 pages...". No long explanations while you work.

## 0. Privacy note

Start by telling the user, once:

> Privacy: your idea is processed by Claude through your own Claude account, under Anthropic's
> terms, and parts of it appear in web search queries. This plugin sends nothing to its author
> or to any server the author runs, and briefs are saved only on your computer.

## 1. Read the request

The request is: $ARGUMENTS

- If it contains `--deep`, the depth is **deep**: about 5-8 competitors and about 15 sources.
- Otherwise the depth is **quick**: about 3-5 competitors and about 10 sources.
- Everything else (without `--deep` and the surrounding quotes) is the idea.
- If there is no idea, ask the user to run it again like
  `/market-copilot:brief "online booking for small dental clinics"` and stop.

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

## 3. Ask only what is missing

You need three things: the **target customer**, the **geography**, and a **price guess**.
Use whatever the idea already says. For each one that is genuinely missing, ask about it.

- Ask with the AskUserQuestion tool, all missing items in **one** call (at most three
  questions). Give each question 2-3 concrete suggested answers that fit the idea. The user
  can always type their own.
- Do not ask in a plain chat message. A typed reply ends this turn, and later steps would then
  prompt for permission.
- If nothing is missing, ask nothing and go on.

## 4. Pick the run folder

The run folder is `market-briefs/<today>-<short-name>/` in the user's current folder, for
example `market-briefs/2026-10-16-dental-booking/`. The short name is 2-4 lowercase words of
the idea joined by hyphens. If that folder already exists, add `-2`, `-3`, and so on. Don't
create it yet; writing the first file in step 6 creates it.

## 5. Research

Say "Searching for competitors..." and use WebSearch to find:

- competitors and close substitutes (including what customers do today without a product),
- their pricing pages,
- figures for how many target customers exist (government statistics, industry associations,
  trade reports).

Then say "Reading N pages..." and read each promising page with:

```
python "${CLAUDE_PLUGIN_ROOT}/copilot/sources.py" fetch <url>
```

From that output, pick quotes for the ledger:

- Copy each quote **character for character** from the script's output. Never write a quote
  from memory, from a search snippet, or in your own words.
- **25 words or fewer**, taken from a single line of the output.
- Pick the words that support your claim directly (the price, the count, the feature).
- If the script cannot load a page (for example, "the site may block scripts"), first look for
  another page with the same fact. Only if the page is important (such as a competitor's own
  pricing page) read it with WebFetch instead. Its quote will usually come out Unverified, and
  that is fine.

Stop at about the source count for the chosen depth. Note what you could not find; those go
in the summary's unknowns.

## 6. Write ledger.json and brief.json

First read the format with the Read tool and follow it exactly:
`${CLAUDE_PLUGIN_ROOT}/skills/brief/brief_schema.md`

Then use the Write tool to write `ledger.json` and `brief.json` into the run folder. Key
points (the schema has the details):

- Ledger ids are `S1`, `S2`, ... with url, title, the exact quote, and today's date.
- Every factual statement is a claim with `status` `"sourced"` (cites ledger ids) or
  `"assumption"` (your estimate). Never write "verified".
- `research_date` is today. `depth` is `"quick"` or `"deep"`.
- Riskiest assumptions come riskiest first, each with a concrete way to test it.
- Interview questions ask about **past behavior** ("Tell me about the last time...", "How do
  you handle ... today?"), never hypotheticals ("Would you buy...", "If we built...").
- Market size is the five inputs (customers, price, purchases_per_year, sam_share, som_share),
  each with low, base, and high. Never write a total.

## 7. Check

Say "Checking N sources..." and run:

```
python "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" <run folder>
```

- **If it lists problems with the files** (it exits with "could not check this run"), fix
  each problem in `brief.json` or `ledger.json` and run it again. After three tries, show the
  user the remaining problems and stop.
- **If it warns that an interview question sounds hypothetical**, rewrite that question to
  ask about past behavior and run it again.
- **Never change a claim's `status`, its `source_ids`, or a quote just to improve the
  counts.** The one exception: you may fix a quote that was copied wrong by reading its page
  again with `sources.py fetch` and copying the exact text from that output. Unverified items
  stay in the brief with their reasons; that is the honest result.
- Never edit `brief.md` or `check_report.json` yourself. `check.py` writes them.

## 8. Report

Finish with a short message:

1. The counts from check.py's last output: verified, assumptions, unverified.
2. The full paths of `brief.md`, `brief.json`, `ledger.json`, and `check_report.json`.
3. "Open brief.md to read your brief. (A viewer with editable market-size numbers is coming.)"
4. A reminder that prices and competitors change, so the brief is a snapshot from today, and
   that it does not show anyone will buy.
5. A nudge: "Next step: pick three people who match your target customer and interview them
   this week with the script in the brief."

Do not repeat any market size figure in this message; point to the Market size section of
brief.md instead.
