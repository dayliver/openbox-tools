"""Filesystem locations for Openbox / Archcraft keybinds."""

from __future__ import annotations

from pathlib import Path

NS = "http://openbox.org/3.4/rc"

HOME = Path.home()
OPENBOX_DIR = HOME / ".config" / "openbox"
RC_XML = OPENBOX_DIR / "rc.xml"
KBIND_TXT = OPENBOX_DIR / "kbinds.txt"
BACKUP_DIR = OPENBOX_DIR / "backups"

SKEL_RC = Path("/etc/skel/.config/openbox/rc.xml")

# Bundled fallback (shipped with the package)
BUNDLED_KEYBOARD = Path(__file__).resolve().parent / "data" / "archcraft-keyboard.xml"
