"""Sanity checks: plausible baselines should not collapse unrealistically fast.

These are *model* sanity tests (educational simulation), not claims about real
markets. They catch regressions where tuning makes a historically-inspired
baseline fail in a few ticks.
"""

from __future__ import annotations

from futurecoins.config import BITCOIN_2009
from futurecoins.engine import Simulation


def test_bitcoin_like_preset_does_not_fail_immediately() -> None:
    """A Bitcoin 2009-like preset should not 'crash'/end in the first 10 ticks.

    Early high issuance is part of a halving schedule (by design), not a sudden
    collapse. The run may be volatile, but it should remain viable initially.
    """
    sim = Simulation(BITCOIN_2009)
    sim.run(30)
    assert not sim.ended, f"Ended at tick {sim.tick}: {sim.end_reason}"
    assert sim.metrics.active_nodes > 0
    assert sim.metrics.health > 10.0, f"Health collapsed too fast: {sim.metrics.health}"


def test_bitcoin_like_preset_stays_viable_over_first_year() -> None:
    """Viability sanity check over ~1 simulated year (365 ticks)."""
    sim = Simulation(BITCOIN_2009)
    sim.run(365)
    assert not sim.ended, f"Ended at tick {sim.tick}: {sim.end_reason}"
    assert sim.metrics.active_nodes >= max(1, sim.metrics.total_nodes // 10)