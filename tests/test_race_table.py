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

    def _build_horses_section(self, count: int) -> str:
        parts: list[str] = []
        for number in range(1, count + 1):
            parts.append(
                f"""
                [[horses]]
                number = {number}
                name = "ホース{number}"
                sex_age = "牡4"
                weight = "58"
                jockey = "騎手{number}"
                ratings = {{ speed = "A" }}
                """
            )
        return "".join(parts)

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
            self.assertEqual(1, table.horses[0].post_position)

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

    def test_post_positions_follow_allocation_rules(self) -> None:
        scenarios = {
            9: [4, 5, 5, 6, 6, 7, 7, 8, 8],
            15: [1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8],
            16: [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8],
            17: [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8],
            18: [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 8, 8, 8],
        }

        race_header = """
        [race]
        title = "枠番テスト"

        [[criteria]]
        key = "speed"
        label = "スピード"
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            for count, expected in scenarios.items():
                toml_content = race_header + self._build_horses_section(count)
                path = self._write_toml(directory, toml_content)
                table = load_race_table(path)
                self.assertEqual(expected, [horse.post_position for horse in table.horses])

    def test_custom_bracket_colors_are_loaded(self) -> None:
        toml_content = """
        [race]
        title = "色"
        bracket_colors = ["#111111", "#222222", "#333333"]

        [[criteria]]
        key = "speed"
        label = "スピード"

        [[horses]]
        number = 1
        name = "カラー"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            table = load_race_table(path)

            self.assertEqual({1: "#111111", 2: "#222222", 3: "#333333"}, table.bracket_colors)
            self.assertEqual(1, table.horses[0].post_position)

    def test_custom_bracket_colors_table_is_loaded(self) -> None:
        toml_content = """
        [race]
        title = "色"
        bracket_colors = { "1" = "#112233", 8 = "#abcdef" }

        [[criteria]]
        key = "speed"
        label = "スピード"

        [[horses]]
        number = 1
        name = "カラー"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            table = load_race_table(path)

            self.assertEqual({1: "#112233", 8: "#abcdef"}, table.bracket_colors)

            html = render_html(table)
            self.assertIn("background:#112233", html)

    def test_manual_post_position_is_rejected(self) -> None:
        toml_content = """
        [race]
        title = "手入力エラー"

        [[criteria]]
        key = "speed"
        label = "スピード"

        [[horses]]
        post_position = 1
        number = 1
        name = "エラー"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            with self.assertRaisesRegex(ValueError, "must not include 'post_position'"):
                load_race_table(path)

    def test_numbers_must_be_contiguous(self) -> None:
        toml_content = """
        [race]
        title = "連番チェック"

        [[criteria]]
        key = "speed"
        label = "スピード"

        [[horses]]
        number = 1
        name = "ホース1"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }

        [[horses]]
        number = 3
        name = "ホース3"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            with self.assertRaisesRegex(ValueError, "contiguous sequence"):
                load_race_table(path)

    def test_horses_are_sorted_by_number(self) -> None:
        toml_content = """
        [race]
        title = "順序テスト"

        [[criteria]]
        key = "speed"
        label = "スピード"

        [[horses]]
        number = 2
        name = "後ろ"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }

        [[horses]]
        number = 1
        name = "先頭"
        sex_age = "牡4"
        weight = "58"
        jockey = "騎手"
        ratings = { speed = "A" }
        """

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            path = self._write_toml(directory, toml_content)
            table = load_race_table(path)

            self.assertEqual([1, 2], [horse.number for horse in table.horses])
            self.assertEqual([1, 2], [horse.post_position for horse in table.horses])

