"""Load race table definitions from TOML files."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .models import AdditionalColumn, Criterion, HorseEntry, RaceTable


def _load_criteria(raw_criteria: Iterable[Any]) -> List[Criterion]:
    criteria: List[Criterion] = []
    for raw in raw_criteria:
        criteria.append(Criterion.from_raw(raw))
    keys = [criterion.key for criterion in criteria]
    if len(keys) != len(set(keys)):
        raise ValueError("Criterion keys must be unique")
    return criteria


def _load_additional_columns(raw_columns: Iterable[Any]) -> List[AdditionalColumn]:
    columns: List[AdditionalColumn] = []
    seen_keys: set[str] = set()
    for raw in raw_columns:
        column = AdditionalColumn.from_raw(raw)
        if column.key in seen_keys:
            raise ValueError("Additional column keys must be unique")
        seen_keys.add(column.key)
        columns.append(column)
    return columns


def _load_bracket_colors(raw: Any) -> Dict[int, str]:
    if raw is None:
        return {}

    colors: Dict[int, str] = {}

    if isinstance(raw, list):
        if len(raw) > 8:
            raise ValueError("race.bracket_colors may define at most eight entries")
        for index, value in enumerate(raw, start=1):
            color = str(value)
            if not color:
                raise ValueError("race.bracket_colors entries must be non-empty strings")
            colors[index] = color
        return colors

    if isinstance(raw, dict):
        for key, value in raw.items():
            try:
                frame = int(key)
            except (TypeError, ValueError) as exc:  # pragma: no cover - defensive programming
                raise ValueError("race.bracket_colors table keys must be integers between 1 and 8") from exc
            if not 1 <= frame <= 8:
                raise ValueError("race.bracket_colors keys must be between 1 and 8")
            if frame in colors:
                raise ValueError("race.bracket_colors keys must be unique")
            color = str(value)
            if not color:
                raise ValueError("race.bracket_colors entries must be non-empty strings")
            colors[frame] = color
        return colors

    raise TypeError("race.bracket_colors must be an array or a table")


def _frame_capacities(total_horses: int) -> Sequence[Tuple[int, int]]:
    if total_horses <= 0:
        raise ValueError("At least one horse entry is required")
    if total_horses <= 8:
        return [(frame, 1) for frame in range(1, total_horses + 1)]
    if 9 <= total_horses <= 15:
        capacities: List[Tuple[int, int]] = []
        remaining = total_horses
        for frame in range(1, 9):
            if remaining <= 0:
                break
            count = 2 if remaining > 1 else 1
            capacities.append((frame, count))
            remaining -= count
        return capacities
    if total_horses == 16:
        return [(frame, 2) for frame in range(1, 9)]
    if total_horses == 17:
        return [(frame, 2) for frame in range(1, 8)] + [(8, 3)]
    if total_horses == 18:
        return [(frame, 2) for frame in range(1, 7)] + [(7, 3), (8, 3)]
    raise ValueError("Races with more than 18 horses are not supported")


def _assign_post_positions(entries: List[HorseEntry]) -> None:
    total = len(entries)
    numbers = sorted(entry.number for entry in entries)
    expected = list(range(1, total + 1))
    if numbers != expected:
        raise ValueError("Horse numbers must form a contiguous sequence starting at 1")

    entries_by_number = {entry.number: entry for entry in entries}
    capacities = _frame_capacities(total)

    index = 0
    for frame, capacity in capacities:
        for _ in range(capacity):
            if index >= len(numbers):
                break
            number = numbers[index]
            entries_by_number[number].post_position = frame
            index += 1

    if index != len(numbers):  # pragma: no cover - defensive programming
        raise ValueError("Failed to assign post positions for every horse")

    # Ensure rows appear in ascending horse-number order even if the TOML input
    # lists them differently. This matches how official race tables are
    # presented and guarantees a deterministic output for rendering/tests.
    entries.sort(key=lambda entry: entry.number)


def load_race_table(path: str | Path) -> RaceTable:
    """Load race table data from a TOML file."""

    data: Dict[str, Any]
    with open(path, "rb") as fp:
        data = tomllib.load(fp)

    race_info = data.get("race")
    if not isinstance(race_info, dict):
        raise ValueError("TOML file must contain a [race] table")

    title = str(race_info.get("title") or "出走表")
    subtitle = race_info.get("subtitle")
    distance_note = race_info.get("distance_note")

    raw_criteria = data.get("criteria", [])
    if not isinstance(raw_criteria, list) or not raw_criteria:
        raise ValueError("TOML file must contain a [ [criteria] ] array with at least one item")

    criteria = _load_criteria(raw_criteria)

    raw_additional_columns = race_info.get("additional_columns", [])
    if not isinstance(raw_additional_columns, list):
        raise TypeError("race.additional_columns must be an array")
    additional_columns = _load_additional_columns(raw_additional_columns)

    bracket_colors = _load_bracket_colors(race_info.get("bracket_colors"))

    legend = data.get("legend", {})
    if not isinstance(legend, dict):
        raise TypeError("legend must be a table of criterion key to description")

    footnote = race_info.get("footnote")

    raw_horses = data.get("horses")
    if not isinstance(raw_horses, list) or not raw_horses:
        raise ValueError("TOML file must contain a [ [horses] ] array with at least one entry")

    horses = [HorseEntry.from_raw(entry, criteria, additional_columns) for entry in raw_horses]
    _assign_post_positions(horses)

    return RaceTable(
        title=title,
        subtitle=str(subtitle) if subtitle else None,
        distance_note=str(distance_note) if distance_note else None,
        criteria=criteria,
        horses=horses,
        additional_columns=additional_columns,
        legend={str(key): str(value) for key, value in legend.items()},
        footnote=str(footnote) if footnote else None,
        bracket_colors=bracket_colors,
    )
