"""Window-manager plumbing shared by ob-grid and ob-layout (libwnck + Gdk).

Everything that talks to the X server lives here, so the rest of the package
stays pure and testable, and so this is the only module to replace if the
Gtk/Wnck dependency is ever swapped out.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Wnck", "3.0")

from gi.repository import Gdk, Gtk, Wnck  # noqa: E402

from ob_windows.rect import Rect  # noqa: E402


@dataclass
class ActiveWindow:
    wnck: Wnck.Window
    rect: Rect  # outer frame geometry (Wnck.get_geometry)
    work: Rect  # workarea of the monitor the window is on


def ensure_gtk() -> None:
    if not Gtk.init_check(sys.argv)[0]:
        raise RuntimeError("Gtk.init failed — is DISPLAY set?")


def pump(seconds: float = 0.12) -> None:
    """Let Gtk process X events for a moment (Wnck only updates from the loop)."""
    end = time.time() + seconds
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.01)


def screen() -> Wnck.Screen:
    ensure_gtk()
    s = Wnck.Screen.get_default()
    s.force_update()
    pump(0.05)
    return s


def is_normal(win: Wnck.Window) -> bool:
    return win.get_window_type() == Wnck.WindowType.NORMAL


def frame_rect(win: Wnck.Window) -> Rect:
    x, y, w, h = win.get_geometry()
    return Rect(int(x), int(y), int(w), int(h))


def _monitor_workarea(monitor: Gdk.Monitor) -> Rect:
    geo = monitor.get_workarea()
    return Rect(geo.x, geo.y, geo.width, geo.height)


def workarea_for_point(px: int, py: int) -> Rect:
    """Workarea (Openbox margins already removed) of the monitor under a point."""
    ensure_gtk()
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("No Gdk display")
    monitor = display.get_monitor_at_point(px, py)
    if monitor is None:
        monitor = display.get_primary_monitor()
    return _monitor_workarea(monitor)


def workarea_for_rect(rect: Rect) -> Rect:
    return workarea_for_point(*rect.center)


def primary_workarea() -> Rect:
    ensure_gtk()
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("No Gdk display")
    monitor = display.get_primary_monitor() or display.get_monitor(0)
    return _monitor_workarea(monitor)


def active_window() -> ActiveWindow:
    """The focused normal window, else the topmost visible normal one."""
    s = screen()
    win = s.get_active_window()
    if win is None or not is_normal(win):
        for candidate in s.get_windows_stacked()[::-1]:
            if is_normal(candidate) and not candidate.is_minimized():
                win = candidate
                break
    if win is None:
        raise RuntimeError("No active normal window")
    rect = frame_rect(win)
    return ActiveWindow(wnck=win, rect=rect, work=workarea_for_rect(rect))


def clear_wm_state(win: Wnck.Window) -> None:
    """Drop fullscreen / maximized so an explicit geometry is honoured."""
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
        pump(0.12)


def apply_frame(win: Wnck.Window, frame: Rect) -> None:
    """Apply desired frame geometry.

    Openbox + libwnck: NORTHWEST gravity treats x/y like client coords and drifts by
    _NET_FRAME_EXTENTS on every call. STATIC gravity accepts frame geometry directly.
    """
    clear_wm_state(win)
    mask = (
        Wnck.WindowMoveResizeMask.X
        | Wnck.WindowMoveResizeMask.Y
        | Wnck.WindowMoveResizeMask.WIDTH
        | Wnck.WindowMoveResizeMask.HEIGHT
    )
    win.set_geometry(
        Wnck.WindowGravity.STATIC,
        mask,
        int(frame.x),
        int(frame.y),
        int(frame.w),
        int(frame.h),
    )
    pump(0.18)


def maximize(win: Wnck.Window) -> None:
    win.maximize()
    pump(0.12)


def minimize(win: Wnck.Window) -> None:
    win.minimize()
    pump(0.12)
