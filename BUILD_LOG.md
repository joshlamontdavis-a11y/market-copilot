# Build log

## 2026-10-16: Phase 1, Skeleton

What changed:
- Recorded the kickoff interview answers in `SPEC.md`.
- Renamed the branch to `main`.
- Added the plugin manifest and marketplace file (`market-copilot`, version 0.1.0).
- Added a stub `/market-copilot:brief` skill that checks Python (tries `python`, then
  `python3`) and repeats the idea back.
- Added the `copilot/` package with a stub `check.py` entry point: Python 3.11+ guard and
  `--version`.
- Added pytest setup and five tests: manifests agree, skill frontmatter is complete, `check.py`
  runs, the version guard works, and `copilot/` imports only the standard library (Rule 5).
- `claude plugin validate .` passes. One warning remains: `CLAUDE.md` at the plugin root is not
  loaded as plugin context. That is expected, because `CLAUDE.md` guides development of this
  repo and is not meant to ship to users.

Files touched: `SPEC.md`, `BUILD_LOG.md`, `CLAUDE.md`, `.gitignore`, `requirements.txt`,
`requirements-dev.txt`, `pytest.ini`, `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `skills/brief/SKILL.md`, `copilot/__init__.py`,
`copilot/check.py`, `tests/test_skeleton.py`

My decisions and what I learned:

I switched from a web app to a Claude Code plugin because I didn’t want to pay for API calls every time someone ran a brief. Now it’s free to run, and anyone with Claude can install it, including future teammates. The decision I’d stand behind most is that unverified sources still show up, but they never count as evidence in the market size. Setup was honestly the hardest part. Most of my problems were PATH stuff and running commands in the wrong folder, so now I check where I am before I run anything.

## 2026-10-16: Phase 2, Sizing engine

What changed:
- Added `copilot/sizing.py`: bottom-up TAM (customers x price x purchases per year), SAM
  (TAM x share who could buy), and SOM (SAM x share we could win). Each of the five
  assumptions has low, base, and high values, a unit, a status, and source ids, and the
  module computes three scenarios: all low, all base, all high.
- Shares are fractions from 0 to 1 (0.25 means 25%).
- Inputs are checked before any math: a missing assumption or value is an error (never
  treated as zero), and so are text, true/false, negative numbers, shares above 1,
  low > base or base > high, an unknown status, and "sourced" with no source ids.
  Zero is allowed.
- Added `mark_unverified_as_assumptions`: a sourced assumption that cites an unverified
  source is relabeled "assumption" (SPEC.md). `check.py` will call it in Phase 4.
- Wrote 16 tests first in `tests/test_sizing.py` using numbers that can be checked by hand
  (base: 20,000 x $50 x 2 = $2,000,000 TAM, $500,000 SAM, $50,000 SOM). 21 tests pass.

Files touched: `copilot/sizing.py`, `tests/test_sizing.py`, `BUILD_LOG.md`, `CLAUDE.md`

My decisions and what I learned:

The most important thing the sizing code does is treat a missing number as an error instead of a zero. A zero would quietly give you a fake market size, and nobody would know. I had Claude write the tests before the code, so I got to see them fail and then pass, which showed me the tests were actually checking something. I also ran the base case on my calculator: 20,000 customers buying twice a year at $50 is $2,000,000, and it matched.

## 2026-10-16: Phase 3, Source checker

What changed:
- Added `copilot/sources.py` (standard library only):
  - `fetch_text(url)` downloads a page with a normal browser User-Agent and a 10-second
    timeout and returns its readable text. Text inside `script`, `style`, `noscript`, and
    `template` is skipped. Headings, paragraphs, and list items each get their own line, while
    links and bold text join into the sentence around them.
  - Only `http` and `https` links are read (urllib would otherwise open `file://` paths on the
    user's computer). Downloads stop at about 5 MB.
  - Any failure (HTTP error, timeout, nothing listening, not a web page) raises `FetchError`
    with a plain-English reason starting "page did not load:", which check.py will show as the
    Unverified reason in Phase 4.
  - `quote_in_text(quote, text)` compares after normalizing both sides: curly quotes become
    straight, invisible characters (zero-width spaces, soft hyphens, and similar) are removed,
    case is ignored, and all whitespace collapses to single spaces. Nothing else is loosened.
    An empty quote never matches.
  - Command line: `python copilot/sources.py fetch <url>` prints the page text (exit 0) or the
    reason it failed (exit 1). Output is UTF-8 so the Windows console doesn't crash on curly
    quotes.
- Added three small hand-made test pages about a made-up company in `tests/fixtures/pages/`.
- Added `tests/conftest.py`: a local test server on 127.0.0.1 that serves those pages (plus a
  404 and a slow page), and a guard on every test that fails any connection to anywhere other
  than this computer, so tests can never touch the live web.
- Added 16 tests in `tests/test_sources.py`: quote on the page, not on the page, one changed
  word, split across link and bold tags, curly quotes and extra spaces both ways, invisible
  characters, empty quote, scripts and styles excluded, entities decoded, User-Agent sent,
  404, timeout, nothing listening, `file://` refused, the live-web guard, and the command line
  for success and failure. 37 tests pass.
- Tried the command on a real page (python.org/about): 218 lines of readable text, a real quote
  was found, and a made-up quote was not.
- Updated the `tests/` line in `CLAUDE.md`: fixtures are hand-made pages, never copies of real
  websites.

Files touched: `copilot/sources.py`, `tests/conftest.py`, `tests/test_sources.py`,
`tests/fixtures/pages/pricing.html`, `tests/fixtures/pages/testimonials.html`,
`tests/fixtures/pages/about.html`, `CLAUDE.md`, `BUILD_LOG.md`

My decisions and what I learned:

The source checker is what makes the whole tool honest. Claude can find a quote, but my code decides whether it’s actually on the page, and if even one word is off, it doesn’t count. What surprised me was how many ways a real quote can fail to match, like curly quotes, extra spaces, or invisible characters hidden inside words, so we handled those without loosening anything you can actually see. I also like that the tests can’t touch the internet at all, so a passing test means my code works, not that some website happened to be up.

## 2026-10-16: Phase 4a, Brief schema, check.py, and brief.md

What changed:
- Added `skills/brief/brief_schema.md`: the formats of `ledger.json` (id, url, title, quote of
  25 words or fewer, date accessed) and `brief.json` (summary, riskiest assumptions, interview
  script, competitors, market size). Every factual statement is a "claim" with text, a status
  of "sourced" or "assumption", and source ids. The brief never says "verified"; check.py does.
  Its example JSON is checked by a test, so the doc can't drift from the code.
- Rewrote `copilot/check.py` (`python check.py <run folder>`):
  - Checks both files first. If anything is malformed, it lists every problem at once, writes
    nothing, and exits 1.
  - Checks every source, downloading each page once (a few at a time, for speed). The first
    failing reason wins: quote over 25 words, page did not load, or quote not found on the page.
  - Labels every claim Verified, Assumption, or Unverified. An Unverified claim lists one reason
    per bad source id, including "missing id (not in the ledger)".
  - Sizes the market with `sizing.py`, using `mark_unverified_as_assumptions` so a figure with an
    unverified source is used in the math as an assumption. The report keeps both labels.
  - Warns (does not fail) about interview questions that sound hypothetical ("would you",
    "will you", "if we built", and similar), for Rule 4.
  - Writes `check_report.json` and `brief.md`, and prints the counts, warnings, and file paths.
- Added `copilot/render.py`: turns the brief and the report into `brief.md` in the SPEC.md order
  (summary, riskiest assumptions, interview script, competitors, market size), then a sources
  table. It shows the research date, a note that prices and competitors change, a line that the
  brief does not show anyone will buy, a badge on every claim, and a "Rewrite" marker on any
  flagged interview question.
- Added a hand-made test run (`tests/fixtures/runs/maplewood/`) about a made-up company, plus a
  made-up census page. It plants a fake id (S999), a quote with one changed word, a missing page,
  and a 35-word quote. The test server now records requested paths so a test can prove each page
  is downloaded only once.
- Added 26 tests in `tests/test_check.py`. 63 tests pass.
- Follow-up: `brief.md` now says near the top that Verified means the quoted text is on the
  cited page, and the reader should judge whether the quote supports the claim. The Sources
  table shows only the first 25 words of an over-limit quote, followed by "..."
  (`check_report.json` keeps the whole quote). The 25-word limit now lives in `sources.py` so
  `check.py` and `render.py` share it. 3 more tests; 66 tests pass.

Files touched: `skills/brief/brief_schema.md`, `copilot/check.py`, `copilot/render.py`,
`tests/conftest.py`, `tests/test_check.py`, `tests/fixtures/pages/census.html`,
`tests/fixtures/runs/maplewood/brief.json`, `tests/fixtures/runs/maplewood/ledger.json`, `copilot/sources.py`,
`BUILD_LOG.md`

My decisions and what I learned:

This phase is where everything came together. My code now reads the whole brief, checks every source, and labels each claim itself, so Claude never gets to call its own work verified. My favorite part is that every Unverified item says exactly why, like a missing source or a page that didn’t load, so the reader knows what to go check. I made hypothetical interview questions a warning instead of an error, because a simple keyword check gets some questions wrong, and I didn’t want that stopping a brief in the middle of a demo.
