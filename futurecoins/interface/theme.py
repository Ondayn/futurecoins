"""Visual identity: dark, neon, readable.

All styling lives in one CSS string. The grid, cards and glossary share the
same role colours, so a miner is the same amber everywhere. Keeping the CSS in
one place also means a contrast fix happens once.

Colour choices are deliberately high-contrast on a near-black background. The
palette is not purely decorative: each role has a distinct hue *and* a distinct
emoji, so colour is never the only signal (important for colour-blind players).
"""

from __future__ import annotations

import streamlit as st

CSS = """
<style>
:root {
  --fc-bg: #070b14;
  --fc-panel: #0f172a;
  --fc-panel-2: #111c33;
  --fc-border: #1e2d4a;
  --fc-text: #e6edf7;
  --fc-muted: #8ba0bd;
  --fc-accent: #5eead4;
  --fc-accent-2: #a78bfa;
  --fc-good: #4ade80;
  --fc-warn: #fbbf24;
  --fc-bad: #fb7185;
  --fc-miner: #fbbf24;
  --fc-validator: #5eead4;
  --fc-user: #93c5fd;
  --fc-trader: #f0abfc;
  --fc-developer: #86efac;
  --fc-attacker: #fb7185;
}

/* Streamlit shell */
button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(180deg, #5eead4 0%, #2dd4bf 100%) !important;
  color: #04131a !important;
  border: 1px solid #2dd4bf !important;
  font-weight: 700 !important;
}
button[data-testid="stBaseButton-primary"]:hover {
  background: linear-gradient(180deg, #7ef0e0 0%, #5eead4 100%) !important;
  color: #04131a !important;
}
button[data-testid="stBaseButton-secondary"] {
  background: rgba(30, 45, 74, 0.6) !important;
  color: var(--fc-text) !important;
  border: 1px solid var(--fc-border) !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
  background: rgba(45, 65, 100, 0.8) !important;
  color: var(--fc-text) !important;
}
.stApp {
  background:
    radial-gradient(1100px 500px at 15% -10%, rgba(94, 234, 212, 0.10), transparent 60%),
    radial-gradient(900px 450px at 90% 0%, rgba(167, 139, 250, 0.10), transparent 55%),
    var(--fc-bg);
  color: var(--fc-text);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0b1220 0%, #0a0f1a 100%);
  border-right: 1px solid var(--fc-border);
}
@media (min-width: 900px) {
  /* A little narrower than the default, so the game keeps more width.
     Only while expanded: forcing the width on the collapsed panel would keep
     it in the layout after it slides away, and the page would never adapt. */
  [data-testid="stSidebar"]:not([data-collapsed="true"]) {
    width: 252px !important;
    min-width: 252px !important;
  }
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--fc-text);
}
h1, h2, h3 { letter-spacing: -0.02em; }

/* Layout: the game is meant to be watched, not scrolled.
   The default Streamlit block container spends 96px above and 160px below the
   content, which alone is a quarter of a laptop screen. Trim it, then let the
   grid and the tab panel share what is left. */
.stMainBlockContainer {
  padding: 0.5rem 0.9rem 0.4rem 0.9rem !important;
  max-width: 100% !important;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"] { gap: 0.35rem; }
[data-testid="stMain"] [data-testid="stCaptionContainer"] {
  margin: 0;
  font-size: 0.76rem;
  line-height: 1.3;
}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p { margin-bottom: 0.1rem; }
[data-testid="stMain"] [data-testid="stHtml"] { margin: 0; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem; }

/* Everything below the hero has to fit one screen. The board is square, so its
   width is also its height: budget the vertical space first (hero + cards +
   captions + legend + padding) and let the height decide the board size. The
   horizontal room the board gives up goes to the tab panel, not to empty
   space beside it. */
:root { --fc-grid-max: clamp(280px, calc(100vh - 320px), 800px); }

/* The tab panel scrolls inside itself. Made visually obvious (scrollbar + cue).
   min-height reduces layout "jump" when switching to a shorter tab. */
[data-testid="stTabs"] [role="tabpanel"] {
  min-height: clamp(160px, 28vh, 360px);
  max-height: clamp(180px, calc(100vh - 320px), 720px);
  overflow-y: auto;
  padding-right: 0.35rem;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: rgba(94, 234, 212, 0.45) rgba(30, 45, 74, 0.35);
  box-shadow: inset 0 -10px 10px -12px rgba(94, 234, 212, 0.18);
}
[data-testid="stTabs"] [role="tabpanel"]::-webkit-scrollbar { width: 8px; }
[data-testid="stTabs"] [role="tabpanel"]::-webkit-scrollbar-track {
  background: rgba(30, 45, 74, 0.35);
  border-radius: 999px;
}
[data-testid="stTabs"] [role="tabpanel"]::-webkit-scrollbar-thumb {
  background: rgba(94, 234, 212, 0.45);
  border-radius: 999px;
}
[data-testid="stTabs"] [role="tabpanel"]::-webkit-scrollbar-thumb:hover {
  background: rgba(94, 234, 212, 0.65);
}

/* Two-column game layout: board on the left, tabs on the right.
   On a narrow window (or a tall, portrait-ish one) the right column squeezes
   the board too much, so stack instead: full-width board, tabs underneath.
   The 3-column layout (sidebar, board, tabs) is kept for wide screens. */
.st-key-fc-split [data-testid="stHorizontalBlock"] {
  align-items: flex-start;
  /* Streamlit wraps columns by default. Keep them on one line: the board is
     sized from the height budget, so the remainder is always the graph. */
  flex-wrap: nowrap !important;
  gap: 0.75rem !important;
}
.st-key-fc-split [data-testid="stVerticalBlock"] { gap: 0.4rem; }
@media (min-width: 1201px) and (min-aspect-ratio: 3/2) {
  /* The board column is exactly as wide as the board. Whatever width the
     height budget took away is handed to the tabs and their graph. */
  .st-key-fc-split [data-testid="stHorizontalBlock"] > div:first-child {
    flex: 0 0 var(--fc-grid-max) !important;
    width: var(--fc-grid-max) !important;
    max-width: var(--fc-grid-max) !important;
  }
  .st-key-fc-split [data-testid="stHorizontalBlock"] > div:last-child {
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
  }
}
@media (max-width: 1200px), (max-aspect-ratio: 3/2) {
  /* Narrow or portrait-ish: stack and keep scroll behavior consistent by
     resizing the grid rather than forcing awkward nested scroll. */
  :root { --fc-grid-max: clamp(240px, min(82vw, 52vh), 560px); }
  [data-testid="stTabs"] [role="tabpanel"] {
    min-height: clamp(140px, 24vh, 300px);
    max-height: min(46vh, 420px);
  }
  .st-key-fc-split [data-testid="stHorizontalBlock"] {
    flex-direction: column;
    gap: 0.7rem;
  }
  .st-key-fc-split [data-testid="stHorizontalBlock"] > div {
    width: 100% !important;
    max-width: none !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
  }
}
/* Very short viewports (e.g., landscape phone, small laptop height): shrink the
   grid and tab panel so a single scroll pattern remains usable. */
@media (max-height: 720px) {
  :root { --fc-grid-max: clamp(220px, min(70vw, calc(100vh - 360px)), 520px); }
  [data-testid="stTabs"] [role="tabpanel"] {
    min-height: 120px;
    max-height: clamp(140px, calc(100vh - 380px), 360px);
  }
}
@media (max-height: 560px) {
  :root { --fc-grid-max: clamp(180px, min(64vw, calc(100vh - 300px)), 360px); }
  [data-testid="stTabs"] [role="tabpanel"] {
    min-height: 100px;
    max-height: clamp(120px, calc(100vh - 320px), 240px);
  }
}

/* Hero */
.fc-hero {
  display: flex;
  align-items: baseline;
  gap: 0.7rem;
  flex-wrap: wrap;
  margin: 0;
}
.fc-title {
  font-size: 1.55rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  background: linear-gradient(90deg, var(--fc-accent), var(--fc-accent-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.fc-tagline { color: var(--fc-muted); font-size: 0.85rem; }
.fc-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.12rem 0.55rem;
  border: 1px solid var(--fc-border);
  border-radius: 999px;
  color: var(--fc-muted);
  font-size: 0.75rem;
  background: rgba(15, 23, 42, 0.7);
}
.fc-pill.live { color: var(--fc-good); border-color: rgba(74, 222, 128, 0.35); }
.fc-pill.paused { color: var(--fc-warn); border-color: rgba(251, 191, 36, 0.35); }

/* Grid: fluid and square-ish, never scrolls sideways.
   --fc-cols / --fc-rows are set per grid instance by the renderer. The width
   is the smaller of the column width and the height budget, so a 30x30 board
   fits the viewport instead of forcing a vertical scrollbar. */
.fc-grid {
  display: grid;
  grid-template-columns: repeat(var(--fc-cols), minmax(0, 1fr));
  grid-auto-rows: 1fr;
  gap: clamp(1px, 0.15vh, 2px);
  padding: clamp(0.25rem, 0.7vh, 0.55rem);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(7, 11, 20, 0.95));
  border: 1px solid var(--fc-border);
  border-radius: 12px;
  width: min(100%, var(--fc-grid-max));
  aspect-ratio: var(--fc-cols) / var(--fc-rows);
  margin-inline: auto;
  overflow: hidden;
  container-type: size;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
}
.fc-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 0;
  font-size: clamp(0.4rem, 1.1vh, 1rem);
  line-height: 1;
  border-radius: 3px;
  background: rgba(30, 45, 74, 0.35);
  user-select: none;
}
/* Container-query units size the glyph from the board itself, so a narrow
   window shrinks the emoji instead of overflowing the cell. */
@supports (container-type: size) {
  .fc-cell { font-size: min(2.2cqw, 1.5rem); }
}
/* An archived achievement badge is a record, not the live board: keep it
   small even though the live board is sized to the viewport. */
.fc-grid.fc-grid-snapshot { width: min(100%, 200px); }

/* Offline agents are hidden: no glyph, no background. The empty span keeps
   the geometry stable so the living cells do not jump around. */
.fc-empty { background: transparent; box-shadow: none; }
/* Cells whose agents produced a block this tick are marked with a static ring.
   No animation: flashing elements can trigger photosensitive reactions. */
.fc-produced {
  box-shadow: 0 0 0 1px rgba(94, 234, 212, 0.5);
}
/* No per-tick animation on the grid. The board updates its contents each tick;
   motion is not needed to show that. */
/* A slot with no agent at all keeps a faint dot, so "nobody lives here" and
   "this agent went offline" never look the same. */
.fc-slot { color: #1e2d4a; background: transparent; box-shadow: none; }
.fc-miner { background: rgba(251, 191, 36, 0.16); box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.22); }
.fc-validator { background: rgba(94, 234, 212, 0.14); box-shadow: inset 0 0 0 1px rgba(94, 234, 212, 0.22); }
.fc-user { background: rgba(147, 197, 253, 0.13); box-shadow: inset 0 0 0 1px rgba(147, 197, 253, 0.20); }
.fc-trader { background: rgba(240, 171, 252, 0.13); box-shadow: inset 0 0 0 1px rgba(240, 171, 252, 0.20); }
.fc-developer { background: rgba(134, 239, 172, 0.13); box-shadow: inset 0 0 0 1px rgba(134, 239, 172, 0.20); }
.fc-attacker { background: rgba(251, 113, 133, 0.16); box-shadow: inset 0 0 0 1px rgba(251, 113, 133, 0.25); }

.fc-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem 0.55rem;
  margin: 0.25rem 0 0 0;
  color: var(--fc-muted);
  font-size: 0.66rem;
  line-height: 1.25;
}
.fc-legend-item { display: inline-flex; align-items: center; gap: 0.2rem; }
.fc-legend .fc-cell { font-size: 0.58rem; width: 1rem; height: 1rem; border-radius: 3px; }
.fc-legend-count { color: var(--fc-text); font-variant-numeric: tabular-nums; }

/* Metric cards: 12 / 6 / 4 / 3 per line as the available width changes.
   The wrapper is a size container so the breakpoints follow the real width of
   the content area, not the browser window (the sidebar changes it). */
.fc-cards-wrap { container-type: inline-size; }
.fc-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.4rem;
  margin: 0 0 0.5rem 0;
}
@container (min-width: 380px) { .fc-cards { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@container (min-width: 520px) { .fc-cards { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@container (min-width: 760px) { .fc-cards { grid-template-columns: repeat(6, minmax(0, 1fr)); } }
@container (min-width: 1400px) { .fc-cards { grid-template-columns: repeat(12, minmax(0, 1fr)); } }
.fc-card {
  background: linear-gradient(180deg, rgba(17, 28, 51, 0.95), rgba(12, 19, 35, 0.95));
  border: 1px solid var(--fc-border);
  border-radius: 10px;
  padding: 0.4rem 0.5rem;
  min-height: 0;
}
.fc-card .label {
  color: var(--fc-muted);
  font-size: 0.6rem;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.fc-card .value {
  color: var(--fc-text);
  font-size: 1.02rem;
  font-weight: 700;
  line-height: 1.2;
  margin-top: 0.1rem;
  font-variant-numeric: tabular-nums;
}
.fc-card .sub {
  color: var(--fc-muted);
  font-size: 0.6rem;
  line-height: 1.2;
  margin-top: 0.05rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fc-badge {
  font-size: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--fc-accent-2);
  border: 1px solid rgba(167, 139, 250, 0.35);
  border-radius: 999px;
  padding: 0 0.24rem;
}
.fc-good { color: var(--fc-good); }
.fc-warn { color: var(--fc-warn); }
.fc-bad { color: var(--fc-bad); }

/* Health bars */
.fc-bars { display: grid; gap: 0.25rem; margin-top: 0.2rem; }
.fc-bar-row { display: grid; grid-template-columns: 7rem 1fr 2.6rem; gap: 0.4rem; align-items: center; font-size: 0.7rem; color: var(--fc-muted); }
.fc-bar { height: 0.4rem; background: rgba(30, 45, 74, 0.6); border-radius: 999px; overflow: hidden; }
.fc-bar > span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--fc-accent), var(--fc-accent-2)); }

/* Misc */
.fc-note {
  border-left: 2px solid var(--fc-accent);
  background: rgba(94, 234, 212, 0.06);
  padding: 0.45rem 0.65rem;
  border-radius: 0 8px 8px 0;
  color: var(--fc-text);
  font-size: 0.8rem;
  margin: 0.3rem 0 0.5rem 0;
}
.fc-guide {
  display: grid;
  gap: 0.5rem;
  margin: 0.2rem 0 0.6rem 0;
}
.fc-guide-card {
  background: linear-gradient(180deg, rgba(17, 28, 51, 0.95), rgba(12, 19, 35, 0.95));
  border: 1px solid var(--fc-border);
  border-radius: 10px;
  padding: 0.55rem 0.7rem;
}
.fc-guide-card h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.88rem;
  color: var(--fc-text);
  letter-spacing: -0.01em;
}
.fc-guide-card p, .fc-guide-card li {
  margin: 0.12rem 0;
  color: var(--fc-muted);
  font-size: 0.8rem;
  line-height: 1.45;
}
.fc-guide-card ol, .fc-guide-card ul {
  margin: 0.15rem 0 0 1.1rem;
  padding: 0;
}
.fc-guide-card strong { color: var(--fc-text); font-weight: 600; }
.fc-guide-card code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.74rem;
  color: var(--fc-accent);
}
.fc-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.74rem; color: var(--fc-muted); }
.fc-score { font-size: 1.9rem; font-weight: 800; font-variant-numeric: tabular-nums; }
.fc-hint { color: var(--fc-text); background: rgba(251, 191, 36, 0.08); border: 1px solid rgba(251, 191, 36, 0.25); border-radius: 10px; padding: 0.4rem 0.6rem; margin: 0.25rem 0; font-size: 0.8rem; }
.fc-award { display: flex; gap: 0.6rem; align-items: flex-start; border: 1px solid var(--fc-border); border-radius: 10px; padding: 0.55rem; background: rgba(17, 28, 51, 0.6); margin-bottom: 0.4rem; }
.fc-award .icon { font-size: 1.35rem; line-height: 1; }
.fc-award .name { font-weight: 700; }
.fc-award .desc { color: var(--fc-muted); font-size: 0.74rem; }
.fc-locked { opacity: 0.55; }
</style>
"""


def inject() -> None:
    """Install the stylesheet. Safe to call once per Streamlit rerun."""
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, tagline: str, running: bool, tick: int | None = None) -> str:
    """HTML for the page header with a live/paused pill and the current tick.

    The tick lives here, inside the animated fragment, rather than in the
    sidebar. The sidebar is rendered once per full page rerun, so a tick
    counter there would sit frozen while the simulation advanced.
    """
    clock = f" · tick {tick:,}" if tick is not None else ""
    state = (
        f'<span class="fc-pill live">● running{clock}</span>'
        if running
        else f'<span class="fc-pill paused">● paused{clock}</span>'
    )
    return (
        f'<div class="fc-hero"><span class="fc-title">{title}</span>'
        f'<span class="fc-tagline">{tagline}</span>{state}</div>'
    )


__all__ = ["CSS", "hero", "inject"]
