"""Frame rectangle ⇄ workarea-relative fractions. Pure — no X connection."""

from __future__ import annotations

from ob_windows.rect import Rect

MIN_SIZE_PX = 50


def to_fractions(rect: Rect, work: Rect) -> dict[str, float]:
    if work.w <= 0 or work.h <= 0:
        raise RuntimeError("invalid workarea")
    return {
        "x": round((rect.x - work.x) / work.w, 6),
        "y": round((rect.y - work.y) / work.h, 6),
        "w": round(rect.w / work.w, 6),
        "h": round(rect.h / work.h, 6),
    }


def from_fractions(fx: float, fy: float, fw: float, fh: float, work: Rect) -> Rect:
    x = int(round(work.x + fx * work.w))
    y = int(round(work.y + fy * work.h))
    w = max(MIN_SIZE_PX, int(round(fw * work.w)))
    h = max(MIN_SIZE_PX, int(round(fh * work.h)))
    # Clamp into workarea
    if x < work.x:
        x = work.x
    if y < work.y:
        y = work.y
    if x + w > work.x2:
        w = max(MIN_SIZE_PX, work.x2 - x)
    if y + h > work.y2:
        h = max(MIN_SIZE_PX, work.y2 - y)
    return Rect(x, y, w, h)
