from __future__ import annotations

from ob_windows.grid.config import Config
from ob_windows.grid.geometry import (
    Rect,
    at_work_bottom,
    at_work_top,
    move_window,
    snap_size,
    span,
)

CFG = Config(
    horizontal=(0.25, 1 / 3, 0.5, 2 / 3, 0.75, 1.0),
    vertical=(1 / 3, 0.5, 2 / 3, 0.75, 1.0),
    inner_gap=10,
    tolerance_px=12,
)
WORK = Rect(10, 40, 1900, 1030)


def test_edge_predicates_use_tolerance():
    top = Rect(WORK.x, WORK.y + 12, 400, 300)
    assert at_work_top(top, WORK, 12)
    assert not at_work_top(Rect(WORK.x, WORK.y + 13, 400, 300), WORK, 12)

    bottom = Rect(WORK.x, WORK.y2 - 300, 400, 300)
    assert at_work_bottom(bottom, WORK, 12)
    assert not at_work_bottom(Rect(WORK.x, WORK.y2 - 320, 400, 300), WORK, 12)


def test_move_up_at_top_is_noop_so_cli_can_maximize():
    """cmd_move maximizes only when move_window reports no change at the top."""
    rect = Rect(WORK.x, WORK.y, 600, 400)
    assert move_window(rect, WORK, CFG, "up") == rect
    assert at_work_top(rect, WORK, CFG.tolerance_px)


def test_move_down_at_bottom_shrinks_until_last_lead_then_cli_minimizes():
    """Flush-bottom window: Super+Down keeps lowering the top edge one lead at a
    time; only on the last lead is move_window a no-op, and cmd_move minimizes."""
    h = span(1 / 3, WORK.h, CFG.inner_gap)
    rect = Rect(WORK.x, WORK.y2 - h, 600, h)
    seen = [rect]
    while (nxt := move_window(seen[-1], WORK, CFG, "down")) != seen[-1]:
        assert nxt.y > seen[-1].y and nxt.y2 == WORK.y2 and nxt.h < seen[-1].h
        seen.append(nxt)
    assert len(seen) > 1
    last_lead = WORK.y + span(0.75, WORK.h, CFG.inner_gap) + CFG.inner_gap
    assert seen[-1].y == last_lead
    assert at_work_bottom(seen[-1], WORK, CFG.tolerance_px)


def test_snap_size_steps_width_keeping_top_left():
    half = span(0.5, WORK.w, CFG.inner_gap)
    rect = Rect(WORK.x, WORK.y, half, 400)
    larger = snap_size(rect, WORK, CFG, "width", True)
    smaller = snap_size(rect, WORK, CFG, "width", False)
    assert (larger.x, larger.y) == (rect.x, rect.y) == (smaller.x, smaller.y)
    assert larger.w == span(2 / 3, WORK.w, CFG.inner_gap)
    assert smaller.w == span(1 / 3, WORK.w, CFG.inner_gap)


def test_snap_size_stops_at_full_height():
    rect = Rect(WORK.x, WORK.y, 400, WORK.h)
    assert snap_size(rect, WORK, CFG, "height", True) == rect
