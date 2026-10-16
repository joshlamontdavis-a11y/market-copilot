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

