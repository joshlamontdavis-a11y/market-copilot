"""Phase 4a tests: check.py checks a run folder and render.py writes brief.md.

The run folder in tests/fixtures/runs/maplewood/ is hand-made and describes a made-up company.
Its ledger points at the local test server (see conftest.py), never the live web:

    S1  pricing.html       real quote                                -> Verified
    S2  about.html         real quote                                -> Verified
    S3  testimonials.html  real quote                                -> Verified
    S4  pricing.html       Team price with one word changed ($89)    -> quote not found
    S5  missing.html       page does not exist                       -> page did not load
    S6  census.html        real quote, but 35 words                  -> quote too long
    S7  census.html        real quote                                -> Verified
    S8  about.html         real quote, but no claim cites it         -> Verified, uncited warning
    S999                   cited by the brief, not in the ledger     -> missing id

Customers cites S7, whose quote says 20,000: base is found, so low and high are guesses.
summary.found.0 is sourced but says "likely", so it gets a guessing-word warning.

Market size by hand (price cites S4, so it is used as an assumption; the numbers don't change):

            customers  units  price  months  TAM          sam   SAM          som   SOM
    low     10,000     1      $29    12      $3,480,000   0.20  $696,000     0.05  $34,800
    base    20,000     1      $50    12      $12,000,000  0.25  $3,000,000   0.10  $300,000
    high    40,000     2      $79    12      $75,840,000  0.50  $37,920,000  0.20  $7,584,000
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from copilot.check import (
    build_report,
    check_sources,
    main,
    numbers_in,
    percents_in,
    validate_brief,
    validate_ledger,
)
from copilot.render import whole_money

ROOT = Path(__file__).resolve().parent.parent
MAPLEWOOD = ROOT / "tests" / "fixtures" / "runs" / "maplewood"


@pytest.fixture
def run_folder(local_server, tmp_path):
    """A copy of the Maplewood run, with its links pointing at the local test server."""
    folder = tmp_path / "maplewood"
    folder.mkdir()
    for name in ("brief.json", "ledger.json"):
        text = (MAPLEWOOD / name).read_text(encoding="utf-8")
        (folder / name).write_text(text.replace("http://LOCAL_SERVER", local_server.url),
                                   encoding="utf-8")
    return folder


@pytest.fixture
def checked(run_folder, local_server):
    """Run check.py on the Maplewood run. Returns (report, brief.md text)."""
    local_server.handler.requested_paths.clear()
    assert main([str(run_folder)]) == 0
    report = json.loads((run_folder / "check_report.json").read_text(encoding="utf-8"))
    return report, (run_folder / "brief.md").read_text(encoding="utf-8")


# --- Sources --------------------------------------------------------------------------


def test_real_quotes_are_verified(checked):
    report, _ = checked
    for sid in ("S1", "S2", "S3", "S7", "S8"):
        assert report["sources"][sid]["verified"], sid
        assert report["sources"][sid]["reason"] is None


def test_one_changed_word_is_not_found(checked):
    report, _ = checked
    assert report["sources"]["S4"]["reason"] == "quote not found on the page"


def test_page_that_does_not_load(checked):
    report, _ = checked
    assert report["sources"]["S5"]["reason"].startswith("page did not load: HTTP 404")


def test_quote_over_25_words(checked):
    report, _ = checked
    assert report["sources"]["S6"]["reason"] == "quote is 35 words (limit is 25)"


def test_each_page_is_downloaded_once(checked, local_server):
    # pricing.html, about.html, and census.html are each quoted by two sources.
    paths = local_server.handler.requested_paths
    assert paths.count("/pricing.html") == 1
    assert paths.count("/about.html") == 1
    assert paths.count("/census.html") == 1


def test_25_words_pass_and_26_fail():
    page = " ".join(f"w{i}" for i in range(30))  # a fake page of 30 words

    def ledger_entry(sid, words):
        return {"id": sid, "url": "https://example.com", "title": "t",
                "quote": " ".join(f"w{i}" for i in range(words)), "accessed": "2026-10-16"}

    results = check_sources([ledger_entry("S1", 25), ledger_entry("S2", 26)],
                            fetch=lambda url: page)
    assert results["S1"]["verified"]
    assert results["S2"]["reason"] == "quote is 26 words (limit is 25)"


# --- Claims ---------------------------------------------------------------------------


def test_claim_labels_and_reasons(checked):
    items = checked[0]["items"]
    assert items["competitors.0.price"] == {
        "label": "Maplewood Booking: price", "verdict": "verified", "reasons": []}
    assert items["competitors.1.description"]["reasons"] == ["S999: missing id (not in the ledger)"]
    assert items["competitors.1.price"]["verdict"] == "assumption"
    assert items["summary.found.1"]["verdict"] == "assumption"
    assert items["summary.found.2"]["reasons"] == ["S6: quote is 35 words (limit is 25)"]
    assert items["market_size.price"]["reasons"] == ["S4: quote not found on the page"]


def test_counts(checked):
    assert checked[0]["counts"] == {"verified": 4, "assumption": 6, "unverified": 4}


# --- Market size ----------------------------------------------------------------------


def test_unverified_figure_is_used_as_an_assumption(checked):
    assumptions = checked[0]["market_size"]["assumptions"]
    assert assumptions["price"]["status"] == "sourced"
    assert assumptions["price"]["status_used"] == "assumption"
    assert assumptions["customers"]["status_used"] == "sourced"  # S7 is verified


def test_scenarios_match_hand_math(checked):
    scenarios = {s["name"]: s for s in checked[0]["market_size"]["scenarios"]}
    assert (scenarios["low"]["tam"], scenarios["low"]["sam"], scenarios["low"]["som"]) == \
        pytest.approx((3_480_000, 696_000, 34_800))
    assert (scenarios["base"]["tam"], scenarios["base"]["sam"], scenarios["base"]["som"]) == \
        pytest.approx((12_000_000, 3_000_000, 300_000))
    assert (scenarios["high"]["tam"], scenarios["high"]["sam"], scenarios["high"]["som"]) == \
        pytest.approx((75_840_000, 37_920_000, 7_584_000))


def test_low_and_high_not_in_the_quote_are_guesses(checked):
    customers = checked[0]["market_size"]["assumptions"]["customers"]
    assert customers["guessed_values"] == ["low", "high"]  # S7 says 20,000, the base value
    assert customers["status_used"] == "sourced"
    assert checked[0]["items"]["market_size.customers"]["verdict"] == "verified"


def report_with_customers(brief, ledger, **values):
    """check.py's report after changing the customers values, using the real fixture pages."""
    brief["market_size"]["customers"].update(values)
    return build_report(brief, ledger)


@pytest.fixture
def run_data(run_folder):
    def load(name):
        return json.loads((run_folder / name).read_text(encoding="utf-8"))
    return load("brief.json"), load("ledger.json")


def test_base_value_must_be_in_the_quote(run_data):
    # Low 20,000 is in S7's quote, but base 25,000 is not, and base drives the main numbers.
    report = report_with_customers(*run_data, low=20000, base=25000)
    assert report["items"]["market_size.customers"] == {
        "label": "Market size: customers", "verdict": "unverified",
        "reasons": ["base value 25,000 is not in the cited quotes"]}
    assert report["market_size"]["assumptions"]["customers"]["status_used"] == "assumption"


def test_worked_out_numbers_are_unverified(run_data):
    # Like a row the model multiplied out itself: none of these numbers is in the quote.
    report = report_with_customers(*run_data, low=800, base=3100, high=6100)
    assert report["items"]["market_size.customers"]["reasons"] == [
        "none of its numbers appears in the cited quotes"]
    assert report["counts"]["unverified"] == 5


@pytest.mark.parametrize("text, expected", [
    ("The census counted 20,000 clinics.", [20_000]),
    ("Starter: $4.99 per month.", [4.99]),
    ("About 1.2 million small businesses", [1_200_000]),
    ("Founded in 2012 with 120 staff", [2012, 120]),  # never read as 12
    ("25% of clinics", []),  # a percentage is not a plain number
])
def test_numbers_in(text, expected):
    assert numbers_in(text) == pytest.approx(expected)


@pytest.mark.parametrize("text, expected", [
    ("25% of clinics", [0.25]),
    ("12 percent of offices", [0.12]),
    ("billed for 12 months", []),  # a 12% share can't match "12 months"
])
def test_percents_in(text, expected):
    assert percents_in(text) == pytest.approx(expected)


@pytest.mark.parametrize("quote, verdict", [
    ("Plans are billed for 12 months.", "unverified"),
    ("12% of clinics switched last year.", "verified"),
])
def test_share_matches_only_a_percentage(quote, verdict):
    page = "Plans are billed for 12 months. 12% of clinics switched last year."
    ledger = [{"id": "S1", "url": "https://example.com", "title": "t", "quote": quote,
               "accessed": "2026-10-16"}]
    brief = schema_examples()[1]
    brief["market_size"]["sam_share"].update(low=0.12, base=0.12, high=0.12,
                                             status="sourced", source_ids=["S1"])
    report = build_report(brief, ledger, fetch=lambda url: page)
    assert report["items"]["market_size.sam_share"]["verdict"] == verdict


# --- Warnings -------------------------------------------------------------------------


def test_hypothetical_question_is_flagged(checked):
    warnings = checked[0]["warnings"]["hypothetical_questions"]
    # Only "Would you switch...". "Tell me about the last time..." is fine.
    assert [w["path"] for w in warnings] == ["interview_script.questions.2"]


def test_guessing_word_in_a_sourced_claim_is_flagged(checked):
    warnings = checked[0]["warnings"]["guessing_words"]
    # found.0 is sourced and says "likely". found.1 says "may" but is an assumption, so it's fine.
    assert [w["path"] for w in warnings] == ["summary.found.0"]


def test_uncited_source_is_flagged(checked):
    report, brief_md = checked
    assert [w["id"] for w in report["warnings"]["uncited_sources"]] == ["S8"]
    assert "Not cited by any claim." in source_row(brief_md, "S8")
    assert "Not cited" not in source_row(brief_md, "S7")


# --- brief.md -------------------------------------------------------------------------


def test_brief_md_sections_in_spec_order(checked):
    _, brief_md = checked
    headings = re.findall(r"^## (.+)$", brief_md, flags=re.MULTILINE)
    assert headings == ["1. Summary", "2. Riskiest assumptions", "3. Interview script",
                        "4. Competitors", "5. Market size", "Sources"]


def test_brief_md_shows_date_price_note_and_counts(checked):
    _, brief_md = checked
    assert "Research date: 2026-10-16." in brief_md
    assert "Prices and competitors change" in brief_md
    assert "4 verified, 6 assumptions, 4 unverified" in brief_md
    assert "It does not show that anyone will buy." in brief_md


def test_brief_md_shows_badges_and_reasons(checked):
    _, brief_md = checked
    assert "**[Verified]** $29 per month for one location. (S1)" in brief_md
    assert "**[Unverified: S999: missing id (not in the ledger)]**" in brief_md
    assert "Used as an assumption in the math." in brief_md
    assert "| Base | $12,000,000 | $3,000,000 | $300,000 |" in brief_md


def test_brief_md_marks_the_hypothetical_question(checked):
    _, brief_md = checked
    flagged = [line for line in brief_md.splitlines() if "[Rewrite:" in line]
    assert len(flagged) == 1
    assert "Would you switch to a new booking tool" in flagged[0]
    assert "1 interview question needs rewriting (see section 3)." in brief_md


def test_brief_md_marks_the_guessing_claim(checked):
    _, brief_md = checked
    flagged = [line for line in brief_md.splitlines() if "[Check: guessing word" in line]
    assert len(flagged) == 1
    assert "missed appointments likely drop" in flagged[0]
    assert "1 sourced claim uses a guessing word" in brief_md


def test_brief_md_shows_guessed_values_and_price_covers(checked):
    _, brief_md = checked
    row = next(line for line in brief_md.splitlines() if line.startswith("| Customers |"))
    assert row.startswith("| Customers | 10,000 (guess) | 20,000 | 40,000 (guess) |")
    assert "Low and high are guesses, not from the source." in row
    assert "| Units per customer | 1 | 1 | 2 |" in brief_md
    assert "Price covers: The monthly subscription only. There is no one-time fee." in brief_md
    assert "TAM = customers x units per customer x price x purchases per year." in brief_md


def test_market_size_is_in_whole_dollars(checked):
    _, brief_md = checked
    assert "| High | $75,840,000 | $37,920,000 | $7,584,000 |" in brief_md
    assert whole_money(395_040.75, "USD") == "$395,041"
    assert whole_money(1_234.4, "EUR") == "1,234 EUR"


def test_whole_dollars_only_in_brief_md(run_folder):
    # A low share of 0.1234 gives SOM = 3,480,000 x 0.1234 x 0.05 = $21,471.60.
    edit_json(run_folder / "brief.json",
              lambda b: b["market_size"]["sam_share"].update(low=0.1234))
    assert main([str(run_folder)]) == 0
    report = json.loads((run_folder / "check_report.json").read_text(encoding="utf-8"))
    assert report["market_size"]["scenarios"][0]["som"] == pytest.approx(21_471.6)  # exact
    brief_md = (run_folder / "brief.md").read_text(encoding="utf-8")
    assert "| Low | $3,480,000 | $429,432 | $21,472 |" in brief_md  # whole dollars


def test_brief_md_explains_what_verified_means_before_the_summary(checked):
    _, brief_md = checked
    line = ("Verified means the quoted text is on the cited page. "
            "Read each quote to judge whether it supports the claim.")
    assert line in brief_md
    assert brief_md.index(line) < brief_md.index("## 1. Summary")


def source_row(brief_md, sid):
    return next(row for row in brief_md.splitlines() if row.startswith(f"| {sid} |"))


def test_long_quote_shows_only_first_25_words(checked):
    report, brief_md = checked
    full_quote = report["sources"]["S6"]["quote"]
    first_25 = " ".join(full_quote.split()[:25])  # ends "...said that missed appointments"
    row = source_row(brief_md, "S6")
    assert f'"{first_25}..."' in row
    assert "cost them" not in row  # word 26 onward is left out
    assert "quote is 35 words (limit is 25)" in row
    # check_report.json still keeps the whole quote.
    assert len(full_quote.split()) == 35


def test_short_quotes_are_shown_in_full(checked):
    _, brief_md = checked
    assert '"Starter: $29 per month for one location" |' in source_row(brief_md, "S1")
    assert "..." not in source_row(brief_md, "S7")


def test_brief_md_has_no_em_dashes(checked):
    assert chr(0x2014) not in checked[1]  # the em dash character


# --- Bad input: list every problem, write nothing -------------------------------------


def edit_json(path, change):
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize("file_name, change, expected", [
    ("brief.json", lambda b: b.pop("competitors"), "competitors: must be a list"),
    ("brief.json", lambda b: b["summary"]["found"][0].update(source_ids=[]),
     "summary.found.0: marked sourced but cites no source ids"),
    ("brief.json", lambda b: b["competitors"][0]["price"].update(status="verified"),
     "competitors.0.price.status: must be 'sourced' or 'assumption'"),
    ("brief.json", lambda b: b.update(research_date="last Tuesday"), "research_date"),
    ("brief.json", lambda b: b["market_size"].pop("price"), "Missing assumptions: price"),
    ("brief.json", lambda b: b["market_size"].pop("price_covers"),
     "market_size.price_covers: must be non-empty text"),
    ("ledger.json", lambda l: l[1].update(id="S1"), "S1 is used more than once"),
])
def test_bad_input_is_explained_and_nothing_is_written(run_folder, capsys,
                                                       file_name, change, expected):
    edit_json(run_folder / file_name, change)
    assert main([str(run_folder)]) == 1
    assert expected in capsys.readouterr().err
    assert not (run_folder / "brief.md").exists()
    assert not (run_folder / "check_report.json").exists()


def test_broken_json_is_explained(run_folder, capsys):
    (run_folder / "ledger.json").write_text('[{"id": "S1",', encoding="utf-8")
    assert main([str(run_folder)]) == 1
    assert "ledger.json: not valid JSON" in capsys.readouterr().err


def test_every_problem_is_listed_at_once(run_folder, capsys):
    edit_json(run_folder / "brief.json", lambda b: b.update(depth="medium", geography=""))
    assert main([str(run_folder)]) == 1
    err = capsys.readouterr().err
    assert "depth: must be 'quick' or 'deep'" in err
    assert "geography: must be non-empty text" in err


# --- The schema doc and the command line ----------------------------------------------


def schema_examples():
    """(ledger, brief) from the example in the brief skill's Format section."""
    doc = (ROOT / "skills" / "brief" / "SKILL.md").read_text(encoding="utf-8")
    ledger_block, brief_block = re.findall(r"```json\n(.*?)```", doc, flags=re.DOTALL)
    return json.loads(ledger_block), json.loads(brief_block)


def test_schema_doc_examples_are_valid():
    ledger, brief = schema_examples()
    assert validate_ledger(ledger) == []
    assert validate_brief(brief) == []


def test_schema_doc_example_checks_as_described():
    # The skill says the example's customers is Verified with low and high shown as guesses.
    ledger, brief = schema_examples()
    page = " ".join(entry["quote"] for entry in ledger)  # a fake page with both quotes on it
    report = build_report(brief, ledger, fetch=lambda url: page)
    assert report["items"]["market_size.customers"]["verdict"] == "verified"
    assert report["market_size"]["assumptions"]["customers"]["guessed_values"] == ["low", "high"]
    assert report["warnings"] == {
        "hypothetical_questions": [], "guessing_words": [], "uncited_sources": []}


def test_command_line(run_folder):
    result = subprocess.run(
        [sys.executable, str(ROOT / "copilot" / "check.py"), str(run_folder)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert "Checking 8 sources on 5 pages..." in result.stdout
    assert "Verified: 4, assumptions: 6, unverified: 4" in result.stdout
    assert "Warning: interview question" in result.stdout
    assert "Warning: sourced claim 'Clinic staff say" in result.stdout
    assert "Warning: source S8 is in the ledger but no claim cites it." in result.stdout
    assert (run_folder / "brief.md").exists()
