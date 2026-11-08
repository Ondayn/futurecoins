"""Pure helpers in the Streamlit controls layer."""

from __future__ import annotations

from futurecoins.agents import Role
from futurecoins.interface.controls import _producer_mix, _scale_counts


def test_scaling_preserves_the_total_exactly() -> None:
    mix = {
        Role.MINER: 150,
        Role.VALIDATOR: 0,
        Role.USER: 250,
        Role.TRADER: 60,
        Role.DEVELOPER: 20,
        Role.ATTACKER: 5,
    }
    for total in (50, 485, 1_000, 5_000):
        scaled = _scale_counts(mix, total)
        assert sum(scaled.values()) == total
        assert scaled[Role.VALIDATOR] == 0
        assert scaled[Role.MINER] > 0


def test_scaling_keeps_every_nonzero_role_alive() -> None:
    mix = {
        Role.MINER: 1,
        Role.VALIDATOR: 0,
        Role.USER: 1,
        Role.TRADER: 1,
        Role.DEVELOPER: 1,
        Role.ATTACKER: 1,
    }
    scaled = _scale_counts(mix, 50)
    assert all(scaled[role] >= 1 for role in mix if mix[role] > 0)


def test_switching_consensus_produces_the_right_producer() -> None:
    mix = {
        Role.MINER: 150,
        Role.VALIDATOR: 0,
        Role.USER: 250,
        Role.TRADER: 60,
        Role.DEVELOPER: 20,
        Role.ATTACKER: 5,
    }

    pos = _producer_mix(mix, "pos")
    assert pos[Role.MINER] == 0
    assert pos[Role.VALIDATOR] == 150

    pow_mix = _producer_mix(pos, "pow")
    assert pow_mix[Role.VALIDATOR] == 0
    assert pow_mix[Role.MINER] == 150
