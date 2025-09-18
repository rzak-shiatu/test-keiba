"""Render race tables to HTML."""

from __future__ import annotations

from html import escape
from textwrap import dedent
from typing import Iterable, Sequence

from .models import AdditionalColumn, Criterion, HorseEntry, RaceTable

DEFAULT_BRACKET_COLORS = {
    1: "#ffffff",
    2: "#000000",
    3: "#ff4b4b",
    4: "#1a7cff",
    5: "#ffd447",
    6: "#3ab66b",
    7: "#ff7f27",
    8: "#ff7fd1",
}

DEFAULT_BRACKET_TEXT_COLORS = {
    1: "#000000",
    2: "#ffffff",
    3: "#ffffff",
    4: "#ffffff",
    5: "#000000",
    6: "#ffffff",
    7: "#000000",
    8: "#000000",
}

RATING_CLASSES = {
    "S": "rating-s",
    "A": "rating-a",
    "B": "rating-b",
    "C": "rating-c",
    "D": "rating-d",
    "E": "rating-e",
}


def _auto_text_color(background: str) -> str:
    """Return black or white text depending on the background colour."""

    hex_value = background.lstrip("#")
    if len(hex_value) != 6:
        return "#000000"
    try:
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)
    except ValueError:  # pragma: no cover - defensive programming
        return "#000000"

    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    return "#000000" if luminance > 0.6 else "#ffffff"


def _render_rating_cell(rating: str | None) -> str:
    if not rating:
        return ""
    css_class = RATING_CLASSES.get(rating.upper(), "rating-generic")
    return f'<span class="rating-chip {css_class}">{escape(rating)}</span>'


def _render_additional_columns(
    entry: HorseEntry, columns: Sequence[AdditionalColumn]
) -> Iterable[str]:
    for column in columns:
        text = entry.notes.get(column.key, "")
        yield f"<td>{escape(text)}</td>"


def _render_legend(criteria: Iterable[Criterion], legend: dict[str, str]) -> str:
    items: list[str] = []
    for criterion in criteria:
        text = legend.get(criterion.key) or criterion.description
        if not text:
            continue
        items.append(
            f"<li><strong>{escape(criterion.label)}:</strong> {escape(text)}</li>"
        )
    if not items:
        return ""
    return "<ul class=\"legend\">" + "".join(items) + "</ul>"


def _post_position_cell(table: RaceTable, entry: HorseEntry) -> str:
    background = table.bracket_colors.get(entry.post_position)
    text_color: str | None = None

    if background:
        text_color = _auto_text_color(background)
    else:
        background = DEFAULT_BRACKET_COLORS.get(entry.post_position)
        if background:
            text_color = DEFAULT_BRACKET_TEXT_COLORS.get(entry.post_position, "#000000")

    style_attr = ""
    if background:
        text_color = text_color or _auto_text_color(background)
        style_attr = f' style="background:{background};color:{text_color};"'

    return (
        f"<td class=\"post-position\"{style_attr}>"
        f"{escape(str(entry.post_position))}</td>"
    )


def render_html(table: RaceTable) -> str:
    """Render the race table to an HTML string."""

    head = dedent(
        """
        <!DOCTYPE html>
        <html lang="ja">
          <head>
            <meta charset="utf-8" />
            <title>出走表</title>
            <style>
              :root {
                color-scheme: light;
                font-family: "Helvetica Neue", "Yu Gothic", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
              }
              body {
                margin: 2rem;
                background: #f7f7f7;
                color: #222;
              }
              h1 {
                margin-bottom: 0.25rem;
                font-size: 1.75rem;
              }
              h2 {
                margin-top: 0.25rem;
                color: #555;
                font-size: 1rem;
              }
              .distance-note {
                margin-top: 0.5rem;
                margin-bottom: 1rem;
                font-size: 0.9rem;
                color: #6c6c6c;
              }
              table.race-table {
                width: 100%;
                border-collapse: collapse;
                background: #fff;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
              }
              table.race-table th,
              table.race-table td {
                border: 1px solid #d0d0d0;
                padding: 0.45rem 0.35rem;
                text-align: center;
                font-size: 0.9rem;
                line-height: 1.2;
              }
              table.race-table th {
                background: #f0f0f0;
                font-weight: 600;
              }
              table.race-table td.name {
                text-align: left;
                font-weight: 600;
              }
              .post-position {
                font-weight: 700;
              }
              .rating-chip {
                display: inline-block;
                min-width: 1.75rem;
                padding: 0.15rem 0.45rem;
                border-radius: 999px;
                font-weight: 700;
                font-size: 0.75rem;
                color: #fff;
              }
              .rating-s { background: #0d9488; }
              .rating-a { background: #14b8a6; }
              .rating-b { background: #0891b2; }
              .rating-c { background: #6366f1; }
              .rating-d { background: #a855f7; }
              .rating-e { background: #f97316; }
              .rating-generic { background: #6b7280; }
              td.comments {
                text-align: left;
                font-size: 0.85rem;
              }
              .legend {
                margin-top: 1.25rem;
                padding-left: 1.2rem;
                font-size: 0.85rem;
                color: #444;
              }
              .legend li {
                margin-bottom: 0.25rem;
              }
              footer {
                margin-top: 1rem;
                font-size: 0.8rem;
                color: #666;
              }
            </style>
          </head>
        """
    )

    body_parts = ["  <body>"]
    body_parts.append(f"    <h1>{escape(table.title)}</h1>")
    if table.subtitle:
        body_parts.append(f"    <h2>{escape(table.subtitle)}</h2>")
    if table.distance_note:
        body_parts.append(
            f"    <div class=\"distance-note\">{escape(table.distance_note)}</div>"
        )

    body_parts.append("    <table class=\"race-table\">")

    headers = table.column_headers()
    header_html = "      <tr>" + "".join(
        f"<th>{escape(header)}</th>" for header in headers
    ) + "</tr>"
    body_parts.append("      <thead>")
    body_parts.append(header_html)
    body_parts.append("      </thead>")
    body_parts.append("      <tbody>")

    for entry in table.horses:
        row_cells: list[str] = []
        row_cells.append(_post_position_cell(table, entry))
        row_cells.append(f"<td>{escape(str(entry.number))}</td>")
        row_cells.append(f"<td class=\"name\">{escape(entry.name)}</td>")
        row_cells.append(f"<td>{escape(entry.sex_age)}</td>")
        row_cells.append(f"<td>{escape(entry.weight)}</td>")
        row_cells.append(f"<td>{escape(entry.jockey)}</td>")

        if table.additional_columns:
            row_cells.extend(_render_additional_columns(entry, table.additional_columns))
        if table.has_running_style:
            row_cells.append(f"<td>{escape(entry.running_style or '')}</td>")

        for criterion in table.criteria:
            rating = entry.ratings.get(criterion.key)
            row_cells.append(f"<td>{_render_rating_cell(rating)}</td>")

        if table.has_comments:
            row_cells.append(
                f"<td class=\"comments\">{escape(entry.comments or '')}</td>"
            )

        body_parts.append("        <tr>" + "".join(row_cells) + "</tr>")

    body_parts.append("      </tbody>")
    body_parts.append("    </table>")

    legend_html = _render_legend(table.criteria, table.legend)
    if legend_html:
        body_parts.append("    <section>")
        body_parts.append("      <h3>評価基準</h3>")
        body_parts.append(f"      {legend_html}")
        body_parts.append("    </section>")

    if table.footnote:
        body_parts.append(f"    <footer>{escape(table.footnote)}</footer>")

    body_parts.append("  </body>")
    body_parts.append("</html>")

    return head + "\n".join(body_parts) + "\n"
