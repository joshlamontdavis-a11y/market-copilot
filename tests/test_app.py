"""Phase 5 tests: app.py, the Streamlit viewer, run with Streamlit's AppTest.

AppTest runs the script without a browser or a server. app.py reads the folder of briefs from
the command line, so each test sets sys.argv the way `streamlit run app.py -- <folder>` would.
"""

import sys
from pathlib import Path

import pytest
from streamlit.runtime.media_file_manager import MediaFileManager
from streamlit.testing.v1 import AppTest, app_test

APP = Path(__file__).resolve().parent.parent / "app.py"
RUNS = Path(__file__).resolve().parent / "fixtures" / "runs"


def open_app(monkeypatch, folder) -> AppTest:
    monkeypatch.setattr(sys, "argv", [str(APP), str(folder)])
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.run()
    assert not app.exception, app.exception
    return app


def page_text(app) -> str:
    """All the text on the page, main pane and sidebar, as Markdown."""
    parts = []
    for kind in ("title", "header", "subheader", "markdown", "caption", "info", "warning"):
        parts += [element.value for element in getattr(app, kind)]
    return "\n".join(parts)


def pick(app, name):
    app.sidebar.radio[0].set_value(name).run()
    assert not app.exception, app.exception


def base_row(app) -> str:
    table = next(m.value for m in app.markdown if m.value.startswith("| Scenario |"))
    return next(line for line in table.splitlines() if line.startswith("| Base |"))


@pytest.fixture
def file_stores(monkeypatch):
    """Every run's download file store, in order. AppTest makes a new one for each run."""
    stores = []

    class RecordedStore(MediaFileManager):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            stores.append(self)

    monkeypatch.setattr(app_test, "MediaFileManager", RecordedStore)
    return stores


def downloaded_text(button, files) -> str:
    """What the browser saves when this download button (Save brief.md) is clicked.

    A button with fixed data points at a file made when the page was drawn. A button with
    deferred data asks the server to make the file when it is clicked.
    """
    if button.proto.deferred_file_id:
        url = files.execute_deferred(button.proto.deferred_file_id)
    else:
        url = button.proto.url
    file_id = url.rsplit("/", 1)[1]
    return files._storage.get_file(file_id).content.decode("utf-8")  # test-only peek


def test_lists_runs_newest_first(monkeypatch, briefs_folder):
    app = open_app(monkeypatch, briefs_folder)
    assert app.sidebar.radio[0].options == ["maplewood", "load-cell-parts-bin"]


def test_real_run_shows_everything_brief_md_shows(monkeypatch, briefs_folder):
    app = open_app(monkeypatch, briefs_folder)
    pick(app, "load-cell-parts-bin")
    text = page_text(app)
    headers = [header.value for header in app.main.header]
    assert headers == ["1. Summary", "2. Riskiest assumptions", "3. Interview script",
                       "4. Competitors", "5. Market size", "Sources"]
    assert "Verified means the quoted text is on the cited page" in text
    assert "Prices and competitors change" in text
    assert "It does not show that anyone will buy." in text
    assert ":green-badge[13 verified]" in text
    assert ":gray-badge[11 assumptions]" in text
    assert ":red-badge[0 unverified]" in text
    assert "| Units per customer |" in text
    assert "12,000 (guess)" in text
    assert "Price covers:" in text
    assert "| Base | \\$16,991,000 | \\$5,097,300 | \\$254,865 |" in text
    assert len(app.expander) == 13  # one expandable quote per source


def test_maplewood_shows_failures_and_warnings(monkeypatch, briefs_folder):
    app = open_app(monkeypatch, briefs_folder)
    text = page_text(app)  # maplewood is the first run, so it is already open
    assert ":red-badge[Unverified] :red[(S4: quote not found on the page)]" in text
    assert "S999: missing id (not in the ledger)" in text
    assert "quote is 35 words (limit is 25)" in text
    assert "page did not load" in text
    assert ":orange-badge[Rewrite: this asks about a hypothetical." in text
    assert ":orange-badge[Check: guessing word in a sourced claim." in text
    assert ":orange-badge[Not cited by any claim.]" in text
    assert "(guess)" in text
    assert "Used as an assumption in the math." in text
    assert "1 interview question needs rewriting" in text


def test_editing_a_base_value_recomputes_and_marks_the_edit(monkeypatch, briefs_folder):
    app = open_app(monkeypatch, briefs_folder)
    pick(app, "load-cell-parts-bin")
    app.number_input(key="load-cell-parts-bin:customers").set_value(20000).run()
    assert not app.exception
    assert base_row(app) == "| Base | \\$20,000,000 | \\$6,000,000 | \\$300,000 |"
    text = page_text(app)
    assert ":blue-badge[Your edit] :blue[(base was 16,991)]" in text
    assert "20,000 (your edit)" in text
    assert ":green-badge[12 verified]" in text
    assert ":blue-badge[1 changed by you]" in text
    assert "Outside the low to high range." in text
    assert len(app.sidebar.button) == 1  # Reset to saved values

    app.sidebar.button[0].click().run()
    assert base_row(app) == "| Base | \\$16,991,000 | \\$5,097,300 | \\$254,865 |"
    assert "Your edit" not in page_text(app)


def test_reset_puts_the_saved_value_back_in_the_box(monkeypatch, briefs_folder):
    app = open_app(monkeypatch, briefs_folder)
    pick(app, "load-cell-parts-bin")
    app.number_input(key="load-cell-parts-bin:customers").set_value(20000).run()
    app.sidebar.button[0].click().run()

    box = app.number_input(key="load-cell-parts-bin:customers")
    assert box.value == 16991
    # The browser keeps showing the number it already has unless the server sends a new one
    # (set_value). Bug: Reset cleared the edit on the server, but the box still showed 20000.
    assert box.proto.set_value
    assert box.proto.value == 16991
    assert "Your edit" not in page_text(app)
    assert not app.sidebar.button  # no Reset button when nothing is edited


def test_download_has_the_edited_numbers(monkeypatch, briefs_folder, file_stores):
    app = open_app(monkeypatch, briefs_folder)
    pick(app, "load-cell-parts-bin")
    # Bug: a download button drawn before an edit kept the saved numbers, and a click that
    # left the number box downloaded them before the page redrew. So no download button may
    # be on the page until the user asks for one.
    assert not app.get("download_button")

    # Typing a number and clicking Prepare reach the server in one message (a button's click
    # carries every box's value), so the file made in that run has the new number.
    app.number_input(key="load-cell-parts-bin:customers").set_value(20000)
    app.button(key="prepare_download").click().run()
    text = downloaded_text(app.get("download_button")[0], file_stores[-1])
    assert "Checked by check.py: 12 verified, 11 assumptions, 0 unverified." in text
    assert "1 market-size value was changed in the viewer" in text
    assert "| Customers | 12,000 (guess) | 20,000 (your edit) |" in text
    assert "**[Your edit: base was 16,991]**" in text
    assert "| Base | $20,000,000 | $6,000,000 | $300,000 |" in text
    assert base_row(app) == "| Base | \$20,000,000 | \$6,000,000 | \$300,000 |"

    # Any later change hides the Save button, so it can't hand out numbers that are gone.
    app.number_input(key="load-cell-parts-bin:customers").set_value(21000).run()
    assert not app.get("download_button")


def test_download_without_edits_matches_brief_md(monkeypatch, briefs_folder, file_stores):
    app = open_app(monkeypatch, briefs_folder)
    pick(app, "load-cell-parts-bin")
    app.button(key="prepare_download").click().run()
    text = downloaded_text(app.get("download_button")[0], file_stores[-1])
    saved = (briefs_folder / "load-cell-parts-bin" / "brief.md").read_text(encoding="utf-8")
    assert text == saved


def test_share_is_edited_as_a_percent(monkeypatch, briefs_folder):
    app = open_app(monkeypatch, briefs_folder)
    pick(app, "load-cell-parts-bin")
    assert app.number_input(key="load-cell-parts-bin:som_share").value == 5
    app.number_input(key="load-cell-parts-bin:som_share").set_value(10).run()
    assert base_row(app) == "| Base | \\$16,991,000 | \\$5,097,300 | \\$509,730 |"


def test_unchecked_run_shows_how_to_check_it(monkeypatch):
    app = open_app(monkeypatch, RUNS)  # the saved Maplewood folder has no check_report.json
    assert "check.py has not checked this run yet" in app.warning[0].value
    assert not app.main.header  # no brief sections without badges


def test_page_downloads_nothing_from_other_sites():
    # A Material page icon would make the browser fetch it from fonts.gstatic.com.
    assert "page_icon" not in APP.read_text(encoding="utf-8").split("set_page_config")[1].split(")")[0]


def test_empty_folder_says_how_to_make_a_brief(monkeypatch, tmp_path):
    app = open_app(monkeypatch, tmp_path / "market-briefs")
    assert "/market-copilot:brief" in app.info[0].value
