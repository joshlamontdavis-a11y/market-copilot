"""Entry point the brief skill runs: python check.py <run folder>.

Reads brief.json and ledger.json from the run folder. Code decides what is verified, not the
model (Rule 2):

    1. Check both files are well formed. If not, print every problem, write nothing, exit 1.
    2. Check every source: the quote is 25 words or fewer, the page loads, the quote is on it.
    3. Label every claim Verified, Assumption, or Unverified (with the reason).
    4. Size the market with sizing.py, treating figures with unverified sources as assumptions.
    5. Write check_report.json and brief.md into the run folder.

The formats are described in skills/brief/brief_schema.md. Standard library only (Rule 5).
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import date
from pathlib import Path

MIN_PYTHON = (3, 11)

# The skill runs this file directly (not as `python -m`), so make the copilot
# package importable by adding the repo root to the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def python_is_new_enough(version_info=sys.version_info) -> bool:
    """True if this Python is at least MIN_PYTHON."""
    return tuple(version_info[:2]) >= MIN_PYTHON


def too_old_message() -> str:
    found = ".".join(str(n) for n in sys.version_info[:3])
    return (
        f"Market Copilot needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer, "
        f"but this is Python {found}. Install a newer Python from "
        "https://www.python.org/downloads/ and try again."
    )


# Check the version before importing the rest of copilot, which may use newer Python features.
if __name__ == "__main__" and not python_is_new_enough():
    print(too_old_message())
    sys.exit(1)

from copilot import render, sizing  # noqa: E402  (imported after the version check on purpose)
from copilot.sources import (  # noqa: E402
    MAX_QUOTE_WORDS,
    FetchError,
    fetch_text,
    quote_in_text,
)

MAX_DOWNLOADS = 8  # pages downloaded at the same time
STATUSES = ("sourced", "assumption")
DEPTHS = ("quick", "deep")
LEDGER_ID = re.compile(r"S[1-9][0-9]*")  # S1, S2, ... S15
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

# Rule 4: interview questions ask about past behavior. These phrases usually mean a question
# asks about a hypothetical instead. A match is a warning, not an error (a false positive must
# not stop a run), and brief.md marks the question so the reader can rewrite it.
HYPOTHETICAL = re.compile(
    r"\b(would you|will you|if we built|if there were|if there was|could you see yourself)\b",
    re.IGNORECASE,
)
HYPOTHETICAL_HINT = (
    'asks about a hypothetical. Ask about past behavior instead, for example '
    '"Tell me about the last time..."'
)


# --- 1. Are the files well formed? -------------------------------------------------------
# Each check_* helper appends a plain-English problem to `problems` instead of stopping, so
# the skill sees every problem at once and can fix them all in one pass.


def check_text(value, where, problems):
    if not isinstance(value, str) or not value.strip():
        problems.append(f"{where}: must be non-empty text")


def check_date(value, where, problems):
    try:
        ok = isinstance(value, str) and ISO_DATE.fullmatch(value) and date.fromisoformat(value)
    except ValueError:  # looks like a date but isn't one, such as 2026-02-30
        ok = False
    if not ok:
        problems.append(f"{where}: must be a date like 2026-10-16, got {value!r}")


def check_list(value, where, problems) -> list:
    """The value if it is a list, otherwise [] (after noting the problem)."""
    if isinstance(value, list):
        return value
    problems.append(f"{where}: must be a list")
    return []


def check_fields(obj, where, keys, problems) -> bool:
    """Check obj is an object whose given keys are all non-empty text. False if not an object."""
    if not isinstance(obj, dict):
        with_keys = " with " + ", ".join(keys) if keys else ""
        problems.append(f"{where}: must be an object{with_keys}")
        return False
    for key in keys:
        check_text(obj.get(key), f"{where}.{key}", problems)
    return True


def check_claim(claim, where, problems):
    """A claim is {"text", "status": "sourced" or "assumption", "source_ids": [...]}."""
    if not check_fields(claim, where, ("text",), problems):
        return
    status = claim.get("status")
    if status not in STATUSES:
        problems.append(f"{where}.status: must be 'sourced' or 'assumption', got {status!r}")
    ids = claim.get("source_ids", [])
    if not isinstance(ids, list) or not all(isinstance(sid, str) for sid in ids):
        problems.append(f"{where}.source_ids: must be a list of source ids like \"S1\"")
    elif status == "sourced" and not ids:
        problems.append(f"{where}: marked sourced but cites no source ids")


def validate_brief(brief) -> list[str]:
    """Every problem with brief.json's structure, or [] if it is well formed."""
    if not isinstance(brief, dict):
        return ["brief.json: must be a JSON object"]
    problems = []
    for key in ("idea", "target_customer", "geography"):
        check_text(brief.get(key), key, problems)
    check_date(brief.get("research_date"), "research_date", problems)
    if brief.get("depth") not in DEPTHS:
        problems.append(f"depth: must be 'quick' or 'deep', got {brief.get('depth')!r}")
    if "currency" in brief:
        check_text(brief["currency"], "currency", problems)

    summary = brief.get("summary")
    if check_fields(summary, "summary", (), problems):
        for i, claim in enumerate(check_list(summary.get("found"), "summary.found", problems)):
            check_claim(claim, f"summary.found.{i}", problems)
        unknowns = check_list(summary.get("unknowns"), "summary.unknowns", problems)
        for i, unknown in enumerate(unknowns):
            check_text(unknown, f"summary.unknowns.{i}", problems)

    risks = check_list(brief.get("riskiest_assumptions"), "riskiest_assumptions", problems)
    for i, risk in enumerate(risks):
        check_fields(risk, f"riskiest_assumptions.{i}",
                     ("assumption", "why_risky", "how_to_test"), problems)

    script = brief.get("interview_script")
    if check_fields(script, "interview_script", ("intro",), problems):
        questions = check_list(script.get("questions"), "interview_script.questions", problems)
        for i, question in enumerate(questions):
            check_fields(question, f"interview_script.questions.{i}",
                         ("question", "listening_for"), problems)

    for i, competitor in enumerate(check_list(brief.get("competitors"), "competitors", problems)):
        where = f"competitors.{i}"
        if check_fields(competitor, where, ("name", "url"), problems):
            check_claim(competitor.get("description"), f"{where}.description", problems)
            check_claim(competitor.get("price"), f"{where}.price", problems)

    market = brief.get("market_size")
    if check_fields(market, "market_size", (), problems):
        try:
            sizing.load_assumptions(market)
        except sizing.SizingError as error:
            problems.append(f"market_size: {error}")
    return problems


def validate_ledger(ledger) -> list[str]:
    """Every problem with ledger.json's structure, or [] if it is well formed."""
    if not isinstance(ledger, list):
        return ["ledger.json: must be a JSON list of sources"]
    problems = []
    seen = set()
    for i, entry in enumerate(ledger):
        where = f"ledger entry {i + 1}"
        if not check_fields(entry, where, ("url", "title", "quote"), problems):
            continue
        sid = entry.get("id")
        if not isinstance(sid, str) or not LEDGER_ID.fullmatch(sid):
            problems.append(f"{where}.id: must look like S1, S2, S3, got {sid!r}")
        elif sid in seen:
            problems.append(f"{where}.id: {sid} is used more than once")
        seen.add(sid)
        check_date(entry.get("accessed"), f"{where}.accessed", problems)
    return problems


def load_json(path: Path):
    """(data, None) if the file loads, or (None, problem) if it is missing or not valid JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"{path.name}: file not found in {path.parent}"
    except json.JSONDecodeError as error:
        return None, f"{path.name}: not valid JSON (line {error.lineno}: {error.msg})"


def load_run(folder: Path):
    """(brief, ledger, problems). The data is only safe to use when problems is empty."""
    brief, brief_problem = load_json(folder / "brief.json")
    ledger, ledger_problem = load_json(folder / "ledger.json")
    problems = [p for p in (brief_problem, ledger_problem) if p]
    if not problems:
        problems = validate_brief(brief) + validate_ledger(ledger)
    return brief, ledger, problems


# --- 2. Check every source ----------------------------------------------------------------


def download(url, fetch):
    """(page text, None) if the page loads, or (None, reason) if it does not."""
    try:
        return fetch(url), None
    except FetchError as error:
        return None, str(error)


def source_problem(quote, page_text, load_error):
    """Why a source fails, or None if it passes. The first problem found is the reason."""
    words = len(quote.split())
    if words > MAX_QUOTE_WORDS:
        return f"quote is {words} words (limit is {MAX_QUOTE_WORDS})"
    if load_error:
        return load_error  # already starts with "page did not load:"
    if not quote_in_text(quote, page_text):
        return "quote not found on the page"
    return None


def check_sources(ledger, fetch=fetch_text) -> dict[str, dict]:
    """Check every ledger entry. Returns {id: entry plus "verified" and "reason"}.

    Each page is downloaded once, even when several sources quote it, and a few pages download
    at the same time so a run doesn't wait on each slow site in turn.
    """
    urls = list(dict.fromkeys(entry["url"] for entry in ledger))  # unique, in ledger order
    with ThreadPoolExecutor(max_workers=MAX_DOWNLOADS) as pool:
        pages = dict(zip(urls, pool.map(lambda url: download(url, fetch), urls)))

    results = {}
    for entry in ledger:
        page_text, load_error = pages[entry["url"]]
        reason = source_problem(entry["quote"], page_text, load_error)
        results[entry["id"]] = {**entry, "verified": reason is None, "reason": reason}
    return results


# --- 3. Label every claim -----------------------------------------------------------------


def find_claims(brief) -> list[tuple[str, str, dict]]:
    """Every claim in the brief as (path, label, claim). The path says where it is in brief.json."""
    claims = []
    for i, claim in enumerate(brief["summary"]["found"]):
        claims.append((f"summary.found.{i}", "Finding", claim))
    for i, competitor in enumerate(brief["competitors"]):
        name = competitor["name"]
        claims.append((f"competitors.{i}.description", f"{name}: description",
                       competitor["description"]))
        claims.append((f"competitors.{i}.price", f"{name}: price", competitor["price"]))
    for name in sizing.ASSUMPTION_NAMES:
        claims.append((f"market_size.{name}", f"Market size: {name}", brief["market_size"][name]))
    return claims


def judge_claim(claim, sources) -> tuple[str, list[str]]:
    """("verified" | "assumption" | "unverified", reasons). Reasons explain an unverified claim."""
    if claim["status"] == "assumption":
        return "assumption", []
    reasons = []
    for sid in claim["source_ids"]:
        source = sources.get(sid)
        if source is None:
            reasons.append(f"{sid}: missing id (not in the ledger)")
        elif not source["verified"]:
            reasons.append(f"{sid}: {source['reason']}")
    return ("unverified", reasons) if reasons else ("verified", [])


def hypothetical_questions(brief) -> list[dict]:
    """Interview questions that seem to ask about a hypothetical (Rule 4), as warnings."""
    warnings = []
    for i, question in enumerate(brief["interview_script"]["questions"]):
        if HYPOTHETICAL.search(question["question"]):
            warnings.append({
                "path": f"interview_script.questions.{i}",
                "question": question["question"],
                "message": HYPOTHETICAL_HINT,
            })
    return warnings


# --- 4 and 5. Size the market and build the report ----------------------------------------


def size_market(market_size, verified_ids) -> dict:
    """Sizing results for the report. "status_used" is the label the math actually used."""
    assumptions = sizing.load_assumptions(market_size)
    used = sizing.mark_unverified_as_assumptions(assumptions, verified_ids)
    return {
        "assumptions": {
            name: {
                "low": a.low, "base": a.base, "high": a.high, "unit": a.unit,
                "status": a.status, "status_used": used[name].status,
                "source_ids": list(a.source_ids),
            }
            for name, a in assumptions.items()
        },
        "scenarios": [asdict(scenario) for scenario in sizing.size_market(used)],
    }


def build_report(brief, ledger, fetch=fetch_text) -> dict:
    """Everything check.py decided about a well-formed run. Becomes check_report.json."""
    sources = check_sources(ledger, fetch=fetch)
    verified_ids = {sid for sid, source in sources.items() if source["verified"]}

    items = {}
    counts = {"verified": 0, "assumption": 0, "unverified": 0}
    for path, label, claim in find_claims(brief):
        verdict, reasons = judge_claim(claim, sources)
        items[path] = {"label": label, "verdict": verdict, "reasons": reasons}
        counts[verdict] += 1

    return {
        "checked_on": date.today().isoformat(),
        "research_date": brief["research_date"],
        "counts": counts,
        "sources": sources,
        "items": items,
        "market_size": size_market(brief["market_size"], verified_ids),
        "warnings": hypothetical_questions(brief),
    }


def main(argv=None) -> int:
    if not python_is_new_enough():
        print(too_old_message())
        return 1

    from copilot import __version__

    parser = argparse.ArgumentParser(description="Check a market brief run folder.")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("run_folder", nargs="?", help="folder with brief.json and ledger.json")
    args = parser.parse_args(argv)

    if args.version:
        python = ".".join(str(n) for n in sys.version_info[:3])
        print(f"market-copilot {__version__}, Python {python}")
        return 0
    if not args.run_folder:
        parser.error("give the run folder, for example: python check.py market-briefs/my-run")

    # The Windows console can't print every character by default, so print UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    folder = Path(args.run_folder)
    brief, ledger, problems = load_run(folder)
    if problems:
        print("check.py could not check this run. Fix these problems and run it again:",
              file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    pages = len({entry["url"] for entry in ledger})
    print(f"Checking {len(ledger)} sources on {pages} pages...")
    report = build_report(brief, ledger)

    report_path = folder / "check_report.json"
    brief_path = folder / "brief.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    brief_path.write_text(render.render_brief(brief, report), encoding="utf-8")

    counts = report["counts"]
    print(f"Verified: {counts['verified']}, assumptions: {counts['assumption']}, "
          f"unverified: {counts['unverified']}")
    for warning in report["warnings"]:
        print(f"Warning: interview question {warning['question']!r} {warning['message']}")
    print(f"Wrote {brief_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
