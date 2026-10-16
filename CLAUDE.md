# Market Analysis Copilot (Claude Code plugin)

A Claude Code plugin. A user types `/market-copilot:brief "<product idea>"` in Claude Code, and
Claude Code researches the market with web search and saves a sourced market brief: customer
segments, competitors with prices and links, a bottom-up market size, the riskiest assumptions,
and a customer interview script. Everything runs on the user's own computer and Claude plan.
There is no API key, no server, and no paid service.

Owner: Josh Davis, BYU Marriott (Strategic Management). This is a portfolio project for the
BYU Crocker Innovation Fellowship. Reviewers are faculty and student founders. Josh must be able
to explain every part of this code in an interview, so favor simple, readable code with short
comments over clever code.

## Rules (the whole point of the product)

IMPORTANT: these are enforced in code, not only in the skill's instructions.

1. No invented facts. Every competitor, price, and market figure cites source ids from the run's
   source ledger. Each ledger entry has the URL, page title, and an exact quote of 25 words or
   fewer copied from that page.
2. `check.py` decides what is verified, not the model. An item is "Verified" only if every source
   it cites is in the ledger, the page loads, and the quote appears in the page text (after
   normalizing whitespace, case, and curly quotes). Otherwise it is "Unverified", with the reason:
   missing id, page did not load, or quote not found.
3. The model never states a final market size. It proposes assumptions; `sizing.py` does the math
   from assumptions the user can see and edit.
4. The brief prepares founders for customer interviews. It never claims demand is validated.
   Interview questions ask about past behavior, not hypotheticals ("Tell me about the last time..."
   not "Would you buy...").
5. No API keys or paid services anywhere. The brief command needs only Python's standard library;
   Streamlit is used only by the optional viewer.

## Layout

```
.claude-plugin/plugin.json        plugin manifest (name: market-copilot)
.claude-plugin/marketplace.json   lets others install from this GitHub repo
skills/brief/SKILL.md             /market-copilot:brief, the research workflow
skills/brief/brief_schema.md      the brief.json format the skill must write
skills/view/SKILL.md              /market-copilot:view, opens the viewer
copilot/sources.py                fetch a page as plain text; look for a quote (stdlib only)
copilot/check.py                  entry point: validate brief, check sources, size, render
copilot/sizing.py                 TAM, SAM, SOM from explicit assumptions (pure functions)
copilot/render.py                 brief.json + check results -> brief.md
app.py                            Streamlit viewer for saved briefs
tests/                            pytest; fixtures are saved pages and runs, never the live web
samples/                          curated sample briefs for the public demo
backtest/                         past Crocker products described generically
SPEC.md                           Josh's kickoff interview answers (brief order, viewer, first run)
BUILD_LOG.md                      one entry per phase
requirements.txt                  viewer only (streamlit); requirements-dev.txt: pytest
pytest.ini                        test settings (tests/, repo root on the import path)
```

brief.md and the viewer follow the section order in `SPEC.md`: summary, riskiest assumptions,
interview script, competitors, market size.

## How a brief run works

1. The skill clarifies the idea with at most three questions (target customer, geography,
   price guess).
2. It finds candidate sources with WebSearch, then reads each page by running
   `python "${CLAUDE_PLUGIN_ROOT}/copilot/sources.py" fetch <url>` and copies exact quotes from
   that text. If a site blocks the script, it may read the page with WebFetch, but that source
   will usually end up Unverified, and that is acceptable.
3. It writes `ledger.json` (id S1, S2..., url, title, quote, date accessed) and `brief.json`
   per `brief_schema.md`. Every factual field has `source_ids` and
   `status: "sourced" | "assumption"`.
4. It runs `python "${CLAUDE_PLUGIN_ROOT}/copilot/check.py" <run folder>`, which checks every
   source, computes sizing, and writes `check_report.json` and `brief.md`.
5. It reports the counts (verified, assumption, unverified) and where the files are.

Runs are saved in the user's current folder under `market-briefs/<date>-<short-name>/`.
On Windows the command may be `python`; elsewhere `python3`. The skill tries both.

## Stack

- Python 3.11+. `copilot/` uses only the standard library (urllib, html.parser, json,
  dataclasses, pathlib) so users install nothing to make briefs. Send a normal browser
  User-Agent header when fetching pages.
- Viewer: Streamlit, listed in `requirements.txt`. Dev only: pytest.
- Skills: `disable-model-invocation: true` on both (the user triggers them), an `argument-hint`,
  and bundled files referenced with `${CLAUDE_PLUGIN_ROOT}`.
- Josh develops on Windows. Use pathlib; no shell-specific tricks in scripts.
- Read the current docs before writing plugin files:
  plugins https://code.claude.com/docs/en/plugins/create.md
  skills https://code.claude.com/docs/en/skills.md
  publishing https://code.claude.com/docs/en/plugins/publish.md

## Commands

- Run tests: `pytest` (dev setup: `python -m venv .venv`, then
  `.venv\Scripts\python -m pip install -r requirements-dev.txt`)
- Validate the plugin: `claude plugin validate .`
- Try the plugin without installing it: open a second terminal in a scratch folder outside this
  repo, run `claude --plugin-dir <path to this repo>`, then `/market-copilot:brief "..."`.
  After editing plugin files in a running session, run `/reload-plugins`.
- Run the viewer: `streamlit run app.py -- <folder of briefs>`

## Working agreements

- Josh's answers from the kickoff interview are in `SPEC.md`. Read it at the start of every phase.
- Work one phase at a time (below). Plan first, then code, then run the tests and show the output.
- Before every commit, `pytest` and `claude plugin validate .` both pass. Commit at the end of
  each phase with a clear message.
- After each phase, append to `BUILD_LOG.md`: date, phase, what changed, files touched, and a
  blank line "My decisions and what I learned:" for Josh to fill in himself. Do not fill it in.
- When something fails, fix the root cause. Do not silence errors or loosen the rules above.
- Do not commit personal test runs from `market-briefs/`. Copy chosen runs into `samples/` or
  `tests/fixtures/` on purpose.
- Update the checklist below as phases finish.
- Never use em dashes in any file. Use commas, colons, or parentheses instead.

## Build phases

- [x] 1. Skeleton: manifest, marketplace file, stub brief skill, copilot/ package, .gitignore,
        pytest runs, plugin validates
- [x] 2. Sizing engine with tests
- [ ] 3. Source checker with tests on saved pages, including a fake id and a wrong quote
- [ ] 4. Brief skill, brief schema, check.py, brief.md; one real run saved as a test fixture
- [ ] 5. Viewer with badges, editable assumptions, sources, Markdown export, and the view skill
- [ ] 6. Backtest on three past Crocker products
- [ ] 7. README with install steps, sample briefs, public viewer of samples, install test
        from GitHub
