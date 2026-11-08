"""Grid projection and HTML rendering."""

from __future__ import annotations

import random
from collections import Counter

from futurecoins.agents import Agent, Role, make_population
from futurecoins.config import BITCOIN_2009, CHAOS_SANDBOX
from futurecoins.grid import (
    legend_html,
    population_summary,
    project,
    render_html,
)


def test_projection_has_the_requested_dimensions() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid = project(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)

    assert len(grid) == BITCOIN_2009.rows
    assert all(len(row) == BITCOIN_2009.cols for row in grid)


def test_every_agent_is_projected_exactly_once() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid = project(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)

    total = sum(cell.count for row in grid for cell in row if cell is not None)
    assert total == len(agents)


def test_cohorts_appear_when_population_exceeds_cells() -> None:
    agents = make_population(CHAOS_SANDBOX, random.Random(CHAOS_SANDBOX.seed))
    assert len(agents) > CHAOS_SANDBOX.cells

    grid = project(agents, CHAOS_SANDBOX.rows, CHAOS_SANDBOX.cols)
    counts = [cell.count for row in grid for cell in row if cell is not None]
    assert max(counts) >= 2
    assert sum(counts) == len(agents)


def test_html_has_one_cell_per_grid_slot() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid = project(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    html = render_html(grid)

    assert "fc-grid" in html
    assert html.count("fc-cell") == BITCOIN_2009.cells
    assert f"--fc-cols:{BITCOIN_2009.cols}" in html


def test_population_is_always_shown_separately_from_cells() -> None:
    agents = make_population(CHAOS_SANDBOX, random.Random(CHAOS_SANDBOX.seed))
    summary = population_summary(agents, CHAOS_SANDBOX.rows, CHAOS_SANDBOX.cols)

    assert f"{len(agents):,} agents" in summary
    assert f"{CHAOS_SANDBOX.cells:,} cells" in summary
    assert "cohorts" in summary


def test_population_summary_reports_hidden_offline_agents() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    for agent in agents[:7]:
        agent.active = False

    summary = population_summary(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    assert "7 offline (hidden)" in summary


def test_offline_cells_are_blank() -> None:
    """A cell whose whole cohort is offline must not show a role glyph."""
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    for agent in agents:
        agent.active = False

    grid = project(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    html = render_html(grid)

    assert "fc-miner" not in html
    assert "fc-user" not in html
    assert html.count("fc-empty") == len(agents)
    # Slots with no agent at all keep a faint dot.
    assert html.count("fc-slot") == BITCOIN_2009.cells - len(agents)


def test_partly_active_cohort_shows_an_active_role() -> None:
    """If one role in a cohort is offline, the cell shows a role that is online."""
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    first = agents[0]
    # Give this cell a second, offline agent of a different role.
    first.active = True
    mate = Agent(
        id=len(agents),
        role=Role.ATTACKER,
        row=first.row,
        col=first.col,
        active=False,
    )
    grid = project([first, mate], BITCOIN_2009.rows, BITCOIN_2009.cols)
    cell = grid[first.row][first.col]

    assert cell is not None
    assert cell.active == 1
    assert cell.role is first.role
    assert "fc-attacker" not in render_html(grid)


def test_single_agent_per_cell_message() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    summary = population_summary(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    assert "1 agent per cell" in summary


def test_ascii_fallback_uses_letters() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid = project(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    html = render_html(grid, ascii_mode=True)

    assert "⛏" not in html
    assert "M" in html or "u" in html or "T" in html


def test_legend_lists_every_role() -> None:
    html = legend_html()
    for label in ("Miner", "Validator", "User", "Trader", "Developer", "Attacker"):
        assert label in html


def test_legend_carries_the_live_role_counts() -> None:
    """The legend replaces a second caption, so it must show online/total."""
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    agents[0].active = False
    total = Counter(agent.role for agent in agents)
    active = Counter(agent.role for agent in agents if agent.active)
    html = legend_html(total, active)

    for role, count in total.items():
        assert f"{active[role]}/{count}" in html
