"""Load Archcraft stock keybinds and reset helpers."""

from __future__ import annotations

from pathlib import Path

from keybinder.models import Keybind, Origin
from keybinder.parse import (
    extract_keyboard_xml,
    parse_keyboard_xml,
    parse_rc,
    read_rc_text,
)
from keybinder.paths import BUNDLED_KEYBOARD, RC_XML, SKEL_RC
from keybinder.write import write_rc_with_keyboard


class DefaultsError(RuntimeError):
    pass


def stock_keyboard_xml() -> tuple[str, Path]:
    """Return (keyboard_xml, source_path). Prefer live skel, then bundled."""
    if SKEL_RC.is_file():
        text = SKEL_RC.read_text(encoding="utf-8")
        return extract_keyboard_xml(text), SKEL_RC
    if BUNDLED_KEYBOARD.is_file():
        raw = BUNDLED_KEYBOARD.read_text(encoding="utf-8")
        if "<keyboard" in raw:
            return extract_keyboard_xml(raw), BUNDLED_KEYBOARD
        raise DefaultsError(f"Bundled defaults missing <keyboard>: {BUNDLED_KEYBOARD}")
    raise DefaultsError(
        "No Archcraft defaults found. Expected /etc/skel/.config/openbox/rc.xml "
        f"or {BUNDLED_KEYBOARD}"
    )


def stock_keybinds() -> list[Keybind]:
    xml, _ = stock_keyboard_xml()
    return parse_keyboard_xml(xml)


def annotate_origins(
    current: list[Keybind],
    stock: list[Keybind] | None = None,
) -> list[Keybind]:
    stock = stock if stock is not None else stock_keybinds()
    stock_map = {kb.key: kb for kb in stock}
    for kb in current:
        if kb.key not in stock_map:
            kb.origin = Origin.CUSTOM
        elif kb.fingerprint() == stock_map[kb.key].fingerprint():
            kb.origin = Origin.STOCK
        else:
            kb.origin = Origin.MODIFIED
    return current


def load_current(path: Path | None = None) -> list[Keybind]:
    return annotate_origins(parse_rc(path))


def diff_keybinds(
    current: list[Keybind] | None = None,
    stock: list[Keybind] | None = None,
) -> dict[str, list[Keybind]]:
    current = annotate_origins(current or parse_rc(), stock)
    stock = stock or stock_keybinds()
    current_keys = {kb.key for kb in current}
    stock_keys = {kb.key for kb in stock}
    stock_map = {kb.key: kb for kb in stock}

    modified = [kb for kb in current if kb.origin == Origin.MODIFIED]
    custom = [kb for kb in current if kb.origin == Origin.CUSTOM]
    missing = [stock_map[k] for k in sorted(stock_keys - current_keys)]
    return {
        "modified": modified,
        "custom": custom,
        "missing": missing,  # in stock but not in current
    }


def _fingerprint_map(binds: list[Keybind]) -> dict[str, str]:
    return {kb.key: kb.fingerprint() for kb in binds}


def reset_all(
    path: Path | None = None,
    *,
    dry_run: bool = False,
    do_backup: bool = True,
) -> dict:
    target = path or RC_XML
    stock_xml, source = stock_keyboard_xml()
    stock_binds = parse_keyboard_xml(stock_xml)
    if dry_run:
        current_binds = parse_rc(target)
        changed = _fingerprint_map(current_binds) != _fingerprint_map(stock_binds)
        return {
            "dry_run": True,
            "source": str(source),
            "changed": changed,
            "stock_keybinds": len(stock_binds),
        }
    backup = write_rc_with_keyboard(stock_xml, path=target, do_backup=do_backup)
    return {
        "dry_run": False,
        "source": str(source),
        "backup": str(backup) if backup else None,
        "path": str(target),
        "stock_keybinds": len(stock_binds),
    }


def _replace_or_insert_keybind(keyboard_xml: str, key: str, new_keybind_xml: str | None) -> str:
    """Replace keybind for `key` inside keyboard_xml. None deletes it."""
    from lxml import etree

    root = etree.fromstring(keyboard_xml.encode("utf-8"))

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1] if tag.startswith("{") else tag

    removed = False
    for child in list(root):
        if isinstance(child.tag, str) and local(child.tag) == "keybind" and child.get("key") == key:
            root.remove(child)
            removed = True
    if new_keybind_xml:
        new_elem = etree.fromstring(new_keybind_xml.encode("utf-8"))
        # Append before closing — after last keybind if possible
        root.append(new_elem)
    elif not removed:
        raise KeyError(f"Keybind not found: {key}")

    # Prefer keeping xmlns off children; tostring may add xmlns on keyboard
    return etree.tostring(root, encoding="unicode")


def reset_one(
    key: str,
    path: Path | None = None,
    *,
    dry_run: bool = False,
    do_backup: bool = True,
    remove_custom: bool = False,
) -> dict:
    """Restore a single key to stock. Custom keys: delete if remove_custom else error."""
    target = path or RC_XML
    stock = {kb.key: kb for kb in stock_keybinds()}
    current_text = read_rc_text(target)
    current_kb_xml = extract_keyboard_xml(current_text)
    current = {kb.key: kb for kb in parse_keyboard_xml(current_kb_xml)}

    if key in stock:
        new_raw = stock[key].raw_xml
        action = "restore"
    elif key in current:
        if not remove_custom:
            raise DefaultsError(
                f"{key} is a custom keybind (not in Archcraft defaults). "
                "Pass remove_custom=True / --remove-custom to delete it."
            )
        new_raw = None
        action = "remove-custom"
    else:
        raise KeyError(f"Unknown keybind: {key}")

    if dry_run:
        return {"dry_run": True, "key": key, "action": action}

    new_keyboard = _replace_or_insert_keybind(current_kb_xml, key, new_raw)
    backup = write_rc_with_keyboard(new_keyboard, path=target, do_backup=do_backup)
    return {
        "dry_run": False,
        "key": key,
        "action": action,
        "backup": str(backup) if backup else None,
        "path": str(target),
    }
