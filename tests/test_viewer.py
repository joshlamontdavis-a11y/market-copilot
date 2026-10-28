"""Phase 5 tests: the viewer's logic in copilot/viewer.py (no Streamlit needed).

Uses the two saved runs: the real load-cell run (13 verified, 11 assumptions, 0 unverified)
and the hand-made Maplewood run, checked against the local test server by briefs_folder.

Market size by hand for the edits below:

    load-cell, customers base 16,991 -> 20,000 (units 50, price $80, purchases 0.25):
        TAM 20,000 x 50 x 80 x 0.25 = $20,000,000   SAM x 0.30 = $6,000,000   SOM x 0.05 = $300,000
    Maplewood, customers base 20,000 -> 30,000 (units 1, price $50, 12 months):
        TAM 30,000 x 1 x 50 x 12 = $18,000,000      SAM x 0.25 = $4,500,000   SOM x 0.10 = $450,000
"""

import copy
import json
import shutil
from pathlib import Path

import pytest

from copilot import viewer
from copilot.render import whole_money

RUNS = Path(__file__).resolve().parent / "fixtures" / "runs"
REAL_RUN = RUNS / "load-cell-parts-bin"


@pytest.fixture
def real_run():
    run = viewer.load_saved_run(REAL_RUN)
    assert run.problems == []
    return run


def base_scenario(report):
    return next(s for s in report["market_size"]["scenarios"] if s["name"] == "base")


# --- Loading runs -------------------------------------------------------------------------


def test_find_runs_lists_run_folders_newest_first(tmp_path):
    for name in ("2026-10-01-old", "2026-10-20-new", "notes"):
        (tmp_path / name).mkdir()
    for name in ("2026-10-01-old", "2026-10-20-new"):
        (tmp_path / name / "brief.json").write_text("{}", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("not a run", encoding="utf-8")
    assert [path.name for path in viewer.find_runs(tmp_path)] == ["2026-10-20-new",
                                                                  "2026-10-01-old"]


def test_find_runs_on_a_missing_folder_is_empty(tmp_path):
    assert viewer.find_runs(tmp_path / "market-briefs") == []


def test_find_runs_on_the_saved_runs():
    assert [path.name for path in viewer.find_runs(RUNS)] == ["maplewood", "load-cell-parts-bin"]


def test_real_run_loads_with_its_saved_report(real_run):
    assert real_run.report["counts"] == {"verified": 13, "assumption": 11, "unverified": 0}


def test_unchecked_run_is_not_shown():
    # The saved Maplewood folder has no check_report.json, so there are no badges to show.
    run = viewer.load_saved_run(RUNS / "maplewood")
    assert run.report is None
    assert len(run.problems) == 1
    assert "check.py has not checked this run yet" in run.problems[0]


def test_checked_maplewood_loads(briefs_folder):
    run = viewer.load_saved_run(briefs_folder / "maplewood")
    assert run.problems == []
    assert run.report["counts"]["unverified"] > 0


def copy_real_run(tmp_path):
    folder = tmp_path / "run"
    shutil.copytree(REAL_RUN, folder)
    return folder


def edit_json(path, change):
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize("file_name, change, expected", [
    ("brief.json", lambda b: b["market_size"]["customers"].update(base=15000), "customers values"),
    ("brief.json", lambda b: b["competitors"].pop(), "claims"),
    ("ledger.json", lambda l: l[0].update(quote="A different quote"), "sources"),
])
def test_report_older_than_the_files_is_not_shown(tmp_path, file_name, change, expected):
    folder = copy_real_run(tmp_path)
    edit_json(folder / file_name, change)
    run = viewer.load_saved_run(folder)
    assert len(run.problems) == 1
    assert "check_report.json is out of date" in run.problems[0]
    assert expected in run.problems[0]


def test_broken_brief_lists_its_problems(tmp_path):
    folder = copy_real_run(tmp_path)
    edit_json(folder / "brief.json", lambda b: b.pop("idea"))
    run = viewer.load_saved_run(folder)
    assert run.report is None
    assert any("idea" in problem for problem in run.problems)


def test_broken_report_is_explained(tmp_path):
    folder = copy_real_run(tmp_path)
    (folder / "check_report.json").write_text("{not json", encoding="utf-8")
    run = viewer.load_saved_run(folder)
    assert "not valid JSON" in run.problems[0]


# --- Badges and Markdown ------------------------------------------------------------------


def test_badges_and_colors():
    assert viewer.badge({"verdict": "verified", "reasons": []}) == ("Verified", "green", "")
    assert viewer.badge({"verdict": "assumption", "reasons": []}) == ("Assumption", "gray", "")
    assert viewer.badge({"verdict": "unverified", "reasons": ["S4: quote not found on the page"]}
                        ) == ("Unverified", "red", "S4: quote not found on the page")
    assert viewer.badge({"verdict": "edited", "reasons": ["base was 16,991"]}
                        ) == ("Your edit", "blue", "base was 16,991")


def test_source_badges():
    assert viewer.source_badge({"verified": True, "reason": None}) == ("Verified", "green", "")
    assert viewer.source_badge({"verified": False, "reason": "quote not found on the page"}
                               ) == ("Unverified", "red", "quote not found on the page")


def test_markdown_escapes_dollars_and_formatting():
    # "$29 ... $79" would otherwise turn into a math formula in Streamlit.
    assert viewer.md("$29 to $79") == "\\$29 to \\$79"
    assert viewer.md("*bold* [link] a|b") == "\\*bold\\* \\[link\\] a\\|b"


def test_link_keeps_the_address_whole():
    assert viewer.link("Pricing [new]", "https://x.com/a (b)") == (
        "[Pricing \\[new\\]](https://x.com/a%20%28b%29)")


# --- Editing ------------------------------------------------------------------------------


def test_shares_are_shown_as_percents():
    assert viewer.to_input("sam_share", 0.3) == 30
    assert viewer.to_input("som_share", 0.07) == 7  # not 7.000000000000001
    assert viewer.from_input("sam_share", 30) == 0.3
    assert viewer.to_input("customers", 16991) == 16991
    assert viewer.from_input("price", 80) == 80


def saved_inputs(report):
    return {name: viewer.to_input(name, a["base"])
            for name, a in report["market_size"]["assumptions"].items()}


def test_saved_values_are_not_edits(real_run):
    assert viewer.find_edits(real_run.report, saved_inputs(real_run.report)) == {}


def test_changed_value_is_an_edit(real_run):
    inputs = saved_inputs(real_run.report) | {"customers": 20000, "som_share": 10}
    assert viewer.find_edits(real_run.report, inputs) == {"customers": 20000, "som_share": 0.1}


def test_no_edits_download_matches_brief_md(real_run):
    text = viewer.brief_markdown(real_run.brief, real_run.report, {})
    assert text == (REAL_RUN / "brief.md").read_text(encoding="utf-8")


def test_edit_recomputes_sizing(real_run):
    report = viewer.apply_edits(real_run.brief, real_run.report, {"customers": 20000})
    base = base_scenario(report)
    assert (base["tam"], base["sam"], base["som"]) == pytest.approx((20_000_000, 6_000_000, 300_000))
    # Low and high keep their saved values.
    saved = real_run.report["market_size"]["scenarios"]
    assert report["market_size"]["scenarios"][0] == saved[0]
    assert report["market_size"]["scenarios"][2] == saved[2]


def test_edited_value_is_never_verified(real_run):
    report = viewer.apply_edits(real_run.brief, real_run.report, {"customers": 20000})
    item = report["items"]["market_size.customers"]
    assert item["verdict"] == "edited"
    # 20,000 is above the high value (16,991), so the badge says so.
    assert viewer.badge(item) == ("Your edit", "blue",
                                  "base was 16,991; outside the low to high range")
    customers = report["market_size"]["assumptions"]["customers"]
    assert customers["status_used"] == "assumption"
    assert customers["edited_from"] == 16991
    assert report["counts"] == {"verified": 12, "assumption": 11, "unverified": 0, "edited": 1}


def test_edits_do_not_change_the_saved_report(real_run):
    before = copy.deepcopy(real_run.report)
    viewer.apply_edits(real_run.brief, real_run.report, {"customers": 20000, "price": 99})
    assert real_run.report == before


def test_edited_download_shows_new_numbers_marked_as_edits(real_run, assert_no_em_dashes):
    text = viewer.brief_markdown(real_run.brief, real_run.report, {"customers": 20000})
    row = next(line for line in text.splitlines() if line.startswith("| Customers |"))
    assert "20,000 (your edit)" in row
    assert "**[Your edit: base was 16,991; outside the low to high range]**" in row
    assert "[Verified]" not in row
    assert "| Base | $20,000,000 | $6,000,000 | $300,000 |" in text
    assert "1 market-size value was changed in the viewer" in text
    assert "Checked by check.py: 12 verified, 11 assumptions, 0 unverified." in text
    assert_no_em_dashes(text, real_run.ledger)


def test_edit_on_maplewood_in_whole_dollars(briefs_folder):
    run = viewer.load_saved_run(briefs_folder / "maplewood")
    report = viewer.apply_edits(run.brief, run.report, {"customers": 30000})
    base = base_scenario(report)
    assert [whole_money(base[key], "USD") for key in ("tam", "sam", "som")] == [
        "$18,000,000", "$4,500,000", "$450,000"]


def test_out_of_range():
    assumption = {"low": 12000, "base": 16991, "high": 16991}
    assert viewer.out_of_range(assumption, 20000)
    assert viewer.out_of_range(assumption, 100)
    assert not viewer.out_of_range(assumption, 15000)


def test_edit_inside_the_range_has_no_range_note(real_run):
    report = viewer.apply_edits(real_run.brief, real_run.report, {"customers": 15000})
    assert report["items"]["market_size.customers"]["reasons"] == ["base was 16,991"]
    text = viewer.brief_markdown(real_run.brief, real_run.report, {"customers": 15000})
    assert "**[Your edit: base was 16,991]**" in text
    assert "outside the low to high range" not in text


def test_edit_below_the_low_says_so_in_the_download(real_run):
    text = viewer.brief_markdown(real_run.brief, real_run.report, {"customers": 100})
    row = next(line for line in text.splitlines() if line.startswith("| Customers |"))
    assert "**[Your edit: base was 16,991; outside the low to high range]**" in row


def test_edited_note_says_it_or_them(real_run):
    one = viewer.brief_markdown(real_run.brief, real_run.report, {"customers": 15000})
    assert "1 market-size value was changed in the viewer (marked Your edit). " \
           "check.py did not check it." in one
    two = viewer.brief_markdown(real_run.brief, real_run.report,
                                {"customers": 15000, "price": 99})
    assert "2 market-size values were changed in the viewer (marked Your edit). " \
           "check.py did not check them." in two
