"""Data models for the race table generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


@dataclass(slots=True)
class AdditionalColumn:
    """Represents an additional informational column displayed per horse."""

    key: str
    label: str

    @staticmethod
    def from_raw(raw: Dict[str, str] | str) -> "AdditionalColumn":
        """Convert TOML values into an :class:`AdditionalColumn` instance."""

        if isinstance(raw, str):
            return AdditionalColumn(key=raw, label=raw)
        if not isinstance(raw, dict):  # pragma: no cover - defensive programming
            raise TypeError("Additional column definitions must be strings or tables")

        key = raw.get("key")
        if not key:
            raise ValueError("Additional column tables must include a 'key'")
        label = raw.get("label", key)
        return AdditionalColumn(key=str(key), label=str(label))


@dataclass(slots=True)
class Criterion:
    """Represents an evaluation criterion displayed in the table."""

    key: str
    label: str
    description: Optional[str] = None

    @staticmethod
    def from_raw(raw: Dict[str, str] | str) -> "Criterion":
        """Convert raw values loaded from TOML into a :class:`Criterion`."""

        if isinstance(raw, str):
            return Criterion(key=raw, label=raw)
        key = raw.get("key")
        label = raw.get("label", key)
        if not key or not label:
            raise ValueError("Criterion definitions must include at least a key and label")
        return Criterion(key=key, label=label, description=raw.get("description"))


@dataclass(slots=True)
class HorseEntry:
    """Represents a single horse entry row in the table."""

    post_position: int
    number: int
    name: str
    sex_age: str
    weight: str
    jockey: str
    running_style: Optional[str] = None
    comments: Optional[str] = None
    ratings: Dict[str, str] = field(default_factory=dict)
    notes: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_raw(
        raw: Dict[str, object],
        criteria: Sequence[Criterion],
        additional_columns: Sequence["AdditionalColumn"] | None = None,
    ) -> "HorseEntry":
        missing = {field for field in ["post_position", "number", "name", "sex_age", "weight", "jockey"] if field not in raw}
        if missing:
            raise ValueError(f"Horse entry is missing required fields: {', '.join(sorted(missing))}")

        ratings = raw.get("ratings", {})
        if not isinstance(ratings, dict):
            raise TypeError("'ratings' must be a table of criterion key to rating value")

        notes = raw.get("notes", {})
        if not isinstance(notes, dict):
            raise TypeError("'notes' must be a table of column key to text value")

        if additional_columns:
            valid_note_keys = {column.key for column in additional_columns}
            invalid_notes = sorted(set(notes) - valid_note_keys)
            if invalid_notes:
                raise ValueError(
                    f"Horse entry '{raw.get('name')}' contains notes for unknown columns: {', '.join(invalid_notes)}"
                )

        # Ensure only known criteria keys appear in ratings.
        valid_keys = {criterion.key for criterion in criteria}
        invalid = sorted(set(ratings) - valid_keys)
        if invalid:
            raise ValueError(f"Horse entry '{raw.get('name')}' contains ratings for unknown criteria: {', '.join(invalid)}")

        return HorseEntry(
            post_position=int(raw["post_position"]),
            number=int(raw["number"]),
            name=str(raw["name"]),
            sex_age=str(raw["sex_age"]),
            weight=str(raw["weight"]),
            jockey=str(raw["jockey"]),
            running_style=str(raw.get("running_style")) if raw.get("running_style") is not None else None,
            comments=str(raw.get("comments")) if raw.get("comments") is not None else None,
            ratings={str(key): str(value) for key, value in ratings.items()},
            notes={str(key): str(value) for key, value in notes.items()},
        )


@dataclass(slots=True)
class RaceTable:
    """Aggregates all information required to render the race table."""

    title: str
    subtitle: Optional[str]
    distance_note: Optional[str]
    criteria: List[Criterion]
    horses: List[HorseEntry]
    additional_columns: List[AdditionalColumn] = field(default_factory=list)
    legend: Dict[str, str] = field(default_factory=dict)
    footnote: Optional[str] = None

    @property
    def has_running_style(self) -> bool:
        return any(entry.running_style for entry in self.horses)

    @property
    def has_comments(self) -> bool:
        return any(entry.comments for entry in self.horses)

    def column_headers(self) -> List[str]:
        base = ["枠", "馬番", "馬名", "性齢", "斤量", "騎手"]
        if self.additional_columns:
            base.extend(column.label for column in self.additional_columns)
        if self.has_running_style:
            base.append("脚質")
        base.extend(criterion.label for criterion in self.criteria)
        if self.has_comments:
            base.append("備考")
        return base
