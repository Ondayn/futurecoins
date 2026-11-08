"""Discovery targets: versioned reference configurations.

A target is what the player is trying to reconstruct. It is *data*, with an
explicit confidence flag per parameter, because some historical numbers are
genuinely uncertain and pretending otherwise would be bad teaching.

Bitcoin 2009 is deliberately the only MVP target. It has the strongest
documentation and the best story: a currency with no premine, no company, and a
supply cap that is a consequence rather than a constant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..config import NEVER, SimConfig

Kind = Literal["categorical", "numeric", "optional_numeric"]
Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ParamSpec:
    """One comparable parameter of a target configuration."""

    key: str
    label: str
    kind: Kind
    target: float | str | None
    weight: float

    # For numeric parameters: how far off counts as "unrecognisable".
    # 2.0 means "a factor of 2 away scores about a third".
    tolerance: float = 2.0

    # For numeric parameters whose target is 0, use an absolute tolerance
    # instead of a ratio (you cannot divide by zero).
    abs_tolerance: float = 1.0

    confidence: Confidence = "high"

    # Directional hints. Never contain the target value.
    hint_low: str = ""
    hint_high: str = ""


@dataclass(frozen=True)
class Target:
    id: str
    name: str
    era: str
    riddle: str
    params: tuple[ParamSpec, ...]
    caveat: str = ""

    @property
    def total_weight(self) -> float:
        return sum(p.weight for p in self.params)


BITCOIN_2009 = Target(
    id="bitcoin_2009",
    name="Bitcoin",
    era="Genesis · 2009",
    riddle=(
        "A network with no premine, no company and no foundation. Blocks arrive slowly "
        "and predictably. The reward for making a block is generous at first and shrinks "
        "on a fixed schedule. Nobody can destroy coins. There are no validators, because "
        "there is no stake."
    ),
    params=(
        ParamSpec(
            key="consensus",
            label="Consensus mechanism",
            kind="categorical",
            target="pow",
            weight=0.20,
            hint_low="This network did not use validators. Something else produced blocks.",
        ),
        ParamSpec(
            key="block_time_s",
            label="Block time",
            kind="numeric",
            target=600.0,
            weight=0.15,
            tolerance=2.0,
            hint_low="Your blocks arrive far too often for this era.",
            hint_high="Your blocks arrive far too slowly. A payment would feel stuck.",
        ),
        ParamSpec(
            key="initial_supply",
            label="Initial supply",
            kind="numeric",
            target=0.0,
            weight=0.10,
            abs_tolerance=50_000.0,
            hint_low="Nothing was handed out at launch. Nobody had coins on day one.",
            hint_high="Nothing was handed out at launch. Nobody had coins on day one.",
        ),
        ParamSpec(
            key="max_supply",
            label="Hard supply cap",
            kind="optional_numeric",
            target=None,
            weight=0.05,
            hint_low="This network had no cap written into its rules.",
            hint_high="This network had no cap written into its rules.",
        ),
        ParamSpec(
            key="initial_block_reward",
            label="Initial block reward",
            kind="numeric",
            target=50.0,
            weight=0.15,
            tolerance=1.5,
            hint_low="The reward was far more generous than this.",
            hint_high="The reward was smaller than this.",
        ),
        ParamSpec(
            key="halving_interval_blocks",
            label="Halving interval",
            kind="numeric",
            target=210_000.0,
            weight=0.20,
            tolerance=2.0,
            hint_low="The reward shrank far more often than this.",
            hint_high="The reward shrank far less often than this.",
        ),
        ParamSpec(
            key="burn_rate",
            label="Burn rate",
            kind="numeric",
            target=0.0,
            weight=0.05,
            abs_tolerance=0.01,
            hint_low="Something is being destroyed that this network never destroyed.",
            hint_high="Something is being destroyed that this network never destroyed.",
        ),
        ParamSpec(
            key="tx_per_block",
            label="Transactions per block",
            kind="numeric",
            target=2500.0,
            weight=0.05,
            tolerance=2.5,
            confidence="medium",
            hint_low="Blocks were smaller than this in the early network.",
            hint_high="Blocks were larger than this, even when empty.",
        ),
        ParamSpec(
            key="base_fee",
            label="Base fee",
            kind="numeric",
            target=0.01,
            weight=0.05,
            tolerance=5.0,
            confidence="low",
            hint_low="Fees were a rounding error in this era.",
            hint_high="Fees were a rounding error in this era.",
        ),
    ),
    caveat=(
        "Early Bitcoin transaction counts are estimates. Parameters marked medium or low "
        "confidence count for less in the score, and the game says which ones they are."
    ),
)


TARGETS: dict[str, Target] = {BITCOIN_2009.id: BITCOIN_2009}


def config_values(config: SimConfig) -> dict[str, float | str | None]:
    """The comparable view of a player's configuration."""
    return {
        "consensus": config.network.consensus,
        "block_time_s": config.network.block_time_s,
        "tx_per_block": float(config.network.tx_per_block),
        "base_fee": config.network.base_fee,
        "initial_supply": config.monetary.initial_supply,
        "max_supply": config.monetary.max_supply,
        "initial_block_reward": config.monetary.initial_block_reward,
        "halving_interval_blocks": float(config.monetary.halving_interval_blocks),
        "burn_rate": config.monetary.burn_rate,
    }


def is_never(value: float) -> bool:
    return value >= NEVER / 10
