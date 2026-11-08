"""FutureCoins — the Streamlit application.

Run with:

    streamlit run app.py

The app is deliberately thin. It owns three things:

1. `st.session_state` — the one live `Simulation`, the achievement manager, and
   a few UI preferences.
2. The 1-second fragment that advances the simulation and redraws the live
   view.
3. Presentation of data the engine already computed.

No simulation formula lives here. If a number is wrong, the fix belongs in the
engine, with a test.
"""

from __future__ import annotations

import html
import json

import streamlit as st

from futurecoins.achievements import (
    ACHIEVEMENT_DEFS,
    AchievementManager,
    RunSummary,
    encode_snapshot,
)
from futurecoins.config import NEVER, PRESET_UNLOCKS, PRESETS
from futurecoins.discovery import BITCOIN_2009, build_hints, near_misses, score_config
from futurecoins.education import GLOSSARY, RESOURCES, categories, search
from futurecoins.engine import Simulation
from futurecoins.interface import controls, dashboard, grid_view, theme, tooltips
from futurecoins.metrics import health_breakdown

st.set_page_config(
    page_title="FutureCoins",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme.inject()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------


def _initialise() -> None:
    if "sim" in st.session_state:
        return

    preset = PRESETS["Blank Canvas"]
    st.session_state.sim = Simulation(preset)
    st.session_state.launch_config = preset
    st.session_state.running = False
    st.session_state.speed = 2
    st.session_state.achievements = AchievementManager()
    st.session_state.event_feed = []
    st.session_state.hints_shown = 1
    st.session_state.ascii_mode = False
    st.session_state.preset_choice = "Blank Canvas"
    st.session_state["_preset_applied"] = None
    st.session_state.seen_guide = False


_initialise()


def _guide_html(*, compact: bool = False) -> str:
    """Styled guide content (shared by welcome screen and Guide tab)."""
    intro = (
        '<div class="fc-guide-card"><p>A sandbox: design a cryptocurrency\'s rules, '
        "run a simulation, and watch what happens to its economy and network. "
        "Everything labelled <em>model</em> is a simulation output, not real market data.</p></div>"
    )
    how = (
        '<div class="fc-guide-card"><h4>🎮 How to play</h4><ol>'
        "<li><strong>Design</strong> your currency in the sidebar (consensus, block time, supply, fees, population).</li>"
        "<li>Press <strong>⚙️ Apply config</strong> to load your settings.</li>"
        "<li>Press <strong>▶ Run</strong>. Each tick = <strong>1 simulated day</strong> (365 ticks = 1 year).</li>"
        "<li>Watch the grid, the 12 indicator cards, and the charts.</li>"
        "<li><strong>⏸ Pause</strong> / <strong>↺ Reset</strong> as needed.</li>"
        "</ol></div>"
    )
    goal = (
        '<div class="fc-guide-card"><h4>🎯 Goal</h4>'
        "<p>Keep your network alive and healthy. Discover Bitcoin 2009 in "
        "Discovery Mode. Earn achievements to unlock presets.</p></div>"
    )
    dashboard = (
        '<div class="fc-guide-card"><h4>📊 Dashboard</h4>'
        "<p>12 cards: active nodes, block interval, throughput, fees, supply, "
        "price index, sentiment, and network health. The <strong>Why</strong> tab "
        "explains changes and feedback loops. The <strong>Dashboard</strong> tab shows "
        "health components and history after you run.</p></div>"
    )
    discovery = (
        '<div class="fc-guide-card"><h4>🔍 Discovery Mode</h4>'
        "<p>Reconstruct Bitcoin 2009 from its behaviour. Adjust parameters, run the simulation, "
        "and use the feedback to improve your match. Reach 95% similarity to unlock the preset.</p></div>"
    )
    tips = (
        '<div class="fc-guide-card"><h4>💡 Tips</h4><ul>'
        "<li>Speed changes ticks per frame (1/2/5/20); the frame rate stays at 1 fps.</li>"
        "<li>Grey/blank cells: offline agents disappear; faint dots are unassigned slots.</li>"
        "<li>If health drops below 15 for 5 ticks, or all users leave, the currency can <strong>fail</strong> and the simulation ends.</li>"
        "<li>If every agent goes offline, the network is <strong>dead</strong> — press Reset.</li>"
        "</ul></div>"
    )
    glossary = (
        '<div class="fc-guide-card"><h4>📚 Glossary & resources</h4>'
        "<p>Hover any card for a definition. The <strong>Glossary</strong> tab has 51 terms, "
        "and the <strong>Why</strong> tab explains formulas and feedback loops.</p></div>"
    )
    cards = [intro, how, goal, dashboard, discovery]
    if not compact:
        cards.extend([tips, glossary])
    return '<div class="fc-guide">' + "".join(cards) + "</div>"


def _welcome_screen() -> None:
    """Full-page guide shown on first visit."""
    st.html(theme.hero("FutureCoins", "Design the rules. Watch the consequences.", False, tick=0))
    st.html('<div class="fc-note">Hover any card or term for a definition. '
            'The Glossary tab has 51 terms. This is an educational model, not financial advice.</div>')
    st.html(_guide_html(compact=False))
    if st.button("🚀 Start playing", type="primary", width="stretch"):
        st.session_state.seen_guide = True
        st.rerun()


if not st.session_state.seen_guide:
    _welcome_screen()
    st.stop()


def _summary(sim: Simulation) -> RunSummary:
    """Build the only object achievements are allowed to inspect."""
    breakdown = score_config(sim.config, BITCOIN_2009)
    return RunSummary(
        tick=sim.tick,
        metrics=sim.metrics,
        config=sim.config,
        history=tuple(sim.history),
        events=tuple(sim.event_history),
        discovery_score=breakdown.total,
        snapshot=encode_snapshot(sim.agents, sim.config.rows, sim.config.cols),
    )


def _compact(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"{value / 1e9:,.2f} B"
    if magnitude >= 1e6:
        return f"{value / 1e6:,.2f} M"
    if magnitude >= 1e3:
        return f"{value / 1e3:,.1f} K"
    return f"{value:,.2f}"


def _param_value(key: str, value: object) -> str:
    """Human-readable player value. Never shows the target."""
    if key == "max_supply" and value is None:
        return "No cap"
    if key == "consensus":
        return "Proof of Work" if value == "pow" else "Proof of Stake"
    if key == "halving_interval_blocks" and value is not None:
        number = float(value)
        return "Never" if number >= NEVER / 10 else f"{number:,.0f} blocks"
    if key == "block_time_s" and value is not None:
        return f"{float(value):,.0f} s"
    if key == "base_fee" and value is not None:
        return f"{float(value):,.4f}"
    if key == "burn_rate" and value is not None:
        return f"{float(value):.0%}"
    if key in ("initial_supply", "max_supply", "initial_block_reward") and value is not None:
        return _compact(float(value))
    if key == "tx_per_block" and value is not None:
        return f"{float(value):,.0f}"
    return str(value)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Currency designer")

    awarded = st.session_state.achievements.awarded_ids
    # Locked presets are shown as "Mystery Currency NNN" until the achievement
    # that unlocks them is earned. The numbering is stable (preset order).
    # Presets not in PRESET_UNLOCKS are permanently locked (no unlock path yet).
    display_names: list[str] = []
    display_to_real: dict[str, str] = {}
    mystery_no = 0
    for real_name in PRESETS:
        if real_name not in PRESET_UNLOCKS:
            # Permanently locked: no achievement unlocks it yet.
            mystery_no += 1
            display = f"🔒 Mystery Currency {mystery_no:03d}"
            display_names.append(display)
            display_to_real[display] = real_name
            continue
        unlock_id = PRESET_UNLOCKS[real_name]
        if unlock_id is None or unlock_id in awarded:
            display_names.append(real_name)
            display_to_real[real_name] = real_name
        else:
            mystery_no += 1
            display = f"🔒 Mystery Currency {mystery_no:03d}"
            display_names.append(display)
            display_to_real[display] = real_name

    st.selectbox(
        "Preset",
        options=display_names,
        key="preset_choice",
        help="A preset is just a named configuration. Locked presets are unlocked "
        "by earning their matching achievement in Discovery Mode.",
    )

    selected_display = st.session_state.preset_choice
    selected_real = display_to_real[selected_display]
    if selected_real not in PRESET_UNLOCKS:
        # Permanently locked preset.
        st.warning(
            "🔒 Locked. This currency has not been discovered yet.",
            icon="🔒",
        )
        st.session_state["_preset_applied"] = selected_display
    else:
        unlock_id = PRESET_UNLOCKS[selected_real]
        locked = unlock_id is not None and unlock_id not in awarded
        if locked:
            achievement = next(
                (a for a in ACHIEVEMENT_DEFS if a.id == unlock_id), None
            )
            name = achievement.name if achievement else unlock_id
            st.warning(
                f"🔒 Locked. Earn **{name}** to unlock this preset.",
                icon="🔒",
            )
            st.session_state["_preset_applied"] = selected_display
        elif st.session_state.get("_preset_applied") != selected_display:
            controls.apply_preset(PRESETS[selected_real])
            st.session_state["_preset_applied"] = selected_display

    config = controls.render_controls()

    st.divider()
    if st.button("⚙️ Apply config", type="primary", width="stretch"):
        if config.population < 1:
            st.error("A simulation needs at least one agent.")
        else:
            st.session_state.sim = Simulation(config)
            st.session_state.launch_config = config
            st.session_state.running = False
            st.session_state.event_feed = []
            st.session_state.hints_shown = 1
            st.toast("New simulation ready. Press Run.", icon="🚀")

    left, right = st.columns(2)
    if left.button(
        "⏸ Pause" if st.session_state.running else "▶ Run",
        width="stretch",
        disabled=st.session_state.sim.ended,
        help="The network has ended. Reset it to run again."
        if st.session_state.sim.ended
        else None,
    ):
        st.session_state.running = not st.session_state.running
        st.rerun()
    if right.button("↺ Reset", width="stretch"):
        st.session_state.sim.reset()
        st.session_state.running = False
        st.session_state.event_feed = []
        st.rerun()
        st.session_state.sim.reset()
        st.session_state.running = False
        st.session_state.event_feed = []
        st.rerun()

    st.selectbox(
        "Speed (ticks per frame)",
        options=[1, 2, 5, 20],
        key="speed",
        format_func=lambda n: f"{n} tick{'s' if n > 1 else ''} / s",
        help="The frame rate stays at 1 fps; this changes how much simulated time each frame covers.",
    )
    st.toggle(
        "ASCII fallback",
        key="ascii_mode",
        help="Use letters instead of emoji if a font renders the grid inconsistently.",
    )

    sim: Simulation = st.session_state.sim
    st.divider()
    st.caption(
        f"**Simulation** · {sim.config.population:,} agents\n\n"
        f"Seed {sim.config.seed} · fingerprint `{sim.config.fingerprint()}`"
    )
    with st.expander("About this simulation"):
        st.write(
            "FutureCoins is an educational model, not a blockchain and not financial advice. "
            "Price, health and sentiment are formula outputs, labelled *model* on the dashboard."
        )
        st.caption("1 tick = 1 simulated day · 365 ticks = 1 simulated year")


# ---------------------------------------------------------------------------
# Live view (fragment: advances the clock without rerunning the sidebar)
# ---------------------------------------------------------------------------


@st.fragment(run_every="1s")
def live_view() -> None:
    sim = st.session_state.sim

    if st.session_state.running:
        results = sim.run(int(st.session_state.speed))
        new_events = [event for result in results for event in result.events]
        if new_events:
            st.session_state.event_feed.extend(new_events)
            st.session_state.event_feed = st.session_state.event_feed[-50:]
            for event in new_events[:3]:
                st.toast(event.message, icon="⚠️")

        awards = st.session_state.achievements.evaluate(_summary(sim))
        for award in awards:
            st.toast(f"{award.icon} {award.name} unlocked!", icon="🏆")

        if sim.ended:
            # Terminal state: stop the clock and refresh the sidebar so its Run
            # button becomes disabled instead of inviting a no-op click.
            st.session_state.running = False
            st.rerun()

    st.html(
        theme.hero(
            "FutureCoins",
            "Design the rules. Watch the consequences.",
            st.session_state.running,
            tick=sim.tick,
        )
    )

    if sim.ended:
        st.warning(
            f"🪦 **Network ended at tick {sim.tick:,}.** {sim.end_reason} "
            "Press **Reset** to start again with the same rules.",
            icon="🪦",
        )

    # Wide screens: a full-width strip of compact indicators, then the board on
    # the left and the tabs on the right. Stacking everything would push half
    # the page below the fold. CSS (theme.py) stacks this block again on narrow
    # screens.
    dashboard.render(sim.metrics, sim.config)

    with st.container(key="fc-split"):
        left, right = st.columns([1.4, 1], gap="medium")

    with left:
        grid_view.render(sim, ascii_mode=st.session_state.ascii_mode)

    with right:
        tabs = st.tabs(["📖 Guide", "Dashboard", "Discovery", "Awards", "Glossary", "Why"])

    # -- Guide -------------------------------------------------------------
    with tabs[0]:
        st.html('<div class="fc-guide-card"><h4>How to play FutureCoins</h4>'
                '<p>Design a cryptocurrency\'s rules, run the simulation, and watch what happens '
                'to its economy and network. Use the sidebar to configure, then Apply and Run.</p></div>')
        st.html(_guide_html(compact=False))
        st.html('<div class="fc-guide-card"><h4>🏆 Achievements</h4>'
                '<p>The <strong>Awards</strong> tab tracks achievements. Earning them can unlock presets '
                '(shown as 🔒 Mystery Currency until unlocked). Export/import JSON to carry progress between machines.</p></div>')
        st.html('<div class="fc-note">1 tick = 1 simulated day · 365 ticks = 1 simulated year · '
                'Educational model, not financial advice.</div>')

    # -- Dashboard ---------------------------------------------------------
    with tabs[1]:
        metrics = sim.metrics
        st.markdown("#### Network health breakdown")
        if sim.tick == 0:
            st.html('<div class="fc-note">Run the simulation to see the health breakdown. '
                    'Components (participation, decentralization, reliability, security, sentiment) '
                    'are weighted into a single score once the network has activity.</div>')
        else:
            st.caption(
                "The score is a weighted average. Every weight is visible, so you can disagree "
                "with the formula instead of guessing what it means."
            )
            dashboard.render_health(metrics)

        history = sim.history[-400:]
        if len(history) > 1:
            prev, curr = history[-2], history[-1]
            deltas = [
                ("Health", curr.health - prev.health, "{:+.1f}"),
                ("Price index", curr.price - prev.price, "{:+.2f}"),
                ("Sentiment", (curr.sentiment - prev.sentiment) * 100, "{:+.1f} pts"),
                ("Active nodes", curr.active_nodes - prev.active_nodes, "{:+,.0f}"),
                ("Avg fee", curr.avg_fee - prev.avg_fee, "{:+.4f}"),
                ("Reliability", (curr.reliability - prev.reliability) * 100, "{:+.1f} pts"),
            ]
            moved = [(name, val, fmt) for name, val, fmt in deltas if abs(val) > 1e-9]
            if moved:
                parts = []
                for name, val, fmt in moved[:4]:
                    arrow = "↑" if val > 0 else "↓"
                    parts.append(f"{arrow} <strong>{html.escape(name)}</strong> {fmt.format(val)}")
                st.html('<div class="fc-note"><strong>Last tick:</strong> ' + " · ".join(parts) +
                        '. See the <strong>Why</strong> tab for causes and events.</div>')
            st.markdown("#### Recent history")
            st.line_chart(
                {
                    "Price index (model)": [m.price for m in history],
                    "Network health (model)": [m.health for m in history],
                    "Sentiment × 100 (model)": [m.sentiment * 100 for m in history],
                },
                height=240,
            )
            st.caption(
                f"Last {len(history)} ticks. These are formula outputs, not market data."
            )

        if st.session_state.event_feed:
            st.markdown("#### Event log")
            for event in reversed(st.session_state.event_feed[-6:]):
                st.markdown(f"**Tick {event.tick} · {event.name}** — {event.message}")

    # -- Discovery ---------------------------------------------------------
    with tabs[2]:
        st.markdown(f"### {BITCOIN_2009.name} — {BITCOIN_2009.era}")
        st.markdown(f"> *{BITCOIN_2009.riddle}*")
        st.markdown("")

        if sim.tick == 0:
            st.html('<div class="fc-note">Set up your currency, press <strong>⚙️ Apply config</strong>, '
                    'then press <strong>▶ Run</strong>. Similarity feedback appears after the simulation starts, '
                    'so you discover the match by observing behaviour — not from a pre-run percentage clue.</div>')
            st.caption(BITCOIN_2009.caveat)
        else:
            breakdown = score_config(sim.config, BITCOIN_2009)
            st.metric("Similarity", f"{breakdown.total:.1%}")
            st.progress(min(max(breakdown.total, 0.0), 1.0))

            st.markdown(f"**{breakdown.message}**")
            misses = near_misses(breakdown)
            if misses:
                st.caption("Close but not exact: " + ", ".join(misses))
            st.markdown("")
            st.caption(BITCOIN_2009.caveat)

            st.markdown("#### How the score is built")
            st.caption(
                "Weights are visible on purpose. A score you cannot inspect is a guessing game. "
                "Parameters historians are less sure about count for less."
            )
            rows = [
                {
                    "Parameter": param.label,
                    "Your value": _param_value(param.key, param.value),
                    "Similarity": f"{param.similarity:.0%}",
                    "Weight": f"{param.effective_weight:.0%}",
                    "Confidence": param.confidence,
                }
                for param in breakdown.params
            ]
            st.dataframe(rows, width="stretch", hide_index=True)

            st.markdown("#### Hints")
            hints = build_hints(breakdown, limit=3)
            shown = min(st.session_state.hints_shown, len(hints))
            if not hints:
                st.success("Every parameter matches. You have reconstructed this currency.")
            for hint in hints[:shown]:
                st.html(f'<div class="fc-hint">💡 {html.escape(hint)}</div>')
            if shown < len(hints) and st.button("Reveal another hint", key="more_hints"):
                st.session_state.hints_shown = shown + 1
                st.rerun()

            if breakdown.total >= 0.95:
                tooltips.note(
                    "Discovery achieved. Notice what you did <em>not</em> need: a supply-cap "
                    "parameter. Bitcoin's 21 million limit is the sum of the halving series "
                    "210,000 × 50 × 2, not a constant in the rules."
                )
            else:
                with st.expander("The teaching moment (spoiler-light)"):
                    st.write(
                        "Bitcoin's 21 million cap is not written as a constant. It is the sum of "
                        "the halving series. If you are stuck on the cap, try asking what the "
                        "halving interval does to the total over a very long time."
                    )

    # -- Achievements ------------------------------------------------------
    with tabs[3]:
        manager: AchievementManager = st.session_state.achievements
        st.markdown("### Achievements")
        st.caption(
            f"{len(manager.awarded_ids)} of {len(ACHIEVEMENT_DEFS)} unlocked. "
            "Each award records the configuration hash and a grid snapshot, so a run can be "
            "reproduced."
        )
        for definition in ACHIEVEMENT_DEFS:
            unlocked = manager.has(definition.id)
            classes = "fc-award" + ("" if unlocked else " fc-locked")
            status = "Unlocked" if unlocked else "Locked"
            st.html(
                f'<div class="{classes}"><span class="icon">{definition.icon}</span>'
                f'<div><div class="name">{html.escape(definition.name)} '
                f'<span class="fc-pill">{status}</span></div>'
                f'<div class="desc">{html.escape(definition.description)}</div>'
                f'<div class="desc">Hint: {html.escape(definition.hint)}</div></div></div>'
            )
            if unlocked:
                award = manager.awards[definition.id]
                with st.expander("Award details"):
                    st.caption(
                        f"Awarded {award.awarded_at} at tick {award.tick:,} · "
                        f"seed {award.seed} · config `{award.config_hash}`"
                    )
                    if award.snapshot:
                        grid_view.render_snapshot(
                            award.snapshot,
                            award.cols or sim.config.cols,
                            ascii_mode=st.session_state.ascii_mode,
                        )

        st.divider()
        st.markdown("### Carry your achievements to another machine")
        st.caption(
            "Unlocked presets follow your achievements. Export them here and "
            "import them on another laptop to keep your progress."
        )
        if manager.awards:
            payload = json.dumps(
                [a.to_dict() for a in manager.as_list()],
                indent=2,
                ensure_ascii=False,
            )
            st.download_button(
                "⬇ Export achievements",
                data=payload,
                file_name="futurecoins-achievements.json",
                mime="application/json",
            )
        else:
            st.caption("Nothing to export yet.")
        uploaded = st.file_uploader(
            "Import achievements (JSON)",
            type="json",
            key="ach_import",
        )
        if uploaded is not None:
            try:
                imported = json.loads(uploaded.read())
                added = manager.import_awards(imported)
                if added:
                    st.toast(f"Imported {added} new achievement(s).", icon="📥")
                else:
                    st.info("No new achievements in that file.")
            except (json.JSONDecodeError, OSError) as exc:
                st.error(f"Could not read file: {exc}")

    # -- Glossary ----------------------------------------------------------
    with tabs[4]:
        st.markdown("### Glossary")
        query = st.text_input(
            "Search",
            key="glossary_query",
            placeholder="fees, halving, stake, reflexivity…",
        )
        category = st.selectbox(
            "Category",
            options=["All", *categories()],
            key="glossary_category",
        )
        results = search(query, None if category == "All" else category)
        st.caption(f"{len(results)} of {len(GLOSSARY)} terms")
        for entry in results:
            with st.expander(f"{entry.term} — {entry.short}"):
                st.write(entry.explanation)
                st.markdown(f"**In this simulation**  \n{entry.in_game}")
                st.markdown(f"**In the real world**  \n{entry.real_world}")
                if entry.link:
                    st.link_button(entry.link_label or "Learn more", entry.link)

        st.markdown("")
        st.html('<div style="height:0.5rem"></div>')
        st.divider()
        st.markdown("")
        st.markdown("### Further reading")
        st.caption("Every link says what you will learn before you click it.")
        st.markdown("")
        for resource in RESOURCES:
            st.markdown(
                f"**[{resource.title}]({resource.url})** · *{resource.topic}*  \n"
                f"{resource.what_you_learn}"
            )

    # -- Why ---------------------------------------------------------------
    with tabs[5]:
        st.markdown("### Why did this happen?")
        st.caption(
            "The last notable changes, written as sentences by the engine. If a number "
            "surprised you, start here before changing a slider."
        )
        recent = list(sim.recent_changes)[-10:]
        if recent:
            for change in reversed(recent):
                st.markdown(f"- {change}")
        else:
            st.info("Nothing notable yet. Press Run and give the network a few ticks.")

        st.markdown("#### Active events")
        active = sim.events.active_names
        if active:
            st.write(", ".join(active))
        else:
            st.caption("No event is currently active.")

        st.markdown("#### Feedback loops")
        st.caption(
            "These are the causal chains that make the model feel alive. "
            "Changing one parameter ripples through several indicators."
        )
        st.markdown(
            "- **Health → Availability**: a sick network produces fewer blocks.\n"
            "- **Health → Price**: price anchor scales with health (0 health = 10% value).\n"
            "- **Sentiment → Demand**: better mood → more transactions.\n"
            "- **Sentiment → Price**: rising prices boost sentiment (momentum).\n"
            "- **Price → Demand**: expensive networks see less usage (elasticity).\n"
            "- **Fees → Churn**: high fees push users to leave.\n"
            "- **Concentration → Security**: concentrated networks are easier to capture.\n"
            "- **Reliability → Sell pressure**: dropped transactions create selling.\n"
            "- **Developers → Capacity**: developers slowly raise throughput."
        )

        st.markdown("#### Health, decomposed")
        if sim.tick == 0:
            st.html('<div class="fc-note">Run the simulation to see how health components contribute.</div>')
        else:
            metrics = sim.metrics
            rows = [
                {
                    "Component": label,
                    "Value": f"{value:.0%}",
                    "Weight": f"{weight:.0%}",
                    "Contribution": f"{value * weight * 100:.1f} points",
                }
                for label, value, weight in health_breakdown(
                    metrics.participation,
                    metrics.concentration,
                    metrics.reliability,
                    metrics.security,
                    metrics.sentiment,
                )
            ]
            st.dataframe(rows, width="stretch", hide_index=True)

        if sim.event_history:
            st.markdown("#### Event history")
            for event in reversed(sim.event_history[-10:]):
                st.markdown(
                    f"**Tick {event.tick} · {event.name}** "
                    f"(severity {event.severity:.2f}, {event.category}) — {event.message}"
                )

        st.divider()
        tooltips.note(
            "Every number on this page is a model output. FutureCoins does not connect to a "
            "real blockchain, does not hold funds, and is not financial advice."
        )


live_view()
