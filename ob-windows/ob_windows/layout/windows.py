"""Layout-specific window queries: enumeration, terminal cwd, waiting for launches."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from ob_windows import wm
from ob_windows.rect import Rect

# A freshly mapped window often resizes itself once more right after appearing;
# give it a moment before we place it.
SETTLE_SECONDS = 0.2
POLL_SECONDS = 0.1


@dataclass
class WinInfo:
    xid: int
    klass: str
    instance: str
    title: str
    desktop: int  # 0-based
    rect: Rect
    maximized: bool
    cwd: str | None = None


_SHELL_NAMES = {
    "bash",
    "zsh",
    "fish",
    "sh",
    "dash",
    "tmux",
    "nu",
    "xonsh",
}


def _proc_comm(pid: int) -> str:
    try:
        return Path(f"/proc/{pid}/comm").read_text().strip()
    except OSError:
        return ""


def _proc_children(pid: int) -> list[int]:
    try:
        text = Path(f"/proc/{pid}/task/{pid}/children").read_text()
    except OSError:
        return []
    return [int(x) for x in text.split() if x.isdigit()]


def _proc_cwd(pid: int) -> str | None:
    try:
        cwd = os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None
    if not cwd or not os.path.isdir(cwd):
        return None
    return cwd


def window_cwd(xid: int) -> str | None:
    """Terminal-aware cwd: prefer foreground shell child over emulator process."""
    root = wm.window_pid(xid)
    if not root:
        return None

    # BFS: collect shell-like children first, else deepest child cwd, else root
    shells: list[int] = []
    others: list[int] = []
    q: deque[int] = deque([root])
    seen = {root}
    while q:
        pid = q.popleft()
        for child in _proc_children(pid):
            if child in seen:
                continue
            seen.add(child)
            q.append(child)
            name = _proc_comm(child)
            if name in _SHELL_NAMES:
                shells.append(child)
            else:
                others.append(child)

    for pid in reversed(shells):
        cwd = _proc_cwd(pid)
        if cwd:
            return cwd
    for pid in reversed(others):
        cwd = _proc_cwd(pid)
        if cwd:
            return cwd
    return _proc_cwd(root)


def list_normal_windows(desktop: int | None = None) -> list[WinInfo]:
    out: list[WinInfo] = []
    for xid in wm.client_list():
        if not wm.is_normal(xid) or wm.is_minimized(xid):
            continue
        desk = wm.window_desktop(xid)
        if desktop is not None and desk != desktop:
            continue
        try:
            rect = wm.frame_rect(xid)
        except RuntimeError:  # closed while we were looking
            continue
        instance, klass = wm.window_class(xid)
        out.append(
            WinInfo(
                xid=xid,
                klass=klass.strip() or "Unknown",
                instance=instance.strip() or "unknown",
                title=wm.window_name(xid).strip(),
                desktop=desk,
                rect=rect,
                maximized=wm.is_maximized(xid),
                cwd=window_cwd(xid),
            )
        )
    # Stable order: top-left first
    out.sort(key=lambda wi: (wi.rect.y, wi.rect.x, wi.klass))
    return out


def wait_for_window(klass: str, instance: str | None, timeout: float = 8.0) -> WinInfo | None:
    """Wait for a new window of this class/instance; else the newest existing match."""
    deadline = time.time() + timeout
    klass_l = klass.lower()
    inst_l = (instance or "").lower()
    seen: set[int] = {w.xid for w in list_normal_windows()}
    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        for wi in list_normal_windows():
            if wi.xid in seen:
                continue
            if wi.klass.lower() == klass_l or (inst_l and wi.instance.lower() == inst_l):
                time.sleep(SETTLE_SECONDS)
                return wi
    # last chance: any matching class
    cands = [w for w in list_normal_windows() if w.klass.lower() == klass_l]
    return cands[-1] if cands else None


def notify(msg: str, urgent: bool = False) -> None:
    try:
        subprocess.run(
            [
                "dunstify",
                "-u",
                "critical" if urgent else "low",
                "-h",
                "string:x-dunst-stack-tag:oblayout",
                "Layout",
                msg,
            ],
            check=False,
        )
    except FileNotFoundError:
        print(msg, file=sys.stderr)
