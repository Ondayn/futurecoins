"""Achievements: pure predicates, idempotence, persistence, snapshots."""

from __future__ import annotations

import random
from datetime import UTC, datetime

from futurecoins.achievements import (
    AchievementManager,
    RunSummary,
    crisis_survivor,
    decode_snapshot,
    encode_snapshot,
    first_currency,
    genesis_discovery,
    network_architect,
    survivor,
)
from futurecoins.agents import make_population
from futurecoins.config import BITCOIN_2009
from futurecoins.events import EventLogEntry
from futurecoins.metrics import Metrics


def _metrics(
    *,
    tick: int = 1,
    active: int = 10,
    total: int = 10,
    participation: float = 1.0,
    health: float = 80.0,
) -> Metrics:
    return Metrics(
        tick=tick,
        active_nodes=active,
        total_nodes=total,
        participation=participation,
        health=health,
    )


def _summary(**overrides) -> RunSummary:
    defaults = {
        "tick": 1,
        "metrics": _metrics(),
        "config": BITCOIN_2009,
        "history": (_metrics(),),
        "events": (),
        "discovery_score": None,
        "snapshot": "",
    }
    defaults.update(overrides)
    return RunSummary(**defaults)


def test_first_currency_requires_a_tick_and_an_active_agent() -> None:
    assert not first_currency(_summary(tick=0, metrics=_metrics(active=10)))
    assert not first_currency(_summary(tick=1, metrics=_metrics(active=0)))
    assert first_currency(_summary(tick=1, metrics=_metrics(active=1)))


def test_survivor_requires_a_full_simulated_year() -> None:
    assert not survivor(_summary(tick=1824, metrics=_metrics(health=50.0)))
    assert survivor(_summary(tick=1825, metrics=_metrics(health=1.0)))
    assert not survivor(_summary(tick=1825, metrics=_metrics(health=0.0)))


def test_genesis_discovery_threshold() -> None:
    assert not genesis_discovery(_summary(discovery_score=0.94))
    assert genesis_discovery(_summary(discovery_score=0.95))


def test_crisis_survivor_needs_a_severe_event_and_recovery() -> None:
    severe = EventLogEntry(
        tick=5,
        event_id="market_crash",
        name="Market Crash",
        category="economic",
        severity=0.7,
        message="crash",
    )
    healthy_after = tuple(_metrics(tick=t, health=30.0) for t in range(5, 12))
    collapsed = tuple(_metrics(tick=t, health=30.0 if t < 8 else 10.0) for t in range(5, 12))

    assert crisis_survivor(_summary(events=(severe,), history=healthy_after))
    assert not crisis_survivor(_summary(events=(severe,), history=collapsed))

    mild = EventLogEntry(
        tick=5,
        event_id="negative_media",
        name="Negative Media",
        category="social",
        severity=0.3,
        message="mild",
    )
    assert not crisis_survivor(_summary(events=(mild,), history=healthy_after))


def test_network_architect_requires_one_hundred_good_ticks() -> None:
    good = tuple(
        _metrics(tick=t, active=60, total=60, participation=0.95, health=70.0)
        for t in range(1, 101)
    )
    assert network_architect(_summary(history=good))

    bad = list(good)
    bad[-1] = _metrics(tick=100, active=60, total=60, participation=0.50, health=70.0)
    assert not network_architect(_summary(history=tuple(bad)))

    assert not network_architect(_summary(history=good[:99]))


def test_manager_awards_once_and_persists(tmp_path) -> None:
    path = tmp_path / "achievements.json"
    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)

    manager = AchievementManager(path=path, clock=clock)
    assert manager.evaluate(_summary(tick=0, metrics=_metrics(active=0))) == []

    awards = manager.evaluate(_summary(tick=1))
    assert [award.id for award in awards] == ["first_currency"]
    assert manager.has("first_currency")

    assert manager.evaluate(_summary(tick=2)) == []
    assert path.exists()

    reloaded = AchievementManager(path=path, clock=clock)
    assert reloaded.has("first_currency")
    assert reloaded.awards["first_currency"].config_hash == BITCOIN_2009.fingerprint()


def test_snapshot_is_one_character_per_cell() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    snapshot = encode_snapshot(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)

    assert len(snapshot) == BITCOIN_2009.cells
    assert set(snapshot) <= set(".MVTUDA")

    counts = decode_snapshot(snapshot)
    assert sum(bucket["active"] + bucket["inactive"] for bucket in counts.values()) > 0


def test_manager_survives_a_corrupt_file(tmp_path) -> None:
    path = tmp_path / "achievements.json"
    path.write_text("this is not json", encoding="utf-8")

    manager = AchievementManager(path=path)
    assert manager.awards == {}


def test_snapshot_counts_match_the_population() -> None:
    agents = make_population(BITCOIN_2009, random.Random(BITCOIN_2009.seed))
    snapshot = encode_snapshot(agents, BITCOIN_2009.rows, BITCOIN_2009.cols)
    counts = decode_snapshot(snapshot)
    cells = sum(bucket["active"] + bucket["inactive"] for bucket in counts.values())
    assert cells == len({(agent.row, agent.col) for agent in agents})


def test_award_records_the_config_and_metrics(tmp_path) -> None:
    manager = AchievementManager(path=tmp_path / "a.json")
    award = manager.evaluate(_summary(tick=1))[0]
    assert award.seed == BITCOIN_2009.seed
    assert award.config_hash == BITCOIN_2009.fingerprint()
    assert award.metrics["tick"] == 1
    assert award.snapshot == ""
    assert (award.rows, award.cols) == (BITCOIN_2009.rows, BITCOIN_2009.cols)


def test_predicate_false_never_awards(tmp_path) -> None:
    manager = AchievementManager(path=tmp_path / "a.json")
    assert manager.evaluate(_summary(tick=0, metrics=_metrics(active=0))) == []
    assert manager.awarded_ids == set()
    assert not (tmp_path / "a.json").exists()


def test_import_awards_merges_new_ones(tmp_path) -> None:
    path = tmp_path / "a.json"
    manager = AchievementManager(path=path)
    payload = [
        {
            "id": "first_currency",
            "name": "First Currency",
            "description": "x",
            "icon": "🪙",
            "awarded_at": "2026-01-01T00:00:00+00:00",
            "config_hash": "abc",
            "seed": 1,
            "tick": 1,
            "metrics": {},
            "snapshot": "",
            "rows": 30,
            "cols": 30,
        }
    ]
    added = manager.import_awards(payload)
    assert added == 1
    assert manager.has("first_currency")
    assert manager.import_awards(payload) == 0
