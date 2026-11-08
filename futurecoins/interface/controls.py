"""Sidebar configuration.

The sidebar writes a *new* `SimConfig` on every rerun. Nothing is applied to
the running simulation until the player presses **Launch** — that is what makes
the frozen-config promise real.

Two modes share one code path:

- Beginner exposes eight consequential controls.
- Advanced adds capacity, burn, per-role populations, costs, event frequency
  and the market's damping constants.

Widget defaults live in `st.session_state` so that choosing a preset replaces
the values cleanly, including when the previous widget keys still exist.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import streamlit as st

from ..agents import Role, role_counts
from ..config import DEFAULT_CONFIG, NEVER, SimConfig
from ..education import short as glossary_short

_MODE_KEY = "fc_mode"


# ---------------------------------------------------------------------------
# Preset plumbing
# ---------------------------------------------------------------------------


def _defaults(config: SimConfig) -> dict[str, Any]:
    """Widget values implied by a configuration."""
    monetary = config.monetary
    network = config.network
    social = config.social

    return {
        "cfg_consensus": network.consensus,
        "cfg_block_time": round(min(max(network.block_time_s, 1.0), 900.0)),
        "cfg_initial_supply": float(monetary.initial_supply),
        "cfg_no_cap": monetary.max_supply is None,
        "cfg_max_supply": float(monetary.max_supply or 21_000_000.0),
        "cfg_block_reward": float(min(max(monetary.initial_block_reward, 0.0), 100.0)),
        "cfg_never_halve": monetary.halving_interval_blocks >= NEVER / 10,
        "cfg_halving": int(
            monetary.halving_interval_blocks
            if monetary.halving_interval_blocks < NEVER / 10
            else 210_000
        ),
        "cfg_base_fee": float(network.base_fee),
        "cfg_population": int(min(max(config.population, 50), 5_000)),
        "cfg_tx_per_block": int(network.tx_per_block),
        "cfg_burn_rate": float(monetary.burn_rate),
        "cfg_seed": int(config.seed),
        "cfg_sentiment_adaptivity": float(social.sentiment_adaptivity),
        "cfg_liquidity": float(social.liquidity),
        "cfg_decentralization": float(social.decentralization),
        "cfg_media_bias": float(social.media_bias),
        "cfg_institutional": float(social.institutional_participation),
        "cfg_event_scale": float(config.events.probability_scale),
        "cfg_target_stake": float(network.target_stake_fraction),
        "cfg_miner_cost": float(config.agents.miner_cost_per_tick),
        "cfg_validator_cost": float(config.agents.validator_cost_per_tick),
        "cfg_user_tx": float(config.agents.user_tx_per_tick),
        "cfg_trader_aggression": float(config.agents.trader_aggressiveness),
    }


def apply_preset(config: SimConfig) -> None:
    """Copy a preset into the widget state.

    Called when the player picks a preset, *before* the widgets are created.
    Also records the role mix so that the population slider can rescale without
    drifting a little further on every rerun.
    """
    st.session_state["_fc_base"] = config
    st.session_state["_fc_role_mix"] = dict(role_counts(config))

    for key, value in _defaults(config).items():
        st.session_state[key] = value

    counts = role_counts(config)
    for role in Role:
        st.session_state[f"cfg_n_{role.value}s"] = int(counts.get(role, 0))


# ---------------------------------------------------------------------------
# Population helpers
# ---------------------------------------------------------------------------


def _scale_counts(mix: dict[Role, int], total: int) -> dict[Role, int]:
    """Scale a role mix to a total, preserving proportions and nonzero roles.

    Integer rounding is handled with largest-remainder, so the counts always sum
    exactly to ``total``. Roles that were zero stay zero.
    """
    total = max(int(total), 1)
    positive = {role: n for role, n in mix.items() if n > 0}
    if not positive:
        return {role: 0 for role in mix}

    current = sum(positive.values())
    raw = {role: positive[role] * total / current for role in positive}
    counts = {role: max(1, int(raw[role])) for role in positive}

    order = sorted(positive, key=lambda role: (-(raw[role] - int(raw[role])), role.value))
    index = 0
    while sum(counts.values()) < total:
        counts[order[index % len(order)]] += 1
        index += 1
    while sum(counts.values()) > total:
        role = order[index % len(order)]
        if counts[role] > 1:
            counts[role] -= 1
        index += 1
        if index > 10_000:  # defensive: should be unreachable
            break

    return {role: counts.get(role, 0) for role in mix}


def _producer_mix(mix: dict[Role, int], consensus: str) -> dict[Role, int]:
    """Make the mix match the chosen consensus.

    Switching PoW -> PoS should not silently produce a network with zero
    validators. The old producer count is reused, with a sane default.
    """
    result = dict(mix)
    if consensus == "pow":
        previous = result.get(Role.VALIDATOR, 0)
        result[Role.VALIDATOR] = 0
        if result.get(Role.MINER, 0) <= 0:
            result[Role.MINER] = previous or 120
    else:
        previous = result.get(Role.MINER, 0)
        result[Role.MINER] = 0
        if result.get(Role.VALIDATOR, 0) <= 0:
            result[Role.VALIDATOR] = previous or 80
    return result


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


def _consensus_widget() -> str:
    return st.selectbox(
        "Consensus mechanism",
        options=["pow", "pos"],
        key="cfg_consensus",
        format_func=lambda value: "Proof of Work (miners)" if value == "pow" else "Proof of Stake (validators)",
        help=glossary_short("Consensus mechanism"),
    )


def _beginner_widgets() -> None:
    st.slider(
        "Target block time (seconds)",
        min_value=1,
        max_value=900,
        step=1,
        key="cfg_block_time",
        help=glossary_short("Block time"),
    )
    st.number_input(
        "Initial supply (tokens)",
        min_value=0.0,
        max_value=1_000_000_000.0,
        step=1_000_000.0,
        format="%.0f",
        key="cfg_initial_supply",
        help=glossary_short("Initial supply"),
    )
    st.checkbox(
        "No hard supply cap",
        key="cfg_no_cap",
        help=glossary_short("Supply cap"),
    )
    if not st.session_state["cfg_no_cap"]:
        st.number_input(
            "Maximum supply (tokens)",
            min_value=1_000_000.0,
            max_value=1_000_000_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key="cfg_max_supply",
            help=glossary_short("Supply cap"),
        )
    st.slider(
        "Initial block reward (tokens)",
        min_value=0.0,
        max_value=100.0,
        step=0.5,
        key="cfg_block_reward",
        help=glossary_short("Block reward"),
    )
    st.checkbox(
        "Never halve the reward",
        key="cfg_never_halve",
        help=glossary_short("Halving"),
    )
    if not st.session_state["cfg_never_halve"]:
        st.number_input(
            "Halving interval (blocks)",
            min_value=10_000,
            max_value=1_000_000,
            step=10_000,
            key="cfg_halving",
            help=glossary_short("Halving"),
        )
    st.number_input(
        "Base transaction fee (tokens)",
        min_value=0.0,
        max_value=10.0,
        step=0.001,
        format="%.4f",
        key="cfg_base_fee",
        help=glossary_short("Fee"),
    )
    pop = st.slider(
        "Population (agents)",
        min_value=50,
        max_value=5_000,
        step=1,
        key="cfg_population",
        help="Total agents. If population exceeds grid cells (900), the grid shows a deterministic 1:1 sampled view; real totals still count.",
    )
    if pop > 3000:
        st.warning(
            "Very high starting population for a new network (unrealistic for genesis). "
            "Consider 200–1,200 for clearer dynamics; large populations can mask early effects.",
            icon="⚠️",
        )
    elif pop > 1200:
        st.info(
            "Large starting population. For a first run, 200–900 agents is often more realistic and easier to interpret.",
            icon="ℹ️",
        )


def _advanced_widgets() -> None:
    st.number_input(
        "Transactions per block",
        min_value=10,
        max_value=100_000,
        step=100,
        key="cfg_tx_per_block",
        help=glossary_short("Throughput (TPS)"),
    )
    st.slider(
        "Fee burn rate",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        key="cfg_burn_rate",
        help=glossary_short("Burn"),
    )
    st.slider(
        "Target staked fraction (PoS)",
        min_value=0.01,
        max_value=1.0,
        step=0.01,
        key="cfg_target_stake",
        help=glossary_short("Stake"),
    )

    consensus = st.session_state["cfg_consensus"]
    st.markdown("**Population by role**")
    if consensus == "pow":
        st.number_input("Miners", min_value=0, max_value=2_000, step=10, key="cfg_n_miners")
    else:
        st.number_input("Validators", min_value=0, max_value=2_000, step=10, key="cfg_n_validators")
    st.number_input("Users", min_value=0, max_value=4_000, step=10, key="cfg_n_users")
    st.number_input("Traders", min_value=0, max_value=2_000, step=10, key="cfg_n_traders")
    st.number_input("Developers", min_value=0, max_value=1_000, step=10, key="cfg_n_developers")
    st.number_input("Attackers", min_value=0, max_value=500, step=5, key="cfg_n_attackers")

    st.markdown("**Costs and behaviour**")
    st.number_input(
        "Miner cost / tick",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        key="cfg_miner_cost",
        help=glossary_short("Miner"),
    )
    st.number_input(
        "Validator cost / tick",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        key="cfg_validator_cost",
        help=glossary_short("Validator"),
    )
    st.number_input(
        "User transactions / tick",
        min_value=0.0,
        max_value=100.0,
        step=0.5,
        key="cfg_user_tx",
        help=glossary_short("Mempool"),
    )
    st.slider(
        "Trader aggressiveness",
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        key="cfg_trader_aggression",
        help=glossary_short("Trader pressure"),
    )

    st.markdown("**Market and events**")
    st.slider(
        "Sentiment adaptivity",
        min_value=0.01,
        max_value=0.50,
        step=0.01,
        key="cfg_sentiment_adaptivity",
        help=glossary_short("Sentiment"),
    )
    st.number_input(
        "Liquidity depth",
        min_value=10_000.0,
        max_value=50_000_000.0,
        step=10_000.0,
        format="%.0f",
        key="cfg_liquidity",
        help=glossary_short("Liquidity"),
    )
    st.slider(
        "Decentralization (governance)",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        key="cfg_decentralization",
        help=glossary_short("Governance"),
    )
    st.slider(
        "Institutional participation",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        key="cfg_institutional",
        help=glossary_short("Institutions"),
    )
    st.slider(
        "Media bias",
        min_value=-1.0,
        max_value=1.0,
        step=0.05,
        key="cfg_media_bias",
        help=glossary_short("Media"),
    )
    st.slider(
        "Event frequency multiplier",
        min_value=0.0,
        max_value=5.0,
        step=0.1,
        key="cfg_event_scale",
        help="Multiplies every event probability. 0 disables random events.",
    )
    st.number_input(
        "Random seed",
        min_value=0,
        max_value=1_000_000,
        step=1,
        key="cfg_seed",
        help=glossary_short("Seed"),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def render_controls() -> SimConfig:
    """Draw the sidebar widgets and return the configuration they describe."""
    base: SimConfig = st.session_state.get("_fc_base", DEFAULT_CONFIG)

    mode = st.radio(
        "Mode",
        options=["Beginner", "Advanced"],
        key=_MODE_KEY,
        horizontal=True,
        help="Advanced exposes capacity, burn, per-role populations and market damping.",
    )

    consensus = _consensus_widget()

    if mode == "Beginner":
        _beginner_widgets()
        mix = _producer_mix(
            st.session_state.get("_fc_role_mix", dict(role_counts(base))),
            consensus,
        )
        counts = _scale_counts(mix, int(st.session_state["cfg_population"]))
        tx_per_block = base.network.tx_per_block
        burn_rate = base.monetary.burn_rate
        seed = base.seed
        social_overrides: dict[str, Any] = {}
        agent_overrides: dict[str, Any] = {}
    else:
        _advanced_widgets()
        counts = {
            Role.MINER: int(st.session_state["cfg_n_miners"]) if consensus == "pow" else 0,
            Role.VALIDATOR: int(st.session_state["cfg_n_validators"]) if consensus == "pos" else 0,
            Role.USER: int(st.session_state["cfg_n_users"]),
            Role.TRADER: int(st.session_state["cfg_n_traders"]),
            Role.DEVELOPER: int(st.session_state["cfg_n_developers"]),
            Role.ATTACKER: int(st.session_state["cfg_n_attackers"]),
        }
        total_pop = sum(counts.values())
        if total_pop > 3000:
            st.warning(
                "Very high starting population for a new network (unrealistic for genesis). "
                "Consider 200–1,200 for clearer dynamics.",
                icon="⚠️",
            )
        elif total_pop > 1200:
            st.info(
                "Large starting population. For a first run, 200–900 agents is often more realistic.",
                icon="ℹ️",
            )
        tx_per_block = int(st.session_state["cfg_tx_per_block"])
        burn_rate = float(st.session_state["cfg_burn_rate"])
        seed = int(st.session_state["cfg_seed"])
        social_overrides = {
            "sentiment_adaptivity": float(st.session_state["cfg_sentiment_adaptivity"]),
            "liquidity": float(st.session_state["cfg_liquidity"]),
            "decentralization": float(st.session_state["cfg_decentralization"]),
            "media_bias": float(st.session_state["cfg_media_bias"]),
            "institutional_participation": float(st.session_state["cfg_institutional"]),
        }
        agent_overrides = {
            "miner_cost_per_tick": float(st.session_state["cfg_miner_cost"]),
            "validator_cost_per_tick": float(st.session_state["cfg_validator_cost"]),
            "user_tx_per_tick": float(st.session_state["cfg_user_tx"]),
            "trader_aggressiveness": float(st.session_state["cfg_trader_aggression"]),
        }

    initial_supply = float(st.session_state["cfg_initial_supply"])
    max_supply = (
        None if st.session_state["cfg_no_cap"] else float(st.session_state["cfg_max_supply"])
    )
    if max_supply is not None and max_supply < initial_supply:
        st.warning(
            "The cap is below the initial supply. The cap will be raised to the initial "
            "supply so the run stays consistent."
        )
        max_supply = initial_supply

    halving = (
        NEVER
        if st.session_state["cfg_never_halve"]
        else int(st.session_state["cfg_halving"])
    )

    network = replace(
        base.network,
        consensus=consensus,
        block_time_s=float(st.session_state["cfg_block_time"]),
        tx_per_block=tx_per_block,
        base_fee=float(st.session_state["cfg_base_fee"]),
        target_stake_fraction=float(st.session_state["cfg_target_stake"]),
    )
    monetary = replace(
        base.monetary,
        initial_supply=initial_supply,
        max_supply=max_supply,
        initial_block_reward=float(st.session_state["cfg_block_reward"]),
        halving_interval_blocks=halving,
        burn_rate=burn_rate,
    )
    agents = replace(
        base.agents,
        n_miners=counts[Role.MINER],
        n_validators=counts[Role.VALIDATOR],
        n_users=counts[Role.USER],
        n_traders=counts[Role.TRADER],
        n_developers=counts[Role.DEVELOPER],
        n_attackers=counts[Role.ATTACKER],
        **agent_overrides,
    )
    social = replace(base.social, **social_overrides)
    events = replace(
        base.events,
        probability_scale=float(st.session_state["cfg_event_scale"]),
    )

    config = SimConfig(
        seed=seed,
        rows=base.rows,
        cols=base.cols,
        network=network,
        monetary=monetary,
        agents=agents,
        social=social,
        events=events,
    )

    st.caption(
        f"Config fingerprint `{config.fingerprint()}` · seed {config.seed} · "
        f"{config.population:,} agents"
    )
    return config


__all__ = ["apply_preset", "render_controls"]
