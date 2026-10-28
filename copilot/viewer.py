"""The viewer's logic, kept out of app.py so pytest can test it without Streamlit.

    find_runs(folder)            the run folders in a folder of briefs, newest first
    load_saved_run(run folder)   brief.json, ledger.json, and check_report.json, or the problems
    badge(item)                  the label and color the viewer shows for a check result
    find_edits(report, inputs)   which base values the user changed in the sidebar
    apply_edits(...)             a copy of the report with those values and new TAM, SAM, SOM

Badges always come from check_report.json, never from brief.json (Rule 2). A value the user
changes is marked "Your edit" and is never shown as Verified. Nothing here writes a file, so
the viewer never changes a saved run. Standard library only (Rule 5).
"""

import copy
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from copilot import check, render, sizing

REPORT_PARTS = ("counts", "sources", "items", "market_size", "warnings")
# Characters Markdown (or Streamlit's LaTeX, for "$") would treat as formatting.
MARKDOWN_SPECIALS = set("\\`*_[]<>#~|$")
OUT_OF_RANGE = "outside the low to high range"


# --- Loading saved runs -------------------------------------------------------------------


def find_runs(folder) -> list[Path]:
    """Subfolders that hold a brief.json, newest first (run folder names start with the date)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    runs = [path for path in folder.iterdir() if (path / "brief.json").is_file()]
    return sorted(runs, key=lambda path: path.name, reverse=True)


@dataclass
class SavedRun:
    folder: Path
    brief: dict | None
    ledger: list | None
    report: dict | None
    problems: list[str]  # if not empty, the viewer shows these instead of the brief


def not_checked_message(folder) -> str:
    return (
        "check.py has not checked this run yet, so nothing in it has a badge. Check it with: "
        f'python "<plugin folder>/copilot/check.py" "{folder}"'
    )


def report_problems(brief, ledger, report) -> list[str]:
    """Why check_report.json doesn't describe this brief.json and ledger.json, or [].

    The badges come from the report, so a report from before the files were changed would show
    the wrong badges. Any difference means check.py has to run again.
    """
    if not isinstance(report, dict) or any(part not in report for part in REPORT_PARTS):
        return ["check_report.json is missing parts. Run check.py on this run again."]
    problems = []
    if set(report["items"]) != {path for path, _, _ in check.find_claims(brief)}:
        problems.append("its claims don't match brief.json")
    sources = report["sources"]
    if list(sources) != [entry["id"] for entry in ledger] or any(
        sources[entry["id"]]["url"] != entry["url"]
        or sources[entry["id"]]["quote"] != entry["quote"]
        for entry in ledger
    ):
        problems.append("its sources don't match ledger.json")
    saved = report["market_size"].get("assumptions", {})
    for name in sizing.ASSUMPTION_NAMES:
        if name not in saved or any(saved[name][s] != brief["market_size"][name][s]
                                    for s in sizing.SCENARIOS):
            problems.append(f"its {name} values don't match brief.json")
    if problems:
        return ["check_report.json is out of date (" + "; ".join(problems) + "). "
                "Run check.py on this run again."]
    return []


def load_saved_run(folder) -> SavedRun:
    """Load one run folder. The run is safe to show only when problems is empty."""
    folder = Path(folder)
    brief, ledger, problems = check.load_run(folder)  # also checks both files are well formed
    if problems:
        return SavedRun(folder, None, None, None, problems)
    if not (folder / "check_report.json").is_file():
        return SavedRun(folder, brief, ledger, None, [not_checked_message(folder)])
    report, problem = check.load_json(folder / "check_report.json")
    if problem:
        return SavedRun(folder, brief, ledger, None, [problem])
    return SavedRun(folder, brief, ledger, report, report_problems(brief, ledger, report))


# --- Showing check results ----------------------------------------------------------------


def badge(item) -> tuple[str, str, str]:
    """(label, color, detail) for a claim's check result. detail is the reason, or ""."""
    verdict = item["verdict"]
    reasons = "; ".join(item["reasons"])
    if verdict == "verified":
        return "Verified", "green", ""
    if verdict == "assumption":
        return "Assumption", "gray", ""
    if verdict == "edited":
        return "Your edit", "blue", reasons
    return "Unverified", "red", reasons


def source_badge(source) -> tuple[str, str, str]:
    """(label, color, detail) for one ledger source, as check.py judged it."""
    if source["verified"]:
        return "Verified", "green", ""
    return "Unverified", "red", source["reason"]


def md(text) -> str:
    """Text that Streamlit's Markdown shows exactly as written. "$29" would otherwise be math."""
    return "".join("\\" + ch if ch in MARKDOWN_SPECIALS else ch for ch in str(text))


def link(text, url) -> str:
    """A Markdown link whose text and address can't break the Markdown around them."""
    safe_url = url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
    return f"[{md(text)}]({safe_url})"


# --- Editing market-size inputs -----------------------------------------------------------


def to_input(name, value) -> float:
    """A saved value as the sidebar shows it. Shares are shown as percents: 0.25 -> 25."""
    if name in sizing.SHARE_NAMES:
        return round(value * 100, 10)  # round away float noise such as 7.000000000000001
    return float(value)


def from_input(name, value) -> float:
    """A sidebar value back as the math uses it: 25 -> 0.25 for shares."""
    return value / 100 if name in sizing.SHARE_NAMES else value


def find_edits(report, inputs) -> dict[str, float]:
    """{name: new base} for each sidebar value that differs from the saved base value."""
    saved = report["market_size"]["assumptions"]
    edits = {}
    for name, shown in inputs.items():
        value = from_input(name, shown)
        if not math.isclose(value, saved[name]["base"]):
            edits[name] = value
    return edits


def out_of_range(assumption, value) -> bool:
    """True if a new base value is below the low value or above the high value."""
    return not assumption["low"] <= value <= assumption["high"]


def apply_edits(brief, report, edits) -> dict:
    """A copy of the report with the user's base values, marked as edits, and new sizes.

    An edited value is the user's own guess, so it is labeled "edited" (never Verified) and is
    used as an assumption in the math. sizing.py recomputes all three scenarios. The report
    passed in is not changed, and with no edits it comes back as it was.
    """
    if not edits:
        return report
    report = copy.deepcopy(report)
    currency = brief.get("currency", "USD")
    assumptions = report["market_size"]["assumptions"]
    for name, value in edits.items():
        saved = assumptions[name]
        reasons = ["base was " + render.sizing_value(name, saved["base"], currency)]
        if out_of_range(saved, value):  # said in the download too, not only in the sidebar
            reasons.append(OUT_OF_RANGE)
        saved.update(
            edited_from=saved["base"],
            base=value,
            status_used="assumption",
            guessed_values=[s for s in saved["guessed_values"] if s != "base"],
        )
        report["items"][f"market_size.{name}"].update(verdict="edited", reasons=reasons)

    counts = {"verified": 0, "assumption": 0, "unverified": 0, "edited": 0}
    for item in report["items"].values():
        counts[item["verdict"]] += 1
    report["counts"] = counts

    used = {
        name: sizing.Assumption(name=name, low=a["low"], base=a["base"], high=a["high"],
                                unit=a["unit"], status=a["status_used"],
                                source_ids=tuple(a["source_ids"]))
        for name, a in assumptions.items()
    }
    report["market_size"]["scenarios"] = [asdict(s) for s in sizing.size_market(used)]
    return report


def brief_markdown(brief, report, edits) -> str:
    """brief.md as render.py writes it, with the user's edits if there are any."""
    return render.render_brief(brief, apply_edits(brief, report, edits))
