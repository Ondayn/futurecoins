"""Grid projection and HTML rendering.

The grid is a *projection* of the agent population, not the simulation itself.
When there are more agents than cells, a cell represents a **cohort** and shows
the dominant role. The real population is always displayed separately, because
confusing "800 cells" with "800 agents" is the easiest way to teach the wrong
lesson.

Rendering is a CSS grid with a fixed cell width. Emoji are not monospaced, so a
plain string grid drifts; a fixed-width cell removes the problem entirely.
"""

from __future__ import annotations

import html
from collections import Counter
from dataclasses import dataclass

from .agents import ROLE_META, Agent, Role

# Fixed role order, used to break ties when a cohort has no majority role.
_ROLE_ORDER = {
    Role.MINER: 0,
    Role.VALIDATOR: 1,
    Role.USER: 2,
    Role.TRADER: 3,
    Role.DEVELOPER: 4,
    Role.ATTACKER: 5,
}


@dataclass(frozen=True)
class Cell:
    """One rendered cell: either a single agent or a cohort."""

    row: int
    col: int
    role: Role
    count: int
    active: int

    @property
    def active_ratio(self) -> float:
        return self.active / self.count if self.count else 0.0

    @property
    def label(self) -> str:
        name = ROLE_META[self.role]["label"]
        if self.count == 1:
            return f"{name} · cell {self.row},{self.col} · {'active' if self.active else 'inactive'}"
        return (
            f"{self.count} agents · {name} (dominant) · {self.active} active · "
            f"cell {self.row},{self.col}"
        )


def project(agents: list[Agent], rows: int, cols: int) -> list[list[Cell | None]]:
    """Assign agents to cells.

    Agents already carry a (row, col) assigned at genesis, so this is a grouping
    operation, not a physics simulation. That is deliberate: it keeps the grid
    O(n) and keeps the engine independent of the view.
    """
    buckets: dict[tuple[int, int], list[Agent]] = {}
    for agent in agents:
        row = min(max(agent.row, 0), rows - 1)
        col = min(max(agent.col, 0), cols - 1)
        buckets.setdefault((row, col), []).append(agent)

    grid: list[list[Cell | None]] = [[None] * cols for _ in range(rows)]

    for (row, col), group in buckets.items():
        counts = Counter(a.role for a in group)
        # Deterministic tie-break: most common role, then fixed role order.
        dominant = min(
            counts.items(),
            key=lambda item: (-item[1], _ROLE_ORDER[item[0]]),
        )[0]
        active = sum(1 for a in group if a.active)
        grid[row][col] = Cell(
            row=row, col=col, role=dominant, count=len(group), active=active
        )

    return grid


def render_html(
    grid: list[list[Cell | None]],
    *,
    ascii_mode: bool = False,
    show_titles: bool = True,
) -> str:
    """Turn a projected grid into a self-contained HTML fragment.

    The caller (Streamlit) only has to pass this string to `st.html`. No
    Streamlit import lives in this file.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    parts: list[str] = [
        (
            f'<div class="fc-grid" style="--fc-cols:{cols}" role="img" '
            f'aria-label="Simulated network grid, {rows} by {cols} cells">'
        )
    ]

    for row in grid:
        for cell in row:
            if cell is None:
                parts.append('<span class="fc-cell fc-empty">·</span>')
                continue

            meta = ROLE_META[cell.role]
            glyph = meta["ascii"] if ascii_mode else meta["emoji"]
            classes = ["fc-cell", f"fc-{meta['css']}"]
            if cell.active == 0:
                classes.append("fc-offline")

            # Opacity encodes how much of the cohort is active.
            opacity = 0.35 + 0.65 * cell.active_ratio
            title = (
                f' title="{html.escape(cell.label)}"' if show_titles else ""
            )
            parts.append(
                f'<span class="{" ".join(classes)}" style="opacity:{opacity:.2f}"{title}>'
                f"{glyph}</span>"
            )

    parts.append("</div>")
    return "".join(parts)


def population_summary(agents: list[Agent], rows: int, cols: int) -> str:
    """The sentence that must always accompany the grid."""
    cells = rows * cols
    population = len(agents)
    if population <= cells:
        return f"Population: {population:,} agents · {cells:,} cells · 1 agent per cell"
    per_cell = population / cells
    return (
        f"Population: {population:,} agents · {cells:,} cells · "
        f"~{per_cell:.1f} agents per cell (cohorts)"
    )


def legend_html() -> str:
    """A compact legend, generated from the same role metadata as the grid."""
    items = "".join(
        f'<span class="fc-legend-item"><span class="fc-cell fc-{meta["css"]}">{meta["emoji"]}</span>'
        f"{meta['label']}</span>"
        for meta in ROLE_META.values()
    )
    return f'<div class="fc-legend">{items}</div>'
