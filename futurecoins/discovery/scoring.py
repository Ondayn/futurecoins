"""Similarity scoring for Discovery Mode.

The score is a weighted average of per-parameter similarities, in [0, 1].

    S = Σ (effective_weight_i × similarity_i) / Σ effective_weight_i

Two deliberate choices:

1. **Weights are visible.** A score the player cannot inspect is a guessing game.
2. **Confidence discounts weight.** A parameter historians are unsure about
   (early transaction counts, fee levels) counts for less than one that is
   documented in the protocol.

Numeric similarity uses a *ratio*, not an absolute difference, because a
block time of 600 s versus 1200 s is a factor of two, and so is 0.4 s versus
0.8 s. Absolute differences would make seconds dominate everything.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..config import SimConfig
from .targets import ParamSpec, Target, config_values

_CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.75, "low": 0.5}

# Score bands, from docs/GDD.md section 8.
BANDS: tuple[tuple[float, str], ...] = (
    (0.95, "Discovery achieved."),
    (0.80, "Almost there — one or two rules are off."),
    (0.60, "You're getting close."),
    (0.40, "Some characteristics match."),
    (0.00, "This is a different kind of money."),
)


@dataclass(frozen=True)
class ParamScore:
    key: str
    label: str
    similarity: float
    weight: float
    effective_weight: float
    confidence: str
    value: float | str | None
    target: float | str | None
    hint_low: str = ""
    hint_high: str = ""


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    band: str
    message: str
    params: tuple[ParamScore, ...]
    target_id: str

    @property
    def discovered(self) -> bool:
        return self.total >= 0.95


def numeric_similarity(value: float, target: float, spec: ParamSpec) -> float:
    """1.0 when identical, falling to 0 as the ratio drifts."""
    if target == 0:
        return max(0.0, 1.0 - abs(value) / max(spec.abs_tolerance, 1e-9))

    if value <= 0:
        return 0.0

    ratio = value / target
    distance = abs(math.log(ratio))
    scale = math.log(1.0 + max(spec.tolerance, 1e-9))
    return max(0.0, 1.0 - distance / scale)


def score_config(config: SimConfig, target: Target) -> ScoreBreakdown:
    """Compare a player configuration against a target configuration."""
    values = config_values(config)
    params: list[ParamScore] = []

    for spec in target.params:
        value = values.get(spec.key)

        if spec.kind == "categorical":
            similarity = 1.0 if value == spec.target else 0.0
        elif spec.kind == "optional_numeric":
            # "No cap" is a distinct choice, not the number 0.
            similarity = 1.0 if (value is None) == (spec.target is None) else 0.0
        else:
            similarity = numeric_similarity(float(value or 0.0), float(spec.target or 0.0), spec)

        params.append(
            ParamScore(
                key=spec.key,
                label=spec.label,
                similarity=similarity,
                weight=spec.weight,
                effective_weight=spec.weight * _CONFIDENCE_WEIGHT.get(spec.confidence, 1.0),
                confidence=spec.confidence,
                value=value,
                target=spec.target,
                hint_low=spec.hint_low,
                hint_high=spec.hint_high,
            )
        )

    total_weight = sum(p.effective_weight for p in params) or 1.0
    total = sum(p.effective_weight * p.similarity for p in params) / total_weight

    message = next(text for threshold, text in BANDS if total >= threshold)

    return ScoreBreakdown(
        total=total,
        band=band_for(total),
        message=message,
        params=tuple(params),
        target_id=target.id,
    )


def band_for(score: float) -> str:
    if score >= 0.95:
        return "discovered"
    if score >= 0.80:
        return "almost"
    if score >= 0.60:
        return "close"
    if score >= 0.40:
        return "partial"
    return "far"
