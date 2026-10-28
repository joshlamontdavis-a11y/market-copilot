"""Phase 6 tests: the backtest runs in backtest/runs/ open cleanly in the viewer.

Josh ran each command in backtest/README.md and copied the run folders into backtest/runs/.
RESULTS.md must match those runs: its market sizes come from sizing.py (Rule 3), never typed.
"""

import re
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from copilot import viewer
from copilot.render import whole_money

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


def test_all_three_cases_have_a_run():
    assert len(viewer.find_runs(RUNS)) == 3


def results_row(run_name) -> str:
    """The RESULTS.md table row for one run folder."""
    rows = [line for line in (BACKTEST / "RESULTS.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("| ") and f"`{run_name}`" in line]
    assert len(rows) == 1, f"RESULTS.md needs one row for {run_name}"
    return rows[0]


@pytest.mark.parametrize("run_folder", viewer.find_runs(RUNS), ids=lambda path: path.name)
def test_results_row_matches_the_run(run_folder):
    run = viewer.load_saved_run(run_folder)
    row = results_row(run_folder.name)
    currency = run.brief.get("currency", "USD")
    base = next(s for s in run.report["market_size"]["scenarios"] if s["name"] == "base")
    size = " / ".join(whole_money(base[key], currency) for key in ("tam", "sam", "som"))
    assert f"| {size} |" in row  # the base market size sizing.py computed
    counts = run.report["counts"]
    assert (f"| {counts['verified']} verified, {counts['assumption']} assumptions, "
            f"{counts['unverified']} unverified |") in row
    for competitor in run.brief["competitors"][:3]:
        assert competitor["name"] in row
    for risk in run.brief["riskiest_assumptions"]:
        assert risk["assumption"] in row


@pytest.mark.parametrize("name", ["README.md", "RESULTS.md"])
def test_no_em_dashes(name):
    assert chr(0x2014) not in (BACKTEST / name).read_text(encoding="utf-8")
