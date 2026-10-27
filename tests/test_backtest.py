"""Phase 6 tests: the backtest runs in backtest/runs/ open cleanly in the viewer.

Josh runs each command in backtest/README.md and copies the run folders into backtest/runs/.
Until a run is copied in, the tests that need runs have nothing to check.
"""

import re
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from copilot import viewer

ROOT = Path(__file__).resolve().parent.parent
BACKTEST = ROOT / "backtest"
RUNS = BACKTEST / "runs"
APP = ROOT / "app.py"
BRIEF_COMMAND = re.compile(r'^/market-copilot:brief "([^"]+)"$', re.MULTILINE)


@pytest.mark.parametrize("run_folder", viewer.find_runs(RUNS), ids=lambda path: path.name)
def test_run_loads_with_no_problems(run_folder):
    run = viewer.load_saved_run(run_folder)
    assert run.problems == []


def test_viewer_shows_every_run(monkeypatch):
    runs = [path.name for path in viewer.find_runs(RUNS)]
    if not runs:
        pytest.skip("no backtest runs copied into backtest/runs/ yet")
    # The same folder argument /market-copilot:view backtest/runs passes to app.py.
    monkeypatch.setattr(sys, "argv", [str(APP), str(RUNS)])
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.run()
    assert app.sidebar.radio[0].options == runs
    for name in runs:
        app.sidebar.radio[0].set_value(name).run()
        assert not app.exception, (name, app.exception)
        assert not app.warning, (name, [w.value for w in app.warning])
        assert "1. Summary" in [header.value for header in app.main.header], name


def test_readme_has_three_commands_that_ask_nothing():
    # The brief asks only when the target customer, geography, or price is missing.
    text = (BACKTEST / "README.md").read_text(encoding="utf-8")
    ideas = BRIEF_COMMAND.findall(text)
    assert len(ideas) == 3
    for idea in ideas:
        for part in ("Target customer:", "Geography: United States.", "Price guess: $"):
            assert part in idea, (part, idea)
        assert "--deep" not in idea  # all three run at the default quick depth


@pytest.mark.parametrize("name", ["README.md", "RESULTS.md"])
def test_no_em_dashes(name):
    assert chr(0x2014) not in (BACKTEST / name).read_text(encoding="utf-8")
