"""Discovery: scoring, bands, and hints that never leak the answer."""

from __future__ import annotations

from dataclasses import replace

import pytest

from futurecoins.config import BITCOIN_2009, NEVER, PRESETS
from futurecoins.discovery import BITCOIN_2009 as TARGET
from futurecoins.discovery import build_hints, hint_for, near_misses, score_config
from futurecoins.discovery.scoring import band_for, numeric_similarity
from futurecoins.discovery.targets import ParamSpec


def test_bitcoin_preset_scores_perfectly() -> None:
    breakdown = score_config(BITCOIN_2009, TARGET)
    assert breakdown.total == pytest.approx(1.0)
    assert breakdown.discovered
    assert breakdown.band == "discovered"
    assert build_hints(breakdown) == []


def test_a_deliberately_wrong_config_scores_low() -> None:
    wrong = replace(
        BITCOIN_2009,
        network=replace(
            BITCOIN_2009.network,
            consensus="pos",
            block_time_s=1.0,
            tx_per_block=10,
            base_fee=1.0,
        ),
        monetary=replace(
            BITCOIN_2009.monetary,
            initial_supply=1_000_000_000.0,
            max_supply=1_000_000_000.0,
            initial_block_reward=0.0,
            halving_interval_blocks=NEVER,
            burn_rate=0.5,
        ),
        agents=replace(BITCOIN_2009.agents, n_miners=0, n_validators=100),
    )

    breakdown = score_config(wrong, TARGET)
    assert breakdown.total < 0.40
    assert breakdown.band == "far"


def test_every_preset_scores_between_zero_and_one() -> None:
    for name, config in PRESETS.items():
        breakdown = score_config(config, TARGET)
        assert 0.0 <= breakdown.total <= 1.0, name


def test_only_the_bitcoin_preset_solves_discovery() -> None:
    """The app must not open on the answer.

    If any other preset (especially the default one) reached the 95 % band,
    ``Genesis Discovery`` would unlock for free on the first tick.
    """
    for name, config in PRESETS.items():
        breakdown = score_config(config, TARGET)
        if name == "Bitcoin 2009":
            assert breakdown.total >= 0.95
        else:
            assert breakdown.total < 0.95, name


def test_hints_never_contain_a_number() -> None:
    """Direction and magnitude only — never the target value."""
    for name, config in PRESETS.items():
        for hint in build_hints(score_config(config, TARGET)):
            assert not any(char.isdigit() for char in hint), (name, hint)


def test_hint_for_a_correct_parameter_is_none() -> None:
    breakdown = score_config(BITCOIN_2009, TARGET)
    for param in breakdown.params:
        assert hint_for(param) is None


def test_numeric_similarity_is_monotonic_and_bounded() -> None:
    spec = ParamSpec(
        key="block_time_s",
        label="Block time",
        kind="numeric",
        target=600.0,
        weight=1.0,
        tolerance=2.0,
    )
    exact = numeric_similarity(600.0, 600.0, spec)
    close = numeric_similarity(700.0, 600.0, spec)
    far = numeric_similarity(6_000.0, 600.0, spec)

    assert exact == pytest.approx(1.0)
    assert 0.0 <= far < close < exact <= 1.0


def test_zero_target_uses_absolute_tolerance() -> None:
    spec = ParamSpec(
        key="burn_rate",
        label="Burn rate",
        kind="numeric",
        target=0.0,
        weight=1.0,
        abs_tolerance=0.01,
    )
    assert numeric_similarity(0.0, 0.0, spec) == pytest.approx(1.0)
    assert numeric_similarity(0.005, 0.0, spec) == pytest.approx(0.5)
    assert numeric_similarity(1.0, 0.0, spec) == 0.0


def test_bands_match_the_documented_thresholds() -> None:
    assert band_for(0.96) == "discovered"
    assert band_for(0.85) == "almost"
    assert band_for(0.65) == "close"
    assert band_for(0.45) == "partial"
    assert band_for(0.10) == "far"


def test_near_misses_only_reports_high_weight_close_parameters() -> None:
    breakdown = score_config(BITCOIN_2009, TARGET)
    assert near_misses(breakdown) == []
