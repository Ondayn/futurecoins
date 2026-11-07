"""Agents: the individual participants of the simulated network.

An agent is one emoji on the grid (or one member of a cohort when the population
is larger than the grid). Agents have a role, a balance, and a small set of
behaviour rules.

Design note
-----------
There is deliberately no class hierarchy (no MinerAgent subclass, no
ValidatorAgent subclass). Roles differ by a handful of numbers and one `match`
statement. Five subclasses would be five places to look for the same bug.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from .config import SimConfig


class Role(str, Enum):
    """Who an agent is in the network."""

    MINER = "miner"
    VALIDATOR = "validator"
    USER = "user"
    TRADER = "trader"
    DEVELOPER = "developer"
    ATTACKER = "attacker"


# Presentation data for each role. Emoji are single codepoints (no ZWJ
# sequences) so they render consistently across operating systems.
ROLE_META: dict[Role, dict[str, str]] = {
    Role.MINER: {"emoji": "⛏️", "ascii": "M", "label": "Miner", "css": "miner"},
    Role.VALIDATOR: {"emoji": "✅", "ascii": "V", "label": "Validator", "css": "validator"},
    Role.USER: {"emoji": "👤", "ascii": "u", "label": "User", "css": "user"},
    Role.TRADER: {"emoji": "📈", "ascii": "T", "label": "Trader", "css": "trader"},
    Role.DEVELOPER: {"emoji": "💻", "ascii": "D", "label": "Developer", "css": "developer"},
    Role.ATTACKER: {"emoji": "🏴", "ascii": "A", "label": "Attacker", "css": "attacker"},
}

PRODUCER_ROLES = (Role.MINER, Role.VALIDATOR)


@dataclass
class Agent:
    """One simulated participant.

    Attributes
    ----------
    capacity:
        Hashrate for a miner, stake for a validator, unused for other roles.
        This is what determines a producer's share of block rewards.
    cost_per_tick:
        What it costs this agent to keep operating, in tokens per tick.
    streak_bad / streak_good:
        Consecutive losing / winning ticks. These implement *hysteresis*: an
        agent does not flip between active and inactive on a single bad tick.
        Without them the grid strobes every frame.
    """

    id: int
    role: Role
    row: int
    col: int
    balance: float = 0.0
    active: bool = True
    confidence: float = 0.5
    capacity: float = 1.0
    cost_per_tick: float = 0.0
    streak_bad: int = 0
    streak_good: int = 0
    age: int = 0

    # Ticks during which this agent must stay offline, even if conditions
    # improve. Events that force a producer offline use this so the normal
    # "rewards look good again" rule cannot undo the shock on the next tick.
    cooldown: int = 0

    @property
    def is_producer(self) -> bool:
        return self.role in PRODUCER_ROLES

    @property
    def emoji(self) -> str:
        return ROLE_META[self.role]["emoji"]

    def ascii(self) -> str:
        return ROLE_META[self.role]["ascii"]


def role_counts(config: SimConfig) -> dict[Role, int]:
    """How many agents of each role this configuration asks for.

    Miners only exist under Proof of Work, validators only under Proof of Stake.
    A network with both would need a hybrid consensus model, which is out of
    scope for the MVP.
    """
    a = config.agents
    counts = {
        Role.MINER: 0,
        Role.VALIDATOR: 0,
        Role.USER: a.n_users,
        Role.TRADER: a.n_traders,
        Role.DEVELOPER: a.n_developers,
        Role.ATTACKER: a.n_attackers,
    }
    if config.network.consensus == "pow":
        counts[Role.MINER] = a.n_miners
    else:
        counts[Role.VALIDATOR] = a.n_validators
    return counts


# Share of the initial supply handed to each role at genesis. Producers get a
# smaller slice: their income comes from block rewards, not from a premine.
_GENESIS_SHARES: dict[Role, float] = {
    Role.USER: 0.55,
    Role.TRADER: 0.20,
    Role.DEVELOPER: 0.10,
    Role.MINER: 0.075,
    Role.VALIDATOR: 0.075,
    Role.ATTACKER: 0.0,
}


def make_population(config: SimConfig, rng: random.Random) -> list[Agent]:
    """Create the starting agents and place them on the grid.

    Placement is deterministic: the same seed always produces the same grid.
    Cells are shuffled once and dealt out; when there are more agents than
    cells, several agents share a cell (a *cohort*).

    Parameters
    ----------
    config:
        Frozen simulation configuration.
    rng:
        The simulation's seeded random generator. Never use the global `random`
        module here, or runs stop being reproducible.
    """
    counts = role_counts(config)
    cells = [(r, c) for r in range(config.rows) for c in range(config.cols)]
    rng.shuffle(cells)

    # Distribute the non-treasury part of the initial supply.
    distributable = config.monetary.initial_supply * (1.0 - config.monetary.treasury_fraction)
    total_population = sum(counts.values())

    agents: list[Agent] = []
    next_id = 0
    cell_index = 0

    # Fixed role order => deterministic ids => deterministic behaviour.
    for role in (Role.MINER, Role.VALIDATOR, Role.USER, Role.TRADER, Role.DEVELOPER, Role.ATTACKER):
        n = counts[role]
        if n <= 0:
            continue

        pool = distributable * _GENESIS_SHARES.get(role, 0.0)
        per_agent = pool / n if n else 0.0

        for _ in range(n):
            row, col = cells[cell_index % len(cells)]
            cell_index += 1

            if role is Role.MINER:
                capacity = config.agents.hashrate_per_miner
                cost = config.agents.miner_cost_per_tick
            elif role is Role.VALIDATOR:
                capacity = config.agents.stake_per_validator
                cost = config.agents.validator_cost_per_tick
            else:
                capacity = 1.0
                cost = 0.0

            agents.append(
                Agent(
                    id=next_id,
                    role=role,
                    row=row,
                    col=col,
                    balance=per_agent,
                    active=True,
                    confidence=min(1.0, max(0.0, 0.5 + rng.uniform(-0.1, 0.1))),
                    capacity=capacity,
                    cost_per_tick=cost,
                )
            )
            next_id += 1

    # Keep ids contiguous and ordered. `next_id` should equal len(agents), but
    # assert it so a future edit cannot silently break determinism.
    assert next_id == total_population, "population bookkeeping is inconsistent"
    return agents


def active_agents(agents: list[Agent], role: Role | None = None) -> list[Agent]:
    """Active agents, optionally filtered by role. Iterates in id order."""
    return [a for a in agents if a.active and (role is None or a.role is role)]
