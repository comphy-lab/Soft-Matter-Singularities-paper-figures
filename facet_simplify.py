#!/usr/bin/env python3
"""Chain Basilisk getFacet 2-point segments into continuous polylines (and
optionally simplify them), so the interface stays vector without bloating the PDF.

getFacet emits the interface as thousands of disconnected 2-point segments, one
per cell crossing. Drawn as a matplotlib LineCollection of 2-point segments, each
becomes its own stroked subpath in the PDF — at lvl16 near pinch-off that is
hundreds of thousands of paths and tens of MB. Chaining the segments end-to-end
into a handful of polylines collapses that to a few paths carrying the SAME
vertices (geometry unchanged). An optional Douglas-Peucker pass at a sub-pixel
tolerance then drops near-collinear vertices for a further, visually-lossless
reduction.

Returns polylines as a list of (M, 2) arrays, ready to hand to a single
``LineCollection`` (one path per polyline instead of one per segment).
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np


def parse_getfacet(text: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Parse getFacet output (pairs of "x y" lines, blank-separated) into a list
    of 2-point segments."""
    segments = []
    seg: list[tuple[float, float]] = []
    for line in text.splitlines():
        s = line.split()
        if len(s) != 2:
            seg = []
            continue
        try:
            p = (float(s[0]), float(s[1]))
        except ValueError:
            seg = []
            continue
        seg.append(p)
        if len(seg) == 2:
            segments.append((seg[0], seg[1]))
            seg = []
    return segments


def chain_segments(segments, quant: float = 1e-9) -> list[np.ndarray]:
    """Chain unordered 2-point segments into ordered polylines.

    Endpoints are matched after rounding to ``quant``; getFacet shares exact
    vertex coordinates between adjacent segments, so the match is effectively
    exact. Returns a list of (M, 2) float arrays, each a connected polyline.
    Geometry is preserved exactly — only the segment ordering/grouping changes.
    """
    segs = [(tuple(map(float, a)), tuple(map(float, b))) for a, b in segments]
    if not segs:
        return []
    inv = 1.0 / quant

    def key(p):
        return (round(p[0] * inv), round(p[1] * inv))

    adj = defaultdict(list)  # key -> list of (seg_index, end) with end in {0, 1}
    coord = {}
    for i, (a, b) in enumerate(segs):
        ka, kb = key(a), key(b)
        coord[ka], coord[kb] = a, b
        adj[ka].append((i, 0))
        adj[kb].append((i, 1))

    used = [False] * len(segs)

    def other_key(i, end):
        a, b = segs[i]
        return key(b) if end == 0 else key(a)

    def walk(start):
        line = [coord[start]]
        cur = start
        while True:
            step = next(((i, e) for (i, e) in adj[cur] if not used[i]), None)
            if step is None:
                break
            i, e = step
            used[i] = True
            nk = other_key(i, e)
            line.append(coord[nk])
            cur = nk
        return line

    polylines = []
    # Open chains first: start at degree-1 nodes so a curve is never bisected.
    for k, lst in adj.items():
        if len(lst) == 1 and not used[lst[0][0]]:
            polylines.append(walk(k))
    # Remaining segments belong to closed loops.
    for i, (a, _) in enumerate(segs):
        if not used[i]:
            polylines.append(walk(key(a)))

    return [np.asarray(pl, dtype=float) for pl in polylines if len(pl) >= 2]


def rdp(points: np.ndarray, eps: float) -> np.ndarray:
    """Iterative Douglas-Peucker simplification (perpendicular distance, no
    recursion-depth limit)."""
    n = len(points)
    if n < 3 or eps <= 0:
        return points
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        s, e = stack.pop()
        if e <= s + 1:
            continue
        a = points[s]
        b = points[e]
        ab = b - a
        seg = points[s + 1:e] - a
        length = float(np.hypot(ab[0], ab[1]))
        if length == 0.0:
            d = np.hypot(seg[:, 0], seg[:, 1])
        else:
            d = np.abs(ab[0] * seg[:, 1] - ab[1] * seg[:, 0]) / length
        if d.size == 0:
            continue
        idx = int(np.argmax(d))
        if d[idx] > eps:
            k = s + 1 + idx
            keep[k] = True
            stack.append((s, k))
            stack.append((k, e))
    return points[keep]


def chain_and_simplify(segments, eps: float = 0.0, quant: float = 1e-9) -> list[np.ndarray]:
    """Chain segments into polylines, then optionally RDP-simplify each.

    `segments`: iterable of ((x1, y1), (x2, y2)).
    `eps`: Douglas-Peucker tolerance in data units (0 = chaining only, lossless).
    """
    lines = chain_segments(segments, quant=quant)
    if eps and eps > 0:
        lines = [rdp(pl, eps) for pl in lines]
    return lines
