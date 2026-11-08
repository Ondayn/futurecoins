"""Achievements: long-term goals, evaluated once per tick.

An achievement is a *pure predicate* over a `RunSummary` plus some metadata.
Keeping the predicates pure means they can be tested with hand-built summaries
and no simulation at all — the same trick that makes the economy functions
easy to test.
"""

from __future__ import annotations

from .conditions import (
    ACHIEVEMENT_DEFS,
    AchievementDef,
    RunSummary,
    crisis_survivor,
    first_currency,
    genesis_discovery,
    network_architect,
    survivor,
)
from .manager import AchievementManager, Award
from .snapshots import decode_snapshot, encode_snapshot

__all__ = [
    "ACHIEVEMENT_DEFS",
    "AchievementDef",
    "AchievementManager",
    "Award",
    "RunSummary",
    "crisis_survivor",
    "decode_snapshot",
    "encode_snapshot",
    "first_currency",
    "genesis_discovery",
    "network_architect",
    "survivor",
]
