"""Configuration objects for a FutureCoins simulation.

Everything the player can change lives here, as frozen dataclasses.

Why frozen?  Because a configuration that can change halfway through a run makes
every bug impossible to reproduce. A frozen config is a promise: "this run used
these exact rules". The UI builds a *new* config when the player presses Launch.

Units used throughout the project
---------------------------------
- 1 tick            = 1 simulated day
- block_time_s      = seconds per block (a protocol rule)
- token amounts     = abstract "tokens", not money, not a real asset
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Literal

Consensus = Literal["pow", "pos"]

# A halving interval this large means "this protocol never halves".
NEVER = 10**12


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NetworkParams:
    """Protocol rules about how blocks are produced."""

    consensus: Consensus = "pow"

    # Target time between blocks, in seconds. 600 s = 10 minutes, like Bitcoin.
    block_time_s: float = 600.0

    # Maximum number of transactions that fit in one block.
    tx_per_block: int = 500

    # Fee paid for a transaction when the network is empty.
    base_fee: float = 0.05

    # How strongly congestion raises the fee. fee = base * (1 + k * max(0, congestion - 1)).
    fee_congestion_multiplier: float = 2.0

    # How strongly fees reduce demand. demand * exp(-k * (fee/base - 1)).
    fee_elasticity: float = 0.2

    # Fraction of total supply that must be staked for full Proof-of-Stake
    # availability. Below it, block production slows down.
    target_stake_fraction: float = 0.30


# ---------------------------------------------------------------------------
# Monetary policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MonetaryParams:
    """Rules about how tokens are created and destroyed."""

    initial_supply: float = 1_000_000.0

    # None means "no hard cap". Bitcoin has no cap *parameter*: its 21 M is the
    # sum of the halving series. See docs/GDD.md section 8.
    max_supply: float | None = 21_000_000.0

    initial_block_reward: float = 50.0

    # Reward halves every N blocks (not ticks: real protocols count blocks).
    halving_interval_blocks: int = 210_000

    # Share of transaction fees that is destroyed forever.
    burn_rate: float = 0.0

    # Share of the initial supply held by the protocol instead of agents.
    treasury_fraction: float = 0.10


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentParams:
    """How many agents of each role, and how they behave."""

    n_miners: int = 120
    n_validators: int = 0
    n_users: int = 300
    n_traders: int = 100
    n_developers: int = 40
    n_attackers: int = 10

    # Capacity is "hashrate" for miners and "stake" for validators.
    hashrate_per_miner: float = 1.0
    stake_per_validator: float = 10_000.0

    # Operating cost per tick, in tokens.
    miner_cost_per_tick: float = 36.0
    validator_cost_per_tick: float = 36.0

    # Transactions one user wants to make per tick.
    user_tx_per_tick: float = 144.0

    # 0..1 — how much a trader amplifies price noise.
    trader_aggressiveness: float = 0.5

    # How fast developers improve network capacity, per tick, per developer.
    dev_improvement_rate: float = 0.0096

    # Hysteresis: an agent must be unprofitable for N ticks before leaving.
    exit_patience_ticks: int = 3
    entry_patience_ticks: int = 5

    # Below this confidence, a user starts thinking about leaving.
    churn_confidence_threshold: float = 0.25


# ---------------------------------------------------------------------------
# Social / market
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SocialParams:
    """The mood of the market and the wider public."""

    initial_sentiment: float = 0.25

    # 0..1 — how fast sentiment catches up with reality.
    sentiment_adaptivity: float = 0.15

    # Constant media bias added to the sentiment target (-1..1).
    media_bias: float = 0.0

    # 0..1 — how decentralized governance is. Feeds the health score.
    decentralization: float = 0.70

    # 0..1 — how much institutions participate. Adds liquidity.
    institutional_participation: float = 0.20

    # Depth of the market. Thin liquidity means small flows move the price a lot.
    liquidity: float = 1_000_000.0

    # Share of their rewards that producers sell to pay operating costs.
    sell_propensity: float = 0.40

    # Price-index sensitivity constants (documented in ARCHITECTURE section 6.6).
    # price_flow_k is a mean-reversion strength; price_sent_k is deliberately
    # small, because a sentiment *offset* applied every tick would drift the
    # index forever instead of nudging it.
    price_flow_k: float = 0.9
    price_sent_k: float = 0.05
    price_sigma: float = 0.015

    # How fast adoption follows utility and mood.
    adoption_adaptivity: float = 0.05


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventParams:
    """Random event probabilities, per tick."""

    enabled: bool = True
    probability_scale: float = 1.0
    # Per-tick (1 tick = 1 simulated day). Tuned for a few notable events per
    # simulated year in typical conditions, not constant crisis.
    crash_probability: float = 0.012
    congestion_probability: float = 0.020
    media_probability: float = 0.016
    exodus_probability: float = 0.008


# ---------------------------------------------------------------------------
# The root config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SimConfig:
    """A complete, immutable description of one simulation."""

    seed: int = 42

    # Visual grid size (cells). If population exceeds cells, the grid shows a
    # deterministic 1:1 sampled snapshot of part of the population.
    rows: int = 30
    cols: int = 30

    network: NetworkParams = field(default_factory=NetworkParams)
    monetary: MonetaryParams = field(default_factory=MonetaryParams)
    agents: AgentParams = field(default_factory=AgentParams)
    social: SocialParams = field(default_factory=SocialParams)
    events: EventParams = field(default_factory=EventParams)

    # -- derived values -----------------------------------------------------

    @property
    def cells(self) -> int:
        return self.rows * self.cols

    @property
    def population(self) -> int:
        """Total number of agents, including inactive ones."""
        a = self.agents
        producers = a.n_miners if self.network.consensus == "pow" else a.n_validators
        return producers + a.n_users + a.n_traders + a.n_developers + a.n_attackers

    @property
    def blocks_per_tick(self) -> float:
        """How many blocks a healthy network produces in one simulated day."""
        return 86400.0 / max(self.network.block_time_s, 0.001)

    def to_dict(self) -> dict:
        """Plain dict, used for hashing and for saving a run's configuration."""
        return asdict(self)

    def fingerprint(self) -> str:
        """Short stable hash of the configuration.

        Two runs with the same fingerprint used the same rules. This is what an
        achievement records, so a badge can be traced back to its exact config.
        """
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Presets
#
# A preset is just a named SimConfig. There is no special code path for it.
# ---------------------------------------------------------------------------

BITCOIN_2009 = SimConfig(
    seed=2009,
    network=NetworkParams(
        consensus="pow",
        block_time_s=600.0,
        tx_per_block=2500,
        base_fee=0.01,
        fee_congestion_multiplier=2.0,
        fee_elasticity=0.15,
    ),
    monetary=MonetaryParams(
        initial_supply=0.0,          # nobody owned coins at genesis
        max_supply=None,             # the 21 M cap is emergent, not a parameter
        initial_block_reward=50.0,
        halving_interval_blocks=210_000,
        burn_rate=0.0,
        treasury_fraction=0.0,
    ),
    agents=AgentParams(
        n_miners=150,
        n_validators=0,
        n_users=250,
        n_traders=60,
        n_developers=20,
        n_attackers=5,
        miner_cost_per_tick=36.0,
        user_tx_per_tick=96.0,
    ),
    social=SocialParams(
        liquidity=500_000.0,
        sell_propensity=0.50,
        price_sigma=0.020,
        decentralization=0.90,
        institutional_participation=0.05,
    ),
)

ETHEREUM_2015 = SimConfig(
    seed=2015,
    network=NetworkParams(
        consensus="pow",
        block_time_s=15.0,
        tx_per_block=400,
        base_fee=0.02,
    ),
    monetary=MonetaryParams(
        initial_supply=72_000_000.0,
        max_supply=None,
        initial_block_reward=5.0,
        halving_interval_blocks=NEVER,   # Ethereum did not halve
        burn_rate=0.0,
        treasury_fraction=0.12,
    ),
    agents=AgentParams(
        n_miners=100,
        n_users=320,
        n_traders=90,
        n_developers=80,
        n_attackers=10,
    ),
    social=SocialParams(liquidity=2_000_000.0),
)

SOLANA_2020 = SimConfig(
    seed=2020,
    network=NetworkParams(
        consensus="pos",
        block_time_s=0.4,
        tx_per_block=10_000,
        base_fee=0.001,
        fee_congestion_multiplier=0.5,
    ),
    monetary=MonetaryParams(
        initial_supply=500_000_000.0,
        max_supply=None,
        initial_block_reward=0.5,
        halving_interval_blocks=NEVER,
        burn_rate=0.5,
        treasury_fraction=0.20,
    ),
    agents=AgentParams(
        n_miners=0,
        n_validators=80,
        n_users=400,
        n_traders=120,
        n_developers=100,
        n_attackers=15,
        # 80 validators x 1.875 M = 150 M staked, i.e. the 30 % target for a
        # 500 M supply. Capacity is an abstraction: agents do not need to hold
        # the full stake in their wallet for the security model to make sense.
        stake_per_validator=1_875_000.0,
    ),
    social=SocialParams(liquidity=5_000_000.0, decentralization=0.80),
)

STABLE_UTILITY = SimConfig(
    seed=7,
    network=NetworkParams(
        consensus="pos",
        block_time_s=2.0,
        tx_per_block=2_000,
        base_fee=0.001,
    ),
    monetary=MonetaryParams(
        initial_supply=100_000_000.0,
        max_supply=100_000_000.0,   # fixed supply, no inflation
        initial_block_reward=0.0,
        halving_interval_blocks=NEVER,
        burn_rate=0.2,
        treasury_fraction=0.05,
    ),
    agents=AgentParams(
        n_miners=0,
        n_validators=60,
        n_users=400,
        n_traders=40,
        n_developers=60,
        n_attackers=5,
        # 60 validators x 500 000 = 30 M staked = 30 % of a 100 M supply.
        stake_per_validator=500_000.0,
        # A fixed-supply utility coin pays validators from fees alone. If the
        # operating cost were positive, every validator would eventually leave
        # — a real design trap, but not the preset's intended lesson.
        validator_cost_per_tick=0.0,
    ),
    social=SocialParams(liquidity=8_000_000.0, price_sigma=0.005),
)

CHAOS_SANDBOX = SimConfig(
    seed=666,
    network=NetworkParams(
        consensus="pow",
        block_time_s=30.0,
        tx_per_block=80,             # tiny blocks => permanent congestion
        base_fee=2.0,
        fee_congestion_multiplier=5.0,
        fee_elasticity=0.5,
    ),
    monetary=MonetaryParams(
        initial_supply=10_000.0,
        max_supply=50_000.0,
        initial_block_reward=500.0,  # hyperinflation until the cap
        halving_interval_blocks=500,
        burn_rate=0.0,
        treasury_fraction=0.0,
    ),
    agents=AgentParams(
        n_miners=200,
        n_users=500,
        n_traders=200,
        n_developers=20,
        n_attackers=40,
        miner_cost_per_tick=48.0,
    ),
    social=SocialParams(liquidity=100_000.0, price_sigma=0.05),
    events=EventParams(probability_scale=3.0),
)

# A neutral starting point. It is deliberately *not* any historical network:
# the app opens here, so Discovery Mode stays a puzzle instead of being solved
# by the preset the player happens to be looking at.
BLANK_CANVAS = SimConfig()

PRESETS: dict[str, SimConfig] = {
    "Blank Canvas": BLANK_CANVAS,
    "Bitcoin 2009": BITCOIN_2009,
    "Ethereum 2015": ETHEREUM_2015,
    "Solana 2020": SOLANA_2020,
    "Stable Utility Coin": STABLE_UTILITY,
    "Chaos Sandbox": CHAOS_SANDBOX,
}

# Which achievement unlocks which preset. A preset not listed here (or listed
# with None) is always available. Blank Canvas is the starter and is never
# locked, so a new player always has somewhere to begin.
# Presets not listed here are permanently locked (mystery) until a discovery
# target/unlock path is added for them. Blank Canvas and Chaos Sandbox are always open.
PRESET_UNLOCKS: dict[str, str | None] = {
    "Blank Canvas": None,
    "Chaos Sandbox": None,
    "Bitcoin 2009": "genesis_discovery",
    "Ethereum 2015": "ethereum_discovery",
    "Solana 2020": "solana_discovery",
}

# The library's default is the same object as the Blank Canvas preset, so
# "default" and "Blank Canvas" can never drift apart.
DEFAULT_CONFIG = BLANK_CANVAS
