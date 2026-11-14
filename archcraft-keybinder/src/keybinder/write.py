"""Backup and write keyboard section into rc.xml without touching other sections."""

from __future__ import annotations

import re
import tempfile
from datetime import datetime
from pathlib import Path

from keybinder.paths import BACKUP_DIR, RC_XML
from keybinder.parse import extract_keyboard_xml

_KEYBOARD_RE = re.compile(r"[ \t]*<keyboard\b[^>]*>.*?</keyboard>", re.DOTALL)


def backup_rc(path: Path | None = None, backup_dir: Path | None = None) -> Path:
    src = path or RC_XML
    dest_dir = backup_dir or BACKUP_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = dest_dir / f"rc.xml.{stamp}"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def replace_keyboard_section(
    rc_text: str,
    new_keyboard_xml: str,
) -> str:
    new_keyboard_xml = new_keyboard_xml.strip()
    if not new_keyboard_xml.startswith("<keyboard"):
        raise ValueError("new_keyboard_xml must start with <keyboard>")
    if not _KEYBOARD_RE.search(rc_text):
        raise ValueError("No <keyboard> section found to replace")
    # Preserve leading indentation of the original block if new blob has none
    return _KEYBOARD_RE.sub(lambda _: new_keyboard_xml, rc_text, count=1)


def write_rc_with_keyboard(
    new_keyboard_xml: str,
    path: Path | None = None,
    *,
    do_backup: bool = True,
) -> Path | None:
    """Replace <keyboard> in rc.xml. Returns backup path if created."""
    target = path or RC_XML
    text = target.read_text(encoding="utf-8")
    # Validate both sides parse as keyboard
    extract_keyboard_xml(text)
    extract_keyboard_xml(new_keyboard_xml if "<keyboard" in new_keyboard_xml else f"<keyboard>{new_keyboard_xml}</keyboard>")

    backup_path = backup_rc(target) if do_backup else None
    updated = replace_keyboard_section(text, new_keyboard_xml)

    # Atomic replace
    fd, tmp_name = tempfile.mkstemp(
        prefix=".rc.xml.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with open(fd, "w", encoding="utf-8") as fh:
            fh.write(updated)
        tmp_path.replace(target)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return backup_path
