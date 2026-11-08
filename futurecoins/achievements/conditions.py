"""Pure predicates for achievements.

Every function here takes a `RunSummary` and returns a bool. No randomness, no
clock, no file access. That is what makes an achievement trustworthy: the same
run always produces the same verdict.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..config import SimConfig
from ..events import EventLogEntry
from ..metrics import Metrics


@dataclass(frozen=True)
class RunSummary:
    """Everything an achievement is allowed to look at.

    The interface builds one of these from the live `Simulation`. Tests build
    one by hand. Neither path needs a running UI.
    """

    tick: int
    metrics: Metrics
    config: SimConfig

    # A bounded window of recent metric snapshots. The engine keeps the last
    # 2 000, which is enough for the 100-tick "Network Architect" condition.
    history: tuple[Metrics, ...] = ()

    # Every event that has fired during this run, oldest first.
    events: tuple[EventLogEntry, ...] = ()

    # Backward-compatible Bitcoin 2009 discovery score.
    discovery_score: float | None = None

    # Per-target discovery similarity scores (target_id -> score in 0..1).
    discovery_scores: dict[str, float] = field(default_factory=dict)

    # 800-character grid snapshot (see snapshots.py). Stored with the award.
    snapshot: str = ""


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------


def first_currency(summary: RunSummary) -> bool:
    """One tick completed with at least one active participant."""
    return summary.tick >= 1 and summary.metrics.active_nodes >= 1


def survivor(summary: RunSummary) -> bool:
    """Five simulated years (1825 ticks) without the network dying."""
    return summary.tick >= 1825 and summary.metrics.health > 0.0


def _discovery_score(summary: RunSummary, target_id: str, legacy: float | None = None) -> float:
    scores = getattr(summary, "discovery_scores", {}) or {}
    if target_id in scores:
        return float(scores[target_id] or 0.0)
    if legacy is not None:
        return float(legacy or 0.0)
    return float(summary.discovery_score or 0.0) if target_id == "bitcoin_2009" else 0.0


def genesis_discovery(summary: RunSummary) -> bool:
    """Reconstructed Bitcoin 2009 to at least 95 % similarity."""
    return _discovery_score(summary, "bitcoin_2009", summary.discovery_score) >= 0.95


def ethereum_discovery(summary: RunSummary) -> bool:
    """Reconstructed Ethereum 2015 (early-era abstraction) to >= 95% similarity."""
    return _discovery_score(summary, "ethereum_2015") >= 0.95


def solana_discovery(summary: RunSummary) -> bool:
    """Reconstructed Solana 2020 (launch-era abstraction) to >= 95% similarity."""
    return _discovery_score(summary, "solana_2020") >= 0.95


def crisis_survivor(summary: RunSummary) -> bool:
    """Survived a severe event without health collapsing below 20.

    A severe event is one whose *scaled* severity reached 0.6. The run must
    have continued for at least three ticks after the event started, and health
    must never have fallen below 20 since. That "since" matters: a crash you
    recovered from still counts, but a crash that killed the network does not.
    """
    severe = [e for e in summary.events if e.severity >= 0.6]
    if not severe:
        return False

    for event in severe:
        after = [m for m in summary.history if m.tick >= event.tick]
        if len(after) < 3:
            continue
        if all(m.health >= 20.0 for m in after):
            return True
    return False


def network_architect(summary: RunSummary) -> bool:
    """100 consecutive ticks with >= 90 % participation and >= 50 active nodes."""
    if len(summary.history) < 100:
        return False
    window = summary.history[-100:]
    return all(
        m.participation >= 0.90 and m.active_nodes >= 50 for m in window
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AchievementDef:
    """The static definition of one achievement."""

    id: str
    name: str
    description: str
    icon: str
    condition: Callable[[RunSummary], bool] = field(repr=False)
    hint: str = ""


ACHIEVEMENT_DEFS: tuple[AchievementDef, ...] = (
    AchievementDef(
        id="first_currency",
        name="First Currency",
        description="Complete one simulated day with at least one active participant.",
        icon="🪙",
        condition=first_currency,
        hint="Press Run once.",
    ),
    AchievementDef(
        id="survivor",
        name="Survivor",
        description="Keep a network alive for 1825 ticks — five simulated years.",
        icon="🌱",
        condition=survivor,
        hint="Use Speed 20 and a balanced configuration.",
    ),
    AchievementDef(
        id="genesis_discovery",
        name="Genesis Discovery",
        description="Reconstruct Bitcoin 2009 with at least 95 % similarity.",
        icon="🔍",
        condition=genesis_discovery,
        hint="Open Discovery Mode and read the riddle carefully.",
    ),
    AchievementDef(
        id="ethereum_discovery",
        name="Frontier Discovery",
        description=(
            "Reconstruct the Ethereum 2015 early-era abstraction with at least 95 % similarity "
            "(educational model, not a 1:1 historical reproduction)."
        ),
        icon="🧭",
        condition=ethereum_discovery,
        hint="Use Discovery Mode: a fast programmable early network with a launch allocation.",
    ),
    AchievementDef(
        id="solana_discovery",
        name="High-Throughput Discovery",
        description=(
            "Reconstruct the Solana 2020 launch-era abstraction with at least 95 % similarity "
            "(educational model, not a 1:1 historical reproduction)."
        ),
        icon="⚡",
        condition=solana_discovery,
        hint="Use Discovery Mode: staked validators, very fast blocks, low fees, and fee burn.",
    ),
    AchievementDef(
        id="crisis_survivor",
        name="Crisis Survivor",
        description="Survive a severe event without network health dropping below 20.",
        icon="🛡️",
        condition=crisis_survivor,
        hint="A decentralized, well-participating network absorbs shocks.",
    ),
    AchievementDef(
        id="network_architect",
        name="Network Architect",
        description="Keep >= 90 % participation and >= 50 active nodes for 100 ticks.",
        icon="🏗️",
        condition=network_architect,
        hint="Low fees and reliable blocks keep users from churning.",
    ),
)
