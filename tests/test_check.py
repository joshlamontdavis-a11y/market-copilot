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
    S999                   cited by the brief, not in the ledger     -> missing id

Market size by hand (price cites S4, so it is used as an assumption; the numbers don't change):

            customers  price  months  TAM          sam   SAM          som   SOM
    low     10,000     $29    12      $3,480,000   0.20  $696,000     0.05  $34,800
    base    20,000     $50    12      $12,000,000  0.25  $3,000,000   0.10  $300,000
    high    40,000     $79    12      $37,920,000  0.50  $18,960,000  0.20  $3,792,000
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from copilot.check import check_sources, main, validate_brief, validate_ledger

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
    for sid in ("S1", "S2", "S3", "S7"):
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
    # pricing.html and census.html are each quoted by two sources.
    paths = local_server.handler.requested_paths
    assert paths.count("/pricing.html") == 1
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
    assert items["summary.found.1"]["reasons"] == ["S6: quote is 35 words (limit is 25)"]
    assert items["market_size.price"]["reasons"] == ["S4: quote not found on the page"]


def test_counts(checked):
    assert checked[0]["counts"] == {"verified": 4, "assumption": 4, "unverified": 4}


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
        pytest.approx((37_920_000, 18_960_000, 3_792_000))


# --- Rule 4 warning -------------------------------------------------------------------


def test_hypothetical_question_is_flagged(checked):
    warnings = checked[0]["warnings"]
    # Only "Would you switch...". "Tell me about the last time..." is fine.
    assert [w["path"] for w in warnings] == ["interview_script.questions.2"]


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
    assert "4 verified, 4 assumptions, 4 unverified" in brief_md
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


def test_schema_doc_examples_are_valid():
    doc = (ROOT / "skills" / "brief" / "brief_schema.md").read_text(encoding="utf-8")
    ledger_block, brief_block = re.findall(r"```json\n(.*?)```", doc, flags=re.DOTALL)
    assert validate_ledger(json.loads(ledger_block)) == []
    assert validate_brief(json.loads(brief_block)) == []


def test_command_line(run_folder):
    result = subprocess.run(
        [sys.executable, str(ROOT / "copilot" / "check.py"), str(run_folder)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert "Checking 7 sources on 5 pages..." in result.stdout
    assert "Verified: 4, assumptions: 4, unverified: 4" in result.stdout
    assert "Warning: interview question" in result.stdout
    assert (run_folder / "brief.md").exists()
