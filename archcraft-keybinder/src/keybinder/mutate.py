"""Mutate individual keybinds inside the keyboard section."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from keybinder.parse import extract_keyboard_xml, parse_keyboard_xml, read_rc_text
from keybinder.paths import RC_XML
from keybinder.write import write_rc_with_keyboard


class MutateError(RuntimeError):
    pass


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) and tag.startswith("{") else str(tag)


def _qname(parent: etree._Element, name: str) -> str:
    """Tag for a new child, in the same namespace as ``parent``.

    A <keyboard> fragment cut out of rc.xml carries no xmlns of its own (it is
    inherited from <openbox_config>), so forcing the Openbox namespace here
    would serialise new nodes as ``<ns0:keybind xmlns:ns0=…>``.
    """
    ns = etree.QName(parent).namespace
    return f"{{{ns}}}{name}" if ns else name


def _load_keyboard(path: Path | None = None) -> tuple[Path, etree._Element]:
    target = path or RC_XML
    text = read_rc_text(target)
    kb_xml = extract_keyboard_xml(text)
    root = etree.fromstring(kb_xml.encode("utf-8"))
    return target, root


def _dump_keyboard(root: etree._Element) -> str:
    return etree.tostring(root, encoding="unicode")


def _find_keybinds(root: etree._Element, key: str) -> list[etree._Element]:
    found = []
    for child in root:
        if isinstance(child.tag, str) and _local(child.tag) == "keybind" and child.get("key") == key:
            found.append(child)
    return found


def _action_elements(keybind: etree._Element) -> list[etree._Element]:
    return [
        child
        for child in keybind
        if isinstance(child.tag, str) and _local(child.tag) == "action"
    ]


def _set_leaf_param(action: etree._Element, name: str, value: str) -> None:
    """Set/create a simple text child on an action without touching nested structures."""
    for child in action:
        if isinstance(child.tag, str) and _local(child.tag) == name:
            # Don't overwrite container nodes that have element children (e.g. finalactions)
            if len(child):
                return
            child.text = value
            return
    node = etree.SubElement(action, _qname(action, name))
    node.text = value


def set_execute(
    key: str,
    command: str,
    path: Path | None = None,
    *,
    do_backup: bool = True,
) -> dict:
    """Set (or create) a single Execute keybind for `key` (replaces all actions)."""
    target, root = _load_keyboard(path)
    existing = _find_keybinds(root, key)
    if existing:
        elem = existing[0]
        for extra in existing[1:]:
            root.remove(extra)
        for child in list(elem):
            elem.remove(child)
    else:
        elem = etree.SubElement(root, _qname(root, "keybind"))
        elem.set("key", key)
    elem.set("key", key)
    action = etree.SubElement(elem, _qname(elem, "action"))
    action.set("name", "Execute")
    _set_leaf_param(action, "command", command)
    backup = write_rc_with_keyboard(_dump_keyboard(root), path=target, do_backup=do_backup)
    return {
        "key": key,
        "command": command,
        "backup": str(backup) if backup else None,
        "path": str(target),
    }


def update_keybind(
    old_key: str,
    *,
    new_key: str | None = None,
    action_name: str | None = None,
    params: dict[str, str] | None = None,
    path: Path | None = None,
    do_backup: bool = True,
    create_if_missing: bool = False,
    replace_primary: bool = False,
) -> dict:
    """Update key chord and/or primary action.

    - Renames the keybind when ``new_key`` differs.
    - Updates the first ``<action>`` name/params surgically (keeps sibling actions
      and nested nodes like ``finalactions``).
    - If ``replace_primary`` and action is Execute-only style, clears primary
      action children then applies params (used by set_execute).
    """
    target, root = _load_keyboard(path)
    existing = _find_keybinds(root, old_key)
    new_key = (new_key or old_key).strip()
    if not new_key:
        raise MutateError("Key chord cannot be empty")

    if not existing:
        if not create_if_missing:
            raise KeyError(f"Keybind not found: {old_key}")
        elem = etree.SubElement(root, _qname(root, "keybind"))
        elem.set("key", new_key)
        action = etree.SubElement(elem, _qname(elem, "action"))
        action.set("name", action_name or "Execute")
        for pname, pval in (params or {}).items():
            if pval.strip():
                _set_leaf_param(action, pname, pval.strip())
        backup = write_rc_with_keyboard(_dump_keyboard(root), path=target, do_backup=do_backup)
        return {
            "old_key": old_key,
            "key": new_key,
            "backup": str(backup) if backup else None,
            "path": str(target),
        }

    elem = existing[0]
    for extra in existing[1:]:
        root.remove(extra)

    if new_key != old_key:
        clashes = _find_keybinds(root, new_key)
        # elem still has old_key until we set it; clashes shouldn't include self
        clashes = [c for c in clashes if c is not elem]
        if clashes:
            raise MutateError(f"Key already in use: {new_key}")
        elem.set("key", new_key)

    actions = _action_elements(elem)
    if not actions:
        action = etree.SubElement(elem, _qname(elem, "action"))
        action.set("name", action_name or "Execute")
        actions = [action]
    primary = actions[0]

    if action_name:
        primary.set("name", action_name)

    if params is not None:
        if replace_primary:
            for child in list(primary):
                primary.remove(child)
        for pname, pval in params.items():
            pval = pval.strip()
            if not pval:
                continue
            _set_leaf_param(primary, pname, pval)

    backup = write_rc_with_keyboard(_dump_keyboard(root), path=target, do_backup=do_backup)
    return {
        "old_key": old_key,
        "key": new_key,
        "action": primary.get("name"),
        "backup": str(backup) if backup else None,
        "path": str(target),
    }


def remove_key(
    key: str,
    path: Path | None = None,
    *,
    do_backup: bool = True,
) -> dict:
    target, root = _load_keyboard(path)
    found = _find_keybinds(root, key)
    if not found:
        raise KeyError(f"Keybind not found: {key}")
    for elem in found:
        root.remove(elem)
    backup = write_rc_with_keyboard(_dump_keyboard(root), path=target, do_backup=do_backup)
    return {
        "key": key,
        "removed": len(found),
        "backup": str(backup) if backup else None,
        "path": str(target),
    }


def get_key(key: str, path: Path | None = None):
    binds = [
        kb
        for kb in parse_keyboard_xml(extract_keyboard_xml(read_rc_text(path)))
        if kb.key == key
    ]
    if not binds:
        raise KeyError(f"Keybind not found: {key}")
    return binds
