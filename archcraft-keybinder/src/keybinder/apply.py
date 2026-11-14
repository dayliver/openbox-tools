"""Regenerate kbinds.txt and reconfigure Openbox."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from keybinder.models import Keybind
from keybinder.paths import KBIND_TXT, RC_XML


def format_kbinds_txt(keybinds: list[Keybind]) -> str:
    """Approximate Archcraft ac-kb listing format."""
    lines: list[str] = []
    for kb in keybinds:
        is_execute = any(a.name == "Execute" for a in kb.actions)
        flag = "x " if is_execute else "o "
        summary = kb.summary()
        lines.append(f"{flag}{kb.key:<16}\t{summary}")
    return "\n".join(lines) + ("\n" if lines else "")


def write_kbinds_txt(keybinds: list[Keybind], path: Path | None = None) -> Path:
    target = path or KBIND_TXT
    target.write_text(format_kbinds_txt(keybinds), encoding="utf-8")
    return target


def reconfigure_openbox() -> subprocess.CompletedProcess[str]:
    openbox = shutil.which("openbox")
    if not openbox:
        raise FileNotFoundError("openbox not found on PATH")
    return subprocess.run(
        [openbox, "--reconfigure"],
        check=False,
        capture_output=True,
        text=True,
    )


def apply_changes(keybinds: list[Keybind] | None = None) -> dict:
    from keybinder.defaults import load_current

    binds = keybinds if keybinds is not None else load_current(RC_XML)
    kbinds_path = write_kbinds_txt(binds)
    result = reconfigure_openbox()
    return {
        "kbinds": str(kbinds_path),
        "reconfigure_returncode": result.returncode,
        "reconfigure_stderr": (result.stderr or "").strip(),
        "reconfigure_stdout": (result.stdout or "").strip(),
    }
