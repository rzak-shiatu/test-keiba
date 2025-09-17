"""Unit tests for the race table loader and renderer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from keiba_table import load_race_table, render_html  # noqa: E402


class RaceTableTests(unittest.TestCase):
    def _write_toml(self, directory: Path, content: str) -> Path:
        path = directory / "race.toml"
        path.write_text(dedent(content), encoding="utf-8")
        return path

    def test_structured_additional_columns_are_loaded(self) -> None:
        toml_content = """
        [race]
        title = "テスト"
        additional_columns = [
          { key = "prev_race", label = "前走" },
          "ローテ"
        ]

        [[criteria]]
        key = "speed"
        label = "スピード"
        description = "スピード評価について"

        [[horses]]
        post_position = 1
        number = 1
        name = "テストホース"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }
        notes = { prev_race = "日経賞", "ローテ" = "中2週" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            table = load_race_table(path)

            self.assertEqual(["prev_race", "ローテ"], [c.key for c in table.additional_columns])
            self.assertEqual(["前走", "ローテ"], [c.label for c in table.additional_columns])
            self.assertEqual("日経賞", table.horses[0].notes["prev_race"])
            self.assertEqual("中2週", table.horses[0].notes["ローテ"])

            html = render_html(table)
            self.assertIn("<th>前走</th>", html)
            self.assertIn("<th>ローテ</th>", html)
            self.assertIn("<td>日経賞</td>", html)
            self.assertIn("<td>中2週</td>", html)
            self.assertIn("<strong>スピード:</strong> スピード評価について", html)

    def test_unknown_additional_column_key_raises(self) -> None:
        toml_content = """
        [race]
        title = "エラー"
        additional_columns = [ { key = "prev", label = "前走" } ]

        [[criteria]]
        key = "speed"
        label = "スピード"

        [[horses]]
        post_position = 1
        number = 1
        name = "エラーホース"
        sex_age = "牡3"
        weight = "56"
        jockey = "騎手"
        ratings = { speed = "B" }
        notes = { unknown = "should fail" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            with self.assertRaisesRegex(ValueError, "unknown columns"):
                load_race_table(path)

