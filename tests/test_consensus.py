"""Consensus: halving, caps, reward shares, PoS availability."""

from __future__ import annotations

import random
from dataclasses import replace

import pytest

from futurecoins.agents import Role, make_population
from futurecoins.config import BITCOIN_2009, NEVER, SOLANA_2020
from futurecoins.consensus import (
    availability,
    current_block_reward,
    produce,
    security_margin,
)


def test_halving_is_exact_at_every_boundary() -> None:
    interval = BITCOIN_2009.monetary.halving_interval_blocks
    assert current_block_reward(BITCOIN_2009, 0) == pytest.approx(50.0)
    assert current_block_reward(BITCOIN_2009, interval - 1) == pytest.approx(50.0)
    assert current_block_reward(BITCOIN_2009, interval) == pytest.approx(25.0)
    assert current_block_reward(BITCOIN_2009, interval * 2) == pytest.approx(12.5)
    assert current_block_reward(BITCOIN_2009, interval * 10) == pytest.approx(50.0 / 1024)


def test_never_halving_keeps_the_initial_reward() -> None:
    config = replace(
        BITCOIN_2009,
        monetary=replace(BITCOIN_2009.monetary, halving_interval_blocks=NEVER),
    )
    assert current_block_reward(config, 10**9) == pytest.approx(50.0)


def test_pow_reward_shares_sum_to_issuance() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    production = produce(
        BITCOIN_2009,
        agents,
        total_blocks=0,
        total_supply=0,
        fees_pool=10.0,
    )

    assert sum(production.reward_by_agent.values()) == pytest.approx(production.issuance)
    assert sum(production.fees_by_agent.values()) == pytest.approx(
        production.distributable_fees
    )
    assert production.concentration > 0.0
    assert production.issuance > 0.0


def test_hard_cap_stops_issuance_without_destroying_tokens() -> None:
    config = replace(
        BITCOIN_2009,
        monetary=replace(BITCOIN_2009.monetary, max_supply=1_000.0),
    )
    agents = make_population(config, random.Random(config.seed))

    production = produce(config, agents, total_blocks=0, total_supply=990.0, fees_pool=0.0)

    assert production.issuance == pytest.approx(10.0)
    assert production.issuance >= 0.0


def test_no_cap_means_no_headroom_limit() -> None:
    config = replace(
        BITCOIN_2009,
        monetary=replace(BITCOIN_2009.monetary, max_supply=None),
    )
    agents = make_population(config, random.Random(config.seed))
    production = produce(config, agents, total_blocks=0, total_supply=0.0, fees_pool=0.0)
    assert production.issuance == pytest.approx(
        config.blocks_per_tick * config.monetary.initial_block_reward
    )


def test_pos_availability_falls_with_offline_stake() -> None:
    agents = make_population(SOLANA_2020, random.Random(SOLANA_2020.seed))
    assert availability(SOLANA_2020, agents) == pytest.approx(1.0, abs=1e-6)

    validators = [agent for agent in agents if agent.role is Role.VALIDATOR]
    for agent in validators[len(validators) // 2 :]:
        agent.active = False

    assert 0.45 <= availability(SOLANA_2020, agents) <= 0.55


def test_pow_availability_is_one_even_when_miners_leave() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    for agent in agents:
        if agent.role is Role.MINER:
            agent.active = False
    assert availability(BITCOIN_2009, agents) == 1.0


def test_security_margin_is_bounded() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    assert 0.0 <= security_margin(BITCOIN_2009, agents, 1.0) <= 1.0

    pos_agents = make_population(SOLANA_2020, random.Random(SOLANA_2020.seed))
    assert 0.0 <= security_margin(SOLANA_2020, pos_agents, 0.5) <= 1.0


def test_no_producers_means_no_blocks() -> None:
    config = replace(BITCOIN_2009, agents=replace(BITCOIN_2009.agents, n_miners=0))
    agents = make_population(config, random.Random(config.seed))
    production = produce(config, agents, total_blocks=0, total_supply=0, fees_pool=0)
    assert production.blocks == 0.0
    assert production.issuance == 0.0
