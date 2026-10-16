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

