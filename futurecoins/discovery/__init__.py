"""Discovery Mode: reconstruct a historical currency from its behaviour."""

from __future__ import annotations

from .hints import build_hints, hint_for, near_misses
from .scoring import BANDS, ScoreBreakdown, score_config
from .targets import BITCOIN_2009, TARGETS, Target

__all__ = [
    "BANDS",
    "BITCOIN_2009",
    "TARGETS",
    "ScoreBreakdown",
    "Target",
    "build_hints",
    "hint_for",
    "near_misses",
    "score_config",
]
