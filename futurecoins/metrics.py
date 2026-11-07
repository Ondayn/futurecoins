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
) -> float:
    """A 0..100 composite score.

    The brief asks for "network health" without defining it. An undefined health
    score is a vibe, not a lesson — so the weights are explicit and the UI shows
    them when the player clicks the card.

    Weights: participation 30 %, decentralization 20 %, reliability 25 %,
    security 15 %, sentiment 10 %.
    """
    decentralization = clamp(1.0 - concentration, 0.0, 1.0)
    health = 100.0 * (
        0.30 * clamp(participation, 0.0, 1.0)
        + 0.20 * decentralization
        + 0.25 * clamp(reliability, 0.0, 1.0)
        + 0.15 * clamp(security, 0.0, 1.0)
        + 0.10 * clamp(sentiment, 0.0, 1.0)
    )
    return clamp(health, 0.0, 100.0)


def health_breakdown(
    participation: float,
    concentration: float,
    reliability: float,
    security: float,
    sentiment: float,
) -> list[tuple[str, float, float]]:
    """(label, value 0..1, weight) — used by the "why" popover in the UI."""
    return [
        ("Participation", clamp(participation, 0.0, 1.0), 0.30),
        ("Decentralization", clamp(1.0 - concentration, 0.0, 1.0), 0.20),
        ("Reliability", clamp(reliability, 0.0, 1.0), 0.25),
        ("Security", clamp(security, 0.0, 1.0), 0.15),
        ("Sentiment", clamp(sentiment, 0.0, 1.0), 0.10),
    ]
