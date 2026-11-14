"""Key collision helpers."""

from __future__ import annotations

from collections import defaultdict

from keybinder.models import Keybind


def find_conflicts(keybinds: list[Keybind], key: str | None = None) -> dict[str, list[Keybind]]:
    """Return keys that appear more than once (optionally filter to one key)."""
    buckets: dict[str, list[Keybind]] = defaultdict(list)
    for kb in keybinds:
        buckets[kb.key].append(kb)
    conflicts = {k: v for k, v in buckets.items() if len(v) > 1}
    if key is not None:
        return {key: conflicts[key]} if key in conflicts else {}
    return conflicts
