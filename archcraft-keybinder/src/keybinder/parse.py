"""Parse Openbox rc.xml keyboard section into Keybind models."""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

from keybinder.categorize import assign_category
from keybinder.models import Action, Keybind
from keybinder.paths import NS, RC_XML

_KEYBOARD_RE = re.compile(r"[ \t]*<keyboard\b[^>]*>.*?</keyboard>", re.DOTALL)


def extract_keyboard_xml(text: str) -> str:
    match = _KEYBOARD_RE.search(text)
    if not match:
        raise ValueError("No <keyboard> section found in rc.xml")
    return match.group(0)


def read_rc_text(path: Path | None = None) -> str:
    target = path or RC_XML
    return target.read_text(encoding="utf-8")


def _local(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _action_from_elem(elem: etree._Element) -> Action:
    name = elem.get("name") or ""
    params: dict[str, str] = {}
    for child in elem:
        if not isinstance(child.tag, str):
            continue
        local = _local(child.tag)
        if local == "action":
            continue
        text = (child.text or "").strip()
        if text:
            params[local] = text
    return Action(name=name, params=params)


def _keybind_from_elem(elem: etree._Element) -> Keybind:
    key = elem.get("key") or ""
    actions = [
        _action_from_elem(child)
        for child in elem
        if isinstance(child.tag, str) and _local(child.tag) == "action"
    ]
    raw = etree.tostring(elem, encoding="unicode")
    kb = Keybind(key=key, actions=actions, raw_xml=raw)
    return assign_category(kb)


def parse_keyboard_xml(keyboard_xml: str) -> list[Keybind]:
    """Parse a <keyboard>...</keyboard> fragment (or full rc.xml)."""
    # Ensure a single root for fragments that already are <keyboard>
    root = etree.fromstring(keyboard_xml.encode("utf-8"))
    if _local(root.tag) == "keyboard":
        keyboard = root
    else:
        keyboard = root.find(f"{{{NS}}}keyboard")
        if keyboard is None:
            keyboard = root.find("keyboard")
        if keyboard is None:
            raise ValueError("Could not find keyboard element")

    binds: list[Keybind] = []
    for child in keyboard:
        if isinstance(child.tag, str) and _local(child.tag) == "keybind":
            binds.append(_keybind_from_elem(child))
    return binds


def parse_rc(path: Path | None = None) -> list[Keybind]:
    text = read_rc_text(path)
    keyboard_xml = extract_keyboard_xml(text)
    return parse_keyboard_xml(keyboard_xml)


def parse_rc_with_meta(path: Path | None = None) -> tuple[str, str, list[Keybind]]:
    """Return (full_text, keyboard_xml, keybinds)."""
    text = read_rc_text(path)
    keyboard_xml = extract_keyboard_xml(text)
    return text, keyboard_xml, parse_keyboard_xml(keyboard_xml)
