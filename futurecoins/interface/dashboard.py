"""Dashboard: twelve metric cards and the health breakdown.

Cards are plain HTML rather than `st.metric` for two reasons:

1. A card can show two related numbers (active / total, total / circulating)
   side by side, which is the whole point of the metric pairs in the GDD.
2. The same card can carry a "model" badge and a hover definition without
   fighting Streamlit's layout.

Every number here comes from a `Metrics` snapshot. The UI does not compute
metrics; it formats them.
"""

from __future__ import annotations

import html

import streamlit as st

from ..config import SimConfig
from ..education import short as glossary_short
from ..metrics import Metrics, health_breakdown


def _amount(value: float) -> str:
    """Compact token amounts: 1.2 B, 340.5 M, 12.3 K."""
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"{value / 1e9:,.2f} B"
    if magnitude >= 1e6:
        return f"{value / 1e6:,.2f} M"
    if magnitude >= 1e3:
        return f"{value / 1e3:,.1f} K"
    return f"{value:,.2f}"


def _card(
    label: str,
    value: str,
    sub: str = "",
    *,
    badge: str = "",
    tooltip: str = "",
    colour: str = "",
) -> str:
    badge_html = f'<span class="fc-badge">{badge}</span>' if badge else ""
    tip = f' title="{html.escape(tooltip)}"' if tooltip else ""
    value_class = f"value {colour}".strip()
    sub_html = f'<div class="sub">{html.escape(sub)}</div>' if sub else ""
    return (
        f'<div class="fc-card"{tip}>'
        f'<div class="label">{html.escape(label)} {badge_html}</div>'
        f'<div class="{value_class}">{html.escape(value)}</div>'
        f"{sub_html}</div>"
    )


def cards_html(metrics: Metrics, config: SimConfig) -> str:
    """The full dashboard, grouped Network / Money / Market / Health."""
    health_colour = (
        "fc-good" if metrics.health >= 60 else "fc-warn" if metrics.health >= 30 else "fc-bad"
    )
    sentiment_colour = (
        "fc-good"
        if metrics.sentiment >= 0.6
        else "fc-warn"
        if metrics.sentiment >= 0.35
        else "fc-bad"
    )

    cards = [
        # -- Network --------------------------------------------------------
        _card(
            "Active nodes",
            f"{metrics.active_nodes:,} / {metrics.total_nodes:,}",
            f"{metrics.participation:.1%} of the population is working",
            tooltip=glossary_short("Participation"),
        ),
        _card(
            "Block interval",
            f"{metrics.block_interval:,.1f} s" if metrics.block_interval > 0 else "—",
            f"target {config.network.block_time_s:,.1f} s",
            tooltip=glossary_short("Block time"),
        ),
        _card(
            "Throughput",
            f"{metrics.tps:,.1f} tx/s",
            f"{metrics.blocks_total:,.0f} blocks · cap {metrics.capacity_multiplier:.2f}×",
            tooltip=glossary_short("Throughput (TPS)"),
        ),
        _card(
            "Average fee",
            f"{metrics.avg_fee:,.4f}",
            f"congestion {metrics.congestion:.0%} · {metrics.dropped_txs:,.0f} dropped",
            tooltip=glossary_short("Fee"),
        ),
        # -- Money ----------------------------------------------------------
        _card(
            "Total supply",
            _amount(metrics.total_supply),
            "minted minus burned",
            tooltip=glossary_short("Total supply"),
        ),
        _card(
            "Circulating supply",
            _amount(metrics.circulating_supply),
            "total minus treasury",
            tooltip=glossary_short("Circulating supply"),
        ),
        _card(
            "Inflation rate",
            f"{metrics.inflation_rate:,.1f} % / yr",
            "annualised from this tick",
            tooltip=glossary_short("Inflation rate"),
        ),
        _card(
            "Burned to date",
            _amount(metrics.burned_total),
            f"treasury {_amount(metrics.treasury)}",
            tooltip=glossary_short("Burn"),
        ),
        # -- Market ---------------------------------------------------------
        _card(
            "Price index",
            f"{metrics.price:,.2f}",
            "base 100 at launch",
            badge="model",
            tooltip=glossary_short("Price index"),
        ),
        _card(
            "Volatility",
            f"{metrics.volatility:.3f}",
            "EWMA of absolute log return",
            badge="model",
            tooltip=glossary_short("Volatility"),
        ),
        _card(
            "Sentiment",
            f"{metrics.sentiment * 100:,.0f} / 100",
            "public mood",
            badge="model",
            tooltip=glossary_short("Sentiment"),
            colour=sentiment_colour,
        ),
        _card(
            "Network health",
            f"{metrics.health:,.0f} / 100",
            "weighted composite",
            badge="model",
            tooltip=glossary_short("Network health"),
            colour=health_colour,
        ),
    ]

    return (
        '<div class="fc-cards-wrap"><div class="fc-cards">'
        + "".join(cards)
        + "</div></div>"
    )


def health_bars_html(metrics: Metrics) -> str:
    """The five components of the health score, with their weights visible."""
    rows: list[str] = []
    for label, value, weight in health_breakdown(
        metrics.participation,
        metrics.concentration,
        metrics.reliability,
        metrics.security,
        metrics.sentiment,
    ):
        rows.append(
            '<div class="fc-bar-row">'
            f"<span>{html.escape(label)} <span class='fc-mono'>({weight:.0%})</span></span>"
            f'<span class="fc-bar"><span style="width:{value * 100:.1f}%"></span></span>'
            f"<span class='fc-mono'>{value * 100:,.0f}%</span>"
            "</div>"
        )
    return '<div class="fc-bars">' + "".join(rows) + "</div>"


def render(metrics: Metrics, config: SimConfig) -> None:
    st.html(cards_html(metrics, config))


def render_health(metrics: Metrics) -> None:
    st.html(health_bars_html(metrics))


__all__ = ["cards_html", "health_bars_html", "render", "render_health"]
