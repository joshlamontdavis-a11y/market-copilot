"""Entry point the brief skill runs: python check.py <run folder>.

Phase 1 stub. For now it only checks the Python version and prints the version.
Source checking, sizing, and rendering are added in later phases.
"""

import argparse
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)

# The skill runs this file directly (not as `python -m`), so make the copilot
# package importable by adding the repo root to the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def python_is_new_enough(version_info=sys.version_info) -> bool:
    """True if this Python is at least MIN_PYTHON."""
    return tuple(version_info[:2]) >= MIN_PYTHON


def main(argv=None) -> int:
    if not python_is_new_enough():
        found = ".".join(str(n) for n in sys.version_info[:3])
        print(
            f"Market Copilot needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer, "
            f"but this is Python {found}. Install a newer Python from "
            "https://www.python.org/downloads/ and try again."
        )
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

    print("check.py: not implemented yet (Phase 4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
