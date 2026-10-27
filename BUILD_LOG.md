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

## 2026-10-16: Phase 4b, Brief skill

What changed:
- Replaced the stub `skills/brief/SKILL.md` with the full research workflow: privacy note,
  `--deep` flag (deep: about 5-8 competitors and 15 sources; quick: about 3-5 and 10), the
  Python check (`python`, then `python3`), clarifying questions only for a missing target
  customer, geography, or price (one AskUserQuestion call, at most three questions), the run
  folder `market-briefs/<date>-<short-name>/`, research with WebSearch and
  `sources.py fetch`, writing `ledger.json` and `brief.json` per `brief_schema.md`, running
  `check.py`, and a final message with counts, file paths, and an interview nudge.
- If `check.py` lists problems with the files, the skill fixes them and runs it again (up to
  three tries). It must never change a claim's status, its source ids, or a quote to improve
  the counts. It may fix a quote only by reading the page again with `sources.py fetch`.
- Until the Phase 5 viewer exists, the final message points to `brief.md`.
- Added `allowed-tools` so a first-time user isn't flooded with permission prompts. It
  pre-approves `check.py` and `sources.py fetch` (with `python` or `python3`), WebSearch,
  WebFetch (fallback for sites that block the script), and writes under `market-briefs/`.
  Per the skills docs, the grant lasts only for the turn that ran the skill, so questions go
  through AskUserQuestion instead of a chat reply, and every command is written exactly as
  its rule (no `cd`, `&&`, or `mkdir`).
- Added two tests: every `${CLAUDE_PLUGIN_ROOT}` path a skill names exists, and the brief
  skill's commands are pre-approved. 68 tests pass.

Files touched: `skills/brief/SKILL.md`, `tests/test_skeleton.py`, `BUILD_LOG.md`

My decisions and what I learned:

This was the first time I ran the tool on a real idea instead of a made-up test. I picked dealership parts departments as the customer because those are people I can actually go talk to. The research found something I didn’t expect: the real competition isn’t other smart bins, it’s Chrysler’s automatic parts ordering and the distributor reps who already restock shop bins for free. I opened three of the sources myself and all three quotes were right there on the page. The rule I’d defend first is that the skill can’t change a claim’s status or a quote just to make the counts look better, because then the counts wouldn’t mean anything.

## 2026-10-16: Phase 4c, Fixes from the first real run

What changed:
- Sourced claims say only what their quotes say. The skill now puts any conclusion in its own
  assumption claim. `check.py` warns when a sourced claim uses a guessing word (may, might,
  likely, unlikely, often, probably, possibly, perhaps), and brief.md marks it "Check". It is
  a warning, not an error, like the hypothetical-question check.
- Market size has a sixth input, `units_per_customer`:
  TAM = customers x units per customer x price x purchases per year. Each sizing value must be
  one number from one quote or one guess, never a number the model worked out. A new required
  field, `market_size.price_covers`, says which part of a price (monthly or one-time) the
  market size counts.
- `check.py` now reads the numbers in a sourced sizing input's quotes. The base value must be
  there, or the input is Unverified ("base value ... is not in the cited quotes", or "none of
  its numbers appears in the cited quotes") and is used as an assumption in the math. A low or
  high value that isn't in a quote is shown in brief.md as "(guess)". Shares only match numbers
  written with % or "percent", so a 12% share can't match "12 months". Matching uses
  `math.isclose` at its default tolerance.
- brief.md shows TAM, SAM, and SOM in whole dollars. check_report.json keeps the exact numbers.
- `check.py` warns about ledger sources that no claim cites, and brief.md marks them in the
  Sources table. The skill removes those entries; it never adds a claim just to use a source.
- `report["warnings"]` is now a dict with three lists: `hypothetical_questions`,
  `guessing_words`, and `uncited_sources`.
- Fixed the "read outside the working directories" prompt. The docs say `${CLAUDE_PLUGIN_ROOT}`
  is filled in only inside Bash rules in `allowed-tools`, so a Read rule can't point at an
  installed plugin's folder. The format from `brief_schema.md` now lives in a Format section
  at the end of `SKILL.md`, which Claude Code loads with the skill, so there is no file to read
  and no new permission. `brief_schema.md` is deleted.
- Maplewood fixture: added `units_per_customer`, `price_covers`, a sourced claim with "likely",
  an assumption claim, and an uncited source S8. New tests cover each change; 89 tests pass.

Files touched: `copilot/check.py`, `copilot/render.py`, `copilot/sizing.py`,
`skills/brief/SKILL.md`, `skills/brief/brief_schema.md` (deleted), `SPEC.md`, `CLAUDE.md`,
`tests/test_check.py`, `tests/test_sizing.py`, `tests/fixtures/runs/maplewood/brief.json`,
`tests/fixtures/runs/maplewood/ledger.json`, `BUILD_LOG.md`

My decisions and what I learned:

Reading that first brief closely taught me that Verified doesn’t mean true. One line said distributors might be a better buyer and was marked Verified, but the quote only said Fastenal’s bins alert the local branch, so that conclusion came from Claude, not the source. The model also worked out a price row on its own and got the math wrong the first time before fixing it, which is exactly why my code does the math instead. Now check.py reads the numbers inside the quotes, and if the base number isn’t there, the input doesn’t count as sourced. I also added units per customer to the formula, since most IoT products sell more than one unit to each customer.

## 2026-10-16: Phase 4d, A real run as a test fixture

What changed:
- Copied Josh's real run "A load-cell parts bin that weighs its contents and alerts when stock
  runs low" into `tests/fixtures/runs/load-cell-parts-bin/`: `brief.json`, `ledger.json`, and
  the `check_report.json` and `brief.md` that `check.py` wrote that day.
- Added `page_excerpts.json` instead of copies of the 8 real pages: for each page, only the
  sentence around each ledger quote, copied exactly from `sources.py fetch` output. Each
  excerpt was checked to be an exact piece of the live page text.
- New `tests/test_real_run.py` re-runs `check.py` on the run with the excerpts standing in for
  the web. The new report must match the saved one (13 verified, 11 assumptions,
  0 unverified), and `brief.md` must come out identical.
- Quote S11 keeps the em dash from its source page, since changing it would break the match.
  The em-dash tests now skip quotes copied from sources (a shared `assert_no_em_dashes`
  fixture in `conftest.py`), and CLAUDE.md notes that exception.
- Ticked Phase 4 in CLAUDE.md. 96 tests pass.

Files touched: `tests/fixtures/runs/load-cell-parts-bin/` (5 files), `tests/test_real_run.py`,
`tests/conftest.py`, `tests/test_check.py`, `CLAUDE.md`, `BUILD_LOG.md`

My decisions and what I learned:

I ran the same idea again after the fixes, and this time it picked up a different angle: the dealer software already flags when to reorder, so the bin’s real job might be catching wrong counts. Neither run was wrong, which reminded me that the brief gets me ready for interviews, but the interviews are what actually answer the question. That second run is now a test that re-checks everything without going online, using only a sentence or so from each page instead of copying other companies’ websites into my repo. One quote had an em dash, which breaks my own style rule, but changing it would have made the quote stop matching the page. Copying sources exactly matters more than my formatting preferences, so the quote kept it.

## 2026-10-26: Phase 5, Viewer and /market-copilot:view

What changed:
- New `app.py`, a Streamlit viewer. The sidebar lists the run folders in a folder of briefs
  (newest first). The main pane follows brief.md: summary, riskiest assumptions, interview
  script, competitors, market size, sources. Badges come from check_report.json: green
  Verified, gray Assumption, red Unverified with the reason. It shows the "Verified means"
  line, Check marks for guessing words, Rewrite marks for hypothetical questions, (guess)
  values, the units per customer row, the Price covers line, uncited sources, and each quote
  in an expandable box.
- The sidebar has a number input for each market-size base value. A change recomputes TAM,
  SAM, and SOM through sizing.py, in whole dollars. A changed value gets a blue "Your edit"
  badge (with the old value), is used as an assumption in the math, and is never shown as
  Verified; the counts change to match. "Reset to saved values" undoes edits. Edits last until
  the page is refreshed or another brief is picked; the viewer never writes to a run folder.
- "Download as Markdown" uses render.py, so with no edits it is the same text as brief.md. With
  edits, the new numbers are marked "(your edit)" and "[Your edit: base was ...]", and the
  summary says how many values were changed and that check.py did not check them.
- New `copilot/viewer.py` holds the logic (finding runs, loading them, badges, Markdown
  escaping, edits and recomputing), so app.py is mostly layout and Streamlit stays out of
  copilot/. A run without check_report.json, or with a report that no longer matches
  brief.json or ledger.json, shows a message to run check.py instead of claims without badges.
- render.py: shared text constants and two small helpers (`sizing_cells`, `sizing_note`) so the
  viewer and brief.md say the same things, plus the "Your edit" badge. brief.md output for an
  unedited run is unchanged (the real-run test still matches byte for byte).
- New `skills/view/SKILL.md`. It checks Python, checks Streamlit (and tells the user the
  install command instead of installing it), then starts Streamlit in the background with
  `--server.headless=true` (no first-run email prompt, no browser popup),
  `--server.address=localhost` (only this computer can open it, and no public address
  lookup), `--browser.gatherUsageStats=false`, and `--client.toolbarMode=minimal` (no Deploy
  button). It tells the user the URL and that /tasks stops it. Its commands are pre-approved.
  `.streamlit/config.toml` has the same settings for running from the repo.
- The first live run printed an "External URL", which meant Streamlit had looked up the
  computer's public address online, and it listened on the whole network. Setting
  server.address fixed both. The browser also fetched the page icon from Google's font
  server, so the page uses Streamlit's own icon instead. After both fixes, every request the
  browser made went to localhost.
- The brief skill's last message now says to run /market-copilot:view.
- requirements.txt: `streamlit>=1.66`. requirements-dev.txt includes it, for the AppTest tests.
- Tests: `tests/test_viewer.py` (logic, both saved runs, hand-computed edits),
  `tests/test_app.py` (app.py run with Streamlit's AppTest), and skill checks in
  `tests/test_skeleton.py`. A shared `briefs_folder` fixture checks the Maplewood run against
  the local test server. 131 tests pass.

Files touched: `app.py`, `copilot/viewer.py`, `copilot/render.py`, `skills/view/SKILL.md`,
`skills/brief/SKILL.md`, `.streamlit/config.toml`, `requirements.txt`, `requirements-dev.txt`,
`tests/test_viewer.py`, `tests/test_app.py`, `tests/test_skeleton.py`, `tests/conftest.py`,
`CLAUDE.md`, `BUILD_LOG.md`

Fix, 2026-10-27 (two bugs Josh found testing on his real briefs):
- Reset to saved values removed the Your edit mark, but the sidebar box kept showing the
  edited number. Cause: Reset deleted each box's value from the session. The server then
  used the saved value, but the browser was never told, so it kept showing its own number.
  Fix: each box now starts from a session value (no `value=` argument), and Reset sets that
  value to the saved number, which makes Streamlit send it to the browser.
- The download could have the saved numbers after a change. The page itself did update.
  Cause: a download button's file is made when the page is drawn. Typing a number and then
  clicking Download sends the new number when focus leaves the box, but the click downloads
  the file the browser already has, before the page redraws. In the browser, a click 0 ms
  after leaving the box got the old numbers. A first fix (making the file when clicked)
  failed: 0 ms got the previous number, and clicks 20-100 ms after leaving the box
  downloaded nothing, because the redraw dropped the request. Fix: two steps. "Prepare
  Markdown download" is a normal button, and a normal button's click carries every box's
  current value, so the run it starts has the new number. Only that run shows "Save
  brief.md", and any later change hides it. In the browser, 8 of 8 clicks from 0 to 400 ms
  gave the typed number, in the file and on the page.
- Known limit: if a Save button from an earlier Prepare is still showing, and a number is
  typed and Save clicked within about 0.1 s, the file has the numbers from that Prepare (what
  the page showed then), not the new number. The redraw hides Save within about 0.3 s.
  Streamlit can't change a download button's file once it is in the browser.
- New AppTest tests fail on the old app.py and pass now: Reset puts the saved value back in
  the box (checks the value sent to the browser), and a prepared download has the edited
  numbers and "(your edit)". The download file name is now `<run folder>-brief.md`.

Files touched: `app.py`, `tests/test_app.py`, `skills/view/SKILL.md`, `BUILD_LOG.md`

My decisions and what I learned:

The viewer is where the brief starts to feel like a real product, since you can change a number and watch the market size update. The decision I’d defend first is that an edited number can never show as Verified, because once you change it, it’s your guess and not the source’s. Claude Code also caught that Streamlit was open to anyone on my Wi-Fi and was pulling an icon from Google, so now the viewer only talks to my own computer. What I learned the most from was finding two bugs myself that 131 passing tests missed: Reset cleared the edit mark but left my number in the box, and the download could still have the old numbers. The tests were checking what the server thought, not what the browser actually showed, so passing tests aren’t the same as the thing working for a real person.

## 2026-10-27: Phase 6a, Backtest cases and commands

What changed:
- New `backtest/README.md` with three past products described generically, with no company
  names: an infant vital-signs sock for new parents, a smart sprinkler controller for
  homeowners, and a beehive mite sensor for beekeepers. Each has its exact
  `/market-copilot:brief` command, which names the target customer, the geography (United
  States), and a price guess ($300, $200, and $150 per hive, one-time), so the brief has
  nothing to ask. It also says how to run them in the second terminal and copy the run
  folders into `backtest/runs/`.
- Both backtest files say this is not a blind test: web search can find the real companies,
  and each description matches a real product.
- New `backtest/RESULTS.md` skeleton: one row per case for the top competitors, riskiest
  assumptions, base market size from sizing.py, and check.py counts, plus a blank "What
  actually happened" column for Josh. Rows say "run pending" until the runs are in (Phase 6b).
- New `tests/test_backtest.py`: every run in `backtest/runs/` loads in the viewer with no
  problems, and app.py opened on `backtest/runs` (the folder `/market-copilot:view
  backtest/runs` passes) lists every run and shows each with no warning. The README must have
  exactly three commands that ask nothing. No em dashes in either file. With no runs yet, the
  run tests are skipped. A trial copy of a saved run passed, and an unchecked run failed as it
  should; both copies were removed.
- The view skill already takes a folder argument, so it needed no change.

Files touched: `backtest/README.md`, `backtest/RESULTS.md`, `tests/test_backtest.py`,
`BUILD_LOG.md`

My decisions and what I learned:

