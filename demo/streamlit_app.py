"""The public demo viewer, for Streamlit Community Cloud.

Community Cloud can't pass a folder on the command line, so this file names the folders
itself: the sample brief in samples/ and the three backtest runs in backtest/runs/. It reuses
app.py unchanged. The .streamlit/config.toml next to this file replaces the localhost-only
setting, which would stop Cloud from serving the page; the local viewer keeps it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so app.py and the copilot package import from the repo root

import app  # noqa: E402

REPO = "https://github.com/joshlamontdavis-a11y/market-copilot"

app.main(
    [ROOT / "samples", ROOT / "backtest" / "runs"],
    note=f"Sample briefs made with Market Copilot. Edits here last until you refresh. "
         f"To make your own, install the plugin: {REPO}",
)
