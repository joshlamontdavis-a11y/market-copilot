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

I started out planning a web app that called the Claude API, but I didn’t want to pay for every brief, so I switched to a Claude Code plugin. That change made it free to run and turned it into something a teammate can actually install, which I think makes it more useful than a demo. The decision I’d defend first is keeping unverified sources visible in the brief but never letting them count as evidence in the market size math. Setup taught me more than I expected: half my problems were PATH and being in the wrong folder, so now I check where I am before I run anything.

