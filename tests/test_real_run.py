"""Phase 4 test: re-check a real brief run without touching the live web.

tests/fixtures/runs/load-cell-parts-bin/ is Josh's run of
/market-copilot:brief "A load-cell parts bin that weighs its contents and alerts when stock runs low"
from 2026-10-16. brief.json and ledger.json are the skill's output; check_report.json and
brief.md are what check.py wrote that day.

Instead of downloading the pages, the test reads page_excerpts.json: for each page, only the
sentences around its ledger quotes, copied exactly from `sources.py fetch` output. If check.py
or render.py changes how this run is judged or written, these tests show the difference.
"""

import json
from pathlib import Path

import pytest

from copilot.check import build_report, validate_brief, validate_ledger
from copilot.render import render_brief
from copilot.sources import FetchError

RUN = Path(__file__).resolve().parent / "fixtures" / "runs" / "load-cell-parts-bin"


def load(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def fetch_excerpt(url):
    """Stands in for sources.fetch_text: the saved excerpt of the page, one sentence a line."""
    pages = load("page_excerpts.json")["pages"]
    if url not in pages:
        raise FetchError(f"page did not load: no saved excerpt for {url}")
    return "\n".join(pages[url])


@pytest.fixture(scope="module")
def run():
    """(brief, ledger, a fresh report from check.py, the report saved on the day of the run)."""
    brief, ledger = load("brief.json"), load("ledger.json")
    return brief, ledger, build_report(brief, ledger, fetch=fetch_excerpt), load("check_report.json")


def test_files_are_well_formed(run):
    brief, ledger, _, _ = run
    assert validate_brief(brief) == []
    assert validate_ledger(ledger) == []


def test_every_page_has_an_excerpt(run):
    _, ledger, _, _ = run
    pages = load("page_excerpts.json")["pages"]
    assert set(pages) == {entry["url"] for entry in ledger}


def test_recheck_matches_the_saved_report(run):
    _, _, report, saved = run
    # checked_on is the day check.py ran, so it is the one field that may differ.
    for key in ("counts", "sources", "items", "market_size", "warnings"):
        assert report[key] == saved[key], key
    assert report["counts"] == {"verified": 13, "assumption": 11, "unverified": 0}


def test_brief_md_matches_the_saved_brief_md(run):
    brief, _, report, _ = run
    assert render_brief(brief, report) == (RUN / "brief.md").read_text(encoding="utf-8")


def test_customers_low_is_marked_as_a_guess(run):
    # S1 says 16,991 dealers: that is the base and high value; the low value 12,000 is a guess.
    customers = run[2]["market_size"]["assumptions"]["customers"]
    assert customers["guessed_values"] == ["low"]
    assert customers["status_used"] == "sourced"


def test_quote_with_an_em_dash_is_kept_exactly(run):
    # S11 was copied from a page that uses em dashes. Changing it would break the match.
    _, ledger, report, _ = run
    s11 = next(entry for entry in ledger if entry["id"] == "S11")
    assert chr(0x2014) in s11["quote"]
    assert report["sources"]["S11"]["verified"]


def test_brief_md_has_no_em_dashes_outside_quotes(run, assert_no_em_dashes):
    _, ledger, _, _ = run
    assert_no_em_dashes((RUN / "brief.md").read_text(encoding="utf-8"), ledger)
