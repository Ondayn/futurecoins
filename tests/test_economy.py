"""Economy: demand, fees, price bounds, sentiment, adoption."""

from __future__ import annotations

import random

import pytest

from futurecoins.agents import Role, make_population
from futurecoins.config import BITCOIN_2009
from futurecoins.economy import (
    EconomyState,
    clamp,
    generate_demand,
    settle_mempool,
    trader_pressure,
    update_economy,
)


def test_clamp() -> None:
    assert clamp(5.0, 0.0, 1.0) == 1.0
    assert clamp(-5.0, 0.0, 1.0) == 0.0
    assert clamp(0.4, 0.0, 1.0) == 0.4


def test_demand_scales_with_users_and_sentiment() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    low = generate_demand(BITCOIN_2009, agents, sentiment=0.1, adoption=1.0)
    high = generate_demand(BITCOIN_2009, agents, sentiment=0.9, adoption=1.0)
    assert high > low

    for agent in agents:
        if agent.role is Role.USER:
            agent.active = False
    assert generate_demand(BITCOIN_2009, agents, sentiment=0.9, adoption=1.0) == 0.0


def test_congestion_raises_fees_and_reduces_demand() -> None:
    calm = settle_mempool(BITCOIN_2009, demand=100.0, capacity=10_000.0)
    busy = settle_mempool(BITCOIN_2009, demand=12_000.0, capacity=10_000.0)
    jammed = settle_mempool(BITCOIN_2009, demand=50_000.0, capacity=10_000.0)

    assert calm.fee < busy.fee < jammed.fee
    assert jammed.included <= 10_000.0
    assert jammed.dropped > 0.0
    assert jammed.utilisation == pytest.approx(1.0)


def test_mempool_never_returns_negative_values() -> None:
    outcome = settle_mempool(BITCOIN_2009, demand=0.0, capacity=0.0)
    assert outcome.included == 0.0
    assert outcome.dropped == 0.0
    assert outcome.fee == pytest.approx(BITCOIN_2009.network.base_fee)


def test_price_stays_inside_the_documented_clamp() -> None:
    state = EconomyState(price=100.0, sentiment=0.55, adoption=1.0)
    rng = random.Random(7)

    for _ in range(5_000):
        update_economy(
            state,
            BITCOIN_2009,
            health=60.0,
            utilisation=0.5,
            reliability=0.9,
            inflation_fraction=0.01,
            price_shock=0.0,
            sentiment_shock=0.0,
            trader_pressure=0.0,
            rng=rng,
        )

    assert 1.0 <= state.price <= 100_000.0
    assert 0.0 <= state.sentiment <= 1.0
    assert 0.2 <= state.adoption <= 3.0
    assert state.volatility >= 0.0


def test_price_is_mean_reverting_not_exploding() -> None:
    """A healthy network should not turn 100 into 100,000 in a thousand ticks."""
    state = EconomyState(price=100.0, sentiment=0.55, adoption=1.0)
    rng = random.Random(11)

    for _ in range(1_000):
        update_economy(
            state,
            BITCOIN_2009,
            health=60.0,
            utilisation=0.5,
            reliability=0.9,
            inflation_fraction=0.01,
            price_shock=0.0,
            sentiment_shock=0.0,
            trader_pressure=0.0,
            rng=rng,
        )

    assert 10.0 < state.price < 1_000.0


def test_trader_pressure_needs_traders() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    assert trader_pressure(agents, BITCOIN_2009, momentum=0.1) != 0.0

    for agent in agents:
        if agent.role is Role.TRADER:
            agent.active = False
    assert trader_pressure(agents, BITCOIN_2009, momentum=0.1) == 0.0
