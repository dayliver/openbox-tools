"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Category(str, Enum):
    APPS = "apps"
    MENUS = "menus"
    WINDOW = "window"
    HARDWARE = "hardware"
    SESSION = "session"
    OTHER = "other"


class Origin(str, Enum):
    STOCK = "stock"  # identical to Archcraft default
    MODIFIED = "modified"  # same key as stock, different payload
    CUSTOM = "custom"  # key not in stock


@dataclass
class Action:
    name: str
    params: dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        if self.name == "Execute":
            return self.params.get("command") or self.params.get("execute") or "Execute"
        if self.name == "ShowMenu":
            return self.params.get("menu") or "ShowMenu"
        return self.name


@dataclass
class Keybind:
    key: str
    actions: list[Action] = field(default_factory=list)
    category: Category = Category.OTHER
    origin: Origin = Origin.CUSTOM
    # Raw XML snippet for this <keybind>...</keybind> (round-trip / reset-one)
    raw_xml: str = ""

    def summary(self) -> str:
        if not self.actions:
            return ""
        if len(self.actions) == 1:
            return self.actions[0].summary()
        return " + ".join(a.summary() for a in self.actions)

    def fingerprint(self) -> str:
        """Stable comparison key against stock (ignores whitespace in raw_xml)."""
        parts: list[str] = []
        for action in self.actions:
            parts.append(action.name)
            for k in sorted(action.params):
                parts.append(f"{k}={action.params[k]}")
        return "|".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "category": self.category.value,
            "origin": self.origin.value,
            "summary": self.summary(),
            "actions": [
                {"name": a.name, "params": a.params} for a in self.actions
            ],
        }
