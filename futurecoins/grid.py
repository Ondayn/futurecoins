"""Grid projection and HTML rendering.

The grid is a 1:1 *projection* of agents onto cells (one displayed agent per
cell). This keeps the core metaphor clear: you watch individuals live under the
rules.

When the population exceeds the grid, we show a **deterministic sampled snapshot
of part of the population** (stable for a given seed and population) and always
display real totals separately. This avoids misleading averaging and keeps
state changes legible.

Rendering uses a CSS grid with fluid, equal-width cells. Offline agents are
rendered as empty cells so the board geometry stays stable.
"""

from __future__ import annotations

import html
from collections import Counter
from dataclasses import dataclass

from .agents import ROLE_META, Agent, Role


@dataclass(frozen=True)
class Cell:
    """One rendered cell representing a single displayed agent."""

    row: int
    col: int
    role: Role
    count: int  # always 1 in 1:1 view (kept for compatibility)
    active: int  # 0 or 1

    @property
    def active_ratio(self) -> float:
        return float(self.active) if self.count else 0.0

    @property
    def label(self) -> str:
        name = ROLE_META[self.role]["label"]
        state = "active" if self.active else "offline"
        return f"{name} · cell {self.row},{self.col} · {state}"


def _stable_rank(seed: int, agent_id: int) -> int:
    """Deterministic rank for sampling (no reliance on PYTHONHASHSEED)."""
    x = (seed * 0x9E3779B1) ^ (agent_id * 0x85EBCA77)
    x &= 0xFFFFFFFF
    x ^= x >> 16
    x = (x * 0x7FEB352D) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x846CA68B) & 0xFFFFFFFF
    x ^= x >> 16
    return x


def sample_agents(agents: list[Agent], rows: int, cols: int, seed: int = 0) -> list[Agent]:
    """Deterministically select up to rows*cols agents for display."""
    capacity = max(0, rows * cols)
    if len(agents) <= capacity:
        return list(agents)
    ranked = sorted(agents, key=lambda a: (_stable_rank(seed, a.id), a.id))
    return ranked[:capacity]


def project(
    agents: list[Agent], rows: int, cols: int, *, seed: int = 0
) -> tuple[list[list[Cell | None]], dict[int, tuple[int, int]], int]:
    """Project agents onto a 1:1 grid.

    Returns (grid, display_pos_by_agent_id, sampled_count). When the population
    exceeds grid capacity, a deterministic sampled subset is displayed. Display
    placement is deterministically shuffled (stable for seed+population view) so
    the grid keeps a natural scattered look.
    """
    import random as _random

    displayed = sample_agents(agents, rows, cols, seed)
    sampled_count = len(displayed)
    grid: list[list[Cell | None]] = [[None] * cols for _ in range(rows)]
    display_pos: dict[int, tuple[int, int]] = {}

    # Deterministic random-looking placement (local RNG, does not touch sim state).
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    _random.Random(seed ^ 0x5F3759DF).shuffle(cells)

    for idx, agent in enumerate(displayed):
        if idx >= len(cells):
            break
        r, c = cells[idx]
        display_pos[agent.id] = (r, c)
        grid[r][c] = Cell(
            row=r,
            col=c,
            role=agent.role,
            count=1,
            active=1 if agent.active else 0,
        )

    return grid, display_pos, sampled_count


def render_html(
    grid: list[list[Cell | None]],
    *,
    ascii_mode: bool = False,
    show_titles: bool = True,
    active_cells: set[tuple[int, int]] | None = None,
    tick: int = 0,
) -> str:
    """Turn a projected grid into a self-contained HTML fragment."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    parts: list[str] = [
        (
            f'<div class="fc-grid" data-tick="{tick}" style="--fc-cols:{cols};--fc-rows:{rows}" role="img" '
            f'aria-label="Simulated network grid, {rows} by {cols} cells">'
        )
    ]

    active = active_cells or set()
    for row_idx, row in enumerate(grid):
        for col_idx, cell in enumerate(row):
            produced = (row_idx, col_idx) in active

            if cell is None:
                classes = ["fc-cell", "fc-slot"]
                if produced:
                    classes.append("fc-produced")
                parts.append(
                    f'<span class="{" ".join(classes)}" aria-label="empty slot">·</span>'
                )
                continue

            if cell.active == 0:
                title = f' title="{html.escape(cell.label)}"' if show_titles else ""
                classes = ["fc-cell", "fc-empty"]
                if produced:
                    classes.append("fc-produced")
                parts.append(
                    f'<span class="{" ".join(classes)}" aria-label="offline"{title}></span>'
                )
                continue

            meta = ROLE_META[cell.role]
            glyph = meta["ascii"] if ascii_mode else meta["emoji"]
            classes = ["fc-cell", f"fc-{meta['css']}"]
            if produced:
                classes.append("fc-produced")

            opacity = 0.35 + 0.65 * cell.active_ratio
            title = f' title="{html.escape(cell.label)}"' if show_titles else ""
            parts.append(
                f'<span class="{" ".join(classes)}" style="opacity:{opacity:.2f}"{title}>'
                f"{glyph}</span>"
            )

    parts.append("</div>")
    return "".join(parts)


def population_summary(
    agents: list[Agent], rows: int, cols: int, *, sampled: int | None = None
) -> str:
    """The sentence that must always accompany the grid."""
    cells = rows * cols
    population = len(agents)
    inactive = sum(1 for agent in agents if not agent.active)
    hidden = f" · {inactive:,} offline (hidden)" if inactive else " · all active"
    if sampled is not None and sampled < population:
        return (
            f"{population:,} agents · showing {sampled:,} of {cells:,} cells "
            f"(1:1 sampled view, deterministic){hidden}"
        )
    return f"{population:,} agents · {cells:,} cells · 1 agent per cell{hidden}"


def legend_html(
    total: Counter[Role] | None = None,
    active: Counter[Role] | None = None,
) -> str:
    """A compact legend with optional live online/total counts."""
    items: list[str] = []
    for role, meta in ROLE_META.items():
        count = ""
        if total is not None and total.get(role, 0):
            online = active.get(role, 0) if active is not None else total[role]
            count = f' <span class="fc-legend-count">{online}/{total[role]}</span>'
        items.append(
            f'<span class="fc-legend-item">'
            f'<span class="fc-cell fc-{meta["css"]}">{meta["emoji"]}</span>'
            f"{meta['label']}{count}</span>"
        )
    items.append(
        '<span class="fc-legend-item"><span class="fc-cell fc-slot">·</span>'
        "no agent</span>"
    )
    items.append(
        '<span class="fc-legend-item"><span class="fc-cell fc-empty"></span>'
        "offline (hidden)</span>"
    )
    return f'<div class="fc-legend">{"".join(items)}</div>'
