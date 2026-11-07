"""Consensus: who produces blocks, and who gets paid.

This is an *abstraction*, not an implementation. There is no hashing, no
cryptography, no peer-to-peer network. What we model is the economic shape of
two consensus families:

- Proof of Work  (PoW): your share of rewards is your share of hashing power.
- Proof of Stake (PoS): your share of rewards is your share of staked tokens.

The lesson the player should take away: in both systems, rewards are
proportional to a scarce resource, and that resource has a cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .agents import Agent
from .config import SimConfig


@dataclass(frozen=True)
class BlockProduction:
    """The result of one tick of block production."""

    blocks: float = 0.0
    availability: float = 0.0
    block_reward: float = 0.0
    issuance: float = 0.0
    distributable_fees: float = 0.0
    reward_by_agent: dict[int, float] = field(default_factory=dict)
    fees_by_agent: dict[int, float] = field(default_factory=dict)
    total_capacity: float = 0.0
    concentration: float = 1.0


def current_block_reward(config: SimConfig, total_blocks: float) -> float:
    """Reward per block, after applying every halving that has happened.

    Halvings are counted in *blocks*, because that is how real protocols count
    them. Counting in ticks would make the schedule depend on our time model,
    which would be an accident of the simulation rather than a rule of the
    currency.
    """
    interval = config.monetary.halving_interval_blocks
    if interval <= 0 or interval >= 10**11:
        return config.monetary.initial_block_reward
    halvings = int(total_blocks // interval)
    return config.monetary.initial_block_reward / (2**halvings)


def producer_capacity(agents: list[Agent]) -> tuple[list[Agent], float]:
    """Active producers and the sum of their capacity (hashrate or stake)."""
    producers = [a for a in agents if a.active and a.is_producer]
    total = sum(a.capacity for a in producers)
    return producers, total


def availability(config: SimConfig, agents: list[Agent]) -> float:
    """Fraction of the target block production the network can actually achieve.

    PoW: assumed to be 1.0 unless an event takes producers offline.
    PoS: falls when too little stake is online. A chain with 10 % of the
    expected stake cannot finalise blocks at full speed — that is the whole
    security lesson of Proof of Stake, in one line.
    """
    if config.network.consensus == "pow":
        return 1.0

    _, total_stake = producer_capacity(agents)
    required = config.network.target_stake_fraction * max(
        config.monetary.initial_supply, 1.0
    )
    if required <= 0:
        return 1.0
    return max(0.0, min(1.0, total_stake / required))


def produce(
    config: SimConfig,
    agents: list[Agent],
    total_blocks: float,
    total_supply: float,
    fees_pool: float,
    availability_override: float | None = None,
) -> BlockProduction:
    """Produce one tick of blocks and split the rewards.

    Rewards use **expected value**, not a per-block lottery. With six blocks per
    hour and 150 miners, a lottery would leave most miners earning nothing for
    hours and turn the grid into noise. Expected value keeps aggregate behaviour
    correct and individual behaviour readable. The UI says so explicitly.

    Parameters
    ----------
    total_blocks:
        Blocks produced *before* this tick. Used for the halving schedule.
    total_supply:
        Supply before this tick. Used to enforce the hard cap.
    fees_pool:
        Transaction fees collected this tick, before burning.
    """
    producers, total_capacity = producer_capacity(agents)
    avail = availability(config, agents) if availability_override is None else availability_override

    if not producers or total_capacity <= 0 or avail <= 0:
        return BlockProduction(availability=0.0, concentration=1.0)

    blocks = config.blocks_per_tick * avail
    reward = current_block_reward(config, total_blocks)
    issuance = blocks * reward

    # A hard cap stops issuance; it never destroys existing tokens.
    if config.monetary.max_supply is not None:
        headroom = max(0.0, config.monetary.max_supply - total_supply)
        issuance = min(issuance, headroom)

    distributable_fees = fees_pool * (1.0 - config.monetary.burn_rate)

    # Herfindahl index: sum of squared shares. 1.0 = one producer owns everything.
    concentration = 0.0
    reward_by_agent: dict[int, float] = {}
    fees_by_agent: dict[int, float] = {}

    for agent in producers:
        share = agent.capacity / total_capacity
        concentration += share * share
        reward_by_agent[agent.id] = issuance * share
        fees_by_agent[agent.id] = distributable_fees * share

    return BlockProduction(
        blocks=blocks,
        availability=avail,
        block_reward=reward,
        issuance=issuance,
        distributable_fees=distributable_fees,
        reward_by_agent=reward_by_agent,
        fees_by_agent=fees_by_agent,
        total_capacity=total_capacity,
        concentration=concentration,
    )


def security_margin(config: SimConfig, agents: list[Agent], avail: float) -> float:
    """A 0..1 proxy for "how expensive would it be to capture this network?".

    PoS: the more stake online, the more capital an attacker must acquire.
    PoW: the more active producers, the more hardware an attacker must out-mine.

    This is deliberately crude. It is a teaching proxy, not a security audit.
    """
    if config.network.consensus == "pos":
        return avail

    producers, _ = producer_capacity(agents)
    return min(1.0, len(producers) / 50.0)
