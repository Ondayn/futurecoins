"""The simulation engine.

This is the heart of FutureCoins. It is **pure Python**: no Streamlit, no
network, no filesystem, no wall-clock time. Given the same config and seed it
produces the same run, every time.

That property is what makes the game testable, replayable and honest: an
achievement can record a config hash and a seed, and anyone can reproduce the
exact run that earned it.

Time model
----------
1 tick = 1 simulated hour. Blocks are produced *inside* the tick:

    blocks_per_tick = 3600 / block_time_s

So a 600-second block time gives 6 blocks per tick, and a simulated year is
8 760 ticks. See docs/ARCHITECTURE.md section 4.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

from . import consensus, economy
from .agents import Agent, Role, active_agents, make_population
from .config import SimConfig
from .economy import EconomyState, MempoolOutcome, clamp
from .events import EventEngine, EventLogEntry
from .metrics import Metrics, network_health


@dataclass(frozen=True)
class TickResult:
    """Everything the interface needs to know about one tick.

    The UI never reaches into agents or internal state. It reads this.
    """

    tick: int
    metrics: Metrics
    events: tuple[EventLogEntry, ...] = ()
    changes: tuple[str, ...] = ()


class Simulation:
    """One running simulated currency."""

    def __init__(self, config: SimConfig) -> None:
        self.config = config
        self.reset()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Return to tick 0 with the same configuration and seed."""
        cfg = self.config
        self.rng = random.Random(cfg.seed)

        self.agents: list[Agent] = make_population(cfg, self.rng)
        self._by_id: dict[int, Agent] = {a.id: a for a in self.agents}

        self.tick = 0
        self.total_blocks = 0.0
        self.issuance_total = 0.0
        self.burn_total = 0.0
        self.treasury = cfg.monetary.initial_supply * cfg.monetary.treasury_fraction

        self.economy = EconomyState(
            price=100.0,
            sentiment=cfg.social.initial_sentiment,
            adoption=1.0,
            volatility=0.0,
        )

        self.events = EventEngine(cfg)

        # Developers improve this over time. 1.0 = baseline capacity.
        self.capacity_multiplier = 1.0

        self.history: list[Metrics] = []
        self.recent_changes: deque[str] = deque(maxlen=40)
        self.event_history: list[EventLogEntry] = []
        self.last_production = consensus.BlockProduction()
        self.last_mempool = MempoolOutcome()

        self._metrics = self._compute_metrics(
            production=consensus.BlockProduction(),
            mempool=MempoolOutcome(),
            availability=0.0,
            reliability=1.0,
            security=0.0,
            concentration=1.0,
        )
        self.history.append(self._metrics)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def metrics(self) -> Metrics:
        return self._metrics

    @property
    def total_supply(self) -> float:
        return self.config.monetary.initial_supply + self.issuance_total - self.burn_total

    @property
    def circulating_supply(self) -> float:
        return self.total_supply - self.treasury

    def run_tick(self) -> TickResult:
        """Advance the simulation by one simulated hour."""
        self.tick += 1
        previous = self._metrics.as_dict()

        # 1. Events: expire old ones, maybe start a new one.
        outcome = self.events.step(self.tick, previous, self.agents, self.rng)
        mods = outcome.modifiers
        for entry in outcome.entries:
            self.event_history.append(entry)
            self.recent_changes.append(f"Tick {entry.tick} · {entry.message}")

        if outcome.producer_exit > 0:
            self._force_producer_exit(outcome.producer_exit)

        # 2. Capacity for this tick. Slow block production means less room.
        base_availability = consensus.availability(self.config, self.agents)
        availability = base_availability * (1.0 - outcome.producer_exit)

        blocks = self.config.blocks_per_tick * availability
        capacity = (
            self.config.network.tx_per_block
            * blocks
            * mods.capacity
            * self.capacity_multiplier
        )

        # 3. Users create demand.
        demand = economy.generate_demand(
            self.config,
            self.agents,
            self.economy.sentiment,
            self.economy.adoption,
            mods.activity,
        )

        # 4. Mempool: price the transactions, decide how many fit.
        mempool = economy.settle_mempool(self.config, demand, capacity)

        # 5. Fees are capped by what users can actually pay. Early networks with
        #    no coins in circulation collect no fees — which is historically
        #    accurate for Bitcoin's first months.
        users = active_agents(self.agents, Role.USER)
        user_pool = sum(a.balance for a in users)
        paid_fees = min(mempool.fees_pool, max(0.0, user_pool))
        if user_pool > 0 and paid_fees > 0:
            for user in users:
                user.balance -= paid_fees * (user.balance / user_pool)

        # 6. Block production and rewards.
        production = consensus.produce(
            self.config,
            self.agents,
            total_blocks=self.total_blocks,
            total_supply=self.total_supply,
            fees_pool=paid_fees,
            availability_override=availability,
        )

        # 7. Apply rewards, fees and burns to balances and supply.
        for agent_id, amount in production.reward_by_agent.items():
            self._by_id[agent_id].balance += amount
        for agent_id, amount in production.fees_by_agent.items():
            self._by_id[agent_id].balance += amount

        self.issuance_total += production.issuance
        burned = paid_fees * self.config.monetary.burn_rate
        self.burn_total += burned
        self.total_blocks += production.blocks

        # 8. Producers sell part of their income to pay operating costs. This is
        #    how coins reach users in a network with no premine.
        self._circulate_producer_proceeds(production)

        # 9. Agents react.
        self._update_producer_behaviour(production, availability)
        self._update_user_behaviour(mempool)
        self._update_developers()

        # 10. Economy reacts to this tick's activity.
        participation = self._participation()
        security = consensus.security_margin(self.config, self.agents, availability)
        reliability = self._reliability(mempool)

        health = network_health(
            participation=participation,
            concentration=production.concentration,
            reliability=reliability,
            security=security,
            sentiment=self.economy.sentiment,
        )

        supply_denominator = max(self.total_supply, production.issuance, 1.0)
        economy.update_economy(
            self.economy,
            self.config,
            health=health,
            utilisation=mempool.utilisation,
            reliability=reliability,
            inflation_fraction=production.issuance / supply_denominator,
            price_shock=mods.price_shock,
            sentiment_shock=mods.sentiment,
            trader_pressure=economy.trader_pressure(
                self.agents, self.config, self.economy.last_log_return
            ),
            rng=self.rng,
        )

        # 11. Metrics snapshot.
        self._metrics = self._compute_metrics(
            production=production,
            mempool=mempool,
            availability=availability,
            reliability=reliability,
            security=security,
            concentration=production.concentration,
        )
        self.history.append(self._metrics)
        if len(self.history) > 2000:
            del self.history[: len(self.history) - 2000]

        self.last_production = production
        self.last_mempool = mempool

        changes = tuple(self.recent_changes)[-3:]
        return TickResult(
            tick=self.tick,
            metrics=self._metrics,
            events=outcome.entries,
            changes=changes,
        )

    def run(self, ticks: int) -> list[TickResult]:
        """Advance several ticks. Used by tests and by the fast-forward button."""
        return [self.run_tick() for _ in range(max(0, ticks))]

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    def _participation(self) -> float:
        total = len(self.agents)
        if total == 0:
            return 0.0
        return sum(1 for a in self.agents if a.active) / total

    def _reliability(self, mempool: MempoolOutcome) -> float:
        """Share of attempted transactions that made it in, minus invalid ones.

        Attackers do not steal anything in this model. They make the network
        noisier and less trustworthy, which is the educational point.
        """
        attackers = len(active_agents(self.agents, Role.ATTACKER))
        invalid_rate = 0.02 * (attackers / 10.0) * (1.0 - self._security_guess())
        return clamp(mempool.reliability * (1.0 - invalid_rate), 0.0, 1.0)

    def _security_guess(self) -> float:
        return consensus.security_margin(
            self.config, self.agents, consensus.availability(self.config, self.agents)
        )

    def _force_producer_exit(self, fraction: float) -> None:
        """Take the weakest producers offline. Deterministic: lowest balance first."""
        producers = [a for a in self.agents if a.is_producer and a.active]
        if not producers:
            return
        count = max(1, round(len(producers) * fraction))
        weakest = sorted(producers, key=lambda a: (a.balance, a.id))[:count]
        for agent in weakest:
            agent.active = False
            agent.streak_bad = 0
            agent.streak_good = 0
            agent.cooldown = self.config.agents.entry_patience_ticks
        self.recent_changes.append(
            f"Tick {self.tick} · {count} producers forced offline by an event."
        )

    def _circulate_producer_proceeds(self, production: consensus.BlockProduction) -> None:
        """Producers sell a share of their income to users to cover costs.

        Total supply is unchanged: this is a transfer, not issuance. It is what
        lets a currency with no premine (Bitcoin 2009) develop a user economy.
        """
        users = active_agents(self.agents, Role.USER)
        if not users:
            return

        sold = 0.0
        propensity = self.config.social.sell_propensity
        for agent_id, amount in production.reward_by_agent.items():
            producer = self._by_id[agent_id]
            income = amount + production.fees_by_agent.get(agent_id, 0.0)
            transfer = min(producer.balance, income * propensity)
            producer.balance -= transfer
            sold += transfer

        if sold <= 0:
            return

        share = sold / len(users)
        for user in users:
            user.balance += share

    def _update_producer_behaviour(
        self, production: consensus.BlockProduction, availability: float
    ) -> None:
        producers = [a for a in self.agents if a.is_producer and a.active]
        average_income = 0.0
        if producers:
            average_income = (production.issuance + production.distributable_fees) / len(producers)

        exited = 0
        joined = 0

        for agent in self.agents:
            if not agent.is_producer:
                continue

            # A forced exit (event) sets a cooldown. Honour it before the normal
            # entry/exit rules get a chance to react.
            if agent.cooldown > 0:
                agent.cooldown -= 1
                continue

            if agent.active:
                income = production.reward_by_agent.get(
                    agent.id, 0.0
                ) + production.fees_by_agent.get(agent.id, 0.0)
                profit = income - agent.cost_per_tick

                if profit < 0:
                    agent.streak_bad += 1
                    agent.streak_good = 0
                else:
                    agent.streak_good += 1
                    agent.streak_bad = 0

                if agent.streak_bad >= self.config.agents.exit_patience_ticks:
                    agent.active = False
                    agent.streak_bad = 0
                    exited += 1
            else:
                # Would it be worth coming back? Compare expected income to cost.
                if average_income > agent.cost_per_tick:
                    agent.streak_good += 1
                else:
                    agent.streak_good = 0

                if agent.streak_good >= self.config.agents.entry_patience_ticks:
                    agent.active = True
                    agent.streak_good = 0
                    joined += 1

        if exited >= 3:
            self.recent_changes.append(
                f"Tick {self.tick} · {exited} producers went offline: reward per tick "
                f"({average_income:.2f}) no longer covered operating cost."
            )
        if joined >= 3:
            self.recent_changes.append(
                f"Tick {self.tick} · {joined} producers came back online as rewards recovered."
            )

    def _update_user_behaviour(self, mempool: MempoolOutcome) -> None:
        cfg = self.config
        base_fee = max(cfg.network.base_fee, 1e-9)
        expensive = mempool.fee > 3.0 * base_fee
        unreliable = mempool.reliability < 0.80

        for agent in self.agents:
            if agent.role is not Role.USER:
                continue

            if agent.active:
                target = self.economy.sentiment
                agent.confidence += 0.10 * (target - agent.confidence) + self.rng.gauss(0.0, 0.02)
                if expensive:
                    agent.confidence -= 0.03
                if unreliable:
                    agent.confidence -= 0.03
                agent.confidence = clamp(agent.confidence, 0.0, 1.0)

                if agent.confidence < cfg.agents.churn_confidence_threshold:
                    agent.streak_bad += 1
                else:
                    agent.streak_bad = 0

                if agent.streak_bad >= cfg.agents.exit_patience_ticks:
                    agent.active = False
                    agent.streak_bad = 0
            else:
                if self.economy.sentiment > 0.60:
                    agent.streak_good += 1
                else:
                    agent.streak_good = 0

                if agent.streak_good >= cfg.agents.entry_patience_ticks:
                    agent.active = True
                    agent.streak_good = 0
                    agent.confidence = 0.5

    def _update_developers(self) -> None:
        """Developers slowly raise capacity. This is the 'upgrade' abstraction."""
        devs = len(active_agents(self.agents, Role.DEVELOPER))
        if devs == 0:
            return
        growth = self.config.agents.dev_improvement_rate * (devs / 100.0)
        self.capacity_multiplier = min(3.0, self.capacity_multiplier * (1.0 + growth))

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _compute_metrics(
        self,
        *,
        production: consensus.BlockProduction,
        mempool: MempoolOutcome,
        availability: float,
        reliability: float,
        security: float,
        concentration: float,
    ) -> Metrics:
        total_nodes = len(self.agents)
        active_nodes = sum(1 for a in self.agents if a.active)
        participation = active_nodes / total_nodes if total_nodes else 0.0

        total_supply = self.total_supply
        block_interval = (
            self.config.network.block_time_s / availability if availability > 0 else 0.0
        )

        health = network_health(
            participation=participation,
            concentration=concentration,
            reliability=reliability,
            security=security,
            sentiment=self.economy.sentiment,
        )

        inflation_rate = 0.0
        if total_supply > 1.0:
            # Annualised: 8 760 ticks in a simulated year.
            inflation_rate = (production.issuance * 8760.0 / total_supply) * 100.0

        return Metrics(
            tick=self.tick,
            active_nodes=active_nodes,
            total_nodes=total_nodes,
            participation=participation,
            total_supply=total_supply,
            circulating_supply=self.circulating_supply,
            burned_total=self.burn_total,
            treasury=self.treasury,
            inflation_rate=inflation_rate,
            price=self.economy.price,
            volatility=self.economy.volatility,
            sentiment=self.economy.sentiment,
            health=health,
            reliability=reliability,
            concentration=concentration,
            security=security,
            block_interval=block_interval,
            tps=mempool.included / 3600.0,
            avg_fee=mempool.fee,
            congestion=mempool.congestion,
            blocks_total=self.total_blocks,
            dropped_txs=mempool.dropped,
        )
