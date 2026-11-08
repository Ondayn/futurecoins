"""Metrics: the numbers on the dashboard.

Every metric here is derived from simulation state. None of them is measured
from a real blockchain. The ones that are pure model outputs (price, health,
sentiment) are labelled as such in the interface.

Definitions that are easy to confuse, and therefore written down:

- block_interval : seconds between blocks, *actual* (block_time / availability)
- tps            : included transactions per second (not per tick, not per block)
- total_supply   : initial + all issuance - all burns
- circulating    : total_supply - protocol treasury (staked tokens DO count)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .economy import clamp


def compute_economic_stress(
    inflation_rate: float,
    volatility: float,
    *,
    scheduled_halving: bool = False,
    supply: float = 0.0,
    issuance: float = 0.0,
) -> float:
    """0..1 stress from bad economics (extreme inflation, instability).

    High early issuance in a *scheduled-halving* bootstrap (premine-less launch)
    is treated more gently than runaway/unscheduled inflation, so legitimate
    designs aren't mislabeled as "bad economics".
    """
    vol = clamp(volatility / 0.12, 0.0, 1.0)

    infl_raw = abs(inflation_rate)
    if scheduled_halving:
        # Bootstrap artifact: annualized % explodes when supply is tiny but issuance
        # follows a declining halving schedule. Discount that phase.
        bootstrap = 1.0
        if supply > 1e-9 and issuance > 0:
            years_of_supply = supply / (issuance * 365.0)
            if years_of_supply < 1.0:
                bootstrap = clamp(years_of_supply / 1.0, 0.05, 1.0)
        infl = clamp((infl_raw - 150.0) / 600.0, 0.0, 1.0) * bootstrap
    else:
        # Unscheduled/perpetual high issuance is a stronger "bad choice" signal.
        infl = clamp((infl_raw - 40.0) / 260.0, 0.0, 1.0)

    return clamp(0.65 * infl + 0.35 * vol, 0.0, 1.0)


@dataclass(frozen=True)
class Metrics:
    """An immutable snapshot of one tick."""

    tick: int = 0
    active_nodes: int = 0
    total_nodes: int = 0
    participation: float = 0.0

    total_supply: float = 0.0
    circulating_supply: float = 0.0
    burned_total: float = 0.0
    treasury: float = 0.0
    inflation_rate: float = 0.0

    price: float = 100.0
    volatility: float = 0.0
    sentiment: float = 0.5

    health: float = 50.0
    reliability: float = 1.0
    concentration: float = 1.0
    security: float = 0.0
    capacity_multiplier: float = 1.0
    economic_stress: float = 0.0

    block_interval: float = 0.0
    tps: float = 0.0
    avg_fee: float = 0.0
    congestion: float = 0.0
    blocks_total: float = 0.0
    dropped_txs: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def network_health(
    participation: float,
    concentration: float,
    reliability: float,
    security: float,
    sentiment: float,
    economic_stress: float = 0.0,
) -> float:
    """A 0..100 composite score for the cryptocurrency network (not internet).

    Weights (base): participation 30 %, decentralization 20 %, reliability 25 %,
    security 15 %, sentiment 10 %. Bad economic choices (extreme inflation,
    instability) apply an economic stress penalty so unhealthy designs don't read
    as perfectly healthy.
    """
    decentralization = clamp(1.0 - concentration, 0.0, 1.0)
    base = 100.0 * (
        0.30 * clamp(participation, 0.0, 1.0)
        + 0.20 * decentralization
        + 0.25 * clamp(reliability, 0.0, 1.0)
        + 0.15 * clamp(security, 0.0, 1.0)
        + 0.10 * clamp(sentiment, 0.0, 1.0)
    )
    stress = clamp(economic_stress, 0.0, 1.0)
    # Economic stress penalizes health, but mild stress acts as a warning signal
    # rather than collapsing otherwise-viable configs. Severe stress still hurts.
    penalty = 0.35 * (stress ** 1.5)
    health = base * (1.0 - penalty)
    return clamp(health, 0.0, 100.0)


def health_breakdown(
    participation: float,
    concentration: float,
    reliability: float,
    security: float,
    sentiment: float,
    economic_stress: float = 0.0,
) -> list[tuple[str, float, float, str | None]]:
    """(label, value 0..1, weight, note) — used by the "why" UI."""
    rows: list[tuple[str, float, float, str | None]] = [
        ("Participation", clamp(participation, 0.0, 1.0), 0.30, None),
        ("Decentralization", clamp(1.0 - concentration, 0.0, 1.0), 0.20, None),
        ("Reliability", clamp(reliability, 0.0, 1.0), 0.25, None),
        ("Security", clamp(security, 0.0, 1.0), 0.15, None),
        ("Sentiment", clamp(sentiment, 0.0, 1.0), 0.10, None),
    ]
    stress = clamp(economic_stress, 0.0, 1.0)
    if stress > 0.001:
        rows.append(("Economic stress penalty", stress, 0.0, "reduces total health (bad economics)"))
    return rows
