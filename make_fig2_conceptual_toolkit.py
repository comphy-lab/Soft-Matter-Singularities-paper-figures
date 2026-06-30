#!/usr/bin/env python3
"""Generate Figure 2: conceptual toolkit schematic.

This is a schematic phase diagram, not a data plot.  The horizontal direction
tracks physical time t from an early outer-scale state toward the singular
event at t0.  The time-to-singularity tau = t0 - t decreases along that route.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, PathPatch, Polygon
from matplotlib.path import Path as MplPath


WIDTH_MM = 135.0
HEIGHT_MM = 92.0
MM_TO_INCH = 1.0 / 25.4

LIQUID = "#58B7E6"
LIQUID_DARK = "#156D9A"
GAS = "#FFFFFF"
INK = "#171717"
MUTED = "#6A6A6A"
FRAME = "#B9B9B9"
FORCING = "#C95F2D"
CUTOFF = "#2F7D59"
SIMILARITY = "#2F6FA3"
MEMORY = "#8C5A9E"
SHADE_ORANGE = "#F3D6C8"
SHADE_BLUE = "#DCEFF8"
SHADE_GREY = "#ECECEC"
SHADE_GREEN = "#DBEFE5"


def configure_matplotlib(use_tex: bool = True) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 8.2,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.usetex": use_tex,
        }
    )
    if use_tex:
        matplotlib.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
    else:
        matplotlib.rcParams["mathtext.fontset"] = "cm"


def arrow(
    ax: plt.Axes,
    xy0: tuple[float, float],
    xy1: tuple[float, float],
    color: str = INK,
    lw: float = 0.8,
    mutation_scale: float = 7.5,
    style: str = "-|>",
    zorder: int = 6,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            xy0,
            xy1,
            arrowstyle=style,
            mutation_scale=mutation_scale,
            lw=lw,
            color=color,
            shrinkA=0,
            shrinkB=0,
            zorder=zorder,
        )
    )


def text_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    color: str = INK,
    edgecolor: str = FRAME,
    fontsize: float = 5.8,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.008",
            facecolor=GAS,
            edgecolor=edgecolor,
            lw=0.55,
            zorder=8,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=color,
        linespacing=0.92,
        zorder=9,
    )


def draw_neck_icon(ax: plt.Axes, cx: float, cy: float, height: float, max_r: float, neck_r: float) -> None:
    yy = np.linspace(-0.5, 0.5, 160)
    r = max_r - (max_r - neck_r) * np.exp(-(yy / 0.21) ** 2)
    x_left = cx - r
    x_right = cx + r
    y = cy + height * yy
    poly = np.column_stack([np.r_[x_left, x_right[::-1]], np.r_[y, y[::-1]]])
    ax.add_patch(Polygon(poly, closed=True, facecolor=LIQUID, edgecolor=INK, lw=0.72, zorder=3))
    ax.plot([cx, cx], [cy - 0.36 * height, cy + 0.36 * height], color=MUTED, lw=0.42, ls=(0, (2, 2)), zorder=4)


def draw_extensional_flow(ax: plt.Axes, cx: float, cy: float, height: float, radius: float) -> None:
    x_left = cx - radius * 0.86
    x_right = cx + radius * 0.86
    y_top = cy + 0.50 * height
    y_bottom = cy - 0.50 * height
    for x in (x_left, x_right):
        arrow(ax, (x, y_top - 0.018), (x, y_top + 0.034), color=FORCING, lw=0.62, mutation_scale=5.4)
        arrow(ax, (x, y_bottom + 0.018), (x, y_bottom - 0.034), color=FORCING, lw=0.62, mutation_scale=5.4)


def draw_main_diagram(ax: plt.Axes) -> None:
    x0, x1 = 0.215, 0.785
    y0, y1 = 0.205, 0.585
    bands = [
        (x0, 0.355, SHADE_ORANGE, "outer\nflow", FORCING),
        (0.355, 0.555, SHADE_BLUE, "similarity\nwindow", SIMILARITY),
        (0.555, 0.695, SHADE_GREY, "crossover\nmemory", MEMORY),
        (0.695, x1, SHADE_GREEN, "cutoff", CUTOFF),
    ]

    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="square,pad=0", facecolor=GAS, edgecolor=FRAME, lw=0.62, zorder=1))
    for xa, xb, shade, name, color in bands:
        ax.add_patch(Polygon([(xa, y0), (xb, y0), (xb, y1), (xa, y1)], closed=True, facecolor=shade, edgecolor="none", alpha=0.72, zorder=1))
        ax.text((xa + xb) / 2, y1 + 0.034, name, ha="center", va="center", fontsize=6.25, color=color, linespacing=0.9)
        if xa != x0:
            ax.plot([xa, xa], [y0, y1], color=FRAME, lw=0.52, ls=(0, (2, 2)), zorder=3)

    row_edges = np.linspace(y0, y1, 5)
    for y in row_edges[1:-1]:
        ax.plot([x0, x1], [y, y], color=GAS, lw=1.0, zorder=2)
        ax.plot([x0, x1], [y, y], color=FRAME, lw=0.38, alpha=0.55, zorder=3)

    rows = [
        (0.537, "singularity?", FORCING),
        (0.442, "self-similar?", SIMILARITY),
        (0.347, "universal?", MEMORY),
        (0.252, "regularised?", CUTOFF),
    ]
    for y, name, color in rows:
        ax.text(0.173, y, name, ha="right", va="center", fontsize=7.0, color=color)

    # Claim windows in the four lanes.
    arrow(ax, (0.358, 0.537), (0.757, 0.537), color=FORCING, lw=1.0, mutation_scale=8.2)
    ax.text(0.545, 0.559, r"ideal $h_{\min}\to 0$ at $t_0$", color=FORCING, fontsize=6.35, ha="center", va="center")

    ax.plot([0.372, 0.615], [0.442, 0.442], color=SIMILARITY, lw=2.0, solid_capstyle="round", zorder=5)
    ax.text(0.494, 0.464, "profile collapse", color=SIMILARITY, fontsize=6.35, ha="center", va="center")

    ax.plot([0.410, 0.555], [0.347, 0.347], color=MEMORY, lw=2.0, solid_capstyle="round", zorder=5)
    ax.plot([0.555, 0.692], [0.347, 0.347], color=MEMORY, lw=1.15, ls=(0, (2, 2)), alpha=0.80, zorder=5)
    ax.text(0.495, 0.369, "forgets outer details", color=MEMORY, fontsize=6.15, ha="center", va="center")
    ax.text(0.636, 0.323, "memory?", color=MEMORY, fontsize=6.0, ha="center", va="center")

    ax.plot([0.697, 0.785], [0.252, 0.252], color=CUTOFF, lw=2.0, solid_capstyle="round", zorder=5)
    ax.scatter([0.740], [0.252], s=32, color=CUTOFF, edgecolor=GAS, linewidth=0.6, zorder=6)
    ax.text(0.742, 0.281, "new\nphysics", color=CUTOFF, fontsize=5.8, ha="center", va="center", linespacing=0.82)

    # Physical-time axis.  The singularity is at t=t0; tau decreases as t advances.
    arrow(ax, (x0, 0.145), (x1, 0.145), color=INK, lw=0.8, mutation_scale=8.5)
    ax.plot([x0, x0], [0.136, 0.154], color=INK, lw=0.55)
    ax.plot([x1, x1], [0.136, 0.154], color=INK, lw=0.55)
    ax.text(x0, 0.174, r"outer scale $R$", ha="center", va="center", fontsize=6.65, color=MUTED)
    ax.text(x1, 0.174, r"cutoff $\ell_m$", ha="center", va="center", fontsize=6.65, color=CUTOFF)
    ax.text(x0, 0.112, r"$t=0$", ha="center", va="center", fontsize=6.55, color=INK)
    ax.text(x1, 0.112, r"$t=t_0$", ha="center", va="center", fontsize=6.55, color=INK)
    ax.text(0.50, 0.070, r"physical time $t$ increases; $\tau=t_0-t\to 0$", ha="center", va="center", fontsize=6.75, color=INK)

    # Neck snapshots above the bands.
    ax.text(0.50, 0.895, r"shrinking length $h_{\min}(t)$", ha="center", va="center", fontsize=7.0, color=INK)
    necks = [(0.270, 0.040), (0.430, 0.026), (0.590, 0.014), (0.735, 0.006)]
    for i, (cx, neck_r) in enumerate(necks):
        draw_neck_icon(ax, cx, 0.785, 0.165, 0.034, neck_r)
        if i == 0:
            draw_extensional_flow(ax, cx, 0.785, 0.165, 0.034)
        if i < len(necks) - 1:
            arrow(ax, (cx + 0.055, 0.785), (necks[i + 1][0] - 0.055, 0.785), color=MUTED, lw=0.55, mutation_scale=6.0)
    ax.text(0.520, 0.675, r"$h_{\min}\sim A\tau^\alpha$", ha="center", va="center", fontsize=7.0, color=INK)


def draw_callouts(ax: plt.Axes) -> None:
    text_box(ax, 0.032, 0.765, 0.142, 0.112, "drop\npinch-off:\nsingular +\noften similar", color=FORCING, edgecolor=FORCING)
    arrow(ax, (0.174, 0.800), (0.236, 0.855), color=FORCING, lw=0.56, mutation_scale=5.7)

    text_box(ax, 0.032, 0.608, 0.142, 0.118, "diffusion:\nself-similar,\nno finite-\ntime $t_0$", color=SIMILARITY, edgecolor=SIMILARITY)
    arrow(ax, (0.174, 0.628), (0.383, 0.442), color=SIMILARITY, lw=0.56, mutation_scale=5.7)

    text_box(ax, 0.828, 0.442, 0.145, 0.120, "breakup\nmemory:\nprefactor or\nshape survives", color=MEMORY, edgecolor=MEMORY)
    arrow(ax, (0.828, 0.500), (0.615, 0.347), color=MEMORY, lw=0.56, mutation_scale=5.7)

    text_box(ax, 0.828, 0.210, 0.145, 0.142, "contact line:\nsingularity\nafter continuum\nextrapolation", color=CUTOFF, edgecolor=CUTOFF, fontsize=5.45)
    arrow(ax, (0.828, 0.238), (0.740, 0.252), color=CUTOFF, lw=0.56, mutation_scale=5.7)


def build_figure(use_tex: bool = True) -> plt.Figure:
    configure_matplotlib(use_tex=use_tex)
    fig, ax = plt.subplots(figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH))
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.055, top=0.985)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("auto")
    ax.set_facecolor(GAS)
    ax.axis("off")

    ax.add_patch(FancyBboxPatch((0.012, 0.020), 0.976, 0.950, boxstyle="square,pad=0", facecolor=GAS, edgecolor=FRAME, lw=0.55, zorder=0))
    draw_main_diagram(ax)
    draw_callouts(ax)
    return fig


def save_with_fallback(out_pdf: Path, out_png: Path) -> None:
    try:
        fig = build_figure(use_tex=True)
        fig.savefig(out_pdf)
        fig.savefig(out_png, dpi=450)
        plt.close(fig)
    except RuntimeError:
        plt.close("all")
        fig = build_figure(use_tex=False)
        fig.savefig(out_pdf)
        fig.savefig(out_png, dpi=450)
        plt.close(fig)


def main() -> None:
    here = Path(__file__).resolve().parent
    save_with_fallback(
        here / "fig2_conceptual_toolkit.pdf",
        here / "fig2_conceptual_toolkit.png",
    )


if __name__ == "__main__":
    main()
