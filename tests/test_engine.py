"""The engine: conservation, determinism, lifecycle, cooldown."""

from __future__ import annotations

import time

import pytest

from futurecoins.agents import Role
from futurecoins.config import BITCOIN_2009, CHAOS_SANDBOX
from futurecoins.engine import Simulation


def test_supply_is_conserved_across_balances_treasury_and_burns() -> None:
    sim = Simulation(BITCOIN_2009)
    sim.run(200)

    held = sum(agent.balance for agent in sim.agents)
    accounted = held + sim.treasury + sim.burn_total
    minted = BITCOIN_2009.monetary.initial_supply + sim.issuance_total

    assert accounted == pytest.approx(minted, rel=1e-9, abs=1e-6)
    assert sim.total_supply == pytest.approx(
        BITCOIN_2009.monetary.initial_supply + sim.issuance_total - sim.burn_total
    )


def test_population_is_never_created_or_destroyed() -> None:
    sim = Simulation(BITCOIN_2009)
    before = len(sim.agents)
    sim.run(100)
    assert len(sim.agents) == before
    assert [agent.id for agent in sim.agents] == list(range(before))


def test_same_seed_reproduces_the_exact_history() -> None:
    first = Simulation(BITCOIN_2009)
    second = Simulation(BITCOIN_2009)

    first.run(150)
    second.run(150)

    assert [m.as_dict() for m in first.history] == [m.as_dict() for m in second.history]
    assert first.total_supply == second.total_supply
    assert first.event_history == second.event_history


def test_different_seeds_produce_different_runs() -> None:
    first = Simulation(BITCOIN_2009)
    second = Simulation(BITCOIN_2009)

    # Only the random generator differs, not the rules.
    second.rng.seed(999_999)

    first.run(50)
    second.run(50)
    assert [m.price for m in first.history] != [m.price for m in second.history]


def test_reset_returns_to_the_initial_state() -> None:
    sim = Simulation(BITCOIN_2009)
    fresh = Simulation(BITCOIN_2009)

    sim.run(25)
    sim.reset()

    assert sim.tick == 0
    assert len(sim.history) == 1
    assert sim.metrics.as_dict() == fresh.metrics.as_dict()
    assert [a.balance for a in sim.agents] == [a.balance for a in fresh.agents]


def test_forced_exit_survives_the_next_tick() -> None:
    """A shock must not be undone immediately by the normal entry rule."""
    sim = Simulation(BITCOIN_2009)
    sim.run(5)

    sim._force_producer_exit(0.25)
    forced_offline = {
        agent.id for agent in sim.agents if agent.is_producer and not agent.active
    }
    assert forced_offline

    sim.run_tick()

    still_offline = {
        agent.id
        for agent in sim.agents
        if agent.id in forced_offline and not agent.active
    }
    assert still_offline == forced_offline


def test_events_are_recorded_in_a_history() -> None:
    sim = Simulation(CHAOS_SANDBOX)
    sim.run(200)
    assert len(sim.event_history) >= 1
    assert all(event.message for event in sim.event_history)
    assert all(event.tick >= 1 for event in sim.event_history)


def test_500_ticks_are_fast_enough_for_a_live_demo() -> None:
    sim = Simulation(BITCOIN_2009)
    started = time.perf_counter()
    sim.run(500)
    elapsed = time.perf_counter() - started
    assert elapsed < 10.0, f"500 ticks took {elapsed:.2f}s"


def test_network_ends_when_every_agent_is_offline() -> None:
    sim = Simulation(BITCOIN_2009)
    sim.run(3)

    for agent in sim.agents:
        agent.active = False
        agent.streak_good = 0
        agent.streak_bad = 0

    assert sim.is_dead
    sim.run_tick()

    assert sim.ended
    assert sim.active_nodes == 0
    assert "network ended" in sim.recent_changes[-1]
    assert sim.end_reason


def test_ended_network_does_not_advance() -> None:
    sim = Simulation(BITCOIN_2009)
    for agent in sim.agents:
        agent.active = False
    sim.run_tick()
    tick = sim.tick

    assert sim.ended
    assert sim.run(10) == []
    assert sim.run_tick().tick == tick
    assert sim.tick == tick


def test_reset_revives_an_ended_network() -> None:
    sim = Simulation(BITCOIN_2009)
    for agent in sim.agents:
        agent.active = False
    sim.run_tick()
    assert sim.ended

    sim.reset()

    assert not sim.ended
    assert sim.end_reason == ""
    assert sim.active_nodes == len(sim.agents)
    assert sim.tick == 0


def test_followers_leave_a_collapsing_market() -> None:
    """Traders and developers must be able to go offline too, otherwise the
    "everyone is dead" ending could never be reached."""
    sim = Simulation(BITCOIN_2009)
    sim.economy.sentiment = 0.0

    for _ in range(BITCOIN_2009.agents.exit_patience_ticks):
        sim._update_follower_behaviour()

    offline = {agent.role for agent in sim.agents if not agent.active}
    assert Role.TRADER in offline
    assert Role.DEVELOPER in offline
