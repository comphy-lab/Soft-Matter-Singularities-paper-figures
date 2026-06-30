#!/usr/bin/env python3
"""Generate Figure 3: experimental and numerical drop pinch-off.

The heavy Basilisk snapshot extraction is done on Hamilton. This script assembles
the paper figure from the resulting tight snapshot panels plus reduced h_min
data stored under fig3_drop_pinch/.
"""

from __future__ import annotations

import csv
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FixedLocator, FuncFormatter
from scipy.interpolate import UnivariateSpline


WIDTH_MM = 135.0
HEIGHT_MM = 151.0
MM_TO_INCH = 1.0 / 25.4

HERE = Path(__file__).resolve().parent
ASSET_DIR = HERE / "fig3_drop_pinch"
PANEL_DIR = ASSET_DIR / "panels"
SNAP_DIR = ASSET_DIR / "snapshots"
DATA_DIR = ASSET_DIR / "data"
PREVIEW_DIR = ASSET_DIR / "previews"

EXPERIMENT_SOURCE = HERE / "drop-water-only.pdf"
WATER_PANEL_PNG = PANEL_DIR / "drop-water-only.png"
WATER_PANEL_PDF = PANEL_DIR / "drop-water-only.pdf"

ANALYSIS_DIR = Path(os.environ.get(
    "FIG3_ANALYSIS_DIR",
    "/Users/comphy-mac/Documents/Projects-cowork/share-files/elastic-pinchoff-analysis",
))
LOCAL_LOG_DIR = DATA_DIR / "raw_logs"
LOG_DIR = Path(os.environ.get(
    "FIG3_LOG_DIR",
    str(LOCAL_LOG_DIR if LOCAL_LOG_DIR.exists() else ANALYSIS_DIR / "logs"),
))
REDUCED_DATA = DATA_DIR / "fig3_l16_hmin_dhdt.csv"
FIT_SUMMARY = DATA_DIR / "fig3_fit_summary.txt"

INK = "#171717"
MUTED = "#666666"
GREEN = "#228833"
OH001 = 1e-2
VISCOUS_SLOPE = 0.0709 / OH001
EXPERIMENT_TAU_LABELS_MS = [4.55, 2.275, 0.0, -0.2, -0.4, -0.6]
EXPERIMENT_TAU_LABEL_X = [300, 535, 770, 1005, 1240, 1475]
EXPERIMENT_TAU_LABEL_Y = -10

CASES = [
    {
        "case": "c1023",
        "label": r"$Oh=0$",
        "log": LOG_DIR / "c1023-log",
        "oh": 0.0,
        "t0": 14.26669,
        "colour": "#009E73",
        "marker": "^",
    },
    {
        "case": "c1024",
        "label": r"$Oh=10^{-2}$",
        "log": LOG_DIR / "c1024-log",
        "oh": 1e-2,
        "t0": 14.49957211361072,
        "colour": "#CC79A7",
        "marker": "D",
    },
]


def configure_matplotlib(use_tex: bool = True) -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 7.2,
            "axes.linewidth": 0.65,
            "axes.labelsize": 7.8,
            "xtick.labelsize": 6.8,
            "ytick.labelsize": 6.8,
            "legend.fontsize": 6.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.usetex": use_tex,
        }
    )
    if use_tex:
        mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
    else:
        mpl.rcParams["mathtext.fontset"] = "cm"


def ensure_dirs() -> None:
    for path in (PANEL_DIR, SNAP_DIR, DATA_DIR, PREVIEW_DIR):
        path.mkdir(parents=True, exist_ok=True)


def render_pdf_to_png(src: Path, stem: Path, dpi: int = 500) -> Path:
    out = stem.with_suffix(".png")
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return out
    cmd = ["pdftoppm", "-png", "-singlefile", "-r", str(dpi), str(src), str(stem)]
    subprocess.run(cmd, check=True)
    return out


def trim_white_margin(img: np.ndarray, threshold: float = 0.985, pad: int = 10) -> np.ndarray:
    rgb = img[:, :, :3] if img.ndim == 3 else img
    content = np.any(rgb < threshold, axis=2) if rgb.ndim == 3 else rgb < threshold
    rows = np.where(np.any(content, axis=1))[0]
    cols = np.where(np.any(content, axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return img
    y0 = max(int(rows[0]) - pad, 0)
    y1 = min(int(rows[-1]) + pad + 1, img.shape[0])
    x0 = max(int(cols[0]) - pad, 0)
    x1 = min(int(cols[-1]) + pad + 1, img.shape[1])
    return img[y0:y1, x0:x1]


def compose_water_only_image() -> Path:
    if not EXPERIMENT_SOURCE.exists():
        raise FileNotFoundError(f"Missing experimental source: {EXPERIMENT_SOURCE}")

    rendered = render_pdf_to_png(EXPERIMENT_SOURCE, PREVIEW_DIR / "drop-water-only-500")
    img = plt.imread(rendered)
    if img.ndim == 2:
        img = np.repeat(img[:, :, None], 3, axis=2)
    if img.shape[2] > 3:
        img = img[:, :, :3]
    img = trim_white_margin(img)
    plt.imsave(WATER_PANEL_PNG, img)
    return WATER_PANEL_PNG


def save_water_panel(use_tex: bool = True) -> None:
    configure_matplotlib(use_tex)
    png = compose_water_only_image()
    image = plt.imread(png)
    aspect = image.shape[0] / image.shape[1]
    fig, ax = plt.subplots(figsize=(WIDTH_MM * MM_TO_INCH, WIDTH_MM * aspect * MM_TO_INCH), dpi=300)
    ax.imshow(image)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(WATER_PANEL_PDF, dpi=300, bbox_inches="tight", pad_inches=0.01)
    fig.savefig(WATER_PANEL_PNG, dpi=300, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)


def read_log(path: Path) -> np.ndarray:
    rows = []
    with path.open() as f:
        for line in f:
            parts = line.split()
            if len(parts) < 6:
                continue
            try:
                rows.append((int(parts[0]), float(parts[1]), float(parts[2]), float(parts[4]), float(parts[5])))
            except ValueError:
                continue
    return np.asarray(rows, dtype=float)


def prepare_case(case: dict[str, object]) -> dict[str, object]:
    raw = read_log(case["log"])  # type: ignore[index]
    t = raw[:, 2]
    h = raw[:, 3]
    tau = float(case["t0"]) - t
    mask_h = np.isfinite(tau) & np.isfinite(h) & (tau > 0) & (h > 0)
    out = dict(case)
    out["tau"] = tau[mask_h]
    out["h"] = h[mask_h]
    out["raw_rows"] = raw.shape[0]
    out["h_rows"] = int(mask_h.sum())
    return out


def fit_summary_by_case() -> dict[str, dict[str, str]]:
    if not FIT_SUMMARY.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    for line in FIT_SUMMARY.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        case = parts[0]
        fields: dict[str, str] = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        out[case] = fields
    return out


def load_reduced_data() -> list[dict[str, object]]:
    if not REDUCED_DATA.exists():
        raise FileNotFoundError(
            f"Missing raw logs and reduced data. Expected {REDUCED_DATA} for a portable rebuild."
        )
    fit_summary = fit_summary_by_case()
    rows_by_case: dict[str, list[dict[str, str]]] = {}
    with REDUCED_DATA.open() as f:
        for row in csv.DictReader(f):
            rows_by_case.setdefault(row["case"], []).append(row)

    prepared: list[dict[str, object]] = []
    for case in CASES:
        name = str(case["case"])
        rows = rows_by_case.get(name)
        if not rows:
            raise RuntimeError(f"No reduced Figure 3 data found for {name} in {REDUCED_DATA}")
        tau = np.asarray([float(row["tau"]) for row in rows])
        order = np.argsort(tau)
        h = np.asarray([float(row["hmin"]) for row in rows])[order]
        h_fit = np.asarray([float(row["hfit"]) for row in rows])[order]
        dhdt_fit = np.asarray([float(row["minus_dhdt_fit"]) for row in rows])[order]
        tau = tau[order]
        out = dict(case)
        out["tau"] = tau
        out["h"] = h
        out["tau_fit"] = tau
        out["h_fit"] = h_fit
        out["dhdt_fit"] = dhdt_fit
        out["h_fit_raw_tau"] = h_fit
        out["dhdt_fit_raw_tau"] = dhdt_fit
        out["raw_rows"] = len(rows)
        out["h_rows"] = len(rows)
        out["fit_kind"] = rows[0].get("fit_kind", "")
        out["fit_meta"] = fit_summary.get(name, {})
        prepared.append(out)
    return prepared


def reduce_data(prepared: list[dict[str, object]]) -> None:
    with REDUCED_DATA.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["case", "oh", "t0", "tau", "hmin", "hfit", "minus_dhdt_fit", "fit_kind"])
        for case in prepared:
            for tau, h, hfit, dfit in zip(case["tau"], case["h"], case["h_fit_raw_tau"], case["dhdt_fit_raw_tau"]):  # type: ignore[index]
                writer.writerow([
                    case["case"], case["oh"], case["t0"],
                    f"{tau:.12e}", f"{h:.12e}", f"{hfit:.12e}", f"{dfit:.12e}",
                    case["fit_kind"],
                ])

    with FIT_SUMMARY.open("w") as f:
        for case in prepared:
            fields = [f"{case['case']} fit_kind={case['fit_kind']}"]
            fields.extend(f"{key}={value}" for key, value in case["fit_meta"].items())  # type: ignore[index]
            f.write(" ".join(fields) + "\n")


def logbin_for_fit(tau: np.ndarray, h: np.ndarray, mask: np.ndarray, bins: int = 260) -> tuple[np.ndarray, np.ndarray]:
    x = tau[mask]
    y = h[mask]
    edges = np.logspace(np.log10(x.min()), np.log10(x.max()), bins + 1)
    xb = []
    yb = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (x >= lo) & (x < hi)
        if np.any(sel):
            xb.append(float(np.exp(np.mean(np.log(x[sel])))))
            yb.append(float(np.exp(np.mean(np.log(y[sel])))))
    return np.asarray(xb), np.asarray(yb)


def inertial_fit(tau: np.ndarray, h: np.ndarray) -> dict[str, object]:
    mask = np.isfinite(tau) & np.isfinite(h) & (tau > 0) & (h > 5e-4) & (h < 5e-2)
    x = tau[mask]
    y = h[mask]
    prefactor = float(np.exp(np.mean(np.log(y) - (2.0 / 3.0) * np.log(x))))
    return {"kind": "inertial_2_3", "A": prefactor, "nfit": int(x.size)}


def inertial_spline_fit(tau: np.ndarray, h: np.ndarray) -> dict[str, object]:
    base = inertial_fit(tau, h)
    prefactor = float(base["A"])
    mask = np.isfinite(tau) & np.isfinite(h) & (tau >= 2e-5) & (h > 2e-4) & (h < 0.98)
    x, y = logbin_for_fit(tau, h, mask, bins=95)
    log_x = np.log(x)
    residual = np.log(y / (prefactor * x ** (2.0 / 3.0)))

    anchor_end = min(float(x.min()) * 0.72, 1.2e-5)
    anchor_start = anchor_end / 1.0e4
    anchor_tau = np.logspace(np.log10(anchor_start), np.log10(anchor_end), 7)
    knots = np.concatenate([np.log(anchor_tau), log_x])
    values = np.concatenate([np.zeros_like(anchor_tau), residual])
    weights = np.concatenate([np.full_like(anchor_tau, 50.0), np.ones_like(residual)])
    smooth = 0.5
    spline = UnivariateSpline(knots, values, w=weights, k=3, s=smooth)
    pred = spline(log_x)
    rms = float(np.sqrt(np.mean((pred - residual) ** 2)))
    return {
        "kind": "inertial_2_3_spline",
        "spline": spline,
        "A": prefactor,
        "anchor_max_tau": float(anchor_tau.max()),
        "rms_log_residual": rms,
        "smooth": smooth,
        "nfit": int(x.size),
        "nfit_prefactor": int(base["nfit"]),
    }


def viscous_spline_fit(tau: np.ndarray, h: np.ndarray) -> dict[str, object]:
    mask = np.isfinite(tau) & np.isfinite(h) & (tau >= 2e-5) & (h > 2e-4) & (h < 0.55)
    x, y = logbin_for_fit(tau, h, mask, bins=95)
    log_x = np.log(x)
    residual = np.log(y / (VISCOUS_SLOPE * x))

    anchor_end = min(float(x.min()) * 0.72, 1.2e-5)
    anchor_start = anchor_end / 1.0e4
    anchor_tau = np.logspace(np.log10(anchor_start), np.log10(anchor_end), 7)
    knots = np.concatenate([np.log(anchor_tau), log_x])
    values = np.concatenate([np.zeros_like(anchor_tau), residual])
    weights = np.concatenate([np.full_like(anchor_tau, 50.0), np.ones_like(residual)])
    smooth = 0.5
    spline = UnivariateSpline(knots, values, w=weights, k=3, s=smooth)
    pred = spline(log_x)
    rms = float(np.sqrt(np.mean((pred - residual) ** 2)))
    return {
        "kind": "viscous_slope_spline",
        "spline": spline,
        "slope": VISCOUS_SLOPE,
        "anchor_max_tau": float(anchor_tau.max()),
        "rms_log_residual": rms,
        "smooth": smooth,
        "nfit": int(x.size),
    }


def inertial_spline_h_and_rate(tau: np.ndarray, spline: UnivariateSpline, prefactor: float) -> tuple[np.ndarray, np.ndarray]:
    log_tau = np.log(tau)
    residual = spline(log_tau)
    dresidual_dlogtau = spline(log_tau, 1)
    h = prefactor * tau ** (2.0 / 3.0) * np.exp(residual)
    dh_dtau = h / tau * (2.0 / 3.0 + dresidual_dlogtau)
    return h, dh_dtau


def viscous_spline_h_and_rate(tau: np.ndarray, spline: UnivariateSpline, slope: float = VISCOUS_SLOPE) -> tuple[np.ndarray, np.ndarray]:
    log_tau = np.log(tau)
    residual = spline(log_tau)
    dresidual_dlogtau = spline(log_tau, 1)
    h = slope * tau * np.exp(residual)
    dh_dtau = h / tau * (1.0 + dresidual_dlogtau)
    return h, dh_dtau


def apply_fits(prepared: list[dict[str, object]]) -> None:
    for case in prepared:
        tau = case["tau"]  # type: ignore[assignment]
        h = case["h"]  # type: ignore[assignment]
        tau_line = np.logspace(np.log10(max(float(tau.min()), 2e-5)), np.log10(float(tau.max())), 800)
        if float(case["oh"]) == 0.0:
            fit = inertial_spline_fit(tau, h)
            spline = fit["spline"]
            A = float(fit["A"])
            case["fit_kind"] = fit["kind"]
            case["fit_meta"] = {
                "A": f"{A:.12g}",
                "anchor_max_tau": f"{float(fit['anchor_max_tau']):.12g}",
                "rms_log_residual": f"{float(fit['rms_log_residual']):.12g}",
                "smooth": f"{float(fit['smooth']):.12g}",
                "nfit": fit["nfit"],
                "nfit_prefactor": fit["nfit_prefactor"],
            }
            case["tau_fit"] = tau_line
            case["h_fit"], case["dhdt_fit"] = inertial_spline_h_and_rate(tau_line, spline, A)
            case["h_fit_raw_tau"], case["dhdt_fit_raw_tau"] = inertial_spline_h_and_rate(tau, spline, A)
        else:
            fit = viscous_spline_fit(tau, h)
            spline = fit["spline"]
            case["fit_kind"] = fit["kind"]
            case["fit_meta"] = {
                "slope": f"{VISCOUS_SLOPE:.12g}",
                "anchor_max_tau": f"{float(fit['anchor_max_tau']):.12g}",
                "rms_log_residual": f"{float(fit['rms_log_residual']):.12g}",
                "smooth": f"{float(fit['smooth']):.12g}",
                "nfit": fit["nfit"],
            }
            case["tau_fit"] = tau_line
            case["h_fit"], case["dhdt_fit"] = viscous_spline_h_and_rate(tau_line, spline)
            case["h_fit_raw_tau"], case["dhdt_fit_raw_tau"] = viscous_spline_h_and_rate(tau, spline)


def fit_two_thirds(prepared: list[dict[str, object]]) -> tuple[float, int]:
    for case in prepared:
        if float(case["oh"]) == 0.0 and "A" in case.get("fit_meta", {}):
            meta = case["fit_meta"]  # type: ignore[assignment]
            return float(meta["A"]), int(meta.get("nfit_prefactor", meta["nfit"]))
    raise RuntimeError("No Oh=0 inertial fit available.")


def set_log_ticks(ax: plt.Axes) -> None:
    xticks = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1]
    yticks = [1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1]
    ax.xaxis.set_major_locator(FixedLocator(xticks))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))


def style_log_axis(ax: plt.Axes) -> None:
    ax.tick_params(which="major", direction="in", width=0.65, length=3.6, top=True, right=True, pad=2.0)
    ax.tick_params(which="minor", direction="in", width=0.45, length=1.9, top=True, right=True)
    for spine in ax.spines.values():
        spine.set_linewidth(0.65)
    ax.minorticks_on()


def positive_curve_points(case: dict[str, object], xkey: str, ykey: str) -> tuple[np.ndarray, np.ndarray]:
    tau = np.asarray(case[xkey], dtype=float)
    y = np.asarray(case[ykey], dtype=float)
    mask = np.isfinite(tau) & np.isfinite(y) & (tau > 0) & (y > 0)
    return tau[mask], y[mask]


def plot_hmin(ax: plt.Axes, prepared: list[dict[str, object]], show_ylabel: bool = True) -> None:
    xmin = 2e-5
    xmax = max(float(np.max(case["tau"])) for case in prepared) * 1.10
    visible_h = np.concatenate([case["h"][(case["tau"] >= xmin) & (case["tau"] <= xmax)] for case in prepared])
    ymin = max(float(visible_h.min()) * 0.65, 1e-5)
    ymax = min(float(visible_h.max()) * 1.25, 1.5)
    xguide = np.logspace(math.floor(math.log10(xmin)), math.ceil(math.log10(xmax)), 400)

    viscous = 0.0709 / 1e-2 * xguide
    mask = (viscous >= ymin) & (viscous <= ymax)
    viscous_handle = ax.plot(xguide[mask], viscous[mask], "--", color="black", lw=1.05, alpha=0.90, zorder=8, label=r"$0.0709\,\tau/Oh$")[0]

    a23, _ = fit_two_thirds(prepared)
    inertial = a23 * xguide ** (2.0 / 3.0)
    mask = (inertial >= ymin) & (inertial <= ymax)
    inertial_handle = ax.plot(xguide[mask], inertial[mask], "-", color="black", lw=1.15, alpha=0.96, zorder=8, label=r"$\sim\tau^{2/3}$")[0]

    scatter_handles = []
    for case in prepared:
        tau_pts, h_pts = positive_curve_points(case, "tau", "h")
        handle = ax.scatter(
            tau_pts,
            h_pts,
            s=5.8,
            c=case["colour"],
            marker=case["marker"],
            linewidths=0.0,
            alpha=0.88,
            label=case["label"],
            zorder=4,
            rasterized=True,
        )
        scatter_handles.append(handle)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    set_log_ticks(ax)
    style_log_axis(ax)
    ax.set_xlabel(r"$\tau=t_0-t$")
    if show_ylabel:
        ax.set_ylabel(r"$h_{\min}/R_0$")
    ax.set_box_aspect(1)
    leg = ax.legend(
        [*scatter_handles, viscous_handle, inertial_handle],
        [r"$Oh=0$", r"$Oh=10^{-2}$", r"$0.0709\,\tau/Oh$", r"$\sim\tau^{2/3}$"],
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=0.88,
        loc="lower right",
        handlelength=1.8,
        borderpad=0.2,
        labelspacing=0.28,
    )
    leg.set_zorder(20)


def plot_dhdt(ax: plt.Axes, prepared: list[dict[str, object]], show_ylabel: bool = True) -> None:
    xmin = 2e-5
    xmax = max(float(np.max(case["tau_fit"])) for case in prepared) * 1.10
    all_d = []
    for case in prepared:
        tau_rate = case["tau"] if "dhdt_fit_raw_tau" in case else case["tau_fit"]
        d_rate = case["dhdt_fit_raw_tau"] if "dhdt_fit_raw_tau" in case else case["dhdt_fit"]
        mask = (tau_rate >= xmin) & np.isfinite(d_rate) & (d_rate > 0)
        all_d.append(d_rate[mask])

    yvals = np.concatenate(all_d)
    ymin = max(float(np.percentile(yvals, 0.1)) * 0.60, 1e-3)
    ymax = float(yvals.max()) * 1.10
    xguide = np.logspace(math.floor(math.log10(xmin)), math.ceil(math.log10(xmax)), 400)

    a23, _ = fit_two_thirds(prepared)
    inertial_rate = (2.0 / 3.0) * a23 * xguide ** (-1.0 / 3.0)
    mask = (inertial_rate >= ymin) & (inertial_rate <= ymax)
    inertial_handle = ax.plot(xguide[mask], inertial_rate[mask], "-", color="black", lw=1.15, alpha=0.96, zorder=8, label=r"$\sim\tau^{-1/3}$")[0]
    viscous_handle = ax.plot([xmin, xmax], [VISCOUS_SLOPE, VISCOUS_SLOPE], "--", color="black", lw=1.05, alpha=0.90, zorder=8, label=r"$0.0709/Oh$")[0]

    scatter_handles = []
    for case in prepared:
        rate_key = "dhdt_fit_raw_tau" if "dhdt_fit_raw_tau" in case else "dhdt_fit"
        tau_key = "tau" if rate_key == "dhdt_fit_raw_tau" else "tau_fit"
        tau_pts, d_pts = positive_curve_points(case, tau_key, rate_key)
        mask_pts = tau_pts >= xmin
        handle = ax.scatter(
            tau_pts[mask_pts],
            d_pts[mask_pts],
            s=5.8,
            c=case["colour"],
            marker=case["marker"],
            linewidths=0.0,
            alpha=0.88,
            label=case["label"],
            zorder=3,
            rasterized=True,
        )
        scatter_handles.append(handle)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    set_log_ticks(ax)
    style_log_axis(ax)
    ax.set_xlabel(r"$\tau=t_0-t$")
    if show_ylabel:
        ax.set_ylabel(r"$-\mathrm{d}h_{\min}/\mathrm{d}t$", labelpad=5.0)
    ax.set_box_aspect(1)
    leg = ax.legend(
        [*scatter_handles, viscous_handle, inertial_handle],
        [r"$Oh=0$", r"$Oh=10^{-2}$", r"$0.0709/Oh$", r"$\sim\tau^{-1/3}$"],
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=0.88,
        loc="lower left",
        handlelength=1.8,
        borderpad=0.2,
        labelspacing=0.28,
    )
    leg.set_zorder(20)


def save_plot_panels(prepared: list[dict[str, object]]) -> None:
    for stem, plotter in (("fig3_hmin_l16", plot_hmin), ("fig3_dhdt_l16", plot_dhdt)):
        fig, ax = plt.subplots(figsize=(2.45, 2.45), dpi=300)
        plotter(ax, prepared)
        fig.tight_layout(pad=0.25)
        fig.savefig(PANEL_DIR / f"{stem}.pdf", dpi=300, bbox_inches="tight", pad_inches=0.02)
        fig.savefig(PANEL_DIR / f"{stem}.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)

    source_hmin = ANALYSIS_DIR / "hmin-vs-t0-minus-t-scatter-laws-L16.pdf"
    if source_hmin.exists():
        shutil.copy2(source_hmin, PANEL_DIR / source_hmin.name)


def load_snapshot_manifest() -> list[dict[str, str]]:
    manifest = SNAP_DIR / "manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(
            f"Missing {manifest}. Copy the Hamilton fig3-output directory into {SNAP_DIR} first."
        )
    with manifest.open() as f:
        rows = list(csv.DictReader(f))
    wanted = [0, 5, 6, 7, 8, 9]
    by_index = {int(row["index"]): row for row in rows}
    return [by_index[i] for i in wanted]


def snapshot_title(row: dict[str, str]) -> str:
    idx = int(row["index"])
    if idx == 0:
        return r"$t=0$"
    if idx == 8:
        return r"$t\simeq t_0^{-}$"
    if idx == 9:
        return r"$t_0^{+}$"
    return rf"$t={float(row['fraction']):.3f}\,t_0$"


def format_experimental_tau_label(value: float) -> str:
    if abs(value) < 1e-12:
        return r"$0$"
    return rf"${value:g}$"


def annotate_experimental_times(ax: plt.Axes) -> None:
    ax.text(
        178,
        EXPERIMENT_TAU_LABEL_Y,
        r"$t_0-t\;(\mathrm{ms})$",
        ha="right",
        va="center",
        fontsize=5.4,
        color=INK,
        clip_on=False,
    )
    for x, value in zip(EXPERIMENT_TAU_LABEL_X, EXPERIMENT_TAU_LABELS_MS):
        ax.text(
            x,
            EXPERIMENT_TAU_LABEL_Y,
            format_experimental_tau_label(value),
            ha="center",
            va="center",
            fontsize=5.4,
            color=INK,
            clip_on=False,
        )


def build_composite(prepared: list[dict[str, object]]) -> tuple[plt.Figure, list]:
    fig = plt.figure(figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH), dpi=300)
    gs = GridSpec(
        3,
        1,
        figure=fig,
        height_ratios=[0.74, 1.30, 2.47],
        hspace=0.0,
        left=0.064,
        right=0.985,
        bottom=0.045,
        top=0.988,
    )

    ax_exp = fig.add_subplot(gs[0, 0])
    ax_exp.imshow(plt.imread(WATER_PANEL_PNG))
    ax_exp.set_anchor("S")
    ax_exp.set_axis_off()
    annotate_experimental_times(ax_exp)

    rows = load_snapshot_manifest()
    snap_grid = gs[1, 0].subgridspec(2, 12, height_ratios=[1.0, 0.065], hspace=0.0, wspace=0.02)
    snap_axes = []
    vector_panels: list[tuple[Path, object]] = []
    for j, row in enumerate(rows):
        ax = fig.add_subplot(snap_grid[0, 2 * j : 2 * j + 2])
        png = Path(row["png"])
        if not png.exists():
            png = SNAP_DIR / png.name
        # imshow the PNG to fix the layout; the vector PDF sibling (rasterised
        # field + vector interface) is stamped over this exact footprint later.
        im = ax.imshow(plt.imread(png))
        vector_panels.append((png.with_suffix(".pdf"), im))
        ax.set_axis_off()
        ax.set_title(snapshot_title(row), fontsize=6.5, pad=1.0)
        snap_axes.append(ax)
    fig.canvas.draw()
    label_x = 0.051
    ax_exp_pos = ax_exp.get_position()
    snap_top = max(ax.get_position().y1 for ax in snap_axes)
    fig.text(label_x, ax_exp_pos.y1, r"\textbf{(a)}", ha="right", va="top", fontsize=8.6, color=INK)
    fig.text(label_x, snap_top + 0.016, r"\textbf{(b)}", ha="right", va="top", fontsize=8.6, color=INK)
    snap_bottom = min(ax.get_position().y0 for ax in snap_axes)
    cbar_y = snap_bottom - 0.044
    cbar_h = 0.014

    cax_d = fig.add_subplot(snap_grid[1, 1:5])
    cax_d.set_position([cax_d.get_position().x0, cbar_y, cax_d.get_position().width, cbar_h])
    cb_d = fig.colorbar(
        ScalarMappable(norm=Normalize(vmin=-3, vmax=1), cmap="hot_r"),
        cax=cax_d,
        orientation="horizontal",
        ticks=[-3, -1, 1],
    )
    cb_d.ax.tick_params(labelsize=5.7, width=0.45, length=1.8, pad=0.6)
    cb_d.ax.set_title(r"$\log_{10}\Phi$", fontsize=6.1, pad=2.3)

    cax_v = fig.add_subplot(snap_grid[1, 7:11])
    cax_v.set_position([cax_v.get_position().x0, cbar_y, cax_v.get_position().width, cbar_h])
    cb_v = fig.colorbar(
        ScalarMappable(norm=Normalize(vmin=0, vmax=3), cmap="Blues"),
        cax=cax_v,
        orientation="horizontal",
        ticks=[0, 1.5, 3],
    )
    cb_v.ax.tick_params(labelsize=5.7, width=0.45, length=1.8, pad=0.6)
    cb_v.ax.set_title(r"$|\boldsymbol{u}|$", fontsize=6.1, pad=2.3)

    plot_grid = gs[2, 0].subgridspec(1, 2, wspace=0.32)
    ax_h = fig.add_subplot(plot_grid[0, 0])
    ax_d = fig.add_subplot(plot_grid[0, 1])
    plot_hmin(ax_h, prepared)
    plot_dhdt(ax_d, prepared)
    ax_h.set_anchor("N")
    ax_d.set_anchor("N")
    label_box = {"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.35}
    ax_h.text(0.025, 0.965, r"\textbf{(c)}", transform=ax_h.transAxes, ha="left", va="top", fontsize=8.6, bbox=label_box)
    ax_d.text(0.025, 0.965, r"\textbf{(d)}", transform=ax_d.transAxes, ha="left", va="top", fontsize=8.6, bbox=label_box)
    return fig, vector_panels


def copy_to_share_files() -> None:
    share_env = os.environ.get("SMS_SHARE_DIR")
    if share_env:
        share = Path(share_env).expanduser()
    else:
        share = Path("/Users/comphy-mac/Documents/Projects-cowork/share-files/soft-matter-singularities")
        if not share.parent.exists():
            return
    share.mkdir(parents=True, exist_ok=True)
    for name in ("fig3_drop_pinch.pdf", "fig3_drop_pinch.png"):
        shutil.copy2(HERE / name, share / name)


def build_all(use_tex: bool = True) -> None:
    ensure_dirs()
    configure_matplotlib(use_tex)
    save_water_panel(use_tex)
    if all(Path(case["log"]).exists() for case in CASES):
        prepared = [prepare_case(case) for case in CASES]
        apply_fits(prepared)
        reduce_data(prepared)
    else:
        print("[info] Raw Figure 3 logs not found; rebuilding from curated reduced data.")
        prepared = load_reduced_data()
    save_plot_panels(prepared)
    fig, vector_panels = build_composite(prepared)
    from pdf_vector_stamp import save_vector_composite

    save_vector_composite(
        fig,
        HERE / "fig3_drop_pinch.pdf",
        HERE / "fig3_drop_pinch.png",
        vector_panels,
        pad_in=0.015,
    )
    plt.close(fig)
    copy_to_share_files()


def main() -> None:
    try:
        build_all(use_tex=True)
    except RuntimeError as exc:
        print(f"[warn] LaTeX render failed ({exc}); falling back to mathtext.")
        plt.close("all")
        build_all(use_tex=False)


if __name__ == "__main__":
    main()
