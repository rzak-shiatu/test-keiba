"""Command-line interface to generate a race table HTML file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_PATH = REPO_ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from keiba_table import load_race_table, render_html  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a horse racing race-table from TOML data.")
    parser.add_argument("input", type=Path, help="Path to the race definition TOML file")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Optional output path for the generated HTML file. Defaults to <input>.html",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    race_table = load_race_table(args.input)
    html = render_html(race_table)

    output_path = args.output or args.input.with_suffix(".html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Generated {output_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
