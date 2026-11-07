"""Random events: economic, technical and social shocks.

An event is **data**, not code. That matters for three reasons:

1. It can be validated, listed and explained by the interface without special cases.
2. It can later be loaded from a JSON rules file (post-MVP) without executing
   arbitrary Python.
3. Its severity can depend on the player's configuration, which is what makes
   "a validator exodus is worse in a small network" a real mechanic rather than
   a sentence in the documentation.

Attackers and security incidents are modelled as *pressure on numbers*. We never
describe how to perform an attack.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from .agents import Agent, active_agents
from .config import SimConfig
from .economy import clamp

Category = Literal["economic", "technical", "social"]


@dataclass(frozen=True)
class Condition:
    """A declarative trigger condition, e.g. health < 50.

    Declarative on purpose: a dict of these can be serialised to JSON later,
    whereas a Python lambda cannot.
    """

    metric: str
    op: Literal["<", "<=", ">", ">="]
    value: float

    def holds(self, metrics: dict[str, float]) -> bool:
        actual = metrics.get(self.metric)
        if actual is None:
            return False
        if self.op == "<":
            return actual < self.value
        if self.op == "<=":
            return actual <= self.value
        if self.op == ">":
            return actual > self.value
        return actual >= self.value


@dataclass(frozen=True)
class Modifiers:
    """Multipliers and offsets applied for this tick only."""

    capacity: float = 1.0        # multiplies transactions per block
    activity: float = 1.0        # multiplies user demand
    sentiment: float = 0.0       # added to the sentiment target
    price_shock: float = 0.0     # added to this tick's log return
    producer_exit: float = 0.0   # fraction of producers forced offline

    def combined(self, other: Modifiers) -> Modifiers:
        return Modifiers(
            capacity=self.capacity * other.capacity,
            activity=self.activity * other.activity,
            sentiment=self.sentiment + other.sentiment,
            price_shock=self.price_shock + other.price_shock,
            producer_exit=max(self.producer_exit, other.producer_exit),
        )


@dataclass(frozen=True)
class EventSpec:
    """The static definition of an event."""

    id: str
    name: str
    category: Category
    base_severity: float
    duration_ticks: int
    effects: Modifiers
    conditions: tuple[Condition, ...] = ()
    explanation: str = ""


@dataclass
class ActiveEvent:
    """An event currently in progress."""

    spec: EventSpec
    severity: float
    ticks_left: int
    started_tick: int


@dataclass(frozen=True)
class EventLogEntry:
    """One line in the event log, already written as a human sentence."""

    tick: int
    event_id: str
    name: str
    category: Category
    severity: float
    message: str


@dataclass(frozen=True)
class EventOutcome:
    modifiers: Modifiers
    entries: tuple[EventLogEntry, ...]
    producer_exit: float = 0.0


def default_events(config: SimConfig) -> list[EventSpec]:
    """The MVP event set. Probabilities come from the player's config."""
    return [
        EventSpec(
            id="market_crash",
            name="Market Crash",
            category="economic",
            base_severity=0.55,
            duration_ticks=4,
            effects=Modifiers(sentiment=-0.22, price_shock=-0.14, activity=0.80),
            explanation=(
                "A price fall becomes a confidence fall, which becomes more selling. "
                "This is reflexivity: the market's mood feeds its own price."
            ),
        ),
        EventSpec(
            id="network_congestion",
            name="Network Congestion",
            category="technical",
            base_severity=0.45,
            duration_ticks=3,
            effects=Modifiers(capacity=0.40, activity=1.0),
            conditions=(Condition("congestion", ">", 0.35),),
            explanation=(
                "When demand exceeds capacity, fees rise. Fees are how a network rations "
                "scarce blockspace — and how it pushes marginal users away."
            ),
        ),
        EventSpec(
            id="negative_media",
            name="Negative Media Coverage",
            category="social",
            base_severity=0.40,
            duration_ticks=5,
            effects=Modifiers(sentiment=-0.18, activity=0.90),
            explanation=(
                "Narrative is an economic force. Coverage changes who trusts the network, "
                "and trust changes how many people use it."
            ),
        ),
        EventSpec(
            id="validator_exodus",
            name="Validator Exodus",
            category="technical",
            base_severity=0.50,
            duration_ticks=3,
            effects=Modifiers(producer_exit=0.25),
            conditions=(Condition("participation", "<", 0.75),),
            explanation=(
                "When rewards stop covering costs, producers leave. In a small network "
                "each departure hurts more: security scales with participation."
            ),
        ),
    ]


class EventEngine:
    """Decides which events are active, and what they do this tick."""

    def __init__(self, config: SimConfig) -> None:
        self.config = config
        self.specs = default_events(config)
        self.active: dict[str, ActiveEvent] = {}

    # -- public API ---------------------------------------------------------

    def step(
        self,
        tick: int,
        metrics: dict[str, float],
        agents: list[Agent],
        rng: random.Random,
    ) -> EventOutcome:
        self._expire()
        entries: list[EventLogEntry] = []

        if self.config.events.enabled:
            for spec in self.specs:
                if spec.id in self.active:
                    continue
                if not all(c.holds(metrics) for c in spec.conditions):
                    continue

                probability = self._probability(spec) * self.config.events.probability_scale
                if rng.random() >= probability:
                    continue

                severity = self._severity(spec, metrics)
                self.active[spec.id] = ActiveEvent(
                    spec=spec, severity=severity, ticks_left=spec.duration_ticks, started_tick=tick
                )
                entries.append(
                    EventLogEntry(
                        tick=tick,
                        event_id=spec.id,
                        name=spec.name,
                        category=spec.category,
                        severity=severity,
                        message=self._message(spec, severity, metrics, agents),
                    )
                )

        return EventOutcome(
            modifiers=self._modifiers(),
            entries=tuple(entries),
            producer_exit=self._producer_exit(),
        )

    @property
    def active_names(self) -> list[str]:
        return [e.spec.name for e in self.active.values()]

    # -- internals ----------------------------------------------------------

    def _expire(self) -> None:
        for event_id in list(self.active):
            self.active[event_id].ticks_left -= 1
            if self.active[event_id].ticks_left <= 0:
                del self.active[event_id]

    def _probability(self, spec: EventSpec) -> float:
        params = self.config.events
        return {
            "market_crash": params.crash_probability,
            "network_congestion": params.congestion_probability,
            "negative_media": params.media_probability,
            "validator_exodus": params.exodus_probability,
        }.get(spec.id, 0.0)

    def _severity(self, spec: EventSpec, metrics: dict[str, float]) -> float:
        """Severity depends on the player's configuration, not only on the dice.

        A healthy, decentralized network absorbs a shock. A concentrated,
        barely-alive network amplifies it. That is the mechanic.
        """
        if spec.id == "validator_exodus":
            participation = metrics.get("participation", 1.0)
            return clamp(spec.base_severity * (1.0 + 2.0 * (1.0 - participation)), 0.0, 1.0)

        health = metrics.get("health", 50.0)
        resilience = 0.5 * (health / 100.0)
        concentration_penalty = 1.0 - self.config.social.decentralization
        return clamp(
            spec.base_severity * (1.0 + 0.5 * concentration_penalty) * (1.0 - resilience),
            0.0,
            1.0,
        )

    def _modifiers(self) -> Modifiers:
        combined = Modifiers()
        for event in self.active.values():
            scale = event.severity
            effects = event.spec.effects
            combined = combined.combined(
                Modifiers(
                    # Interpolate towards 1.0 by severity: a weak event barely moves.
                    capacity=1.0 + (effects.capacity - 1.0) * scale,
                    activity=1.0 + (effects.activity - 1.0) * scale,
                    sentiment=effects.sentiment * scale,
                    price_shock=effects.price_shock * scale,
                    producer_exit=effects.producer_exit * scale,
                )
            )
        return combined

    def _producer_exit(self) -> float:
        return max((e.spec.effects.producer_exit * e.severity for e in self.active.values()), default=0.0)

    def _message(
        self,
        spec: EventSpec,
        severity: float,
        metrics: dict[str, float],
        agents: list[Agent],
    ) -> str:
        sentiment = metrics.get("sentiment", 0.5) * 100
        utilisation = metrics.get("congestion", 0.0)
        fee = metrics.get("avg_fee", 0.0)
        dropped = metrics.get("dropped_txs", 0.0)

        if spec.id == "market_crash":
            return (
                f"Market crash: the price index fell about {severity * 35:.0f} % and sentiment "
                f"dropped to {sentiment:.0f}/100. Traders sold into the panic."
            )
        if spec.id == "network_congestion":
            return (
                f"Network congestion: demand reached {utilisation:.0%} of capacity. Fees rose to "
                f"{fee:.3f} per transaction and {dropped:.0f} transactions were dropped."
            )
        if spec.id == "negative_media":
            return (
                f"Negative media coverage: public confidence fell to {sentiment:.0f}/100. "
                "Some users are going inactive until the story changes."
            )
        if spec.id == "validator_exodus":
            producers = [a for a in active_agents(agents) if a.is_producer]
            # Severity is already the scaled fraction. Do not scale it twice.
            n = round(len(producers) * 0.25 * severity)
            return (
                f"Validator exodus: {n} producers went offline because rewards no longer covered "
                "their operating costs. Block production slowed down."
            )
        return f"{spec.name} (severity {severity:.2f})."
