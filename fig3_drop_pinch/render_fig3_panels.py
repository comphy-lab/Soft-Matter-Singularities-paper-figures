#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import shutil
import subprocess
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from facet_simplify import chain_and_simplify


T0 = 14.49957211361072
OH = 1e-2
OHA = 1e-4

# Douglas-Peucker tolerance for the interface, in simulation length units
# (~0.5 of the lvl16 cell L0/2^16=1.9e-4): visually lossless, collapses the
# per-cell PLIC facet segments into a few vector polylines.
FACET_EPS = 1.0e-4

HAMILTON_ROOT = Path(os.environ.get(
    "EPO_HAMILTON_ROOT",
    "/Volumes/macOfficeV0/ElasticPinchOff/Hamilton-Newtonian-2026-06-27/simulationCases",
))


@dataclass
class Frame:
    label: str
    fraction: float | None
    target_time: float
    snapshot: Path
    time: float
    index: int = 0
    hmin: float | None = None
    vel: np.ma.MaskedArray | None = None
    diss: np.ma.MaskedArray | None = None
    x: np.ndarray | None = None
    r: np.ndarray | None = None
    facets: list[tuple[tuple[float, float], tuple[float, float]]] | None = None


def snapshot_time(path: Path) -> float:
    return float(path.name.split("snapshot-", 1)[1])


def run_capture(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)
    return proc.stdout + proc.stderr


def compile_helper(src: Path, out: Path, disable_dimensions: bool) -> None:
    cmd = ["qcc", "-O2", "-Wall"]
    if disable_dimensions:
        cmd.append("-disable-dimensions")
    cmd += [src.name, "-o", str(out), "-lm"]
    subprocess.run(cmd, cwd=src.parent, check=True)


def parse_facets(text: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    segments = []
    current = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2:
            current = []
            continue
        try:
            point = (float(parts[0]), float(parts[1]))
        except ValueError:
            current = []
            continue
        current.append(point)
        if len(current) == 2:
            segments.append((current[0], current[1]))
            current = []
    return segments


def neck_center(segments: list[tuple[tuple[float, float], tuple[float, float]]]) -> float:
    points = []
    for seg in segments:
        points.extend(seg)
    positive = [(x, y) for x, y in points if y > 1e-8]
    if not positive:
        raise RuntimeError("Could not infer neck centre from facets.")
    return min(positive, key=lambda p: p[1])[0]


def read_log_hmin(case_dir: Path) -> list[tuple[float, float]]:
    log_path = case_dir / "c1024-log"
    rows = []
    with log_path.open() as f:
        for line in f:
            p = line.split()
            if len(p) >= 5:
                try:
                    rows.append((float(p[2]), float(p[4])))
                except ValueError:
                    pass
    return rows


def nearest_hmin(log_rows: list[tuple[float, float]], t: float) -> float | None:
    if not log_rows:
        return None
    return min(log_rows, key=lambda row: abs(row[0] - t))[1]


def choose_frames(case_dir: Path) -> list[Frame]:
    snapshots = sorted((case_dir / "intermediate").glob("snapshot-*"), key=snapshot_time)
    if not snapshots:
        raise FileNotFoundError(f"No snapshots found in {case_dir / 'intermediate'}")

    fractions = [0.0, 0.25, 0.50, 0.75, 0.90, 0.95, 0.98, 0.995]
    frames: list[Frame] = []
    used: set[Path] = set()
    for f in fractions:
        target = f*T0
        snap = min(snapshots, key=lambda p: abs(snapshot_time(p) - target))
        used.add(snap)
        frames.append(Frame(label=f"f{f:0.3f}".replace(".", "p"), fraction=f,
                            target_time=target, snapshot=snap, time=snapshot_time(snap)))

    pre = [p for p in snapshots if snapshot_time(p) < T0]
    near = max(pre, key=snapshot_time)
    if near not in used:
        frames.append(Frame(label="near_t0", fraction=None, target_time=T0,
                            snapshot=near, time=snapshot_time(near)))
    else:
        frames.append(Frame(label="near_t0", fraction=None, target_time=T0,
                            snapshot=near, time=snapshot_time(near)))

    target_post = 1.1*T0
    post = min(snapshots, key=lambda p: abs(snapshot_time(p) - target_post))
    frames.append(Frame(label="post_1p1t0", fraction=1.1, target_time=target_post,
                        snapshot=post, time=snapshot_time(post)))
    for idx, frame in enumerate(frames):
        frame.index = idx
    return frames


def load_fields(
    frame: Frame,
    data_bin: Path,
    facet_bin: Path,
    case_dir: Path,
    xmin: float,
    xmax: float,
    rmax: float,
    ny: int,
) -> None:
    rel = frame.snapshot.relative_to(case_dir)
    data_text = run_capture([
        str(data_bin), str(rel), f"{xmin:.12g}", "0", f"{xmax:.12g}",
        f"{rmax:.12g}", str(ny), str(OH), str(OHA)
    ], cwd=case_dir)
    arr = np.loadtxt(StringIO(data_text))
    if arr.ndim != 2 or arr.shape[1] < 4:
        raise RuntimeError(f"Bad sampled field output for {frame.snapshot}")
    x = np.unique(arr[:, 0])
    r = np.unique(arr[:, 1])
    nx = len(x)
    nr = len(r)
    vals = arr[:, 2:].reshape(nx, nr, 2).transpose(1, 0, 2)
    frame.x = x
    frame.r = r
    frame.vel = np.ma.masked_invalid(vals[:, :, 0])
    frame.diss = np.ma.masked_less(np.ma.masked_invalid(vals[:, :, 1]), -50)
    frame.facets = parse_facets(run_capture([str(facet_bin), str(rel)], cwd=case_dir))


def mirror_to_image(field: np.ma.MaskedArray, side: str) -> tuple[np.ndarray, np.ma.MaskedArray]:
    mirrored = np.ma.vstack([field[::-1, :], field])
    n = field.shape[0]
    r_full = np.concatenate([-np.arange(n, 0, -1), np.arange(1, n + 1)]).astype(float)
    image = mirrored.T
    if side == "left":
        image[:, n:] = np.ma.masked
    elif side == "right":
        image[:, :n] = np.ma.masked
    else:
        raise ValueError(side)
    return r_full, image


def mirrored_radius_values(r: np.ndarray) -> np.ndarray:
    return np.concatenate([-r[::-1], r])


def mirrored_field_image(field: np.ma.MaskedArray, side: str) -> np.ma.MaskedArray:
    mirrored = np.ma.vstack([field[::-1, :], field]).T
    n = field.shape[0]
    if side == "left":
        mirrored[:, n:] = np.ma.masked
    elif side == "right":
        mirrored[:, :n] = np.ma.masked
    return mirrored


def mirrored_segments(segments):
    """Chain the per-cell facet segments into polylines and RDP-simplify
    (sub-cell tolerance), then map (x,y)->(r,z)=(y,x) and mirror about r=0. Same
    curve, ~100x fewer vector paths than drawing each PLIC segment."""
    out = []
    for pl in chain_and_simplify(segments, eps=FACET_EPS):
        rz = pl[:, [1, 0]]
        out.append(rz)
        out.append(rz * np.array([-1.0, 1.0]))
    return out


def configure_matplotlib() -> None:
    if shutil.which("latex"):
        mpl.rcParams.update({"text.usetex": True, "font.family": "serif"})
    else:
        mpl.rcParams.update({"text.usetex": False, "font.family": "serif", "mathtext.fontset": "cm"})
    mpl.rcParams.update({
        "font.size": 9,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def render_frame(
    frame: Frame,
    out_base: Path,
    xmin: float,
    xmax: float,
    rmax: float,
    vel_vmax: float,
    diss_vmin: float,
    diss_vmax: float,
    vel_cmap: str = "viridis",
    diss_cmap: str = "inferno",
    show_colorbars: bool = True,
    show_title: bool = True,
) -> tuple[Path, Path]:
    assert frame.vel is not None and frame.diss is not None and frame.r is not None
    r_full = mirrored_radius_values(frame.r)
    vel_img = mirrored_field_image(frame.vel, "right")
    diss_img = mirrored_field_image(frame.diss, "left")
    extent = [float(r_full.min()), float(r_full.max()), xmin, xmax]

    if show_colorbars or show_title:
        fig, ax = plt.subplots(figsize=(3.45, 3.95), dpi=320)
    else:
        fig, ax = plt.subplots(figsize=(1.45, 1.62), dpi=620)
    vi = ax.imshow(vel_img, origin="lower", extent=extent, aspect="equal",
                   cmap=vel_cmap, vmin=0.0, vmax=vel_vmax, interpolation="nearest")
    di = ax.imshow(diss_img, origin="lower", extent=extent, aspect="equal",
                   cmap=diss_cmap, vmin=diss_vmin, vmax=diss_vmax, interpolation="nearest")
    segs = mirrored_segments(frame.facets or [])
    if segs:
        ax.add_collection(LineCollection(segs, colors="white", linewidths=1.25, alpha=0.95, zorder=4))
        ax.add_collection(LineCollection(segs, colors="black", linewidths=0.55, alpha=0.95, zorder=5))
    ax.axvline(0.0, color="0.35", linewidth=0.55, linestyle="--", zorder=6)
    ax.set_xlim(-rmax, rmax)
    ax.set_ylim(xmin, xmax)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    if show_title:
        tau = T0 - frame.time
        top = rf"$t/t_0={frame.time/T0:.4f}$"
        if tau >= 0:
            top += rf", $\tau={tau:.2e}$"
        else:
            top += rf", $t-t_0={-tau:.2e}$"
        ax.set_title(top, fontsize=9, pad=2.5)

    if show_colorbars:
        fig.subplots_adjust(left=0.15, right=0.85, bottom=0.045, top=0.91)
        pos = ax.get_position()
        cax_l = fig.add_axes([0.055, pos.y0, 0.026, pos.height])
        cb_l = fig.colorbar(di, cax=cax_l)
        cb_l.ax.set_title(r"$\log_{10}\Phi$", fontsize=7.5, pad=3)
        cb_l.ax.yaxis.set_ticks_position("right")
        cb_l.ax.tick_params(labelsize=7, length=2)

        cax_r = fig.add_axes([0.895, pos.y0, 0.026, pos.height])
        cb_r = fig.colorbar(vi, cax=cax_r)
        cb_r.ax.set_title(r"$|\mathbf{u}|$", fontsize=7.5, pad=3)
        cb_r.ax.tick_params(labelsize=7, length=2)
        save_kwargs = {}
    else:
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        save_kwargs = {"bbox_inches": "tight", "pad_inches": 0}

    png = out_base.with_suffix(".png")
    pdf = out_base.with_suffix(".pdf")
    fig.savefig(png, **save_kwargs)
    fig.savefig(pdf, **save_kwargs)
    plt.close(fig)
    return png, pdf


def make_contact_sheet(frames: list[Path], output: Path) -> None:
    images = [plt.imread(path) for path in frames]
    fig, axs = plt.subplots(2, 5, figsize=(12.5, 6.2), dpi=220)
    for ax, img, idx in zip(axs.flat, images, range(len(images))):
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(f"{idx:02d}", fontsize=9, pad=1)
    fig.tight_layout(pad=0.3)
    fig.savefig(output.with_suffix(".png"))
    fig.savefig(output.with_suffix(".pdf"))
    plt.close(fig)


def parse_scales(path: Path) -> dict:
    d = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            d[k.strip()] = v.strip()
    return d


def resolve_local_snapshot(raw: str) -> Path:
    """Map a manifest snapshot path (Hamilton /nobackup, now deleted) to the
    local archive."""
    p = Path(raw)
    if p.exists():
        return p
    srccase = next((t for t in p.parts if t.startswith("c10")), None) or "c1024-in"
    cand = HAMILTON_ROOT / srccase / "intermediate" / p.name
    if not cand.exists():
        raise FileNotFoundError(f"{raw} -> {cand}")
    return cand


def render_from_manifest(manifest: Path, scales: Path, data_bin: Path,
                         facet_bin: Path, ny: int) -> None:
    """Re-render the exact Figure-3 frames listed in `manifest`, with the framing
    and colour scales fixed by `scales`, as tight no-colourbar/no-title panels
    (so only the now-vector interface changes vs the published panels)."""
    s = parse_scales(scales)
    xmin, xmax, rmax = float(s["xmin"]), float(s["xmax"]), float(s["rmax"])
    vel_vmax = float(s.get("vel_vmax", 3))
    diss_vmin, diss_vmax = float(s["log10_diss_vmin"]), float(s["log10_diss_vmax"])
    vel_cmap, diss_cmap = s.get("vel_cmap", "Blues"), s.get("diss_cmap", "hot_r")
    with manifest.open() as f:
        rows = list(csv.DictReader(f))
    print(f"== fig3: {len(rows)} frames, window x=[{xmin},{xmax}] rmax={rmax} "
          f"vel<= {vel_vmax}, log10Phi=[{diss_vmin},{diss_vmax}] ==")
    for row in rows:
        snap = resolve_local_snapshot(row["snapshot"])
        case_dir = snap.parents[1]
        t = snapshot_time(snap)
        frame = Frame(label=row.get("label", ""), fraction=None, target_time=t,
                      snapshot=snap, time=t, index=int(row.get("index", 0)))
        load_fields(frame, data_bin, facet_bin, case_dir, xmin, xmax, rmax, ny)
        # Write panels next to the manifest (repo snapshots dir); the manifest's
        # own pdf/png columns may point at the original Hamilton output dir.
        out_base = manifest.resolve().parent / Path(row["pdf"]).stem
        render_frame(frame, out_base, xmin, xmax, rmax, vel_vmax, diss_vmin,
                     diss_vmax, vel_cmap=vel_cmap, diss_cmap=diss_cmap,
                     show_colorbars=False, show_title=False)
        print(f"  {row.get('label', ''):>10} <- {snap.name}")
    print("done")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-manifest", type=Path, default=None,
                        help="Re-render exactly the frames in this manifest.csv (uses --scales).")
    parser.add_argument("--scales", type=Path, default=None, help="scales.txt for --from-manifest.")
    parser.add_argument("--getdata", type=Path, default=Path("/tmp/figbuild/getData-c1024-diss"))
    parser.add_argument("--getfacet", type=Path, default=Path("/tmp/figbuild/getFacet"))
    parser.add_argument("--case-dir", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--x-half", type=float, default=1.15)
    parser.add_argument("--rmax", type=float, default=1.05)
    parser.add_argument("--ny", type=int, default=720)
    parser.add_argument("--indices", default=None,
                        help="Comma-separated frame indices from the 10-frame set, e.g. 0,5,6,7,8,9.")
    parser.add_argument("--prefix", default="c1024")
    parser.add_argument("--vel-cmap", default="viridis")
    parser.add_argument("--diss-cmap", default="inferno")
    parser.add_argument("--vel-vmax", type=float, default=None)
    parser.add_argument("--diss-vmin", type=float, default=None)
    parser.add_argument("--diss-vmax", type=float, default=None)
    parser.add_argument("--no-colorbars", action="store_true")
    parser.add_argument("--no-title", action="store_true")
    args = parser.parse_args()

    configure_matplotlib()
    if args.from_manifest:
        if not args.scales:
            parser.error("--from-manifest requires --scales")
        render_from_manifest(args.from_manifest, args.scales, args.getdata,
                             args.getfacet, args.ny)
        return
    if not (args.case_dir and args.out_dir and args.work_dir):
        parser.error("choose-frames mode needs --case-dir, --out-dir, --work-dir")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)

    script_dir = Path(__file__).resolve().parent
    data_bin = args.work_dir / "getData-c1024-diss"
    facet_bin = args.work_dir / "getFacet"
    compile_helper(script_dir / "getData-c1024-diss.c", data_bin, disable_dimensions=True)
    compile_helper(args.case_dir.parents[1] / "postProcess" / "getFacet.c", facet_bin, disable_dimensions=False)

    frames = choose_frames(args.case_dir)
    if args.indices:
        wanted = {int(token.strip()) for token in args.indices.split(",") if token.strip()}
        frames = [frame for frame in frames if frame.index in wanted]
        missing = sorted(wanted - {frame.index for frame in frames})
        if missing:
            raise ValueError(f"Requested frame indices not available: {missing}")
    near_frame = [f for f in frames if f.label == "near_t0"][0]
    near_facets = parse_facets(run_capture([str(facet_bin), str(near_frame.snapshot.relative_to(args.case_dir))], cwd=args.case_dir))
    xc = neck_center(near_facets)
    xmin = xc - args.x_half
    xmax = xc + args.x_half

    log_rows = read_log_hmin(args.case_dir)
    for frame in frames:
        frame.hmin = nearest_hmin(log_rows, frame.time)
        load_fields(frame, data_bin, facet_bin, args.case_dir, xmin, xmax, args.rmax, args.ny)

    vel_values = np.ma.concatenate([f.vel.compressed() for f in frames if f.vel is not None])
    diss_values = np.ma.concatenate([f.diss.compressed() for f in frames if f.diss is not None])
    vel_vmax = args.vel_vmax if args.vel_vmax is not None else float(np.percentile(vel_values[np.isfinite(vel_values)], 99.5))
    diss_vmin, diss_vmax = [float(x) for x in np.percentile(diss_values[np.isfinite(diss_values)], [2.0, 99.5])]
    if args.diss_vmin is not None:
        diss_vmin = args.diss_vmin
    if args.diss_vmax is not None:
        diss_vmax = args.diss_vmax
    if vel_vmax <= 0 or not math.isfinite(vel_vmax):
        vel_vmax = float(np.nanmax(vel_values))

    manifest_rows = []
    pngs = []
    for frame in frames:
        time_tag = f"{frame.time:08.4f}".replace(".", "p")
        out_base = args.out_dir / f"{args.prefix}_{frame.index:02d}_{frame.label}_t{time_tag}"
        png, pdf = render_frame(
            frame, out_base, xmin, xmax, args.rmax, vel_vmax, diss_vmin, diss_vmax,
            vel_cmap=args.vel_cmap, diss_cmap=args.diss_cmap,
            show_colorbars=not args.no_colorbars, show_title=not args.no_title,
        )
        pngs.append(png)
        manifest_rows.append({
            "index": frame.index,
            "label": frame.label,
            "fraction": "" if frame.fraction is None else frame.fraction,
            "target_time": frame.target_time,
            "snapshot_time": frame.time,
            "tau": T0 - frame.time,
            "hmin_nearest_log": "" if frame.hmin is None else frame.hmin,
            "snapshot": str(frame.snapshot),
            "png": str(png),
            "pdf": str(pdf),
        })

    make_contact_sheet(pngs, args.out_dir / "c1024_contact_sheet")

    with (args.out_dir / "manifest.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)
    with (args.out_dir / "scales.txt").open("w") as f:
        f.write(f"t0={T0:.14g}\n")
        f.write(f"Oh={OH:.6g}\nOha={OHA:.6g}\n")
        f.write(f"x_center={xc:.12g}\nxmin={xmin:.12g}\nxmax={xmax:.12g}\nrmax={args.rmax:.12g}\n")
        f.write(f"vel_vmin=0\nvel_vmax={vel_vmax:.12g}\n")
        f.write(f"log10_diss_vmin={diss_vmin:.12g}\nlog10_diss_vmax={diss_vmax:.12g}\n")
        f.write(f"vel_cmap={args.vel_cmap}\ndiss_cmap={args.diss_cmap}\n")
        if args.vel_vmax is None:
            f.write("vel_vmax uses 99.5 percentile over selected frames.\n")
        else:
            f.write("vel_vmax fixed from command line.\n")
        if args.diss_vmin is None or args.diss_vmax is None:
            f.write("Unset diss limits use 2 and 99.5 percentiles.\n")
        else:
            f.write("dissipation limits fixed from command line.\n")

    print(f"WROTE {args.out_dir}")
    print(f"WINDOW x=[{xmin},{xmax}] r=[{-args.rmax},{args.rmax}]")
    print(f"SCALES vel=[0,{vel_vmax}] log10Phi=[{diss_vmin},{diss_vmax}]")


if __name__ == "__main__":
    main()
