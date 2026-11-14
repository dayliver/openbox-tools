from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path

# WM_CLASS (group) → launch command. Extend as needed.
CLASS_LAUNCH: dict[str, str] = {
    "Alacritty": "alacritty",
    "alacritty_fullscreen": "ob-furminal",
    "kitty": "kitty",
    "Thunar": "thunar",
    "firefox": "firefox",
    "Firefox": "firefox",
    "Google-chrome": "google-chrome-stable",
    "Chromium": "chromium",
    "Brave-browser": "brave",
    "Code": "code",
    "code-oss": "code",
    "Cursor": "cursor",
    "cursor": "cursor",
    "Geany": "geany",
    "org.gnome.Nautilus": "nautilus",
    "Gimp": "gimp",
    "obsidian": "obsidian",
    "Spotify": "spotify",
    "TelegramDesktop": "telegram-desktop",
    "Xfce4-terminal": "xfce4-terminal",
}

# Classes that accept a working-directory flag on launch.
TERMINAL_CLASSES = {
    "alacritty",
    "alacritty_fullscreen",
    "kitty",
    "xfce4-terminal",
    "gnome-terminal",
    "org.gnome.terminal",
    "foot",
    "wezterm",
}


def resolve_launch(klass: str, instance: str = "") -> str | None:
    if klass in CLASS_LAUNCH:
        return CLASS_LAUNCH[klass]
    for k, cmd in CLASS_LAUNCH.items():
        if k.lower() == klass.lower():
            return cmd
    cmd = _from_desktop(klass, instance)
    if cmd:
        return cmd
    if shutil.which(klass.lower()):
        return klass.lower()
    return None


def _from_desktop(klass: str, instance: str) -> str | None:
    data_dirs = [
        Path.home() / ".local/share/flatpak/exports/share/applications",
        Path.home() / ".local/share/applications",
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
    ]
    targets = {klass.lower(), instance.lower()} - {""}
    for d in data_dirs:
        if not d.is_dir():
            continue
        for desk in d.glob("*.desktop"):
            try:
                text = desk.read_text(errors="ignore")
            except OSError:
                continue
            wm = ""
            exec_line = ""
            no_display = False
            for line in text.splitlines():
                if line.startswith("StartupWMClass="):
                    wm = line.split("=", 1)[1].strip().lower()
                elif line.startswith("Exec="):
                    exec_line = line.split("=", 1)[1].strip()
                elif line.startswith("NoDisplay=true"):
                    no_display = True
            if no_display or not exec_line:
                continue
            if wm and wm in targets:
                return _clean_exec(exec_line)
    return None


def _clean_exec(exec_line: str) -> str:
    parts = []
    for tok in exec_line.split():
        if tok.startswith("%"):
            continue
        parts.append(tok)
    return " ".join(parts)


def supports_cwd(klass: str) -> bool:
    return klass.lower() in TERMINAL_CLASSES


def build_launch_cmd(base: str, klass: str, cwd: str | None) -> str:
    """Attach working-directory when the app supports it."""
    if not cwd or not os.path.isdir(cwd) or not supports_cwd(klass):
        return base

    k = klass.lower()
    q = shlex.quote(cwd)

    # Maximized furminal wrapper has no cwd flag — rebuild alacritty cmdline.
    if k == "alacritty_fullscreen" or base.strip() == "ob-furminal":
        return (
            "alacritty --class 'alacritty_fullscreen,alacritty_fullscreen' "
            f"--working-directory {q} "
            "-o window.startup_mode=\"'Maximized'\" window.padding.x=45 "
            "window.padding.y=45 window.opacity=1.0 font.size=14 "
            "-e /bin/zsh -l"
        )

    if k == "alacritty" or base.strip().startswith("alacritty"):
        # Insert after binary name
        parts = shlex.split(base)
        if parts and parts[0] == "alacritty":
            parts[1:1] = ["--working-directory", cwd]
            return shlex.join(parts)
        return f"alacritty --working-directory {q}"

    if k == "kitty" or base.strip().startswith("kitty"):
        parts = shlex.split(base)
        if parts and parts[0] == "kitty":
            parts[1:1] = ["--working-directory", cwd]
            return shlex.join(parts)
        return f"kitty --working-directory={q}"

    if k in {"xfce4-terminal"} or "xfce4-terminal" in base:
        return f"{base} --working-directory={q}"

    if "gnome-terminal" in k or "gnome-terminal" in base:
        return f"{base} --working-directory={q}"

    if k == "foot":
        return f"foot --working-directory={q}"

    if k == "wezterm" or base.strip().startswith("wezterm"):
        return f"wezterm start --cwd {q}"

    return base


def launch(cmd: str) -> None:
    env = os.environ.copy()
    subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
    )
