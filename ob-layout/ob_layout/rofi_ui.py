from __future__ import annotations

import subprocess
from pathlib import Path


def current_style() -> str:
    p = Path.home() / ".config/openbox/themes/.current"
    if p.is_file():
        return p.read_text().strip() or "default"
    return "default"


def rofi_theme() -> Path:
    style = current_style()
    base = Path.home() / ".config/openbox/themes" / style / "rofi"
    for name in ("runner.rasi", "launcher.rasi"):
        cand = base / name
        if cand.is_file():
            return cand
    return base / "runner.rasi"


def dmenu(prompt: str, items: list[str], lines: int | None = None) -> str | None:
    theme = rofi_theme()
    cmd = [
        "rofi",
        "-dmenu",
        "-i",
        "-p",
        prompt,
        "-theme",
        str(theme),
    ]
    if lines is not None:
        cmd.extend(["-l", str(lines)])
    proc = subprocess.run(
        cmd,
        input="\n".join(items) + ("\n" if items else ""),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    out = (proc.stdout or "").strip()
    return out or None


def ask_name(prompt: str = "Preset name") -> str | None:
    return dmenu(prompt, [], lines=0)
