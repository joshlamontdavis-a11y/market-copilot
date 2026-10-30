# Sample briefs

Four real runs of `/market-copilot:brief`, saved as the plugin wrote them. Each brief.md is the
readable brief; brief.json, ledger.json, and check_report.json are the files the viewer reads.

| Brief | Research date | Where it lives |
|---|---|---|
| [Load-cell parts bin that alerts when stock runs low](2026-10-16-load-cell-parts-bin/brief.md) | 2026-10-16 | here (the first real run; a copy of it is also a test fixture) |
| [Infant vital-signs sock](../backtest/runs/2026-10-27-infant-sleep-sock/brief.md) | 2026-10-27 | backtest |
| [Smart sprinkler controller](../backtest/runs/2026-10-27-smart-sprinkler-controller/brief.md) | 2026-10-27 | backtest |
| [In-hive varroa mite sensor](../backtest/runs/2026-10-28-varroa-hive-sensor/brief.md) | 2026-10-28 | backtest |

The three backtest briefs stay in [backtest/runs](../backtest/runs) rather than being copied
here. [backtest/RESULTS.md](../backtest/RESULTS.md) compares what each one found with what
really happened. **The backtest is not a blind test:** web search can find the real companies,
so a brief may find the very company it describes.

Prices and competitors change, so each brief is only as current as its research date.

See all four in the viewer online, with nothing to install, at
[market-copilot.streamlit.app](https://market-copilot.streamlit.app). That demo is hosted by
Streamlit Community Cloud, which collects its own usage statistics under Streamlit's terms.

Or open them in the viewer from a copy of this repo:

```
streamlit run app.py -- samples backtest/runs
```
