#!/usr/bin/env python3
"""
render_panel.py

Render a single mirror cross-section panel from one Basilisk snapshot for
Figure 4 of the "Soft Matter Singularities" review.

VELOCITY-ONLY MODE (current Fig-4 spec, a deliberate departure from Fig-3):

  - velocity magnitude |u| on BOTH halves of the mirror (no left/right split),
    cmap Blues, limits [0, vmax] with vmax = 5 by default
  - black interface contour (white halo underneath) on both halves
  - thin dashed grey vertical centreline
  - no axes, no ticks, no title (titles added later by the composite script)
  - framed to the FULL computational domain axially (xmin=0, xmax=L0=4*pi);
    rmax is set per case from the interface so the whole column + neck fit.

The earlier dissipation (hot_r) half has been removed; Oh is no longer needed
for the image. The helper getData-elastic still also computes a dissipation
column, but only the velocity column is used here.

Field extraction reuses the Basilisk post-processing helpers
`getData-elastic` (columns: x y D2c vel trA) and `getFacet` (interface facets).

IMPORTANT runtime note: the C helpers `sprintf` the snapshot path into a fixed
`char filename[80]` buffer, so any path longer than ~79 chars overflows the
stack and the binary traps (SIGTRAP). This renderer therefore copies each
snapshot to a SHORT temp path before invoking the helpers.

Coordinate mapping (axisymmetric): plotted horizontal r = Basilisk y,
plotted vertical z = Basilisk x. Mirror about r = 0.

CLI example
-----------
  python3 render_panel.py \
      --snapshot /path/to/snapshot-14.2100 \
      --out /path/to/out/fig4_c1024_06_t014p2100 \
      --xmin 0 --xmax 12.566370614359172 --rmax 2.165 \
      --vmax 5 \
      --getdata /tmp/fig4_build/getData-elastic \
      --getfacet /tmp/fig4_build/getFacet \
      --ny 1400

`--out` is given WITHOUT extension; both .png and .pdf are written.

The getData-elastic / getFacet helpers are built from the Basilisk sources in
`<case>/postProcess/` (or the elastic src-local) with, e.g.:

  export BASILISK=/Users/comphy-mac/CMP-codes/basilisk/src
  export PATH=$BASILISK:$PATH
  qcc -O2 -Wall -disable-dimensions -I<src-local> getData-elastic.c -o getData-elastic -lm
  qcc -O2 -Wall -disable-dimensions getFacet.c -o getFacet -lm

Use /usr/bin/python3 on this Mac (it has numpy + matplotlib).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from facet_simplify import chain_and_simplify

# Douglas-Peucker tolerance for the interface polyline, in simulation length
# units. ~0.5 of the lvl16 cell size (L0/2^16 = 1.9e-4), so the decimation is
# below the data's own resolution: visually lossless, but it collapses the
# ~10^5 per-cell PLIC facet segments into a few vector polylines.
FACET_EPS = 1.0e-4

# Column index in getData-elastic output: x y D2c vel trA
FIELD_INDEX = {"D2": 2, "vel": 3, "trA": 4}

# Velocity style (Fig-4 spec)
VEL_CMAP = "Blues"
VEL_VMIN = 0.0
DEFAULT_VEL_VMAX = 5.0


def run_capture_stderr(cmd: list[str]) -> str:
    """Run a helper binary; its table output goes to stderr (Basilisk `ferr`)."""
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
    )
    # Helpers write to stderr; include stdout for safety.
    return (result.stderr or "") + (result.stdout or "")


def get_facets(short_snap: Path, getfacet_bin: Path) -> np.ndarray:
    raw = run_capture_stderr([str(getfacet_bin), str(short_snap)])
    pts: list[list[float]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        vals = line.split()
        if len(vals) < 2:
            continue
        try:
            pts.append([float(vals[0]), float(vals[1])])
        except ValueError:
            continue
    if len(pts) < 2:
        return np.empty((0, 2, 2), dtype=float)
    usable = len(pts) - (len(pts) % 2)
    return np.asarray(pts[:usable], dtype=float).reshape(-1, 2, 2)


def get_field_grid(
    short_snap: Path,
    getdata_bin: Path,
    field_key: str,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    ny: int,
) -> tuple[np.ndarray, np.ndarray, np.ma.MaskedArray]:
    """Sample one field on a uniform grid over [xmin,xmax] x [ymin,ymax]."""
    raw = run_capture_stderr(
        [
            str(getdata_bin),
            str(short_snap),
            f"{xmin:.16g}",
            f"{ymin:.16g}",
            f"{xmax:.16g}",
            f"{ymax:.16g}",
            str(ny),
            "0",
            "0",
            "0",
        ]
    )
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        vals = line.split()
        if len(vals) < 5:
            continue
        try:
            rows.append([float(v) for v in vals[:5]])
        except ValueError:
            continue
    if not rows:
        raise RuntimeError(f"No field data parsed for snapshot: {short_snap}")
    arr = np.asarray(rows, dtype=float)
    x = arr[:, 0]
    y = arr[:, 1]
    field = arr[:, FIELD_INDEX[field_key]]

    x_unique = np.unique(x)
    y_unique = np.unique(y)
    ix = np.searchsorted(x_unique, x)
    iy = np.searchsorted(y_unique, y)
    grid = np.full((len(y_unique), len(x_unique)), np.nan, dtype=float)
    grid[iy, ix] = field
    invalid = (~np.isfinite(grid)) | (np.abs(grid) > 1e20)
    return x_unique, y_unique, np.ma.array(grid, mask=invalid)


def grid_extent(x: np.ndarray, y: np.ndarray) -> list[float]:
    dx = float(np.median(np.diff(x))) if len(x) > 1 else 1.0
    dy = float(np.median(np.diff(y))) if len(y) > 1 else 1.0
    return [x[0] - 0.5 * dx, x[-1] + 0.5 * dx, y[0] - 0.5 * dy, y[-1] + 0.5 * dy]


def mirror_field_xy_to_rz(
    field_xy: np.ma.MaskedArray, r_pos: np.ndarray
) -> tuple[np.ndarray, np.ma.MaskedArray]:
    """Build full (-r,+r) field in (r,z) from positive-r data. field_xy is (nr,nz)."""
    field_pos = np.ma.array(field_xy.T, copy=False)  # (nz, nr_pos)
    r_positive = np.asarray(r_pos, dtype=float)
    r_negative = -r_positive[::-1]
    field_negative = field_pos[:, ::-1]
    r_full = np.concatenate([r_negative, r_positive])
    field_full = np.ma.concatenate([field_negative, field_pos], axis=1)
    return r_full, field_full


def map_segments_xy_to_rz(seg: np.ndarray) -> np.ndarray:
    if len(seg) == 0:
        return seg
    return seg[..., [1, 0]].copy()


def mirror_segments_about_r0(seg_rz: np.ndarray) -> np.ndarray:
    if len(seg_rz) == 0:
        return seg_rz
    mirrored = seg_rz.copy()
    mirrored[..., 0] *= -1.0
    return np.concatenate([mirrored, seg_rz], axis=0)


def render(
    snapshot: Path,
    out_base: Path,
    xmin: float,
    xmax: float,
    rmax: float,
    getdata_bin: Path,
    getfacet_bin: Path,
    ny: int,
    vmin: float = VEL_VMIN,
    vmax: float = DEFAULT_VEL_VMAX,
    panel_height_in: float = 6.0,
) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fig4_snap_", dir="/tmp") as td:
        tmpdir = Path(td)
        short_snap = tmpdir / "s"
        shutil.copy2(snapshot, short_snap)

        # Sample velocity magnitude on the physical half-domain y in [0, rmax].
        x_v, y_v, vel_field = get_field_grid(
            short_snap, getdata_bin, "vel", xmin, 0.0, xmax, rmax, ny
        )
        facets = get_facets(short_snap, getfacet_bin)

    # Mirror velocity about r = 0 and show it on BOTH halves (no side masking).
    r_full, vel_rz = mirror_field_xy_to_rz(vel_field, y_v)
    extent = grid_extent(r_full, x_v)  # [rmin, rmax, zmin, zmax]

    # Figure: aspect equal, height fixed, width from r/z span.
    z_span = xmax - xmin
    r_span = 2.0 * rmax
    fig_w = panel_height_in * (r_span / z_span)
    fig, ax = plt.subplots(figsize=(fig_w, panel_height_in), dpi=300)

    ax.imshow(
        vel_rz,
        origin="lower",
        extent=extent,
        cmap=VEL_CMAP,
        vmin=vmin,
        vmax=vmax,
        aspect="equal",
        interpolation="nearest",
        zorder=2,
    )

    # Chain the per-cell PLIC facet segments into connected polylines and
    # RDP-simplify (sub-cell tolerance) before drawing: same curve, ~10^2x fewer
    # vector paths. Map xy->rz (r = Basilisk y, z = Basilisk x) and mirror.
    interface_rz = []
    for pl in chain_and_simplify(facets, eps=FACET_EPS):
        rz = pl[:, [1, 0]]
        interface_rz.append(rz)
        interface_rz.append(rz * np.array([-1.0, 1.0]))
    if interface_rz:
        ax.add_collection(
            LineCollection(interface_rz, colors="white", linewidths=2.8, zorder=3)
        )
        ax.add_collection(
            LineCollection(interface_rz, colors="black", linewidths=1.4, zorder=4)
        )

    ax.axvline(0.0, color="0.5", linewidth=0.9, linestyle=(0, (4, 4)), zorder=5)

    ax.set_xlim(-rmax, rmax)
    ax.set_ylim(xmin, xmax)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Use string concatenation, not with_suffix: out_base may contain dots
    # (e.g. a time stamp like "..._t40.3860") which with_suffix would mangle.
    png = Path(str(out_base) + ".png")
    pdf = Path(str(out_base) + ".pdf")
    fig.savefig(png, bbox_inches="tight", pad_inches=0)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"wrote {png}\nwrote {pdf}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument(
        "--out", type=Path, required=True, help="Output base path WITHOUT extension."
    )
    p.add_argument("--xmin", type=float, required=True, help="Basilisk x (=z) min")
    p.add_argument("--xmax", type=float, required=True, help="Basilisk x (=z) max")
    p.add_argument(
        "--rmax", type=float, required=True, help="Max |r| (Basilisk y) sampled/shown"
    )
    p.add_argument(
        "--vmin",
        type=float,
        default=VEL_VMIN,
        help=f"velocity colour-scale minimum (default: {VEL_VMIN}).",
    )
    p.add_argument(
        "--vmax",
        type=float,
        default=DEFAULT_VEL_VMAX,
        help=f"velocity colour-scale maximum (default: {DEFAULT_VEL_VMAX}).",
    )
    p.add_argument("--getdata", type=Path, required=True, help="getData-elastic binary")
    p.add_argument("--getfacet", type=Path, required=True, help="getFacet binary")
    p.add_argument("--ny", type=int, default=1400, help="grid points along y (radial)")
    p.add_argument("--height", type=float, default=6.0, help="panel height in inches")
    return p.parse_args()


def main() -> int:
    a = parse_args()
    render(
        snapshot=a.snapshot,
        out_base=a.out,
        xmin=a.xmin,
        xmax=a.xmax,
        rmax=a.rmax,
        getdata_bin=a.getdata,
        getfacet_bin=a.getfacet,
        ny=a.ny,
        vmin=a.vmin,
        vmax=a.vmax,
        panel_height_in=a.height,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
