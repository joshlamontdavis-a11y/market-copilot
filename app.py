"""Streamlit viewer for saved market briefs.

    streamlit run app.py -- <folder of briefs>      (default folder: market-briefs)

This file is layout only. Loading runs, badges, and the market-size math live in
copilot/viewer.py, which pytest tests. The page follows brief.md: summary, riskiest
assumptions, interview script, competitors, market size, then sources. Badges come from
check_report.json. Sidebar edits last until the page is refreshed; the viewer never writes to a
run folder.
"""

import sys
from pathlib import Path

import streamlit as st

# Make the copilot package importable however Streamlit was started.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from copilot import render, sizing, viewer  # noqa: E402

DEFAULT_FOLDER = "market-briefs"
SHARE_TITLES = {"sam_share": "Share who could buy", "som_share": "Share we could win"}


def badge_md(label, color, detail="") -> str:
    """A colored badge, then the reason in parentheses and the same color if there is one."""
    text = f":{color}-badge[{viewer.md(label)}]"
    return text + (f" :{color}[({viewer.md(detail)})]" if detail else "")


def cite(source_ids) -> str:
    return viewer.md(render.cite(source_ids))


def claim_md(claim, item, flagged=False) -> str:
    """A claim with its badge, a Check mark if it uses a guessing word, and its source ids."""
    text = badge_md(*viewer.badge(item))
    if flagged:
        text += " " + badge_md(render.GUESSING_NOTE, "orange")
    return f"{text} {viewer.md(claim['text'])}{cite(claim['source_ids'])}"


def table_cell(text) -> str:
    return viewer.md(" ".join(str(text).split()))


# --- Sidebar ------------------------------------------------------------------------------


def pick_run(folder):
    """The run folder the user picked, or None if the folder has no briefs."""
    st.sidebar.title("Market briefs")
    runs = {path.name: path for path in viewer.find_runs(folder)}
    if not runs:
        return None
    name = st.sidebar.radio("Saved briefs", list(runs))
    return runs[name]


def reset_inputs(saved_values):
    # Setting each box's value (not deleting it) makes Streamlit send the saved number to the
    # browser. After a delete, the server forgot the edit but the box kept showing it.
    for key, value in saved_values.items():
        st.session_state[key] = value


def sizing_inputs(run, report, currency) -> dict[str, float]:
    """A number input for each base value. Returns {name: value as shown in the sidebar}."""
    st.sidebar.header("Market size inputs")
    st.sidebar.caption(
        "Change a base value to recompute TAM, SAM, and SOM. Changes last until you refresh "
        "the page or pick another brief; saved files are never changed."
    )
    saved = report["market_size"]["assumptions"]
    inputs, saved_values = {}, {}
    for name, title in render.SIZING_ROWS:
        a = saved[name]
        is_share = name in sizing.SHARE_NAMES
        key = f"{run.folder.name}:{name}"
        saved_values[key] = viewer.to_input(name, a["base"])
        # The box starts from the session's value (not a value= argument), so Reset can
        # change it the same way.
        if key not in st.session_state:
            st.session_state[key] = saved_values[key]
        inputs[name] = st.sidebar.number_input(
            f"{SHARE_TITLES[name]} (base, %)" if is_share else f"{title} (base)",
            min_value=0.0,
            max_value=100.0 if is_share else None,
            step=1.0,
            format="%.2f" if name == "price" else "%g",
            key=key,
            help=a["unit"],
        )
        value = viewer.from_input(name, inputs[name])
        low = render.sizing_value(name, a["low"], currency)
        high = render.sizing_value(name, a["high"], currency)
        edited = name in viewer.find_edits(report, {name: inputs[name]})
        shown_badge = (badge_md("Your edit", "blue") if edited
                       else badge_md(*viewer.badge(run.report["items"][f"market_size.{name}"])[:2]))
        st.sidebar.markdown(f"{shown_badge} Low {viewer.md(low)}, high {viewer.md(high)}")
        if edited and viewer.out_of_range(a, value):
            st.sidebar.caption(":orange[Outside the low to high range.]")
    if viewer.find_edits(report, inputs):
        st.sidebar.button("Reset to saved values", on_click=reset_inputs, args=(saved_values,))
    return inputs


# --- Main pane, in the brief.md order -----------------------------------------------------


def show_header(brief):
    st.title(f"Market brief: {viewer.md(brief['idea'])}")
    st.markdown(viewer.md(f"Research date: {brief['research_date']}. {render.CHANGE_NOTE}"))
    st.markdown(viewer.md(f"Target customer: {brief['target_customer']}. "
                          f"Geography: {brief['geography']}. Depth: {brief['depth']}."))
    st.info(render.INTERVIEWS_NOTE)
    st.markdown(viewer.md(render.VERIFIED_MEANS))


def show_summary(brief, report):
    st.header("1. Summary")
    counts = report["counts"]
    badges = [
        badge_md(f"{counts['verified']} verified", "green"),
        badge_md(f"{counts['assumption']} assumptions", "gray"),
        badge_md(f"{counts['unverified']} unverified", "red"),
    ]
    if counts.get("edited"):
        badges.append(badge_md(f"{counts['edited']} changed by you", "blue"))
    st.markdown("Checked by check.py: " + " ".join(badges))
    if counts.get("edited"):
        st.caption(render.edited_note(counts["edited"]))

    flagged = len(report["warnings"]["hypothetical_questions"])
    if flagged:
        needs = ("1 interview question needs" if flagged == 1
                 else f"{flagged} interview questions need")
        st.warning(f"{needs} rewriting (see section 3).")
    guessing = render.guessing_paths(report)
    if guessing:
        uses = ("1 sourced claim uses" if len(guessing) == 1
                else f"{len(guessing)} sourced claims use")
        st.warning(f"{uses} a guessing word (marked Check). Read its quotes before relying on it.")

    st.subheader("What we found")
    for i, claim in enumerate(brief["summary"]["found"]):
        path = f"summary.found.{i}"
        st.markdown("- " + claim_md(claim, report["items"][path], path in guessing))
    st.subheader("What we still don't know")
    for unknown in brief["summary"]["unknowns"]:
        st.markdown("- " + viewer.md(unknown))


def show_risks(brief):
    st.header("2. Riskiest assumptions")
    for i, risk in enumerate(brief["riskiest_assumptions"], start=1):
        st.markdown(
            f"{i}\\. **{viewer.md(risk['assumption'])}**\n"
            f"- Why it's risky: {viewer.md(risk['why_risky'])}\n"
            f"- How to test it: {viewer.md(risk['how_to_test'])}"
        )


def show_interview(brief, report):
    st.header("3. Interview script")
    script = brief["interview_script"]
    flagged = {warning["path"] for warning in report["warnings"]["hypothetical_questions"]}
    st.markdown(viewer.md(script["intro"]))
    for i, question in enumerate(script["questions"]):
        mark = (badge_md(render.REWRITE_NOTE, "orange") + " "
                if f"interview_script.questions.{i}" in flagged else "")
        st.markdown(
            f"{i + 1}\\. {mark}{viewer.md(question['question'])}\n"
            f"- Listen for: {viewer.md(question['listening_for'])}"
        )


def show_competitors(brief, report):
    st.header("4. Competitors")
    guessing = render.guessing_paths(report)
    for i, competitor in enumerate(brief["competitors"]):
        parts = {}
        for key in ("description", "price"):
            path = f"competitors.{i}.{key}"
            parts[key] = claim_md(competitor[key], report["items"][path], path in guessing)
        st.subheader(viewer.md(competitor["name"]))
        st.markdown(
            f"Link: {viewer.link(competitor['url'], competitor['url'])}\n\n"
            f"- What it does: {parts['description']}\n"
            f"- Price: {parts['price']}"
        )


def show_market_size(brief, report):
    st.header("5. Market size")
    currency = brief.get("currency", "USD")
    sizing_report = report["market_size"]
    st.markdown(viewer.md(render.SIZING_MATH))

    rows = ["| Assumption | Low | Base | High | Unit | Check |", "|---|---|---|---|---|---|"]
    for name, title in render.SIZING_ROWS:
        a = sizing_report["assumptions"][name]
        check = badge_md(*viewer.badge(report["items"][f"market_size.{name}"])) + cite(a["source_ids"])
        if render.sizing_note(a):
            check += " " + viewer.md(render.sizing_note(a))
        cells = [table_cell(value) for value in render.sizing_cells(name, a, currency)]
        rows.append(f"| {title} | " + " | ".join(cells) + f" | {table_cell(a['unit'])} | {check} |")
    st.markdown("\n".join(rows))
    if any("edited_from" in a for a in sizing_report["assumptions"].values()):
        st.caption("Values marked (your edit) were changed in the viewer, so these sizes differ "
                   "from check_report.json.")
    st.markdown(viewer.md(f"Price covers: {sizing_report['price_covers']}"))

    rows = ["| Scenario | TAM | SAM | SOM |", "|---|---|---|---|"]
    for scenario in sizing_report["scenarios"]:
        amounts = [viewer.md(render.whole_money(scenario[key], currency))
                   for key in ("tam", "sam", "som")]
        rows.append(f"| {scenario['name'].capitalize()} | " + " | ".join(amounts) + " |")
    st.markdown("\n".join(rows))
    st.caption(render.SCENARIOS_NOTE)


def show_sources(report):
    st.header("Sources")
    uncited = {warning["id"] for warning in report["warnings"]["uncited_sources"]}
    for sid, source in report["sources"].items():
        line = (f"**{sid}** {badge_md(*viewer.source_badge(source))} "
                f"{viewer.link(source['title'], source['url'])}. "
                f"Accessed {viewer.md(source['accessed'])}.")
        if sid in uncited:
            line += " " + badge_md("Not cited by any claim.", "orange")
        st.markdown(line)
        with st.expander(f"Quote from {sid}"):
            st.markdown("> " + viewer.md(render.short_quote(source["quote"])))


def show_download(brief, run, edits):
    """Download in two steps, so the file always has the numbers on the page.

    A download button's file is made when the page is drawn. Typing a number and clicking it
    straight away downloaded the old numbers, because the click came before the page redrew.
    A normal button's click carries every box's current value, so the run it starts has the
    new numbers; only that run shows the Save button, and any change hides it again.
    """
    if not st.button("Prepare Markdown download", key="prepare_download"):
        return
    st.download_button(
        "Save brief.md",
        data=viewer.brief_markdown(brief, run.report, edits),  # render.py, so it matches brief.md
        file_name=f"{run.folder.name}-brief.md",
        mime="text/markdown",
        on_click="ignore",  # saving doesn't redraw the page, so the button stays
        type="primary",
    )
    note = "with your edits" if edits else "with the saved numbers"
    st.caption(f"Made from the numbers on this page, {note}. Change a number and prepare it "
               "again to include the change.")


# --- The page -----------------------------------------------------------------------------


def main():
    # No page_icon: a Material icon would make the browser download it from Google.
    st.set_page_config(page_title="Market Copilot")
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FOLDER)
    run_folder = pick_run(folder)
    if run_folder is None:
        st.title("Market briefs")
        st.info(f"No saved briefs in {folder.resolve()}. Make one with "
                '/market-copilot:brief "<product idea>" in Claude Code.')
        return

    run = viewer.load_saved_run(run_folder)
    if run.problems:
        st.title(run_folder.name)
        st.warning("This brief can't be shown yet:\n\n"
                   + "\n".join("- " + viewer.md(problem) for problem in run.problems))
        return

    brief = run.brief
    currency = brief.get("currency", "USD")
    inputs = sizing_inputs(run, run.report, currency)
    edits = viewer.find_edits(run.report, inputs)
    report = viewer.apply_edits(brief, run.report, edits)

    show_header(brief)
    show_download(brief, run, edits)
    show_summary(brief, report)
    show_risks(brief)
    show_interview(brief, report)
    show_competitors(brief, report)
    show_market_size(brief, report)
    show_sources(report)


main()
