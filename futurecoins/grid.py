"""Grid projection and HTML rendering.

The grid is a *projection* of the agent population, not the simulation itself.
When there are more agents than cells, a cell represents a **cohort** and shows
the dominant role. The real population is always displayed separately, because
confusing "800 cells" with "800 agents" is the easiest way to teach the wrong
lesson.

Rendering is a CSS grid with fluid, equal-width cells. Emoji are not
monospaced, so a plain string grid drifts; a fixed cell box removes the problem
entirely. Offline agents are rendered as empty cells: the grid only shows who is
actually online, and a cell with no active agent leaves a blank slot so the
board geometry stays stable.
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
        if self.active == 0:
            return (
                f"{self.count} offline agent{'s' if self.count != 1 else ''} · "
                f"cell {self.row},{self.col} · hidden from the grid"
            )
        if self.count == 1:
            return f"{name} · cell {self.row},{self.col} · active"
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
        # Show the dominant *active* role, so a cell never displays a role that
        # is entirely offline while another role in the same cohort is working.
        online = [a for a in group if a.active]
        visible = online or group
        counts = Counter(a.role for a in visible)
        # Deterministic tie-break: most common role, then fixed role order.
        dominant = min(
            counts.items(),
            key=lambda item: (-item[1], _ROLE_ORDER[item[0]]),
        )[0]
        grid[row][col] = Cell(
            row=row, col=col, role=dominant, count=len(group), active=len(online)
        )

    return grid


def render_html(
    grid: list[list[Cell | None]],
    *,
    ascii_mode: bool = False,
    show_titles: bool = True,
    active_cells: set[tuple[int, int]] | None = None,
    tick: int = 0,
) -> str:
    """Turn a projected grid into a self-contained HTML fragment.

    ``active_cells`` are the (row, col) positions that produced a block this
    tick. They are highlighted so the board shows *activity*, not just state:
    a network that is running but doing nothing would otherwise look frozen.
    """
    """Turn a projected grid into a self-contained HTML fragment.

    The caller (Streamlit) only has to pass this string to `st.html`. No
    Streamlit import lives in this file.
    """
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

            # Three visual states:
            #   no agent assigned -> faint dot (the slot exists but is empty)
            #   agent offline     -> fully blank (the agent has disappeared)
            #   agent online      -> role glyph
            # Keeping the two empty states distinct stops an underpopulated
            # board from looking like a dead network.
            if cell is None:
                classes = ["fc-cell", "fc-slot"]
                if produced:
                    classes.append("fc-produced")
                parts.append(
                    f'<span class="{" ".join(classes)}" aria-label="empty slot">·</span>'
                )
                continue

            if cell.active == 0:
                title = (
                    f' title="{html.escape(cell.label)}"' if show_titles else ""
                )
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
    inactive = sum(1 for agent in agents if not agent.active)
    hidden = f" · {inactive:,} offline (hidden)" if inactive else " · all active"
    if population <= cells:
        return f"{population:,} agents · {cells:,} cells · 1 agent per cell{hidden}"
    per_cell = population / cells
    return (
        f"{population:,} agents · {cells:,} cells · "
        f"~{per_cell:.1f} agents per cell (cohorts){hidden}"
    )


def legend_html(
    total: Counter[Role] | None = None,
    active: Counter[Role] | None = None,
) -> str:
    """A compact legend, generated from the same role metadata as the grid.

    When live counts are supplied, each role also shows ``online/total``. That
    turns the legend into the role breakdown, so the interface does not need a
    second caption line under the board.
    """
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
