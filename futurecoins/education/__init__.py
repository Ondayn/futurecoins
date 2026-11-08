"""Educational content: one glossary, one resource list, many surfaces."""

from __future__ import annotations

from .glossary import GLOSSARY, GlossaryEntry, categories, get, search, short
from .resources import RESOURCES, Resource, by_topic, topics

__all__ = [
    "GLOSSARY",
    "RESOURCES",
    "GlossaryEntry",
    "Resource",
    "by_topic",
    "categories",
    "get",
    "search",
    "short",
    "topics",
]
