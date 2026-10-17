# SPEC: Josh's kickoff interview answers (2026-10-16)

## The brief
- Order: (1) one-page summary: what we found, what we still don't know, and counts of
  verified / assumption / unverified items; (2) riskiest assumptions; (3) interview script;
  (4) competitors; (5) market size.
- Depth: user chooses. Quick is the default (about 3-5 competitors, ~10 sources).
  `--deep` flag (about 5-8 competitors, ~15 sources): `/market-copilot:brief "idea" --deep`.
- Unverified items stay in the brief with a badge and the reason. sizing.py never uses an
  unverified figure as a sourced input; it is treated as an assumption instead.
- Every brief shows its research date and a note that prices and competitors change.
- Quotes over 25 words are marked Unverified by check.py (enforced in code).

## Market size
- Bottom-up: customers x units per customer x price x purchases per year -> TAM; reachable
  share -> SAM; winnable share in ~3 years -> SOM. Each step is a visible assumption.
  (units per customer added 2026-10-16 after the first real run, for products sold per bin,
  seat, or location.)
- Every sizing value is one number copied from one source quote, or one guess. The model never
  works a value out from other numbers. A sourced value needs its base number in the cited
  quote; a low or high not in the quote is shown as a guess.
- The brief says what the price covers (for example, the monthly fee but not a one-time
  hardware cost).
- brief.md shows market sizes in whole dollars; check_report.json keeps the exact numbers.
- Each assumption has low, base, and high values. Three scenarios: all low, all base, all high.

## Viewer
- Clean report: sidebar lists saved briefs; main pane reads like a document in the brief order
  above, with colored badges (Verified / Assumption / Unverified) and expandable source quotes.
- Market size: base values are number inputs that recompute TAM/SAM/SOM live; low and high are
  shown alongside.
- Edits are session-only (lost on refresh); Markdown export captures the edited numbers.
  Saved files are never changed by the viewer.

## First run for another person
- Ask clarifying questions only when target customer, geography, or price is genuinely missing
  (max three).
- Short progress lines per step (e.g. "Checking 12 sources...").
- Friendly Python check: try `python` then `python3`, require 3.11+, plain-English install hint
  if neither works.
- Finish with counts, file locations, "run /market-copilot:view to open it", and a nudge to
  interview real customers this week.

## Privacy note (README and skill)
Your idea is processed by Claude through your own Claude account, under Anthropic's terms, and
parts of it appear in web search queries. The plugin sends nothing to Josh or to any server of
his, and briefs are saved only on your computer.

## Reviewers and repo
- Reviewers judge by: public demo viewer of samples, reading the code on GitHub, and a live demo
  in the interview (so runs must be reliable and reasonably fast).
- Branch `main`. Repo private while building; made public with an MIT license in Phase 7,
  before the application is submitted.
