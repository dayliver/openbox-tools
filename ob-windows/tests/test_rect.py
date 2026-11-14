from __future__ import annotations

from ob_windows.rect import Rect


def test_edges_and_center():
    r = Rect(10, 40, 1900, 1030)
    assert (r.x2, r.y2) == (1910, 1070)
    assert r.center == (960, 555)


def test_contains_is_half_open():
    r = Rect(0, 0, 1920, 1080)
    assert r.contains(0, 0) and r.contains(1919, 1079)
    assert not r.contains(1920, 0) and not r.contains(0, 1080) and not r.contains(-1, 5)


def test_intersect_workarea_with_monitor():
    """Desktop workarea spans both monitors; each monitor keeps its own slice."""
    work = Rect(10, 44, 3820, 1026)
    left, right = Rect(0, 0, 1920, 1080), Rect(1920, 0, 1920, 1080)
    assert work.intersect(left) == Rect(10, 44, 1910, 1026)
    assert work.intersect(right) == Rect(1920, 44, 1910, 1026)


def test_intersect_disjoint_is_none():
    assert Rect(0, 0, 100, 100).intersect(Rect(100, 0, 50, 50)) is None
    assert Rect(0, 0, 100, 100).intersect(Rect(500, 500, 50, 50)) is None
