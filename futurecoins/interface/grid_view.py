"""Streamlit wrapper around the pure grid renderer."""

from __future__ import annotations

from collections import Counter

import streamlit as st

from ..agents import ROLE_META, Role, active_agents
from ..engine import Simulation
from ..grid import legend_html, population_summary, project, render_html


def render(sim: Simulation, *, ascii_mode: bool = False) -> None:
    """Draw the grid (1:1, sampled when population exceeds cells), population, legend."""
    config = sim.config
    projected, display_pos, sampled = project(
        sim.agents, config.rows, config.cols, seed=config.seed
    )

    # Highlight displayed cells whose agents produced a block this tick.
    active_cells: set[tuple[int, int]] = set()
    for agent_id in getattr(sim.last_production, "reward_by_agent", {}):
        pos = display_pos.get(agent_id)
        if pos is not None:
            active_cells.add(pos)

    st.html(
        render_html(
            projected,
            ascii_mode=ascii_mode,
            show_titles=True,
            active_cells=active_cells,
            tick=sim.tick,
        )
    )

    st.caption(population_summary(sim.agents, config.rows, config.cols, sampled=sampled))

    # Legend shows real live role counts (not just sampled view).
    counts = Counter(agent.role for agent in sim.agents)
    active = Counter(agent.role for agent in active_agents(sim.agents))
    st.html(legend_html(counts, active))


def render_snapshot(snapshot: str, cols: int, *, ascii_mode: bool = False) -> None:
    """Render a stored achievement snapshot as a small grid.

    A snapshot is one character per cell, which is cheap to draw. Showing the
    exact network that earned a badge makes the award feel like a record rather
    than a popup. The ``fc-grid-snapshot`` modifier keeps the archive small: the
    live board is sized for the viewport, a badge is not.
    """
    if not snapshot or cols <= 0:
        return

    rows = len(snapshot) // cols
    cells: list[str] = []
    for char in snapshot[: rows * cols]:
        # "." = no agent in that slot; lowercase = an agent that was offline
        # when the snapshot was taken. The live grid hides offline agents, so
        # the archived grid must match.
        if char == ".":
            cells.append('<span class="fc-cell fc-slot">·</span>')
            continue
        if char.islower():
            cells.append('<span class="fc-cell fc-empty"></span>')
            continue
        role = _ROLE_FROM_ASCII.get(char.upper())
        if role is None:
            cells.append('<span class="fc-cell fc-slot">·</span>')
            continue
        meta = ROLE_META[role]
        glyph = meta["ascii"] if ascii_mode else meta["emoji"]
        cells.append(f'<span class="fc-cell fc-{meta["css"]}">{glyph}</span>')

    st.html(
        f'<div class="fc-grid fc-grid-snapshot" style="--fc-cols:{cols};--fc-rows:{rows}">'
        + "".join(cells)
        + "</div>"
    )


_ROLE_FROM_ASCII: dict[str, Role] = {
    meta["ascii"].upper(): role for role, meta in ROLE_META.items()
}


__all__ = ["render", "render_snapshot"]
