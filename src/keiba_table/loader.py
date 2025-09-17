"""Load race table definitions from TOML files."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict, Iterable, List

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

    legend = data.get("legend", {})
    if not isinstance(legend, dict):
        raise TypeError("legend must be a table of criterion key to description")

    footnote = race_info.get("footnote")

    raw_horses = data.get("horses")
    if not isinstance(raw_horses, list) or not raw_horses:
        raise ValueError("TOML file must contain a [ [horses] ] array with at least one entry")

    horses = [HorseEntry.from_raw(entry, criteria, additional_columns) for entry in raw_horses]

    return RaceTable(
        title=title,
        subtitle=str(subtitle) if subtitle else None,
        distance_note=str(distance_note) if distance_note else None,
        criteria=criteria,
        horses=horses,
        additional_columns=additional_columns,
        legend={str(key): str(value) for key, value in legend.items()},
        footnote=str(footnote) if footnote else None,
    )
