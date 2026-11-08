"""Hints for Discovery Mode.

Rules, enforced by the tests:

1. A hint never contains the target value.
2. A hint says *direction* and *magnitude*, not numbers.
3. The highest-impact wrong parameter gets the first hint: weight × (1 − similarity).

That last rule is what makes hints feel fair. Telling someone that a low-weight
fee is slightly off while their consensus mechanism is wrong would be useless.
"""

from __future__ import annotations

from .scoring import ParamScore, ScoreBreakdown


def _magnitude(ratio: float) -> str:
    if ratio >= 2.5:
        return "far too high"
    if ratio >= 1.25:
        return "too high"
    if ratio <= 0.40:
        return "far too low"
    if ratio <= 0.80:
        return "too low"
    return "close"


def _spec_hint(param: ParamScore, which: str) -> str | None:
    """Get a target-aware hint from the scored param (preferred) or legacy table."""
    if which == "low" and getattr(param, "hint_low", ""):
        return param.hint_low
    if which == "high" and getattr(param, "hint_high", ""):
        return param.hint_high
    return _SPEC_HINTS.get((param.key, which))


def hint_for(param: ParamScore) -> str | None:
    """One sentence about a single parameter, or None if it is already right."""
    if param.similarity >= 0.98:
        return None

    if param.target is None:
        # "No cap" / optional choice differs.
        return (
            _spec_hint(param, "high")
            or _spec_hint(param, "low")
            or f"{param.label}: this network made a different choice."
        )

    if isinstance(param.target, str):
        return (
            _spec_hint(param, "high")
            or _spec_hint(param, "low")
            or f"{param.label}: this network used something else."
        )

    target = float(param.target)
    value = float(param.value or 0.0)

    if target == 0:
        return (
            _spec_hint(param, "high")
            or _spec_hint(param, "low")
            or f"{param.label}: this network had none of it at launch."
        )

    ratio = value / target if target else 0.0
    direction = _magnitude(ratio)

    if direction == "close":
        return f"{param.label}: close, but not exact."

    if direction in ("too low", "far too low"):
        return _spec_hint(param, "low") or f"{param.label}: {direction}."
    return _spec_hint(param, "high") or f"{param.label}: {direction}."


def build_hints(breakdown: ScoreBreakdown, limit: int = 3) -> list[str]:
    """The most useful hints, highest impact first."""
    ranked = sorted(
        breakdown.params,
        key=lambda p: -(p.effective_weight * (1.0 - p.similarity)),
    )
    hints: list[str] = []
    for param in ranked:
        hint = hint_for(param)
        if hint and hint not in hints:
            hints.append(hint)
        if len(hints) >= limit:
            break
    return hints


def near_misses(breakdown: ScoreBreakdown) -> list[str]:
    """Parameters that are close but not exact — used for the 'almost' message."""
    return [
        p.label
        for p in breakdown.params
        if 0.80 <= p.similarity < 0.98 and p.effective_weight >= 0.10
    ]


# Directional hints keyed by (parameter, "low"/"high").
# They describe the player's value relative to the target, and never print it.
_SPEC_HINTS: dict[tuple[str, str], str] = {
    ("consensus", "high"): "This network did not use validators. Something else produced blocks.",
    ("consensus", "low"): "This network did not use validators. Something else produced blocks.",
    ("block_time_s", "low"): "Your blocks arrive far too often for this era.",
    ("block_time_s", "high"): "Your blocks arrive far too slowly. A payment would feel stuck.",
    ("initial_supply", "low"): "Nothing was handed out at launch. Nobody had coins on day one.",
    ("initial_supply", "high"): "Nothing was handed out at launch. Nobody had coins on day one.",
    ("max_supply", "low"): "This network had no cap written into its rules.",
    ("max_supply", "high"): "This network had no cap written into its rules.",
    ("initial_block_reward", "low"): "The reward was far more generous than this.",
    ("initial_block_reward", "high"): "The reward was smaller than this.",
    ("halving_interval_blocks", "low"): "The reward shrank far more often than this.",
    ("halving_interval_blocks", "high"): "The reward shrank far less often than this.",
    ("burn_rate", "low"): "Something is being destroyed that this network never destroyed.",
    ("burn_rate", "high"): "Something is being destroyed that this network never destroyed.",
    ("tx_per_block", "low"): "Blocks were smaller than this in the early network.",
    ("tx_per_block", "high"): "Blocks were larger than this, even when empty.",
    ("base_fee", "low"): "Fees were a rounding error in this era.",
    ("base_fee", "high"): "Fees were a rounding error in this era.",
}
