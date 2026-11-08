"""Economy: demand, fees, price index, sentiment, adoption.

Everything here is a *model*. None of it predicts a real price. The price index
starts at 100 and moves according to documented formulas; the UI labels it
"simulated price index" everywhere it appears.

The guiding principle: every feedback loop needs damping. `exp()` and `clamp()`
are the seatbelts. If the price reaches 10^9 in thirty ticks, the model is
wrong and a bigger clamp will not fix it.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .agents import Agent, Role, active_agents
from .config import SimConfig


@dataclass
class EconomyState:
    """The mutable economic state of a running simulation."""

    price: float = 100.0          # index, base 100 at launch
    sentiment: float = 0.55       # 0..1
    adoption: float = 1.0         # multiplier, 1.0 = baseline
    volatility: float = 0.0       # EWMA of |log return|
    last_log_return: float = 0.0


@dataclass(frozen=True)
class MempoolOutcome:
    """What happened to this tick's transaction demand."""

    demand: float = 0.0
    included: float = 0.0
    dropped: float = 0.0
    fee: float = 0.0
    fees_pool: float = 0.0
    congestion: float = 0.0
    utilisation: float = 0.0

    @property
    def reliability(self) -> float:
        """Share of attempted transactions that made it into a block."""
        if self.demand <= 0:
            return 1.0
        return self.included / self.demand


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def generate_demand(
    config: SimConfig,
    agents: list[Agent],
    sentiment: float,
    adoption: float,
    price: float = 100.0,
    activity_multiplier: float = 1.0,
) -> float:
    """Transactions users want to make this tick.

    Things that raise demand: more active users, a better mood, higher adoption.
    Things that lower it: events that suppress activity, and a higher price
    (price elasticity — expensive networks see less usage).
    """
    users = active_agents(agents, Role.USER)
    if not users:
        return 0.0
    # Price elasticity: demand falls as price rises. Elasticity of 0.3 means
    # doubling the price reduces demand by ~19%.
    price_factor = (100.0 / max(price, 1.0)) ** 0.3
    return (
        len(users)
        * config.agents.user_tx_per_tick
        * (0.5 + sentiment)
        * adoption
        * price_factor
        * activity_multiplier
    )


def settle_mempool(
    config: SimConfig,
    demand: float,
    capacity: float,
) -> MempoolOutcome:
    """Price the transactions, then decide how many fit.

    Fees are a rationing mechanism, not a price list. As congestion rises, the
    fee rises, and *demand falls* because some users decide it is not worth it.
    That elasticity is what stops a fee market from running away.
    """
    if demand <= 0 or capacity <= 0:
        return MempoolOutcome(demand=demand, fee=config.network.base_fee)

    congestion = demand / capacity
    base = config.network.base_fee
    # Fees only rise once blocks are actually full. A half-empty block does not
    # need to ration anything.
    pressure = max(0.0, congestion - 1.0)
    fee = base * (1.0 + config.network.fee_congestion_multiplier * pressure)

    if base > 0:
        # Smooth, strictly positive elasticity. Never negative demand.
        demand_after = demand * math.exp(-config.network.fee_elasticity * (fee / base - 1.0))
    else:
        demand_after = demand

    included = min(demand_after, capacity)
    dropped = max(0.0, demand_after - capacity)
    fees_pool = included * fee

    return MempoolOutcome(
        demand=demand,
        included=included,
        dropped=dropped,
        fee=fee,
        fees_pool=fees_pool,
        congestion=congestion,
        utilisation=included / capacity,
    )


def update_economy(
    state: EconomyState,
    config: SimConfig,
    *,
    health: float,
    utilisation: float,
    reliability: float,
    inflation_fraction: float,
    price_shock: float,
    sentiment_shock: float,
    trader_pressure: float,
    rng: random.Random,
) -> None:
    """Advance the price index, sentiment, adoption and volatility by one tick.

    Mutates `state` in place. Kept as a function (not a method on Simulation) so
    it can be tested with hand-built numbers and no agents at all.
    """
    social = config.social

    # -- sentiment ---------------------------------------------------------
    # Sentiment chases a target set by network health plus whatever the media
    # and recent events are doing. It never teleports: adaptivity is the damping.
    # Sentiment is "trust". It starts low and rises as the network proves
    # itself reliable over time. Instantaneous health is a small input; the
    # dominant driver is sustained uptime and reliability.
    trust_target = clamp(
        0.15 + 0.4 * reliability + 0.25 * (health / 100.0) + social.media_bias + sentiment_shock
        + 0.3 * clamp(state.last_log_return * 5.0, -0.15, 0.15),
        0.0,
        1.0,
    )
    target_sentiment = clamp(trust_target, 0.0, 1.0)
    noise = rng.gauss(0.0, 0.01)
    state.sentiment = clamp(
        state.sentiment + social.sentiment_adaptivity * (target_sentiment - state.sentiment) + noise,
        0.0,
        1.0,
    )

    # -- price index -------------------------------------------------------
    # Newly issued tokens are a sell pressure: someone has to sell them to pay
    # for electricity. So is a network that keeps dropping transactions.
    sell_pressure = inflation_fraction * social.sell_propensity * (1.0 - state.sentiment)
    sell_pressure += 0.02 * (1.0 - reliability)
    sell_pressure += trader_pressure

    # The index mean-reverts towards a "fundamental" level set by adoption and
    # utilisation. Without this anchor, any constant sentiment offset would
    # compound forever: a 5 % nudge per tick is a 12,000x rise in a year.
    # A failed network has no fundamental value: health scales the anchor.
    health_factor = 0.1 + 0.9 * clamp(health / 100.0, 0.0, 1.0)
    fundamental = 100.0 * state.adoption * (0.8 + 0.4 * clamp(utilisation, 0.0, 1.5)) * health_factor
    fundamental = max(fundamental, 1.0)

    # A thin market moves more for the same flow. Deep liquidity dampens the
    # whole price response, including the noise.
    liquidity_scale = math.sqrt(1_000_000.0 / max(social.liquidity, 1.0))

    log_return = liquidity_scale * (
        social.price_flow_k * 0.15 * math.log(fundamental / max(state.price, 1e-9))
        - 0.5 * sell_pressure
        + social.price_sent_k * (state.sentiment - 0.5)
        + price_shock
    )
    log_return += rng.gauss(0.0, social.price_sigma * liquidity_scale)
    # One tick should never move the index by more than ~35 %.
    log_return = clamp(log_return, -0.35, 0.35)

    state.price = clamp(state.price * math.exp(log_return), 1.0, 100_000.0)
    state.last_log_return = log_return
    state.volatility = 0.8 * state.volatility + 0.2 * abs(log_return)

    # -- adoption ----------------------------------------------------------
    target_adoption = clamp(
        1.0 + 0.8 * (utilisation - 0.5) + 0.5 * (state.sentiment - 0.5),
        0.2,
        3.0,
    )
    state.adoption = clamp(
        state.adoption + social.adoption_adaptivity * (target_adoption - state.adoption),
        0.2,
        3.0,
    )


def trader_pressure(agents: list[Agent], config: SimConfig, momentum: float) -> float:
    """Extra sell/buy pressure from traders.

    Traders move the *price*, not the *supply*: they cannot mint tokens. So they
    appear as pressure on the index, never as a balance change.
    """
    traders = active_agents(agents, Role.TRADER)
    if not traders:
        return 0.0
    share = len(traders) / max(config.population, 1)
    return -config.agents.trader_aggressiveness * share * momentum
