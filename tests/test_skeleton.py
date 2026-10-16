"""Phase 1 tests: the plugin files are well formed and copilot/ uses only the standard library."""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_manifests_parse_and_agree():
    plugin = load_json(".claude-plugin/plugin.json")
    marketplace = load_json(".claude-plugin/marketplace.json")

    # Plugin names must be kebab-case (lowercase words joined by hyphens).
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", plugin["name"])

    # The marketplace lists this plugin, at the repo root.
    entry = marketplace["plugins"][0]
    assert entry["name"] == plugin["name"]
    assert entry["source"] == "./"


def test_every_skill_has_required_frontmatter():
    skill_files = list((ROOT / "skills").glob("*/SKILL.md"))
    assert skill_files, "no skills found"

    for skill_file in skill_files:
        # splitlines() handles both Windows (CRLF) and Unix (LF) line endings.
        lines = skill_file.read_text(encoding="utf-8").splitlines()
        # Frontmatter must start on line 1 and end with a second '---' line.
        assert lines[0] == "---", skill_file
        end = lines.index("---", 1)
        frontmatter = "\n".join(lines[1:end])
        assert "description:" in frontmatter, skill_file
        # The user triggers skills; Claude never runs them on its own.
        assert "disable-model-invocation: true" in frontmatter, skill_file
        assert "argument-hint:" in frontmatter, skill_file


def test_skill_scripts_exist():
    # A renamed or moved file would break every brief run, so check each path a skill names.
    pattern = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)")
    for skill_file in (ROOT / "skills").glob("*/SKILL.md"):
        for relative_path in pattern.findall(skill_file.read_text(encoding="utf-8")):
            assert (ROOT / relative_path).is_file(), f"{skill_file} names missing {relative_path}"


def test_brief_skill_commands_are_pre_approved():
    # The skill runs each script with python or python3. Both must match an allowed-tools rule,
    # or a first-time user gets a permission prompt for the plugin's own scripts.
    text = (ROOT / "skills" / "brief" / "SKILL.md").read_text(encoding="utf-8")
    for command in ('"${CLAUDE_PLUGIN_ROOT}/copilot/check.py" *',
                    '"${CLAUDE_PLUGIN_ROOT}/copilot/sources.py" fetch *'):
        for python in ("python", "python3"):
            assert f"  - Bash({python} {command})" in text, f"no rule for {python} {command}"
    for tool in ("WebSearch", "Edit(market-briefs/**)"):
        assert f"  - {tool}\n" in text, f"{tool} is not pre-approved"


def test_check_py_prints_version():
    from copilot import __version__

    result = subprocess.run(
        [sys.executable, str(ROOT / "copilot" / "check.py"), "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert f"market-copilot {__version__}" in result.stdout


def test_python_version_guard():
    from copilot.check import python_is_new_enough

    assert python_is_new_enough((3, 11, 0))
    assert python_is_new_enough((3, 13, 1))
    assert not python_is_new_enough((3, 10, 9))


def test_copilot_uses_only_standard_library():
    # Rule 5: making a brief must need nothing beyond Python itself.
    for py_file in (ROOT / "copilot").glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module]
            else:
                continue
            for name in names:
                top_level = name.split(".")[0]
                allowed = top_level in sys.stdlib_module_names or top_level == "copilot"
                assert allowed, f"{py_file.name} imports non-standard module {name}"
