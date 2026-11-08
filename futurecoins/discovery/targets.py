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
            hint_high="This network did not use validators. Something else produced blocks.",
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


ETHEREUM_2015 = Target(
    id="ethereum_2015",
    name="Ethereum",
    era="Frontier · 2015 (educational abstraction)",
    riddle=(
        "A programmable network launched with a significant premine. Blocks arrive far "
        "faster than the original slow-chain design. It started with proof of work and "
        "did not follow a fixed halving schedule like Bitcoin. Fees exist, but this early "
        "era did not have the later base-fee burn mechanism. No hard supply cap is written "
        "into the basic monetary rules used here."
    ),
    params=(
        ParamSpec(
            key="consensus",
            label="Consensus mechanism",
            kind="categorical",
            target="pow",
            weight=0.15,
            hint_low="This network did not rely on staked validators in this early era.",
            hint_high="This network did not rely on staked validators in this early era.",
        ),
        ParamSpec(
            key="block_time_s",
            label="Block time",
            kind="numeric",
            target=15.0,
            weight=0.15,
            tolerance=1.8,
            confidence="high",
            hint_low="Blocks arrive too rarely for this fast early network.",
            hint_high="Blocks arrive too quickly, even for this design.",
        ),
        ParamSpec(
            key="initial_supply",
            label="Initial supply (premine/allocation)",
            kind="numeric",
            target=72_000_000.0,
            weight=0.15,
            tolerance=1.5,
            confidence="medium",
            hint_low="A large allocation existed at launch in this abstraction.",
            hint_high="The launch allocation was not that large in this abstraction.",
        ),
        ParamSpec(
            key="max_supply",
            label="Hard supply cap",
            kind="optional_numeric",
            target=None,
            weight=0.05,
            hint_low="This abstraction does not set a fixed hard cap.",
            hint_high="This abstraction does not set a fixed hard cap.",
        ),
        ParamSpec(
            key="initial_block_reward",
            label="Initial block reward",
            kind="numeric",
            target=5.0,
            weight=0.15,
            tolerance=1.7,
            confidence="medium",
            hint_low="The early block reward was more substantial than this.",
            hint_high="The early block reward was lower than this.",
        ),
        ParamSpec(
            key="halving_interval_blocks",
            label="Halving schedule",
            kind="numeric",
            target=float(NEVER),
            weight=0.15,
            tolerance=2.0,
            hint_low="This network did not use a Bitcoin-style frequent halving schedule.",
            hint_high="This network did not use a Bitcoin-style frequent halving schedule.",
        ),
        ParamSpec(
            key="burn_rate",
            label="Fee burn rate",
            kind="numeric",
            target=0.0,
            weight=0.10,
            abs_tolerance=0.01,
            confidence="medium",
            hint_low="This early-era abstraction does not burn fees the way later designs did.",
            hint_high="This early-era abstraction does not burn fees the way later designs did.",
        ),
        ParamSpec(
            key="tx_per_block",
            label="Transactions per block",
            kind="numeric",
            target=400.0,
            weight=0.05,
            tolerance=2.5,
            confidence="low",
            hint_low="Block capacity is too small for this abstraction.",
            hint_high="Block capacity is too large for this abstraction.",
        ),
        ParamSpec(
            key="base_fee",
            label="Base fee",
            kind="numeric",
            target=0.02,
            weight=0.05,
            tolerance=5.0,
            confidence="low",
            hint_low="Fees are not modeled as extremely cheap in this abstraction.",
            hint_high="Fees are not modeled as extremely expensive in this abstraction.",
        ),
    ),
    caveat=(
        "Educational abstraction of Ethereum's early (2015/Frontier, PoW-era) characteristics. "
        "Real Ethereum changed over time (issuance/rewards, gas mechanics, later PoS and fee burn). "
        "Parameters marked medium or low confidence are simplified and count for less in the score."
    ),
)


SOLANA_2020 = Target(
    id="solana_2020",
    name="Solana",
    era="Launch era · 2020 (educational abstraction)",
    riddle=(
        "A high-throughput network secured by staked validators, not miners. Blocks (or slots) "
        "arrive extremely quickly and aim to carry a lot of activity with very low fees. "
        "It launched with a large initial supply and does not use a Bitcoin-style halving "
        "schedule in this abstraction. Part of the fee is destroyed (burned), and there is no "
        "simple hard cap parameter written into the rules here."
    ),
    params=(
        ParamSpec(
            key="consensus",
            label="Consensus mechanism",
            kind="categorical",
            target="pos",
            weight=0.20,
            hint_low="This network secures block production with stake, not mining work.",
            hint_high="This network secures block production with stake, not mining work.",
        ),
        ParamSpec(
            key="block_time_s",
            label="Block time / slot pace",
            kind="numeric",
            target=0.4,
            weight=0.15,
            tolerance=2.5,
            confidence="medium",
            hint_low="This network targets extremely frequent block production.",
            hint_high="Blocks are arriving too slowly for this high-throughput design.",
        ),
        ParamSpec(
            key="initial_supply",
            label="Initial supply",
            kind="numeric",
            target=500_000_000.0,
            weight=0.10,
            tolerance=2.0,
            confidence="medium",
            hint_low="The launch supply was much larger in this abstraction.",
            hint_high="The launch supply was smaller in this abstraction.",
        ),
        ParamSpec(
            key="max_supply",
            label="Hard supply cap",
            kind="optional_numeric",
            target=None,
            weight=0.05,
            hint_low="This abstraction does not set a simple hard cap parameter.",
            hint_high="This abstraction does not set a simple hard cap parameter.",
        ),
        ParamSpec(
            key="initial_block_reward",
            label="Issuance/reward level",
            kind="numeric",
            target=0.5,
            weight=0.10,
            tolerance=2.5,
            confidence="low",
            hint_low="Issuance per block is modeled higher than this in the abstraction.",
            hint_high="Issuance per block is modeled lower than this in the abstraction.",
        ),
        ParamSpec(
            key="halving_interval_blocks",
            label="Halving schedule",
            kind="numeric",
            target=float(NEVER),
            weight=0.10,
            tolerance=2.0,
            hint_low="This network does not use a Bitcoin-style halving schedule.",
            hint_high="This network does not use a Bitcoin-style halving schedule.",
        ),
        ParamSpec(
            key="burn_rate",
            label="Fee burn rate",
            kind="numeric",
            target=0.5,
            weight=0.15,
            tolerance=2.0,
            confidence="medium",
            hint_low="A meaningful share of fees is destroyed in this abstraction.",
            hint_high="Less of each fee is destroyed than in this abstraction.",
        ),
        ParamSpec(
            key="tx_per_block",
            label="Transactions per block",
            kind="numeric",
            target=10_000.0,
            weight=0.10,
            tolerance=2.5,
            confidence="low",
            hint_low="Capacity is far too limited for this high-throughput abstraction.",
            hint_high="Capacity is modeled even higher than this abstraction needs.",
        ),
        ParamSpec(
            key="base_fee",
            label="Base fee",
            kind="numeric",
            target=0.001,
            weight=0.05,
            tolerance=5.0,
            confidence="low",
            hint_low="Fees are modeled as extremely low in this abstraction.",
            hint_high="Fees are higher than this low-fee abstraction expects.",
        ),
    ),
    caveat=(
        "Educational abstraction inspired by Solana's launch-era characteristics. Real Solana uses slots, "
        "a more nuanced inflation/issuance schedule, and different fee mechanics than this simplified model. "
        "Parameters marked medium or low confidence are abstractions and count for less in the score."
    ),
)


TARGETS: dict[str, Target] = {
    BITCOIN_2009.id: BITCOIN_2009,
    ETHEREUM_2015.id: ETHEREUM_2015,
    SOLANA_2020.id: SOLANA_2020,
}


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
