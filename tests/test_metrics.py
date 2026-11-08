"""Metrics: health bounds, breakdown, snapshot shape."""

from __future__ import annotations

import pytest

from futurecoins.metrics import Metrics, health_breakdown, network_health


def test_health_is_bounded() -> None:
    assert network_health(1.0, 0.0, 1.0, 1.0, 1.0) == pytest.approx(100.0)
    assert network_health(0.0, 1.0, 0.0, 0.0, 0.0) == pytest.approx(0.0)
    assert 0.0 <= network_health(0.5, 0.5, 0.5, 0.5, 0.5) <= 100.0


def test_health_weights_sum_to_one() -> None:
    breakdown = health_breakdown(0.5, 0.5, 0.5, 0.5, 0.5)
    assert sum(weight for _, _, weight in breakdown) == pytest.approx(1.0)
    assert len(breakdown) == 5


def test_decentralization_is_the_inverse_of_concentration() -> None:
    centralized = health_breakdown(1.0, 1.0, 1.0, 1.0, 1.0)
    decentralized = health_breakdown(1.0, 0.0, 1.0, 1.0, 1.0)
    central_value = next(value for label, value, _ in centralized if label == "Decentralization")
    free_value = next(value for label, value, _ in decentralized if label == "Decentralization")
    assert central_value == 0.0
    assert free_value == 1.0


def test_metrics_are_serialisable() -> None:
    metrics = Metrics(tick=3, active_nodes=4, total_nodes=5, health=42.0)
    payload = metrics.as_dict()
    assert payload["tick"] == 3
    assert payload["health"] == 42.0
    assert "price" in payload
