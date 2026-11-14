from __future__ import annotations

from ob_grid.config import Config
from ob_grid.geometry import (
    Rect,
    grow_edge,
    leading_edge_lines,
    move_keep_size,
    move_window,
    shrink_toward,
    span,
    trailing_edge_lines,
)

CFG = Config(
    horizontal=(0.25, 1 / 3, 0.5, 2 / 3, 0.75, 1.0),
    vertical=(1 / 3, 0.5, 2 / 3, 0.75, 1.0),
    inner_gap=10,
    tolerance_px=12,
)

WORK = Rect(10, 40, 1900, 1030)


def test_user_half_formula_matches_span():
    g = CFG.inner_gap
    assert span(0.5, WORK.w, g) == round(WORK.w * 0.5 - g / 2)


def test_two_halves_leave_inner_gap():
    half = span(0.5, WORK.w, CFG.inner_gap)
    left = Rect(WORK.x, WORK.y, half, 400)
    right = Rect(WORK.x + half + CFG.inner_gap, WORK.y, half, 400)
    assert left.x2 + CFG.inner_gap == right.x
    assert right.x2 == WORK.x + WORK.w


def test_grow_right_stops_at_half_not_past_gap():
    half = span(0.5, WORK.w, CFG.inner_gap)
    at_half = Rect(WORK.x, WORK.y, half, 400)
    nxt = grow_edge(at_half, WORK, CFG, "right")
    assert nxt.x2 == WORK.x + span(2 / 3, WORK.w, CFG.inner_gap)
    assert nxt.x2 != WORK.x + half + CFG.inner_gap


def test_grow_left_one_step_to_right_half_start():
    half = span(0.5, WORK.w, CFG.inner_gap)
    start = WORK.x + half + CFG.inner_gap
    narrow = Rect(start + 100, WORK.y, half - 100, 400)
    grown = grow_edge(narrow, WORK, CFG, "left")
    assert grown.x == start
    assert grown.w == half


def test_shrink_left_uses_trailing_lines():
    rect = Rect(WORK.x, WORK.y, WORK.w, 400)
    shrunk = shrink_toward(rect, WORK, CFG, "left")
    assert shrunk.x == WORK.x
    assert shrunk.x2 in trailing_edge_lines(WORK.x, WORK.w, CFG.inner_gap, CFG.horizontal)


def test_move_right_half_steps_to_quarter_lead_first():
    """2x2 half-width tile: Super+Right must hit ~1/4 lead, not skip to 1/2."""
    half = span(0.5, WORK.w, CFG.inner_gap)
    left = Rect(WORK.x, WORK.y, half, 400)
    moved = move_keep_size(left, WORK, CFG, "right")
    quarter_lead = WORK.x + span(0.25, WORK.w, CFG.inner_gap) + CFG.inner_gap
    right_half = WORK.x + half + CFG.inner_gap
    assert moved.w == half
    assert moved.x == quarter_lead
    assert moved.x != right_half


def test_move_left_narrow_right_does_not_jump_to_far_left():
    """Width ≠ grid fraction: Super+Left must step onto a leading line, not work.x."""
    half = span(0.5, WORK.w, CFG.inner_gap)
    w = half - 200
    flush = WORK.x + WORK.w - w
    narrow = Rect(flush, WORK.y, w, 400)
    moved = move_keep_size(narrow, WORK, CFG, "left")
    center = WORK.x + half + CFG.inner_gap
    assert moved.w == w
    assert moved.x != WORK.x
    assert moved.x < flush
    # First step stays on the right half (at or right of the center lead).
    assert moved.x >= center


def test_move_right_maximized_shrinks_to_three_quarter():
    """Full-width window: Super+Right ⇒ ~25% lead, width fills to workarea right."""
    full = Rect(WORK.x, WORK.y, WORK.w, WORK.h)
    # keep-size alone cannot move a full-width tile
    assert move_keep_size(full, WORK, CFG, "right") == full

    moved = move_window(full, WORK, CFG, "right")
    quarter_lead = WORK.x + span(0.25, WORK.w, CFG.inner_gap) + CFG.inner_gap
    assert moved.x == quarter_lead
    assert moved.y == WORK.y
    assert moved.h == WORK.h
    assert moved.x2 == WORK.x + WORK.w
    # Complementary width ≈ 75% tile (gap already consumed by the lead offset).
    assert abs(moved.w - span(0.75, WORK.w, CFG.inner_gap)) <= 1


def test_move_right_fitted_steps_again_shrinking():
    """From 25%/75% flush-right, next Super+Right steps lead and shrinks again."""
    quarter_lead = WORK.x + span(0.25, WORK.w, CFG.inner_gap) + CFG.inner_gap
    fitted = Rect(quarter_lead, WORK.y, WORK.x + WORK.w - quarter_lead, WORK.h)
    moved = move_window(fitted, WORK, CFG, "right")
    leads = leading_edge_lines(WORK.x, WORK.w, CFG.inner_gap, CFG.horizontal)
    assert moved.x in leads
    assert moved.x > quarter_lead
    assert moved.x2 == WORK.x + WORK.w
    assert moved.w < fitted.w


def test_move_down_maximized_shrinks_to_fit():
    full = Rect(WORK.x, WORK.y, WORK.w, WORK.h)
    moved = move_window(full, WORK, CFG, "down")
    third_lead = WORK.y + span(1 / 3, WORK.h, CFG.inner_gap) + CFG.inner_gap
    assert moved.y == third_lead
    assert moved.y2 == WORK.y + WORK.h
    assert moved.w == WORK.w
