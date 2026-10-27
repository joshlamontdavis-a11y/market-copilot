# Backtest results

What each brief found, next to what really happened. The cases and commands are in
[README.md](README.md).

**This is not a blind test.** Web search can find the real companies, and each description
matches a real product, so a brief may find the very company it describes.

How the columns are filled:

- Top competitors and riskiest assumptions come from each run's brief.json, with the check
  result check.py gave each competitor's price.
- The base market size is copied from each run's check_report.json, where sizing.py computed
  it from the assumptions in the brief. No number here is typed in by the model.
- The check.py counts are verified, assumption, and unverified items.
- "What actually happened" is filled in by hand from public sources.

| Case | Run folder | Top competitors found | Riskiest assumptions | Base market size (TAM / SAM / SOM, from sizing.py) | check.py counts | What actually happened |
|---|---|---|---|---|---|---|
| 1. Infant vital-signs sock | run pending | run pending | run pending | run pending | run pending | |
| 2. Smart sprinkler controller | run pending | run pending | run pending | run pending | run pending | |
| 3. Beehive mite sensor | run pending | run pending | run pending | run pending | run pending | |
