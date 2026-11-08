"""Awarding and persisting achievements.

Persistence is a single JSON file. No database, no migrations, no server. If
the file is missing or corrupt, the game starts with zero awards rather than
crashing — a lost badge should never stop someone from playing.

Idempotence
-----------
Evaluating the same run twice awards nothing the second time. That property is
tested explicitly, because "did it twice by accident" is the normal state of a
web app that reruns on every click.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .conditions import ACHIEVEMENT_DEFS, RunSummary


@dataclass(frozen=True)
class Award:
    """A permanent record of one achievement earned by one run."""

    id: str
    name: str
    description: str
    icon: str
    awarded_at: str
    config_hash: str
    seed: int
    tick: int
    metrics: dict[str, float] = field(default_factory=dict)
    snapshot: str = ""

    # Grid shape when the snapshot was taken. Stored with the award so a badge
    # still renders correctly after the player changes the grid size.
    rows: int = 0
    cols: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Award:
        """Build an Award, ignoring fields written by a newer version."""
        allowed = {
            "id",
            "name",
            "description",
            "icon",
            "awarded_at",
            "config_hash",
            "seed",
            "tick",
            "metrics",
            "snapshot",
            "rows",
            "cols",
        }
        return cls(**{k: v for k, v in data.items() if k in allowed})


class AchievementManager:
    """Evaluates achievements and keeps the local award history."""

    def __init__(
        self,
        path: str | Path | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = Path(path) if path is not None else Path("data") / "achievements.json"
        self.clock = clock or (lambda: datetime.now(UTC))
        self.awards: dict[str, Award] = {}
        self._load()

    # -- queries ------------------------------------------------------------

    @property
    def awarded_ids(self) -> set[str]:
        return set(self.awards)

    def has(self, achievement_id: str) -> bool:
        return achievement_id in self.awards

    def as_list(self) -> list[Award]:
        """Newest first, for display."""
        return sorted(self.awards.values(), key=lambda a: a.awarded_at, reverse=True)

    def import_awards(self, payload: list) -> int:
        """Merge awards from another machine. Returns how many were new."""
        added = 0
        if not isinstance(payload, list):
            return 0
        for item in payload:
            if not isinstance(item, dict) or "id" not in item:
                continue
            if item["id"] in self.awards:
                continue
            try:
                award = Award.from_dict(item)
            except TypeError:
                continue
            self.awards[award.id] = award
            added += 1
        if added:
            self._save()
        return added

    # -- evaluation ---------------------------------------------------------

    def evaluate(self, summary: RunSummary) -> list[Award]:
        """Award every newly satisfied achievement. Returns only the new ones."""
        new_awards: list[Award] = []

        for definition in ACHIEVEMENT_DEFS:
            if definition.id in self.awards:
                continue
            if not definition.condition(summary):
                continue

            award = Award(
                id=definition.id,
                name=definition.name,
                description=definition.description,
                icon=definition.icon,
                awarded_at=self.clock().isoformat(timespec="seconds"),
                config_hash=summary.config.fingerprint(),
                seed=summary.config.seed,
                tick=summary.tick,
                metrics=summary.metrics.as_dict(),
                snapshot=summary.snapshot,
                rows=summary.config.rows,
                cols=summary.config.cols,
            )
            self.awards[award.id] = award
            new_awards.append(award)

        if new_awards:
            self._save()

        return new_awards

    # -- persistence --------------------------------------------------------

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # A corrupt file must not stop the game. The next save rewrites it.
            return

        if not isinstance(raw, list):
            return

        for item in raw:
            if not isinstance(item, dict) or "id" not in item:
                continue
            try:
                award = Award.from_dict(item)
            except TypeError:
                continue
            self.awards[award.id] = award

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [a.to_dict() for a in self.as_list()]
        # Write to a temporary file then replace: a crash mid-write cannot
        # leave a half-written achievements file.
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(self.path)


__all__ = ["AchievementManager", "Award"]
