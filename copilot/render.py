"""Turn brief.json and check.py's report into brief.md, a document people can read.

Sections follow SPEC.md: summary, riskiest assumptions, interview script, competitors, market
size, then the sources. Every claim carries the badge check.py decided ([Verified],
[Assumption], or [Unverified: reason]); nothing here decides what is verified.

    render_brief(brief, report) -> the Markdown text (this module reads and writes no files)
"""

from copilot.sources import MAX_QUOTE_WORDS

# Market size rows in the order the math uses them, with readable names.
SIZING_ROWS = (
    ("customers", "Customers"),
    ("price", "Price per purchase"),
    ("purchases_per_year", "Purchases per year"),
    ("sam_share", "Share who could buy (SAM)"),
    ("som_share", "Share we could win in ~3 years (SOM)"),
)
REWRITE_MARK = "**[Rewrite: this asks about a hypothetical. Ask about the last time it happened.]**"
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
    return "**[Unverified: " + "; ".join(item["reasons"]) + "]**"


def cite(source_ids) -> str:
    return " (" + ", ".join(source_ids) + ")" if source_ids else ""


def claim_text(claim, item) -> str:
    """A claim with its badge and the source ids it cites."""
    return f"{badge(item)} {claim['text']}{cite(claim['source_ids'])}"


def number(value) -> str:
    """20000 -> "20,000"; 12.5 -> "12.50"."""
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"


def money(value, currency) -> str:
    return "$" + number(value) if currency == "USD" else f"{number(value)} {currency}"


def sizing_value(name, value, currency) -> str:
    if name in ("sam_share", "som_share"):
        return f"{value * 100:g}%"  # 0.25 -> "25%"
    if name == "price":
        return money(value, currency)
    return number(value)


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
        f"Research date: {brief['research_date']}. Prices and competitors change, so check the "
        "links before relying on them.",
        "",
        f"Target customer: {brief['target_customer']}. Geography: {brief['geography']}. "
        f"Depth: {brief['depth']}.",
        "",
        "This brief prepares you for customer interviews. It does not show that anyone will buy.",
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
    flagged = len(report["warnings"])
    if flagged:
        needs = "1 interview question needs" if flagged == 1 else f"{flagged} interview questions need"
        lines += [f"{needs} rewriting (see section 3).", ""]
    lines += ["### What we found", ""]
    for i, claim in enumerate(brief["summary"]["found"]):
        lines.append(f"- {claim_text(claim, report['items'][f'summary.found.{i}'])}")
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
    flagged = {warning["path"] for warning in report["warnings"]}
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
    lines = ["## 4. Competitors", ""]
    for i, competitor in enumerate(brief["competitors"]):
        description = report["items"][f"competitors.{i}.description"]
        price = report["items"][f"competitors.{i}.price"]
        lines += [
            f"### {competitor['name']}",
            "",
            f"Link: {competitor['url']}",
            "",
            f"- What it does: {claim_text(competitor['description'], description)}",
            f"- Price: {claim_text(competitor['price'], price)}",
            "",
        ]
    return lines


def market_size(brief, report) -> list[str]:
    currency = brief.get("currency", "USD")
    sizing = report["market_size"]
    lines = [
        "## 5. Market size",
        "",
        "Computed by sizing.py from the assumptions below, not stated by the model. "
        "TAM = customers x price x purchases per year. SAM = TAM x share who could buy. "
        "SOM = SAM x share we could win in about 3 years.",
        "",
        "| Assumption | Low | Base | High | Unit | Check |",
        "|---|---|---|---|---|---|",
    ]
    for name, title in SIZING_ROWS:
        a = sizing["assumptions"][name]
        label = badge(report["items"][f"market_size.{name}"]) + cite(a["source_ids"])
        if a["status"] != a["status_used"]:
            label += " Used as an assumption in the math."
        values = [sizing_value(name, a[s], currency) for s in ("low", "base", "high")]
        lines.append(f"| {title} | " + " | ".join(values) + f" | {cell(a['unit'])} | {cell(label)} |")

    lines += ["", "| Scenario | TAM | SAM | SOM |", "|---|---|---|---|"]
    for scenario in sizing["scenarios"]:
        amounts = [money(scenario[key], currency) for key in ("tam", "sam", "som")]
        lines.append(f"| {scenario['name'].capitalize()} | " + " | ".join(amounts) + " |")
    return lines + ["", "Low uses every low value, base every base value, high every high value.",
                    ""]


def sources(report) -> list[str]:
    lines = [
        "## Sources",
        "",
        "| Id | Source | Quote | Accessed | Check |",
        "|---|---|---|---|---|",
    ]
    for sid, source in report["sources"].items():
        check = "Verified" if source["verified"] else f"Unverified: {source['reason']}"
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
