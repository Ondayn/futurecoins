"""Grid projection and HTML rendering (1:1 view, deterministic sampling)."""

from __future__ import annotations

import random
from collections import Counter

from futurecoins.agents import make_population
from futurecoins.config import BITCOIN_2009, CHAOS_SANDBOX
from futurecoins.grid import (
    legend_html,
    population_summary,
    project,
    render_html,
)


def _grid(agents, rows, cols, seed=0):
    grid, _pos, sampled = project(agents, rows, cols, seed=seed)
    return grid, sampled


def test_projection_has_the_requested_dimensions() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid, _ = _grid(agents, BITCOIN_2009.rows, BITCOIN_2009.cols, BITCOIN_2009.seed)

    assert len(grid) == BITCOIN_2009.rows
    assert all(len(row) == BITCOIN_2009.cols for row in grid)


def test_every_agent_displayed_when_population_fits() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid, sampled = _grid(agents, BITCOIN_2009.rows, BITCOIN_2009.cols, BITCOIN_2009.seed)

    total = sum(cell.count for row in grid for cell in row if cell is not None)
    assert sampled == len(agents)
    assert total == len(agents)


def test_sampling_when_population_exceeds_cells() -> None:
    agents = make_population(CHAOS_SANDBOX, random.Random(CHAOS_SANDBOX.seed))
    assert len(agents) > CHAOS_SANDBOX.cells

    grid, sampled = _grid(agents, CHAOS_SANDBOX.rows, CHAOS_SANDBOX.cols, CHAOS_SANDBOX.seed)
    cells_filled = [cell for row in grid for cell in row if cell is not None]
    assert sampled == CHAOS_SANDBOX.cells
    assert len(cells_filled) == CHAOS_SANDBOX.cells
    assert all(cell.count == 1 for cell in cells_filled)  # 1:1, no cohorts


def test_html_has_one_cell_per_grid_slot() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid, _ = _grid(agents, BITCOIN_2009.rows, BITCOIN_2009.cols, BITCOIN_2009.seed)
    html = render_html(grid)

    assert "fc-grid" in html
    assert html.count("fc-cell") == BITCOIN_2009.cells
    assert f"--fc-cols:{BITCOIN_2009.cols}" in html


def test_population_summary_reports_sampled_view() -> None:
    agents = make_population(CHAOS_SANDBOX, random.Random(CHAOS_SANDBOX.seed))
    _, sampled = _grid(agents, CHAOS_SANDBOX.rows, CHAOS_SANDBOX.cols, CHAOS_SANDBOX.seed)
    summary = population_summary(
        agents, CHAOS_SANDBOX.rows, CHAOS_SANDBOX.cols, sampled=sampled
    )

    assert f"{len(agents):,} agents" in summary
    assert "sampled view" in summary
    assert "cohorts" not in summary


def test_population_summary_reports_hidden_offline_agents() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    for agent in agents[:7]:
        agent.active = False

    summary = population_summary(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    assert "7 offline (hidden)" in summary


def test_offline_displayed_agents_are_blank() -> None:
    """Displayed agents that are offline must not show a role glyph."""
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    for agent in agents:
        agent.active = False

    grid, sampled = _grid(agents, BITCOIN_2009.rows, BITCOIN_2009.cols, BITCOIN_2009.seed)
    html = render_html(grid)

    assert "fc-miner" not in html
    assert "fc-user" not in html
    assert html.count("fc-empty") == sampled
    assert html.count("fc-slot") == BITCOIN_2009.cells - sampled


def test_single_agent_per_cell_message() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    _, sampled = _grid(agents, BITCOIN_2009.rows, BITCOIN_2009.cols, BITCOIN_2009.seed)
    summary = population_summary(
        agents, BITCOIN_2009.rows, BITCOIN_2009.cols, sampled=sampled
    )
    assert "1 agent per cell" in summary


def test_ascii_fallback_uses_letters() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    grid, _ = _grid(agents, BITCOIN_2009.rows, BITCOIN_2009.cols, BITCOIN_2009.seed)
    html = render_html(grid, ascii_mode=True)

    assert "⛏" not in html
    assert "M" in html or "u" in html or "T" in html


def test_legend_lists_every_role() -> None:
    html = legend_html()
    for label in ("Miner", "Validator", "User", "Trader", "Developer", "Attacker"):
        assert label in html


def test_legend_carries_the_live_role_counts() -> None:
    """Legend shows real online/total counts."""
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    agents[0].active = False
    total = Counter(agent.role for agent in agents)
    active = Counter(agent.role for agent in agents if agent.active)
    html = legend_html(total, active)

    for role, count in total.items():
        assert f"{active[role]}/{count}" in html
