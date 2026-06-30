#!/usr/bin/env python3
"""Generate Figure 8: synthesis map for the review."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, Ellipse, FancyArrowPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath

WIDTH_MM = 135.0
HEIGHT_MM = 100.0
MM_TO_INCH = 1.0 / 25.4
XMAX = WIDTH_MM / HEIGHT_MM

LIQUID = "#58B7E6"
LIQUID_DARK = "#156D9A"
LIQUID_LIGHT = "#DCEFF8"
GAS = "#FFFFFF"
INK = "#171717"
MUTED = "#6A6A6A"
FRAME = "#B9B9B9"
FORCING = "#C95F2D"
CUTOFF = "#2F7D59"
MEMORY = "#7D4A8F"
OUTPUT = "#8A5A20"
TOPOLOGY = "#4D6E3B"
SOFT = "#5A5A86"
NOISE = "#8A6F2A"

OUT_DIR = Path(__file__).parent


def configure_matplotlib(use_tex: bool = True) -> None:
    params: dict = {
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "font.size": 8.0,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    if use_tex:
        params["text.usetex"] = True
        params["text.latex.preamble"] = r"\usepackage{amsmath}"
    else:
        params["text.usetex"] = False
        params["mathtext.fontset"] = "cm"
    matplotlib.rcParams.update(params)


def arrow(
    ax: plt.Axes,
    xy0: tuple[float, float],
    xy1: tuple[float, float],
    color: str = INK,
    lw: float = 0.9,
    style: str = "-|>",
    mutation_scale: float = 8.0,
    alpha: float = 1.0,
    zorder: int = 5,
    connectionstyle: str | None = None,
) -> None:
    patch = FancyArrowPatch(
        posA=xy0,
        posB=xy1,
        arrowstyle=style,
        color=color,
        linewidth=lw,
        mutation_scale=mutation_scale,
        alpha=alpha,
        zorder=zorder,
        connectionstyle=connectionstyle,
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(patch)


def text(
    ax: plt.Axes,
    x: float,
    y: float,
    s: str,
    *,
    color: str = INK,
    fontsize: float = 7.0,
    weight: str = "normal",
    ha: str = "center",
    va: str = "center",
    **kwargs,
) -> None:
    ax.text(x, y, s, color=color, fontsize=fontsize, fontweight=weight, ha=ha, va=va, zorder=20, **kwargs)


def draw_neck(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    y = np.linspace(cy - 1.05 * s, cy + 1.05 * s, 80)
    r = 0.34 * s - 0.25 * s * np.exp(-((y - cy) / (0.35 * s)) ** 2)
    poly = np.column_stack([np.r_[cx - r, (cx + r)[::-1]], np.r_[y, y[::-1]]])
    ax.add_patch(Polygon(poly, closed=True, facecolor=LIQUID, edgecolor=INK, lw=0.75, zorder=4))
    ax.add_patch(Circle((cx, cy), 0.045 * s, facecolor=CUTOFF, edgecolor=GAS, lw=0.4, zorder=7))


def draw_bridge(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.add_patch(Circle((cx - 0.26 * s, cy), 0.33 * s, facecolor=LIQUID, edgecolor=INK, lw=0.65, zorder=4))
    ax.add_patch(Circle((cx + 0.26 * s, cy), 0.33 * s, facecolor=LIQUID, edgecolor=INK, lw=0.65, zorder=4))
    ax.add_patch(Rectangle((cx - 0.14 * s, cy - 0.10 * s), 0.28 * s, 0.20 * s, facecolor=LIQUID, edgecolor="none", zorder=5))
    ax.plot([cx - 0.11 * s, cx + 0.11 * s], [cy, cy], color=INK, lw=0.75, zorder=6)


def draw_contact_line(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.plot([cx - 0.45 * s, cx + 0.50 * s], [cy - 0.28 * s, cy - 0.28 * s], color=MUTED, lw=1.0, zorder=4)
    verts = [
        (cx - 0.40 * s, cy - 0.28 * s),
        (cx - 0.32 * s, cy + 0.20 * s),
        (cx + 0.15 * s, cy + 0.22 * s),
        (cx + 0.34 * s, cy - 0.28 * s),
        (cx - 0.40 * s, cy - 0.28 * s),
    ]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=LIQUID, edgecolor=INK, lw=0.7, zorder=5))
    ax.add_patch(Circle((cx + 0.34 * s, cy - 0.28 * s), 0.045 * s, facecolor=CUTOFF, edgecolor=GAS, lw=0.3, zorder=7))


def draw_film_rupture(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.add_patch(Rectangle((cx - 0.42 * s, cy - 0.18 * s), 0.84 * s, 0.36 * s, facecolor=LIQUID_LIGHT, edgecolor=INK, lw=0.6, zorder=4))
    for radius in [0.08, 0.15, 0.22]:
        ax.add_patch(Circle((cx, cy), radius * s, fill=False, edgecolor=LIQUID_DARK, lw=0.55, alpha=0.75, zorder=5))
    ax.add_patch(Circle((cx, cy), 0.09 * s, facecolor=GAS, edgecolor=CUTOFF, lw=0.8, zorder=7))
    arrow(ax, (cx - 0.36 * s, cy + 0.26 * s), (cx - 0.12 * s, cy + 0.10 * s), color=FORCING, lw=0.55, mutation_scale=5)
    arrow(ax, (cx + 0.36 * s, cy + 0.26 * s), (cx + 0.12 * s, cy + 0.10 * s), color=FORCING, lw=0.55, mutation_scale=5)


def draw_jet(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.add_patch(Ellipse((cx, cy - 0.30 * s), 0.85 * s, 0.22 * s, facecolor=LIQUID, edgecolor=INK, lw=0.7, zorder=4))
    ax.plot([cx - 0.06 * s, cx, cx + 0.06 * s], [cy - 0.22 * s, cy + 0.52 * s, cy - 0.22 * s], color=INK, lw=0.75, zorder=6)
    ax.fill([cx - 0.06 * s, cx, cx + 0.06 * s], [cy - 0.22 * s, cy + 0.52 * s, cy - 0.22 * s], color=LIQUID, zorder=5)
    ax.add_patch(Circle((cx, cy + 0.61 * s), 0.055 * s, facecolor=LIQUID, edgecolor=INK, lw=0.55, zorder=6))


def draw_polymer(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    t = np.linspace(0, 5 * np.pi, 120)
    r = np.linspace(0.08, 0.34, 120) * s
    ax.plot(cx + r * np.cos(t), cy + r * np.sin(t), color=MEMORY, lw=0.75, zorder=6)


def draw_surfactant(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.plot([cx - 0.42 * s, cx + 0.42 * s], [cy, cy], color=LIQUID_DARK, lw=0.9, zorder=5)
    xs = np.linspace(cx - 0.35 * s, cx + 0.35 * s, 6)
    for i, x in enumerate(xs):
        ax.add_patch(Circle((x, cy + 0.025 * s), (0.020 + 0.006 * i) * s, facecolor=FORCING, edgecolor="none", zorder=6))
    ax.plot([cx - 0.36 * s, cx + 0.36 * s], [cy + 0.16 * s, cy + 0.16 * s], color=FORCING, lw=0.65, zorder=5)


def draw_particles(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    offsets = [(-0.22, -0.12), (0.00, -0.14), (0.21, -0.08), (-0.12, 0.10), (0.12, 0.11)]
    for dx, dy in offsets:
        ax.add_patch(Circle((cx + dx * s, cy + dy * s), 0.065 * s, facecolor=TOPOLOGY, edgecolor=INK, lw=0.35, zorder=6))


def draw_noise(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    xs = np.linspace(cx - 0.38 * s, cx + 0.38 * s, 9)
    ys = cy + np.array([0.0, 0.11, -0.04, 0.16, -0.10, 0.07, -0.03, 0.12, 0.0]) * s
    ax.plot(xs, ys, color=NOISE, lw=0.85, zorder=6)
    for x, y in zip(xs[1:-1:2], ys[1:-1:2]):
        ax.add_patch(Circle((x, y), 0.025 * s, facecolor=NOISE, edgecolor="none", zorder=7))


def draw_active_defect(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    for angle in np.linspace(-0.8 * np.pi, 0.8 * np.pi, 7):
        length = 0.18 * s
        x0 = cx - 0.10 * s * np.cos(angle)
        y0 = cy - 0.10 * s * np.sin(angle)
        ax.plot([x0, x0 + length * np.cos(0.5 * angle)], [y0, y0 + length * np.sin(0.5 * angle)], color=SOFT, lw=0.65, zorder=5)
    ax.add_patch(Circle((cx, cy), 0.055 * s, facecolor=SOFT, edgecolor=GAS, lw=0.4, zorder=7))
    ax.plot([cx + 0.06 * s, cx + 0.28 * s], [cy, cy], color=SOFT, lw=0.65, zorder=5)


def draw_slip(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    wall_y = cy - 0.18 * s
    x0 = cx - 0.20 * s
    ax.plot(
        [cx - 0.48 * s, cx + 0.48 * s],
        [wall_y, wall_y],
        color=MUTED,
        lw=1.15,
        solid_capstyle="round",
        zorder=5,
    )
    xs = np.linspace(0.0, 0.62 * s, 120)
    ys = wall_y + 0.045 * s * (1.0 - np.exp(-xs / (0.095 * s))) + 0.45 * xs
    poly = [(x0, wall_y), *[(x0 + x, y) for x, y in zip(xs, ys)], (x0 + xs[-1], wall_y)]
    ax.add_patch(Polygon(poly, closed=True, facecolor=LIQUID, edgecolor=LIQUID_DARK, lw=0.72, alpha=0.92, zorder=5))
    ax.add_patch(Circle((x0, wall_y), 0.095 * s, facecolor=CUTOFF, edgecolor="none", alpha=0.16, zorder=4))
    ax.add_patch(Circle((x0, wall_y), 0.033 * s, facecolor=CUTOFF, edgecolor="none", zorder=8))
    ax.add_patch(Arc((x0, wall_y), 0.23 * s, 0.23 * s, theta1=0, theta2=32, color=INK, lw=0.58, zorder=7))
    text(ax, x0 + 0.205 * s, wall_y + 0.052 * s, r"$\theta$", color=INK, fontsize=5.4, ha="left", va="center")
    arrow(
        ax,
        (x0 - 0.115 * s, wall_y + 0.198 * s),
        (x0 + 0.115 * s, wall_y + 0.198 * s),
        color=CUTOFF,
        lw=0.62,
        style="<->",
        mutation_scale=5.8,
        zorder=7,
    )
    text(ax, x0, wall_y + 0.233 * s, r"$\ell_s$", color=CUTOFF, fontsize=6.8, va="bottom")


def draw_inter_molecular(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.plot([cx - 0.38 * s, cx + 0.38 * s], [cy + 0.12 * s, cy + 0.12 * s], color=LIQUID_DARK, lw=0.9, zorder=5)
    ax.plot([cx - 0.38 * s, cx + 0.38 * s], [cy - 0.12 * s, cy - 0.12 * s], color=LIQUID_DARK, lw=0.9, zorder=5)
    xs = np.linspace(cx - 0.24 * s, cx + 0.24 * s, 5)
    for x in xs:
        ax.add_patch(Circle((x, cy), 0.030 * s, facecolor=CUTOFF, edgecolor="none", zorder=6))


def draw_ambient(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.add_patch(Circle((cx, cy), 0.25 * s, facecolor=LIQUID_LIGHT, edgecolor=LIQUID_DARK, lw=0.65, zorder=5))
    ax.add_patch(Circle((cx, cy), 0.14 * s, facecolor=GAS, edgecolor=MUTED, lw=0.55, zorder=6))
    for angle in np.linspace(0.2, 2 * np.pi - 0.2, 6):
        ax.add_patch(Circle((cx + 0.36 * s * np.cos(angle), cy + 0.24 * s * np.sin(angle)), 0.018 * s, facecolor=MUTED, edgecolor="none", alpha=0.65, zorder=5))


def draw_viscosity_icon(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    yy = np.linspace(cy - 0.16 * s, cy + 0.16 * s, 80)
    xx = cx + 0.10 * s * np.sin(np.linspace(0, 4 * np.pi, 80))
    ax.plot(xx, yy, color=FORCING, lw=0.85, zorder=6)
    ax.plot([cx - 0.28 * s, cx + 0.28 * s], [cy + 0.20 * s, cy + 0.20 * s], color=MUTED, lw=0.65, zorder=5)
    ax.plot([cx - 0.28 * s, cx + 0.28 * s], [cy - 0.20 * s, cy - 0.20 * s], color=MUTED, lw=0.65, zorder=5)


def draw_roughness(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    xs = np.linspace(cx - 0.42 * s, cx + 0.42 * s, 9)
    ys = cy - 0.18 * s + np.array([0.00, 0.10, -0.01, 0.12, 0.02, 0.13, -0.02, 0.09, 0.00]) * s
    ax.plot(xs, ys, color=MUTED, lw=0.75, zorder=5)
    ax.add_patch(Ellipse((cx, cy + 0.11 * s), 0.55 * s, 0.22 * s, facecolor=LIQUID_LIGHT, edgecolor=LIQUID_DARK, lw=0.65, zorder=5))


def draw_thermal_noise_icon(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    offsets = [(-0.30, 0.02), (-0.18, 0.16), (-0.06, -0.12), (0.08, 0.13), (0.20, -0.04), (0.32, 0.10)]
    for i, (dx, dy) in enumerate(offsets):
        ax.add_patch(Circle((cx + dx * s, cy + dy * s), (0.020 + 0.004 * (i % 2)) * s, facecolor=NOISE, edgecolor="none", zorder=6))
    ax.plot([cx - 0.36 * s, cx - 0.20 * s, cx - 0.04 * s, cx + 0.13 * s, cx + 0.33 * s], [cy - 0.12 * s, cy + 0.08 * s, cy - 0.04 * s, cy + 0.14 * s, cy - 0.08 * s], color=NOISE, lw=0.65, zorder=5)


def build_figure(use_tex: bool = True) -> plt.Figure:
    configure_matplotlib(use_tex)

    fig, ax = plt.subplots(1, 1, figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH))
    fig.subplots_adjust(left=0.025, right=0.985, bottom=0.065, top=0.965)
    ax.set_xlim(0, XMAX)
    ax.set_ylim(0.125, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(GAS)

    centre_x, centre_y = 0.665, 0.515
    outer_r, inner_r = 0.242, 0.124

    text(
        ax,
        0.15,
        0.945,
        "examples",
        color=INK,
        fontsize=8.0,
        weight="bold",
    )
    text(ax, centre_x, 0.945, "additional factors", color=INK, fontsize=8.0, weight="bold")
    text(ax, 1.17, 0.945, "regularisation", color=INK, fontsize=8.0, weight="bold")

    # Left: the examples developed through the manuscript.
    left_label_x = 0.020
    left_x = 0.220
    left_y = [0.79, 0.645, 0.500, 0.355, 0.210]
    left_draw = [draw_neck, draw_bridge, draw_contact_line, draw_film_rupture, draw_jet]
    left_labels = ["pinch-off", "coalescence", "contact line", "film", "jet"]
    left_scales = [0.080, 0.080, 0.080, 0.126, 0.080]
    for y, draw_fn, label, scale in zip(left_y, left_draw, left_labels, left_scales):
        text(ax, left_label_x, y, label, color=INK, fontsize=6.5, ha="left")
        draw_fn(ax, left_x, y, scale)

    # Central local problem: the review's reusable result.
    ax.add_patch(Circle((centre_x, centre_y), outer_r, facecolor=LIQUID_LIGHT, edgecolor=LIQUID_DARK, lw=1.15, zorder=3))
    ax.add_patch(Circle((centre_x, centre_y), inner_r, facecolor=GAS, edgecolor=FRAME, lw=0.55, zorder=4))
    draw_neck(ax, centre_x, centre_y, 0.105)

    # Four questions around the local region.
    text(ax, 0.476, centre_y, "length\nand time\nscales", color=INK, fontsize=5.0, ha="center", linespacing=0.82)

    arrow(ax, (centre_x - 0.030, centre_y + 0.095), (centre_x - 0.030, centre_y + 0.160), color=FORCING, lw=0.65, mutation_scale=5.5, zorder=8)
    arrow(ax, (centre_x + 0.030, centre_y + 0.095), (centre_x + 0.030, centre_y + 0.160), color=FORCING, lw=0.65, mutation_scale=5.5, zorder=8)
    arrow(ax, (centre_x - 0.030, centre_y - 0.095), (centre_x - 0.030, centre_y - 0.160), color=FORCING, lw=0.65, mutation_scale=5.5, zorder=8)
    arrow(ax, (centre_x + 0.030, centre_y - 0.095), (centre_x + 0.030, centre_y - 0.160), color=FORCING, lw=0.65, mutation_scale=5.5, zorder=8)
    text(ax, centre_x, centre_y + 0.178, "driving", color=FORCING, fontsize=6.4)

    ax.add_patch(Circle((centre_x, centre_y - 0.172), 0.018, facecolor=CUTOFF, edgecolor=GAS, lw=0.4, zorder=9))
    text(ax, centre_x, centre_y - 0.205, "cutoff", color=CUTOFF, fontsize=6.4)

    t = np.linspace(0, 3.4 * np.pi, 90)
    r = np.linspace(0.002, 0.034, 90)
    memory_x, memory_y = centre_x + 0.170, centre_y + 0.010
    ax.plot(memory_x + r * np.cos(t), memory_y + r * np.sin(t), color=MEMORY, lw=0.65, zorder=9)
    text(ax, memory_x, memory_y - 0.062, "memory", color=MEMORY, fontsize=6.4)

    # Top modifiers feed the same local problem.
    modifier_x = [0.405, 0.535, 0.665, 0.795, 0.925]
    modifier_draw = [draw_polymer, draw_surfactant, draw_particles, draw_noise, draw_active_defect]
    modifier_labels = ["polymer", "Marangoni", "particles", "noise", "activity"]
    modifier_colours = [MEMORY, FORCING, TOPOLOGY, NOISE, SOFT]
    for x, draw_fn, label, colour in zip(modifier_x, modifier_draw, modifier_labels, modifier_colours):
        draw_fn(ax, x, 0.850, 0.086)
        text(ax, x, 0.775, label, color=colour, fontsize=6.0)

    # Bottom centre: what the local problem selects in experiments and applications.
    text(ax, centre_x, 0.228, "selected outputs", color=INK, fontsize=6.8, weight="bold")
    output_items = [
        (0.370, 0.178, "drop size"),
        (0.515, 0.178, "jet speed"),
        (0.645, 0.178, "wetting"),
        (0.785, 0.178, "breakup"),
        (0.930, 0.178, "force/damage"),
    ]
    for x, y, label in output_items:
        text(ax, x, y, label, color=INK, fontsize=5.0)

    # Right: examples of regularisation mechanisms named through the review.
    reg_icon_x = 1.075
    reg_label_x = 1.190
    reg_y = [0.795, 0.675, 0.555, 0.435, 0.315, 0.195]
    reg_draw = [
        draw_slip,
        draw_inter_molecular,
        draw_ambient,
        draw_viscosity_icon,
        draw_roughness,
        draw_thermal_noise_icon,
    ]
    reg_labels = [
        "slip\nlength",
        "intermolecular\nforces",
        "ambient\nmedium",
        "viscosity",
        "surface\nroughness",
        "thermal\nnoise",
    ]
    reg_scales = [0.150, 0.104, 0.104, 0.104, 0.104, 0.104]
    for y, draw_fn, label, scale in zip(reg_y, reg_draw, reg_labels, reg_scales):
        draw_fn(ax, reg_icon_x, y, scale)
        text(ax, reg_label_x, y, label, color=INK, fontsize=5.55, ha="left", linespacing=0.86)

    return fig


def save_with_fallback(out_pdf: Path, out_png: Path) -> None:
    try:
        fig = build_figure(use_tex=True)
        fig.savefig(out_pdf, dpi=300, bbox_inches="tight", pad_inches=0.02)
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)
        print(f"Saved (TeX):  {out_pdf}")
        print(f"Saved (TeX):  {out_png}")
    except RuntimeError as exc:
        print(f"LaTeX failed ({exc}); retrying without TeX.")
        plt.close("all")
        fig = build_figure(use_tex=False)
        fig.savefig(out_pdf, dpi=300, bbox_inches="tight", pad_inches=0.02)
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)
        print(f"Saved (no-TeX): {out_pdf}")
        print(f"Saved (no-TeX): {out_png}")


def main() -> None:
    out_pdf = OUT_DIR / "fig8_broad_family.pdf"
    out_png = OUT_DIR / "fig8_broad_family.png"
    save_with_fallback(out_pdf, out_png)


if __name__ == "__main__":
    main()
