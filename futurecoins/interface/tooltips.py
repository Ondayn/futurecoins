"""Small educational surfaces: popovers and inline notes.

All text comes from `futurecoins.education.glossary`. If a term is missing, the
popover renders nothing rather than inventing an explanation.
"""

from __future__ import annotations

import streamlit as st

from ..education import get


def popover(term: str, label: str | None = None) -> None:
    """A click-to-open explanation with the real-world example and one link."""
    entry = get(term)
    if entry is None:
        return

    with st.popover(f"ⓘ {label or entry.term}"):
        st.markdown(f"**{entry.term}** — {entry.short}")
        st.write(entry.explanation)
        st.markdown(f"**In this simulation**  \n{entry.in_game}")
        st.markdown(f"**In the real world**  \n{entry.real_world}")
        if entry.link:
            st.link_button(entry.link_label or "Learn more", entry.link)


def note(text: str) -> None:
    """A quiet inline callout, used for teaching moments."""
    st.html(f'<div class="fc-note">{text}</div>')


__all__ = ["note", "popover"]
