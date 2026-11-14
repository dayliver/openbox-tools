from __future__ import annotations

import pytest

from ob_windows.layout.ratio import MIN_SIZE_PX, from_fractions, to_fractions
from ob_windows.rect import Rect

WORK = Rect(10, 44, 1900, 1026)


def test_round_trip_is_stable():
    rect = Rect(965, 44, 945, 1026)
    f = to_fractions(rect, WORK)
    assert from_fractions(f["x"], f["y"], f["w"], f["h"], WORK) == rect


def test_same_fractions_follow_a_different_workarea():
    """The point of ratios: a changed margin / resolution still lays out sensibly."""
    f = to_fractions(Rect(10, 44, 950, 1026), WORK)
    other = Rect(0, 0, 2560, 1400)
    assert from_fractions(f["x"], f["y"], f["w"], f["h"], other) == Rect(0, 0, 1280, 1400)


def test_from_fractions_clamps_into_workarea():
    r = from_fractions(-0.2, -0.2, 2.0, 2.0, WORK)
    assert r == WORK
    r = from_fractions(0.9, 0.9, 0.5, 0.5, WORK)
    assert r.x2 == WORK.x2 and r.y2 == WORK.y2


def test_from_fractions_enforces_minimum_size():
    r = from_fractions(0.0, 0.0, 0.0, 0.0, WORK)
    assert r.w == MIN_SIZE_PX and r.h == MIN_SIZE_PX


def test_to_fractions_rejects_empty_workarea():
    with pytest.raises(RuntimeError):
        to_fractions(Rect(0, 0, 10, 10), Rect(0, 0, 0, 100))
