"""Phase 7 tests: the sample briefs, the public demo viewer, and the links in the READMEs.

The demo (demo/streamlit_app.py) is what Streamlit Community Cloud runs. It must show every
sample, and its settings must not change the local viewer, which stays localhost only.
"""

import re
import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from copilot import viewer

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "2026-10-16-load-cell-parts-bin"
FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "load-cell-parts-bin"
DEMO = ROOT / "demo" / "streamlit_app.py"
# Markdown links to files in this repo: [text](path), not http links or #anchors.
LOCAL_LINK = re.compile(r"\]\((?!https?://|#)([^)\s]+)\)")


def test_sample_loads_with_no_problems():
    assert viewer.load_saved_run(SAMPLE).problems == []


@pytest.mark.parametrize("name", ["brief.json", "ledger.json", "check_report.json", "brief.md"])
def test_sample_matches_the_test_fixture(name):
    # The same run is a test fixture, so the tests keep checking what the public sees.
    assert (SAMPLE / name).read_bytes() == (FIXTURE / name).read_bytes()


def test_demo_lists_every_sample():
    app = AppTest.from_file(str(DEMO), default_timeout=30)
    app.run()
    assert not app.exception, app.exception
    assert app.sidebar.radio[0].options == [
        "2026-10-28-varroa-hive-sensor",
        "2026-10-27-smart-sprinkler-controller",
        "2026-10-27-infant-sleep-sock",
        "2026-10-16-load-cell-parts-bin",
    ]
    assert not app.warning  # every sample shows, none needs check.py again
    assert "Sample briefs made with Market Copilot" in app.sidebar.caption[0].value


def test_local_viewer_stays_on_localhost():
    local = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert local["server"]["address"] == "localhost"
    assert local["browser"]["gatherUsageStats"] is False
    demo = tomllib.loads((ROOT / "demo" / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert demo["server"]["address"] == "0.0.0.0"


@pytest.mark.parametrize("readme", ["README.md", "samples/README.md"])
def test_readme_links_point_to_real_files(readme):
    path = ROOT / readme
    links = LOCAL_LINK.findall(path.read_text(encoding="utf-8"))
    assert links
    missing = [link for link in links if not (path.parent / link).exists()]
    assert missing == []
