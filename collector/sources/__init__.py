"""Source registry: maps adapter names to factories.

Resolve the configured ``SOURCES`` env list to concrete adapters via
``resolve_sources``. Register a new board by adding a single entry to
``_REGISTRY``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from .base import Source
from .remoteok import RemoteOKSource
from .seed import SeedSource

logger = logging.getLogger("collector.sources")

# name -> zero-arg factory producing a Source instance.
_REGISTRY: dict[str, Callable[[], Source]] = {
    "seed": SeedSource,
    "remoteok": RemoteOKSource,
}


def available_sources() -> list[str]:
    """Return the names of all registered adapters."""
    return sorted(_REGISTRY)


def resolve_sources(names: list[str]) -> list[Source]:
    """Instantiate adapters for the given names, skipping unknown ones."""
    sources: list[Source] = []
    for name in names:
        factory = _REGISTRY.get(name)
        if factory is None:
            logger.warning("Unknown source '%s' (known: %s)", name, ", ".join(available_sources()))
            continue
        sources.append(factory())
    if not sources:
        logger.info("No valid sources resolved; defaulting to seed adapter")
        sources.append(SeedSource())
    return sources


__all__ = ["Source", "SeedSource", "RemoteOKSource", "resolve_sources", "available_sources"]
