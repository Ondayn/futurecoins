"""Compact grid snapshots for achievement records.

An achievement should be reproducible and *lookable*. Storing one character per
cell costs almost nothing and lets the awards page show the exact network that
earned the badge.

Encoding
--------
- one character per cell, row-major
- uppercase = at least one active agent in the cell
- lowercase = every agent in the cell is inactive
- ``.`` = empty cell

The character itself is the role's ASCII marker (M, V, u, T, D, A).
"""

from __future__ import annotations

from collections import Counter

from ..agents import ROLE_META, Agent, Role


def encode_snapshot(agents: list[Agent], rows: int, cols: int) -> str:
    """Encode the current population as exactly ``rows * cols`` characters."""
    buckets: dict[tuple[int, int], list[Agent]] = {}
    for agent in agents:
        row = min(max(agent.row, 0), rows - 1)
        col = min(max(agent.col, 0), cols - 1)
        buckets.setdefault((row, col), []).append(agent)

    chars: list[str] = []
    for row in range(rows):
        for col in range(cols):
            group = buckets.get((row, col))
            if not group:
                chars.append(".")
                continue

            counts = Counter(a.role for a in group)
            # Deterministic tie-break by role value (alphabetical is fine here;
            # the grid view has its own presentation order).
            dominant = min(counts.items(), key=lambda item: (-item[1], item[0].value))[0]
            marker = ROLE_META[dominant]["ascii"]
            active = any(a.active for a in group)
            chars.append(marker.upper() if active else marker.lower())

    return "".join(chars)


def decode_snapshot(snapshot: str) -> dict[str, dict[str, int]]:
    """Count cells per role, split into active and inactive.

    Used by tests and by the achievements page (e.g. "this run ended with 412
    active user cells"). An empty cell is not a role and is ignored.
    """
    counts: dict[str, dict[str, int]] = {}
    for char in snapshot:
        if char == ".":
            continue
        role = _ROLE_BY_ASCII.get(char.upper())
        if role is None:
            continue
        bucket = counts.setdefault(role, {"active": 0, "inactive": 0})
        bucket["active" if char.isupper() else "inactive"] += 1
    return counts


_ROLE_BY_ASCII: dict[str, str] = {
    meta["ascii"].upper(): role.value for role, meta in ROLE_META.items()
}


def snapshot_dimensions(snapshot: str, cols: int) -> tuple[int, int]:
    """Return ``(rows, cols)`` implied by a snapshot, or ``(0, cols)`` if empty."""
    if cols <= 0 or not snapshot:
        return (0, max(cols, 0))
    return (len(snapshot) // cols, cols)


__all__ = ["Role", "decode_snapshot", "encode_snapshot", "snapshot_dimensions"]
