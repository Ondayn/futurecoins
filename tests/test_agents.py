"""Agents: counts, placement, balances, determinism."""

from __future__ import annotations

import random

import pytest

from futurecoins.agents import Role, active_agents, make_population, role_counts
from futurecoins.config import BITCOIN_2009, PRESETS, SOLANA_2020


def test_role_counts_follow_consensus() -> None:
    pow_counts = role_counts(BITCOIN_2009)
    assert pow_counts[Role.MINER] == BITCOIN_2009.agents.n_miners
    assert pow_counts[Role.VALIDATOR] == 0

    pos_counts = role_counts(SOLANA_2020)
    assert pos_counts[Role.VALIDATOR] == SOLANA_2020.agents.n_validators
    assert pos_counts[Role.MINER] == 0


def test_population_has_contiguous_ids_and_valid_cells() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))

    assert len(agents) == BITCOIN_2009.population
    assert [agent.id for agent in agents] == list(range(len(agents)))
    assert all(0 <= agent.row < BITCOIN_2009.rows for agent in agents)
    assert all(0 <= agent.col < BITCOIN_2009.cols for agent in agents)


def test_genesis_balances_conserve_the_distributable_supply() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    expected = BITCOIN_2009.monetary.initial_supply * (
        1.0 - BITCOIN_2009.monetary.treasury_fraction
    )
    assert sum(agent.balance for agent in agents) == pytest.approx(expected)


def test_population_is_deterministic() -> None:
    first = make_population(BITCOIN_2009, random.Random(1234))
    second = make_population(BITCOIN_2009, random.Random(1234))

    first_view = [(a.id, a.role, a.row, a.col, round(a.balance, 6)) for a in first]
    second_view = [(a.id, a.role, a.row, a.col, round(a.balance, 6)) for a in second]
    assert first_view == second_view


def test_different_seeds_place_agents_differently() -> None:
    first = make_population(BITCOIN_2009, random.Random(1))
    second = make_population(BITCOIN_2009, random.Random(2))
    assert [(a.row, a.col) for a in first] != [(a.row, a.col) for a in second]


def test_active_agents_filters_by_role() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    for agent in agents:
        if agent.role is Role.USER:
            agent.active = False

    assert active_agents(agents, Role.USER) == []
    assert len(active_agents(agents)) == BITCOIN_2009.population - BITCOIN_2009.agents.n_users


def test_every_preset_can_build_a_population() -> None:
    for config in PRESETS.values():
        agents = make_population(config, random.Random(config.seed))
        assert len(agents) == config.population
