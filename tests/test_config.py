"""Configuration: derived values, fingerprints, presets."""

from __future__ import annotations

from dataclasses import replace

import pytest

from futurecoins.agents import role_counts
from futurecoins.config import (
    BITCOIN_2009,
    CHAOS_SANDBOX,
    DEFAULT_CONFIG,
    NEVER,
    PRESETS,
    SimConfig,
)


def test_blocks_per_tick_is_days_over_block_time() -> None:
    assert BITCOIN_2009.blocks_per_tick == pytest.approx(144.0)
    assert replace(BITCOIN_2009, network=replace(BITCOIN_2009.network, block_time_s=1.0)).blocks_per_tick == pytest.approx(86400.0)


def test_population_matches_role_counts_for_every_preset() -> None:
    for config in PRESETS.values():
        assert config.population == sum(role_counts(config).values())


def test_fingerprint_is_stable_and_sensitive() -> None:
    same = SimConfig(seed=42)
    assert DEFAULT_CONFIG.fingerprint() == same.fingerprint()

    changed = replace(DEFAULT_CONFIG, seed=43)
    assert changed.fingerprint() != DEFAULT_CONFIG.fingerprint()


def test_never_is_large_enough_to_mean_never() -> None:
    assert NEVER >= 10**11
    assert BITCOIN_2009.monetary.halving_interval_blocks < NEVER


def test_presets_have_a_playable_population() -> None:
    for name, config in PRESETS.items():
        assert config.population > 0, name
        assert config.rows > 0 and config.cols > 0, name
        assert config.cells > 0, name


def test_chaos_sandbox_is_actually_chaotic() -> None:
    assert CHAOS_SANDBOX.events.probability_scale > 1.0
    assert CHAOS_SANDBOX.network.tx_per_block < 200


def test_to_dict_round_trips_through_fingerprint_input() -> None:
    payload = DEFAULT_CONFIG.to_dict()
    assert payload["network"]["consensus"] == DEFAULT_CONFIG.network.consensus
    assert payload["agents"]["n_users"] == DEFAULT_CONFIG.agents.n_users
