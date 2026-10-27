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
- **A sourced claim says only what its quotes say.** Any conclusion you draw from it goes in
  its own claim marked `"assumption"`.
- **Never state a market size.** You propose assumptions; `check.py` does the math. Every
  sizing value is one number copied from one quote, or one guess. Never a number you worked
  out from other numbers.
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
- Pick the words that support your claim directly (the price, the count, the feature). For a
  market-size figure, the quote must contain the number itself, written as the page writes it.
- If the script cannot load a page (for example, "the site may block scripts"), first look for
  another page with the same fact. Only if the page is important (such as a competitor's own
  pricing page) read it with WebFetch instead. Its quote will usually come out Unverified, and
  that is fine.

Stop at about the source count for the chosen depth. Note what you could not find; those go
in the summary's unknowns.

## 6. Write ledger.json and brief.json

Use the Write tool to write `ledger.json` and `brief.json` into the run folder, following the
**Format** section at the end of this skill exactly. Key points:

- Ledger ids are `S1`, `S2`, ... with url, title, the exact quote, and today's date.
- Every factual statement is a claim with `status` `"sourced"` (cites ledger ids) or
  `"assumption"` (your estimate). Never write "verified".
- `research_date` is today. `depth` is `"quick"` or `"deep"`.
- Riskiest assumptions come riskiest first, each with a concrete way to test it.
- Interview questions ask about **past behavior** ("Tell me about the last time...", "How do
  you handle ... today?"), never hypotheticals ("Would you buy...", "If we built...").
- A sourced claim restates only what its quotes say. Put any conclusion in a separate
  assumption claim.
- Market size is the six inputs (customers, units_per_customer, price, purchases_per_year,
  sam_share, som_share), each with low, base, and high, plus `price_covers`. Never write a
  total.

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
- **If it warns that a sourced claim uses a guessing word** (may, likely, often, probably,
  ...), split it in two: the sourced claim keeps only what its quotes say, and the guess
  becomes a new claim with `status: "assumption"` and no source ids. Then run it again.
- **If it warns that a source is not cited by any claim**, remove that entry from
  `ledger.json` and run it again. Never add a claim just to use a source; that would raise the
  Verified count without adding evidence.
- **Never change a claim's `status`, its `source_ids`, or a quote just to improve the
  counts.** The one exception: you may fix a quote that was copied wrong by reading its page
  again with `sources.py fetch` and copying the exact text from that output. Unverified items
  stay in the brief with their reasons; that is the honest result.
- Never edit `brief.md` or `check_report.json` yourself. `check.py` writes them.

## 8. Report

Finish with a short message:

1. The counts from check.py's last output: verified, assumptions, unverified.
2. The full paths of `brief.md`, `brief.json`, `ledger.json`, and `check_report.json`.
3. "Open brief.md to read your brief, or run /market-copilot:view to open it in the viewer,
   where you can change the market-size numbers."
4. A reminder that prices and competitors change, so the brief is a snapshot from today, and
   that it does not show anyone will buy.
5. A nudge: "Next step: pick three people who match your target customer and interview them
   this week with the script in the brief."

Do not repeat any market size figure in this message; point to the Market size section of
brief.md instead.

## Format: ledger.json and brief.json

This format lives inside the skill on purpose, so you never need to read a file from the
plugin folder. `check.py` refuses to run (and lists every problem) if either file breaks the
rules below. Fix the problems and run it again.

### ledger.json: the sources

A JSON list. One entry per quote you copied from a page:

| Field | Meaning |
|---|---|
| `id` | `S1`, `S2`, `S3`, ... Each id is used once. |
| `url` | The page the quote came from (http or https). |
| `title` | The page title. |
| `quote` | Exact text copied from the page, **25 words or fewer**. Copy it from the output of `sources.py fetch <url>`, never from memory or a search snippet. |
| `accessed` | The date you read the page, like `2026-10-16`. |

Two entries may share a URL (two quotes from one page). Each page is downloaded once. Every
entry must be cited by at least one claim; `check.py` warns about any that are not.

### Claims

Every factual statement is a **claim**:

```
{"text": "...", "status": "sourced" | "assumption", "source_ids": ["S1"]}
```

- `"sourced"`: the text states only what the quotes of the listed sources say. Must cite at
  least one id.
- `"assumption"`: your estimate, guess, or conclusion. `source_ids` may be empty.
- Never write "verified". `check.py` decides that, not you. A sourced claim is Verified only if
  every id it cites is in the ledger, the page loads, the quote is on the page, and the quote is
  25 words or fewer. Otherwise it is Unverified, with the reason, and it stays in the brief.
- Keep facts and conclusions apart. If a quote only says a distributor's bins alert the local
  branch, the sourced claim is "The bins alert the local branch when stock runs low." The
  conclusion "Distributors may be a better buyer than dealerships" is a separate assumption
  claim. `check.py` warns when a sourced claim uses guessing words like may, likely, often, or
  probably.

### Fields

| Field | Meaning |
|---|---|
| `idea` | The product idea, in one line. |
| `research_date` | Today's date, like `2026-10-16`. |
| `depth` | `"quick"` or `"deep"`. |
| `target_customer`, `geography` | Who and where. |
| `currency` | Optional, default `"USD"`. |
| `summary.found` | List of claims: the main things the research found. |
| `summary.unknowns` | List of text: what we still don't know. |
| `riskiest_assumptions` | List of `{assumption, why_risky, how_to_test}`, riskiest first. |
| `interview_script` | `{intro, questions: [{question, listening_for}]}`. |
| `competitors` | List of `{name, url, description: claim, price: claim}`. |
| `market_size` | `price_covers` and the six sizing inputs below. |

### Interview questions

Ask about past behavior, never hypotheticals: "Tell me about the last time...", "What did you
try...", "How do you handle ... today?". Not "Would you buy...", "Will you...", "If we built...".
`check.py` warns about questions that sound hypothetical, and brief.md marks them for rewriting.

### Market size

Never state a market size. Give the six inputs and `sizing.py` does the math:

    TAM = customers x units_per_customer x price x purchases_per_year
    SAM = TAM x sam_share     (share of customers who could buy)
    SOM = SAM x som_share     (share we could win in about 3 years)

- `units_per_customer` is how many units one customer pays for, such as bins per dealership
  or seats per office. Use 1 when each customer buys one.
- Each input has `low`, `base`, and `high` numbers (low <= base <= high, none negative), a
  `unit`, a `status`, and `source_ids`. Shares are fractions from 0 to 1 (0.25 means 25%).
- **Each value is one number copied from one quote, or one guess.** Never multiply, add,
  average, or round numbers yourself to make a value. If no quote gives the number, mark the
  input `"assumption"`.
- For a sourced input, `check.py` looks for each value in the cited quotes. The base value
  must be there, or the input is Unverified and used as an assumption in the math. A low or
  high value that isn't in a quote is shown in brief.md as a guess. Shares match only numbers
  written with % or "percent".
- `price_covers` is text that says what the price counts. If a product has a one-time part
  (hardware, setup) and a monthly part, pick one for `price` and say which, for example "The
  monthly fee per bin only. The one-time hardware cost is left out."

## Example

A made-up example. Both blocks below are checked by the tests, so they always pass `check.py`.

ledger.json:

```json
[
  {
    "id": "S1",
    "url": "https://example.com/pricing",
    "title": "Pricing | Example Booking",
    "quote": "Starter: $29 per month for one location",
    "accessed": "2026-10-16"
  },
  {
    "id": "S2",
    "url": "https://example.org/clinic-census",
    "title": "Clinic Census 2025",
    "quote": "The census counted 20,000 small dental clinics in the United States.",
    "accessed": "2026-10-16"
  }
]
```

brief.json:

```json
{
  "idea": "Online booking and reminder texts for small dental clinics",
  "research_date": "2026-10-16",
  "depth": "quick",
  "target_customer": "Office managers at dental clinics with one to five chairs",
  "geography": "United States",
  "currency": "USD",
  "summary": {
    "found": [
      {"text": "The census counted 20,000 small dental clinics in the US.",
       "status": "sourced", "source_ids": ["S2"]},
      {"text": "Most of those clinics are probably too small to have an IT person.",
       "status": "assumption", "source_ids": []}
    ],
    "unknowns": ["Whether office managers or dentists choose the booking tool."]
  },
  "riskiest_assumptions": [
    {"assumption": "Missed appointments are a top-three problem for office managers.",
     "why_risky": "No independent evidence yet.",
     "how_to_test": "Ask five office managers to walk through their last no-show."}
  ],
  "interview_script": {
    "intro": "Thanks for talking with me. I'm learning how small clinics handle appointments.",
    "questions": [
      {"question": "Tell me about the last time a patient missed an appointment.",
       "listening_for": "What it cost them and what they did afterward."}
    ]
  },
  "competitors": [
    {"name": "Example Booking",
     "url": "https://example.com",
     "description": {"text": "Online booking for small clinics.",
                     "status": "assumption", "source_ids": []},
     "price": {"text": "Starter: $29 per month for one location.",
               "status": "sourced", "source_ids": ["S1"]}}
  ],
  "market_size": {
    "price_covers": "The monthly subscription only. There is no one-time fee.",
    "customers": {"low": 10000, "base": 20000, "high": 40000,
                  "unit": "small dental clinics in the US",
                  "status": "sourced", "source_ids": ["S2"]},
    "units_per_customer": {"low": 1, "base": 1, "high": 2, "unit": "locations per clinic",
                           "status": "assumption", "source_ids": []},
    "price": {"low": 29, "base": 50, "high": 79, "unit": "US dollars per month",
              "status": "assumption", "source_ids": []},
    "purchases_per_year": {"low": 12, "base": 12, "high": 12, "unit": "months billed per year",
                           "status": "assumption", "source_ids": []},
    "sam_share": {"low": 0.2, "base": 0.25, "high": 0.5,
                  "unit": "fraction of clinics who could buy",
                  "status": "assumption", "source_ids": []},
    "som_share": {"low": 0.05, "base": 0.1, "high": 0.2,
                  "unit": "fraction of SAM we could win in 3 years",
                  "status": "assumption", "source_ids": []}
  }
}
```

In this example, customers is sourced from S2: its base value 20,000 is in the quote, so it
can be Verified, and brief.md shows low (10,000) and high (40,000) as guesses.
