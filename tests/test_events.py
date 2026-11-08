"""Events: declarative conditions, triggering, expiry, severity scaling."""

from __future__ import annotations

import random
from dataclasses import replace

from futurecoins.agents import make_population
from futurecoins.config import BITCOIN_2009, EventParams
from futurecoins.events import Condition, EventEngine


def _config(**event_overrides):
    defaults = {
        "enabled": True,
        "probability_scale": 1.0,
        "crash_probability": 0.0,
        "congestion_probability": 0.0,
        "media_probability": 0.0,
        "exodus_probability": 0.0,
    }
    defaults.update(event_overrides)
    return replace(BITCOIN_2009, events=EventParams(**defaults))


def _metrics(**overrides):
    base = {
        "health": 50.0,
        "participation": 1.0,
        "sentiment": 0.5,
        "congestion": 0.0,
        "avg_fee": 0.01,
        "dropped_txs": 0.0,
    }
    base.update(overrides)
    return base


def test_condition_operators() -> None:
    assert Condition("health", "<", 50.0).holds({"health": 49.0})
    assert not Condition("health", "<", 50.0).holds({"health": 50.0})
    assert Condition("health", "<=", 50.0).holds({"health": 50.0})
    assert Condition("health", ">", 50.0).holds({"health": 51.0})
    assert Condition("health", ">=", 50.0).holds({"health": 50.0})
    assert not Condition("missing", ">", 0.0).holds({"health": 50.0})


def test_probability_one_triggers_a_market_crash() -> None:
    config = _config(crash_probability=1.0)
    engine = EventEngine(config)
    agents = make_population(config, random.Random(config.seed))

    outcome = engine.step(1, _metrics(), agents, random.Random(1))

    assert len(outcome.entries) == 1
    assert outcome.entries[0].event_id == "market_crash"
    assert "market_crash" in engine.active
    assert outcome.modifiers.price_shock < 0.0


def test_disabled_events_never_trigger() -> None:
    config = _config(enabled=False, crash_probability=1.0)
    engine = EventEngine(config)
    agents = make_population(config, random.Random(config.seed))

    outcome = engine.step(1, _metrics(), agents, random.Random(1))

    assert outcome.entries == ()
    assert engine.active == {}


def test_conditions_gate_congestion() -> None:
    config = _config(congestion_probability=1.0)
    engine = EventEngine(config)
    agents = make_population(config, random.Random(config.seed))

    quiet = engine.step(1, _metrics(congestion=0.1), agents, random.Random(1))
    assert quiet.entries == ()

    busy = engine.step(2, _metrics(congestion=0.9), agents, random.Random(2))
    assert [entry.event_id for entry in busy.entries] == ["network_congestion"]
    assert busy.modifiers.capacity < 1.0


def test_events_expire_after_their_duration() -> None:
    config = _config(crash_probability=1.0)
    engine = EventEngine(config)
    agents = make_population(config, random.Random(config.seed))

    engine.step(1, _metrics(), agents, random.Random(1))
    assert engine.active

    # Stop new events so we can observe the expiry of this one.
    engine.config = _config(crash_probability=0.0)
    for tick in range(2, 8):
        engine.step(tick, _metrics(), agents, random.Random(tick))

    assert engine.active == {}


def test_validator_exodus_is_worse_in_a_fragile_network() -> None:
    engine = EventEngine(BITCOIN_2009)
    spec = next(s for s in engine.specs if s.id == "validator_exodus")

    fragile = engine._severity(spec, {"participation": 0.2})
    healthy = engine._severity(spec, {"participation": 1.0})

    assert 0.0 <= healthy < fragile <= 1.0


def test_producer_exit_fraction_is_bounded() -> None:
    from futurecoins.events import ActiveEvent

    engine = EventEngine(BITCOIN_2009)
    spec = next(s for s in engine.specs if s.id == "validator_exodus")
    engine.active[spec.id] = ActiveEvent(
        spec=spec, severity=1.0, ticks_left=3, started_tick=0
    )

    assert 0.0 <= engine._producer_exit() <= 1.0
