from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Wnck", "3.0")

from gi.repository import Gdk, Gtk, Wnck  # noqa: E402

from ob_grid.geometry import Rect  # noqa: E402


@dataclass(frozen=True)
class FrameExtents:
    left: int
    right: int
    top: int
    bottom: int


@dataclass
class ActiveWindow:
    wnck: Wnck.Window
    xid: int
    rect: Rect  # outer frame geometry (Wnck.get_geometry)
    work: Rect
    extents: FrameExtents


def _ensure_gtk() -> None:
    if not Gtk.init_check(sys.argv)[0]:
        raise RuntimeError("Gtk.init failed — is DISPLAY set?")


def _pump(seconds: float = 0.15) -> None:
    end = time.time() + seconds
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.01)


def workarea_for_point(px: int, py: int) -> Rect:
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("No Gdk display")
    monitor = display.get_monitor_at_point(px, py)
    if monitor is None:
        monitor = display.get_primary_monitor()
    geo = monitor.get_workarea()
    return Rect(geo.x, geo.y, geo.width, geo.height)


def _frame_extents(xid: int) -> FrameExtents:
    try:
        out = subprocess.check_output(
            ["xprop", "-id", str(xid), "_NET_FRAME_EXTENTS"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return FrameExtents(0, 0, 0, 0)
    m = re.search(r"=\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)", out)
    if not m:
        return FrameExtents(0, 0, 0, 0)
    return FrameExtents(*(int(g) for g in m.groups()))


def get_active() -> ActiveWindow:
    _ensure_gtk()
    screen = Wnck.Screen.get_default()
    screen.force_update()
    _pump(0.05)
    win = screen.get_active_window()
    if win is None or win.get_window_type() != Wnck.WindowType.NORMAL:
        for candidate in screen.get_windows_stacked()[::-1]:
            if candidate.get_window_type() == Wnck.WindowType.NORMAL and not candidate.is_minimized():
                win = candidate
                break
    if win is None:
        raise RuntimeError("No active normal window")

    x, y, w, h = win.get_geometry()
    rect = Rect(int(x), int(y), int(w), int(h))
    xid = int(win.get_xid())
    extents = _frame_extents(xid)
    work = workarea_for_point(rect.x + rect.w // 2, rect.y + rect.h // 2)
    return ActiveWindow(wnck=win, xid=xid, rect=rect, work=work, extents=extents)


def _clear_wm_state(win: Wnck.Window) -> None:
    changed = False
    if hasattr(win, "is_fullscreen") and win.is_fullscreen():
        win.set_fullscreen(False)
        changed = True
    if win.is_maximized():
        win.unmaximize()
        changed = True
    if win.is_maximized_horizontally():
        win.unmaximize_horizontally()
        changed = True
    if win.is_maximized_vertically():
        win.unmaximize_vertically()
        changed = True
    if changed:
        _pump(0.12)


def apply_rect(active: ActiveWindow, frame: Rect) -> None:
    """Apply desired frame geometry.

    Openbox + libwnck: NORTHWEST gravity treats x/y like client coords and drifts by
    _NET_FRAME_EXTENTS on every call. STATIC gravity accepts frame geometry directly.
    """
    _clear_wm_state(active.wnck)

    mask = (
        Wnck.WindowMoveResizeMask.X
        | Wnck.WindowMoveResizeMask.Y
        | Wnck.WindowMoveResizeMask.WIDTH
        | Wnck.WindowMoveResizeMask.HEIGHT
    )
    active.wnck.set_geometry(
        Wnck.WindowGravity.STATIC,
        mask,
        int(frame.x),
        int(frame.y),
        int(frame.w),
        int(frame.h),
    )
    _pump(0.18)


def maximize_window(active: ActiveWindow) -> None:
    active.wnck.maximize()
    _pump(0.12)


def minimize_window(active: ActiveWindow) -> None:
    active.wnck.minimize()
    _pump(0.12)


def at_work_top(rect: Rect, work: Rect, tol: int) -> bool:
    return abs(rect.y - work.y) <= tol


def at_work_bottom(rect: Rect, work: Rect, tol: int) -> bool:
    return abs(rect.y2 - (work.y + work.h)) <= tol
