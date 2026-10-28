"""Turn brief.json and check.py's report into brief.md, a document people can read.

Sections follow SPEC.md: summary, riskiest assumptions, interview script, competitors, market
size, then the sources. Every claim carries the badge check.py decided ([Verified],
[Assumption], or [Unverified: reason]); nothing here decides what is verified. The viewer's
Markdown download uses this module too, and a base value the user changed there shows as
[Your edit: base was ...] (see copilot/viewer.py).

    render_brief(brief, report) -> the Markdown text (this module reads and writes no files)
"""

from copilot.sources import MAX_QUOTE_WORDS

# Market size rows in the order the math uses them, with readable names.
SIZING_ROWS = (
    ("customers", "Customers"),
    ("units_per_customer", "Units per customer"),
    ("price", "Price per purchase"),
    ("purchases_per_year", "Purchases per year"),
    ("sam_share", "Share who could buy (SAM)"),
    ("som_share", "Share we could win in ~3 years (SOM)"),
)
# Marks for the warnings check.py found. The viewer (app.py) shows the same words as badges.
REWRITE_NOTE = "Rewrite: this asks about a hypothetical. Ask about the last time it happened."
GUESSING_NOTE = "Check: guessing word in a sourced claim. Move the guess into an assumption."
REWRITE_MARK = f"**[{REWRITE_NOTE}]**"
GUESSING_MARK = f"**[{GUESSING_NOTE}]**"
CHANGE_NOTE = "Prices and competitors change, so check the links before relying on them."
INTERVIEWS_NOTE = (
    "This brief prepares you for customer interviews. It does not show that anyone will buy."
)
SIZING_MATH = (
    "Computed by sizing.py from the assumptions below, not stated by the model. "
    "TAM = customers x units per customer x price x purchases per year. "
    "SAM = TAM x share who could buy. SOM = SAM x share we could win in about 3 years."
)
SCENARIOS_NOTE = "Low uses every low value, base every base value, high every high value."
# A Verified badge proves the words are on the page, not that they back up the claim.
VERIFIED_MEANS = (
    "Verified means the quoted text is on the cited page. "
    "Read each quote to judge whether it supports the claim."
)


# --- Small formatting helpers ---------------------------------------------------------


def badge(item) -> str:
    if item["verdict"] == "verified":
        return "**[Verified]**"
    if item["verdict"] == "assumption":
        return "**[Assumption]**"
    if item["verdict"] == "edited":  # a base value the user changed in the viewer
        return "**[Your edit: " + "; ".join(item["reasons"]) + "]**"
    return "**[Unverified: " + "; ".join(item["reasons"]) + "]**"


def cite(source_ids) -> str:
    return " (" + ", ".join(source_ids) + ")" if source_ids else ""


def claim_text(claim, item, flagged=False) -> str:
    """A claim with its badge and the source ids it cites. flagged: it uses a guessing word."""
    mark = " " + GUESSING_MARK if flagged else ""
    return f"{badge(item)}{mark} {claim['text']}{cite(claim['source_ids'])}"


def guessing_paths(report) -> set[str]:
    """Where the sourced claims with a guessing word are."""
    return {warning["path"] for warning in report["warnings"]["guessing_words"]}


def number(value) -> str:
    """20000 -> "20,000"; 12.5 -> "12.50"."""
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"


def money(value, currency) -> str:
    return "$" + number(value) if currency == "USD" else f"{number(value)} {currency}"


def whole_money(value, currency) -> str:
    """Market sizes in whole dollars: 395040.75 -> "$395,041". check_report.json keeps cents."""
    amount = f"{value:,.0f}"
    return "$" + amount if currency == "USD" else f"{amount} {currency}"


def sizing_value(name, value, currency) -> str:
    if name in ("sam_share", "som_share"):
        return f"{value * 100:g}%"  # 0.25 -> "25%"
    if name == "price":
        return money(value, currency)
    return number(value)


def guess_note(guessed) -> str:
    """["low", "high"] -> "Low and high are guesses, not from the source."."""
    names = " and ".join(guessed).capitalize()
    verb = "is a guess" if len(guessed) == 1 else "are guesses"
    return f"{names} {verb}, not from the source."


def sizing_cells(name, assumption, currency) -> list[str]:
    """Low, base, and high as the brief shows them, marked (guess) or (your edit)."""
    cells = []
    for s in ("low", "base", "high"):
        value = sizing_value(name, assumption[s], currency)
        if s in assumption["guessed_values"]:
            value += " (guess)"
        elif s == "base" and "edited_from" in assumption:
            value += " (your edit)"
        cells.append(value)
    return cells


def sizing_note(assumption) -> str:
    """The extra words after a market-size row's badge, or "" if there are none."""
    if assumption["status"] != assumption["status_used"]:
        return "Used as an assumption in the math."
    if assumption["guessed_values"]:
        return guess_note(assumption["guessed_values"])
    return ""


def edited_note(count) -> str:
    """The summary line about values the user changed in the viewer."""
    values, it = ("1 market-size value was", "it") if count == 1 else (
        f"{count} market-size values were", "them")
    return f"{values} changed in the viewer (marked Your edit). check.py did not check {it}."


def short_quote(quote) -> str:
    """The quote, or its first 25 words and "..." if it is over the limit."""
    words = quote.split()
    if len(words) <= MAX_QUOTE_WORDS:
        return quote
    return " ".join(words[:MAX_QUOTE_WORDS]) + "..."


def cell(text) -> str:
    """Text that is safe inside a Markdown table cell."""
    return " ".join(str(text).split()).replace("|", "\\|")


# --- Sections -------------------------------------------------------------------------


def header(brief) -> list[str]:
    return [
        f"# Market brief: {brief['idea']}",
        "",
        f"Research date: {brief['research_date']}. {CHANGE_NOTE}",
        "",
        f"Target customer: {brief['target_customer']}. Geography: {brief['geography']}. "
        f"Depth: {brief['depth']}.",
        "",
        INTERVIEWS_NOTE,
        "",
        VERIFIED_MEANS,
        "",
    ]


def summary(brief, report) -> list[str]:
    counts = report["counts"]
    lines = [
        "## 1. Summary",
        "",
        f"Checked by check.py: {counts['verified']} verified, {counts['assumption']} "
        f"assumptions, {counts['unverified']} unverified.",
        "",
    ]
    if counts.get("edited"):
        lines += [edited_note(counts["edited"]), ""]
    flagged = len(report["warnings"]["hypothetical_questions"])
    if flagged:
        needs = "1 interview question needs" if flagged == 1 else f"{flagged} interview questions need"
        lines += [f"{needs} rewriting (see section 3).", ""]
    guessing = guessing_paths(report)
    if guessing:
        uses = "1 sourced claim uses" if len(guessing) == 1 else f"{len(guessing)} sourced claims use"
        lines += [f"{uses} a guessing word (marked Check). Read its quotes before relying on it.",
                  ""]
    lines += ["### What we found", ""]
    for i, claim in enumerate(brief["summary"]["found"]):
        path = f"summary.found.{i}"
        lines.append(f"- {claim_text(claim, report['items'][path], path in guessing)}")
    lines += ["", "### What we still don't know", ""]
    lines += [f"- {unknown}" for unknown in brief["summary"]["unknowns"]]
    return lines + [""]


def riskiest_assumptions(brief) -> list[str]:
    lines = ["## 2. Riskiest assumptions", ""]
    for i, risk in enumerate(brief["riskiest_assumptions"], start=1):
        lines += [
            f"{i}. **{risk['assumption']}**",
            f"   - Why it's risky: {risk['why_risky']}",
            f"   - How to test it: {risk['how_to_test']}",
        ]
    return lines + [""]


def interview_script(brief, report) -> list[str]:
    flagged = {warning["path"] for warning in report["warnings"]["hypothetical_questions"]}
    script = brief["interview_script"]
    lines = ["## 3. Interview script", "", script["intro"], ""]
    for i, question in enumerate(script["questions"]):
        mark = REWRITE_MARK + " " if f"interview_script.questions.{i}" in flagged else ""
        lines += [
            f"{i + 1}. {mark}{question['question']}",
            f"   - Listen for: {question['listening_for']}",
        ]
    return lines + [""]


def competitors(brief, report) -> list[str]:
    guessing = guessing_paths(report)
    lines = ["## 4. Competitors", ""]
    for i, competitor in enumerate(brief["competitors"]):
        parts = {}
        for key in ("description", "price"):
            path = f"competitors.{i}.{key}"
            parts[key] = claim_text(competitor[key], report["items"][path], path in guessing)
        lines += [
            f"### {competitor['name']}",
            "",
            f"Link: {competitor['url']}",
            "",
            f"- What it does: {parts['description']}",
            f"- Price: {parts['price']}",
            "",
        ]
    return lines


def market_size(brief, report) -> list[str]:
    currency = brief.get("currency", "USD")
    sizing = report["market_size"]
    lines = [
        "## 5. Market size",
        "",
        SIZING_MATH,
        "",
        "| Assumption | Low | Base | High | Unit | Check |",
        "|---|---|---|---|---|---|",
    ]
    for name, title in SIZING_ROWS:
        a = sizing["assumptions"][name]
        label = badge(report["items"][f"market_size.{name}"]) + cite(a["source_ids"])
        if sizing_note(a):
            label += " " + sizing_note(a)
        values = sizing_cells(name, a, currency)
        lines.append(f"| {title} | " + " | ".join(values) + f" | {cell(a['unit'])} | {cell(label)} |")

    if any("edited_from" in a for a in sizing["assumptions"].values()):
        lines += ["", "Values marked (your edit) were changed in the viewer, so these sizes "
                  "differ from check_report.json."]
    lines += ["", f"Price covers: {sizing['price_covers']}"]
    lines += ["", "| Scenario | TAM | SAM | SOM |", "|---|---|---|---|"]
    for scenario in sizing["scenarios"]:
        amounts = [whole_money(scenario[key], currency) for key in ("tam", "sam", "som")]
        lines.append(f"| {scenario['name'].capitalize()} | " + " | ".join(amounts) + " |")
    return lines + ["", SCENARIOS_NOTE, ""]


def sources(report) -> list[str]:
    lines = [
        "## Sources",
        "",
        "| Id | Source | Quote | Accessed | Check |",
        "|---|---|---|---|---|",
    ]
    uncited = {warning["id"] for warning in report["warnings"]["uncited_sources"]}
    for sid, source in report["sources"].items():
        check = "Verified" if source["verified"] else f"Unverified: {source['reason']}"
        if sid in uncited:
            check += ". Not cited by any claim."
        lines.append(
            f"| {sid} | [{cell(source['title'])}]({source['url']}) | \"{cell(short_quote(source['quote']))}\" "
            f"| {source['accessed']} | {cell(check)} |"
        )
    return lines + [""]


def render_brief(brief, report) -> str:
    """The whole brief as Markdown, in the SPEC.md section order."""
    lines = (
        header(brief)
        + summary(brief, report)
        + riskiest_assumptions(brief)
        + interview_script(brief, report)
        + competitors(brief, report)
        + market_size(brief, report)
        + sources(report)
    )
    return "\n".join(lines)
