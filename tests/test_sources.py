"""Phase 3 tests: reading pages and finding quotes in them.

The pages are small hand-made HTML files in tests/fixtures/pages/ about a made-up company.
Fetch tests use a server on this computer (see conftest.py), never the live web.
"""

import socket
import subprocess
import sys
from pathlib import Path

import pytest

from copilot.sources import (
    BROWSER_USER_AGENT,
    FetchError,
    fetch_text,
    html_to_text,
    quote_in_text,
)

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "tests" / "fixtures" / "pages"


def page_text(name):
    """Readable text of one fixture page, read from disk."""
    return html_to_text((PAGES / name).read_text(encoding="utf-8"))


# --- Finding quotes ---

def test_quote_on_the_page_is_found():
    assert quote_in_text("Starter: $29 per month for one location", page_text("pricing.html"))


def test_quote_not_on_the_page_is_not_found():
    text = page_text("pricing.html")
    assert not quote_in_text("Free forever for every clinic", text)
    # One changed word (the price) is enough to fail.
    assert not quote_in_text("Starter: $19 per month for one location", text)


def test_quote_split_across_link_and_bold_tags_is_found():
    quote = "Maplewood is online booking for dental and physical therapy clinics."
    assert quote_in_text(quote, page_text("pricing.html"))


def test_curly_quotes_extra_spaces_and_case_are_ignored():
    # Page has curly quotes, extra spaces, and a line break; the quote has none of them.
    quote = '"We stopped losing appointments the week we switched," said the office manager'
    assert quote_in_text(quote, page_text("testimonials.html"))
    assert quote_in_text("WE STOPPED LOSING APPOINTMENTS", page_text("testimonials.html"))
    assert quote_in_text("It's the only tool our front desk didn't complain about.",
                         page_text("testimonials.html"))
    # The reverse: page has straight quotes, the quote has curly ones and extra spaces.
    assert quote_in_text("“no  contracts,   cancel anytime.”", page_text("about.html"))


def test_invisible_characters_are_ignored():
    # The page hides a soft hyphen in "afternoon" and a zero-width space in "training".
    assert quote_in_text("Setup took one afternoon and no training.", page_text("testimonials.html"))


def test_empty_quote_never_matches():
    assert not quote_in_text("", page_text("pricing.html"))
    assert not quote_in_text("   ", page_text("pricing.html"))


# --- Turning HTML into readable text ---

def test_scripts_and_styles_are_not_page_text():
    text = page_text("pricing.html")
    assert "Secret plan" not in text
    assert "$999" not in text
    assert "savings calculator" not in text  # inside <noscript>
    assert not quote_in_text("Secret plan costs $1 per month", text)


def test_entities_are_decoded_and_blocks_are_separate_lines():
    lines = page_text("pricing.html").splitlines()
    assert "Booking & reminders included. No setup fee." in lines
    assert "Starter: $29 per month for one location" in lines
    assert "Simple pricing for small clinics" in lines


# --- Fetching pages (from the local test server) ---

def test_fetch_returns_readable_text_and_sends_browser_user_agent(local_server):
    text = fetch_text(local_server.url + "/pricing.html")
    assert "Simple pricing for small clinics" in text
    assert "Secret plan" not in text
    assert local_server.handler.last_user_agent == BROWSER_USER_AGENT


def test_missing_page_raises_fetch_error(local_server):
    with pytest.raises(FetchError, match="page did not load: HTTP 404"):
        fetch_text(local_server.url + "/missing")


def test_slow_page_times_out(local_server):
    with pytest.raises(FetchError, match="timed out"):
        fetch_text(local_server.url + "/slow", timeout=0.3)


def test_nothing_listening_raises_fetch_error():
    # Grab a free port, then close it, so nothing is listening there.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with pytest.raises(FetchError, match="page did not load"):
        fetch_text(f"http://127.0.0.1:{port}/pricing.html", timeout=2)


def test_only_web_links_are_read():
    pricing_file = (PAGES / "pricing.html").as_uri()  # a file:// link to a local file
    with pytest.raises(FetchError, match="only http and https"):
        fetch_text(pricing_file)


def test_live_web_is_blocked_in_tests():
    # 203.0.113.1 is a reserved documentation address, so nothing real is ever contacted.
    with socket.socket() as sock, pytest.raises(RuntimeError, match="live web"):
        sock.connect(("203.0.113.1", 80))


# --- Command line ---

def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "copilot" / "sources.py"), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_cli_fetch_prints_page_text(local_server):
    result = run_cli("fetch", local_server.url + "/testimonials.html")
    assert result.returncode == 0
    assert "What clinics say" in result.stdout
    assert "It’s the only tool our front desk" in result.stdout


def test_cli_fetch_failure_exits_with_reason(local_server):
    result = run_cli("fetch", local_server.url + "/missing")
    assert result.returncode == 1
    assert "page did not load: HTTP 404" in result.stderr
    assert result.stdout == ""
