#!/usr/bin/env python3
"""Re-render every Figure-4 snapshot panel from the archived raw Basilisk dumps.

Each strip's ``scales.txt`` fixes the framing (xmin/xmax/rmax) and velocity scale,
and its ``manifest.csv`` lists the frames + output paths. This loops those and
calls the (decimated) ``render_panel.render`` so each panel is a tight
field-raster + vector-interface PDF that ``make_fig4_drop_bubble.py`` then
vector-stamps. See ``../RAW_DATA_MANIFEST.md`` for where the raw dumps live.

Binaries (built once with qcc + Basilisk, see render_panel.py docstring):
    GETDATA / GETFACET env vars, else /tmp/figbuild/{getData-elastic,getFacet}.

Raw-data roots (override with EPO_HAMILTON_ROOT / EPO_SNELLIUS_ROOT):
    Hamilton Newtonian archive (c1024-in) and Snellius archive (c103x cases).
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_panel as RP

GETDATA = Path(os.environ.get("GETDATA", "/tmp/figbuild/getData-elastic"))
GETFACET = Path(os.environ.get("GETFACET", "/tmp/figbuild/getFacet"))
NY = int(os.environ.get("FIG4_NY", "1400"))

HAMILTON_ROOT = Path(os.environ.get(
    "EPO_HAMILTON_ROOT",
    "/Volumes/macOfficeV0/ElasticPinchOff/Hamilton-Newtonian-2026-06-27/simulationCases",
))
SNELLIUS_ROOT = Path(os.environ.get(
    "EPO_SNELLIUS_ROOT",
    "/Volumes/macOfficeV0/ElasticPinchOff/Snellius-2026-06-27-Elastic-Pinch-Off/simulationCases",
))

# Strip dir -> nothing extra; per-frame source case is read from the manifest.
# Override the set to re-render on the command line: `render_all_panels.py c1032-in ...`.
ALL_STRIPS = ["c1024-in", "c1030-out", "c1031-c1033-out", "c1032-in"]
STRIPS = sys.argv[1:] or ALL_STRIPS


def resolve_snapshot(raw: str) -> Path:
    """Map a manifest 'snapshot' path (an absolute archive path, or a stale
    /tmp/fig4_snaps/<case>/<snap>) to the local archived dump."""
    p = Path(raw)
    if p.exists():
        return p
    snapname = p.name
    srccase = next((t for t in p.parts if t.startswith("c10")), None)
    if srccase is None:
        raise FileNotFoundError(raw)
    root = HAMILTON_ROOT if srccase == "c1024-in" else SNELLIUS_ROOT
    cand = root / srccase / "intermediate" / snapname
    if not cand.exists():
        raise FileNotFoundError(f"{raw} -> {cand}")
    return cand


def read_scales(strip: str) -> tuple[float, float, float, float]:
    d = {}
    for line in (HERE / strip / "scales.txt").read_text().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            d[k.strip()] = v.strip()
    return float(d["xmin"]), float(d["xmax"]), float(d["rmax"]), float(d["vel_vmax"])


def main() -> None:
    for binary in (GETDATA, GETFACET):
        if not binary.exists():
            sys.exit(f"missing helper binary: {binary} (build with qcc; see render_panel.py)")
    for strip in STRIPS:
        xmin, xmax, rmax, vmax = read_scales(strip)
        with (HERE / strip / "manifest.csv").open() as f:
            rows = list(csv.DictReader(f))
        print(f"== {strip}: {len(rows)} frames, rmax={rmax}, vmax={vmax} ==")
        for row in rows:
            snap = resolve_snapshot(row["snapshot"])
            out_base = Path(row["pdf"]).with_suffix("")
            RP.render(
                snapshot=snap, out_base=out_base, xmin=xmin, xmax=xmax, rmax=rmax,
                getdata_bin=GETDATA, getfacet_bin=GETFACET, ny=NY, vmin=0.0, vmax=vmax,
            )
            print(f"  {row['label']:>10} <- {snap.name}")
    print("done")


if __name__ == "__main__":
    main()
