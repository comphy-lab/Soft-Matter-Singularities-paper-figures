#!/usr/bin/env python3
"""Generate Figure 1: visual dictionary schematics.

The figure is sized to the Contemporary Physics text width used by the paper:
135 mm wide with 8--10 pt labels. Liquid domains are blue; gas is pure white.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, FancyArrowPatch, PathPatch, Polygon
from matplotlib.path import Path as MplPath


WIDTH_MM = 135.0
HEIGHT_MM = 118.0
MM_TO_INCH = 1.0 / 25.4

LIQUID = "#58B7E6"
LIQUID_DARK = "#156D9A"
LIQUID_LIGHT = "#BDE7F7"
GAS = "#FFFFFF"
INK = "#171717"
MUTED = "#6A6A6A"
FRAME = "#B9B9B9"
FORCING = "#C95F2D"
CUTOFF = "#2F7D59"
SOLID = "#7F7F7F"
LABEL_BOX = {"facecolor": GAS, "edgecolor": "none", "pad": 0.45, "alpha": 0.96}


def configure_matplotlib(use_tex: bool = True) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 8.5,
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


def style_panel(ax: plt.Axes, label: str, title: str) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_facecolor(GAS)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.65)
        spine.set_color(FRAME)
    ax.text(0.035, 0.965, label, ha="left", va="top", fontsize=9.5, fontweight="bold")
    ax.text(0.14, 0.965, title, ha="left", va="top", fontsize=8.5)


def arrow(
    ax: plt.Axes,
    xy0: tuple[float, float],
    xy1: tuple[float, float],
    color: str = INK,
    lw: float = 0.9,
    style: str = "-|>",
    mutation_scale: float = 8.0,
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


def curved_arrow(
    ax: plt.Axes,
    xy0: tuple[float, float],
    xy1: tuple[float, float],
    rad: float,
    color: str = INK,
    lw: float = 0.9,
    mutation_scale: float = 8.0,
    zorder: int = 6,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            xy0,
            xy1,
            arrowstyle="-|>",
            connectionstyle=f"arc3,rad={rad}",
            mutation_scale=mutation_scale,
            lw=lw,
            color=color,
            shrinkA=0,
            shrinkB=0,
            zorder=zorder,
        )
    )


def double_arrow(
    ax: plt.Axes,
    xy0: tuple[float, float],
    xy1: tuple[float, float],
    color: str = INK,
    lw: float = 0.8,
    mutation_scale: float = 7.0,
) -> None:
    arrow(ax, xy0, xy1, color=color, lw=lw, style="<->", mutation_scale=mutation_scale)


def label(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    color: str = INK,
    fontsize: float = 7.4,
    ha: str = "center",
    va: str = "center",
    **kwargs,
) -> None:
    ax.text(
        x,
        y,
        text,
        color=color,
        fontsize=fontsize,
        ha=ha,
        va=va,
        bbox=LABEL_BOX,
        zorder=10,
        **kwargs,
    )


def interface_path(xs: np.ndarray, ys: np.ndarray, bottom: float = 0.04) -> MplPath:
    verts = [(float(xs[0]), bottom), *zip(xs, ys), (float(xs[-1]), bottom), (float(xs[0]), bottom)]
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * len(xs) + [MplPath.LINETO, MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


def interface_path_to_top(xs: np.ndarray, ys: np.ndarray, top: float = 0.92) -> MplPath:
    verts = [(float(xs[0]), top), *zip(xs, ys), (float(xs[-1]), top), (float(xs[0]), top)]
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * len(xs) + [MplPath.LINETO, MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


def panel_pinch_off(ax: plt.Axes) -> None:
    style_panel(ax, "(a)", "pinch-off")
    dy = 0.05  # nudge the whole schematic down so the top arrows clear the (a) label
    cy = 0.50 - dy  # neck centre after the shift
    y = np.linspace(0.14 - dy, 0.84 - dy, 320)

    for neck, alpha in [(0.17, 0.22), (0.115, 0.34)]:
        r = 0.19 - (0.19 - neck) * np.exp(-((y - cy) / 0.145) ** 2)
        ax.plot(0.50 - r, y, color=LIQUID_DARK, lw=0.7, alpha=alpha)
        ax.plot(0.50 + r, y, color=LIQUID_DARK, lw=0.7, alpha=alpha)

    r = 0.195 - 0.145 * np.exp(-((y - cy) / 0.135) ** 2)
    poly = np.column_stack([np.r_[0.50 - r, (0.50 + r)[::-1]], np.r_[y, y[::-1]]])
    ax.add_patch(Polygon(poly, closed=True, facecolor=LIQUID, edgecolor=INK, lw=1.0, zorder=2))
    ax.plot([0.50, 0.50], [0.23 - dy, 0.77 - dy], color=MUTED, lw=0.55, ls=(0, (2, 2)), zorder=3)

    x_neck = 0.50 + float(r[np.argmin(np.abs(y - cy))])
    double_arrow(ax, (0.50, cy), (x_neck, cy), color=INK, lw=0.75)
    label(ax, 0.70, 0.54 - dy, r"$h_{\min}$", fontsize=8.3, ha="left")
    arrow(ax, (0.68, 0.525 - dy), (x_neck + 0.015, 0.505 - dy), color=INK, lw=0.55, mutation_scale=6.0)
    ax.add_patch(Circle((0.50, cy), 0.020, facecolor=CUTOFF, edgecolor="white", lw=0.6, zorder=7))
    label(ax, 0.26, cy, "cutoff", color=CUTOFF, fontsize=7.2, ha="center")
    arrow(ax, (0.32, cy), (0.475, cy), color=CUTOFF, lw=0.65, mutation_scale=6.0)

    arrow(ax, (0.33, 0.82 - dy), (0.33, 0.92 - dy), color=FORCING, lw=0.85)
    arrow(ax, (0.67, 0.82 - dy), (0.67, 0.92 - dy), color=FORCING, lw=0.85)
    arrow(ax, (0.33, 0.18 - dy), (0.33, 0.08 - dy), color=FORCING, lw=0.85)
    arrow(ax, (0.67, 0.18 - dy), (0.67, 0.08 - dy), color=FORCING, lw=0.85)
    ax.text(0.84, 0.875 - dy, "outer flow", color=FORCING, fontsize=7.0, ha="center", va="center", zorder=10)


def panel_contact_line(ax: plt.Axes) -> None:
    style_panel(ax, "(b)", "moving contact line")
    substrate_y = 0.22
    ax.plot([0.10, 0.90], [substrate_y, substrate_y], color=SOLID, lw=1.4, solid_capstyle="butt")
    label(ax, 0.15, 0.16, "solid", color=MUTED, fontsize=7.0, ha="center")

    verts = [
        (0.17, substrate_y),
        (0.17, 0.44),
        (0.27, 0.60),
        (0.40, 0.59),
        (0.55, 0.55),
        (0.68, 0.35),
        (0.75, substrate_y),
        (0.17, substrate_y),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=LIQUID, edgecolor=INK, lw=1.0, zorder=2))
    ax.add_patch(Circle((0.75, substrate_y), 0.015, facecolor=CUTOFF, edgecolor="white", lw=0.6, zorder=7))
    label(ax, 0.84, 0.28, r"$\ell_m$", color=CUTOFF, fontsize=8.0, ha="center")
    arrow(ax, (0.81, 0.265), (0.765, substrate_y + 0.015), color=CUTOFF, lw=0.6, mutation_scale=6.0)

    ax.add_patch(Arc((0.75, substrate_y), 0.24, 0.24, theta1=118, theta2=180, color=INK, lw=0.85, zorder=8))
    ax.text(0.585, 0.355, r"$\theta_{\text{app}}$", fontsize=8.0, ha="center", va="center", color=INK, zorder=10)
    arrow(ax, (0.68, 0.13), (0.83, 0.13), color=FORCING, lw=0.85)
    label(ax, 0.755, 0.075, r"$U$", color=FORCING, fontsize=8.0)
    double_arrow(ax, (0.22, 0.72), (0.74, 0.72), color=MUTED, lw=0.65, mutation_scale=6.5)
    label(ax, 0.48, 0.765, "outer scale", color=MUTED, fontsize=7.2)
    label(ax, 0.84, 0.55, "gas", color=MUTED, fontsize=7.0)


def panel_cusp(ax: plt.Axes) -> None:
    style_panel(ax, "(c)", "interfacial cusp")
    x = np.linspace(0.07, 0.93, 360)
    y = 0.76 - 0.39 * np.exp(-np.abs(x - 0.50) / 0.095)
    y += 0.016 * np.cos(2 * np.pi * (x - 0.07) / 0.86)
    liquid_domain = np.column_stack(
        [np.r_[x, x[-1], x[0]], np.r_[y, 0.08, 0.08]]
    )
    ax.add_patch(
        Polygon(liquid_domain, closed=True, facecolor=LIQUID, edgecolor="none", zorder=2)
    )
    ax.plot(x, y, color=INK, lw=1.0, zorder=4)
    tip_y = float(y.min())
    ax.add_patch(Circle((0.50, tip_y), 0.018, facecolor=CUTOFF, edgecolor="white", lw=0.6, zorder=7))
    ax.text(0.705, 0.312, "tip core", color=CUTOFF, fontsize=7.2, ha="center", va="center", zorder=10)
    arrow(ax, (0.640, 0.345), (0.52, tip_y - 0.003), color=CUTOFF, lw=0.65, mutation_scale=6.0)

    curved_arrow(ax, (0.18, 0.62), (0.36, 0.43), rad=-0.32, color=FORCING, lw=1.0, mutation_scale=9.0)
    curved_arrow(ax, (0.82, 0.62), (0.64, 0.43), rad=0.32, color=FORCING, lw=1.0, mutation_scale=9.0)
    ax.text(0.200, 0.665, "imposed\nflow", color=FORCING, fontsize=6.8, ha="center", va="center", linespacing=0.9, zorder=10)
    ax.text(0.800, 0.665, "imposed\nflow", color=FORCING, fontsize=6.8, ha="center", va="center", linespacing=0.9, zorder=10)
    ax.add_patch(Arc((0.50, tip_y), 0.17, 0.11, theta1=25, theta2=155, color=INK, lw=0.8))
    ax.text(0.235, 0.340, "large\ncurvature", color=INK, fontsize=7.0, ha="center", va="center", linespacing=0.9, zorder=10)
    arrow(ax, (0.320, 0.338), (0.445, tip_y + 0.015), color=INK, lw=0.6, mutation_scale=5.5)


def draw_wrinkled_sheet_ridge(ax: plt.Axes, cx: float, cy: float) -> None:
    sheet = Polygon(
        [
            (cx - 0.23, cy - 0.12),
            (cx - 0.18, cy + 0.13),
            (cx + 0.22, cy + 0.11),
            (cx + 0.18, cy - 0.13),
        ],
        closed=True,
        facecolor=LIQUID_LIGHT,
        edgecolor=INK,
        lw=0.75,
        zorder=2,
    )
    ax.add_patch(sheet)

    local_x = np.linspace(-0.17, 0.17, 90)
    for j, local_y in enumerate(np.linspace(-0.075, 0.075, 6)):
        phase = 0.55 * j
        wrinkle_y = cy + local_y + 0.012 * np.sin(7.5 * np.pi * (local_x + 0.17) + phase)
        wrinkle_x = cx + local_x
        ax.plot(wrinkle_x, wrinkle_y, color=LIQUID_DARK, lw=0.45, alpha=0.70, zorder=3)

    ridge_x = np.array([cx - 0.035, cx - 0.012, cx + 0.018, cx + 0.045])
    ridge_y = np.array([cy + 0.115, cy + 0.035, cy - 0.045, cy - 0.125])
    ax.plot(ridge_x, ridge_y, color=LIQUID_DARK, lw=1.55, solid_capstyle="round", zorder=4)
    ax.add_patch(Circle((cx + 0.01, cy - 0.02), 0.014, facecolor=CUTOFF, edgecolor="white", lw=0.5, zorder=7))


def draw_nematic_defect(ax: plt.Axes, cx: float, cy: float) -> None:
    grid = np.linspace(-0.16, 0.16, 7)
    for dx in grid:
        for dy in grid:
            r = float(np.hypot(dx, dy))
            if r < 0.045 or r > 0.185:
                continue
            angle = 0.5 * np.arctan2(dy, dx)
            length = 0.030
            x0 = cx + dx - length * np.cos(angle)
            y0 = cy + dy - length * np.sin(angle)
            x1 = cx + dx + length * np.cos(angle)
            y1 = cy + dy + length * np.sin(angle)
            ax.plot([x0, x1], [y0, y1], color=INK, lw=0.75, alpha=0.86, solid_capstyle="round")
    ax.add_patch(Circle((cx, cy), 0.024, facecolor=CUTOFF, edgecolor="white", lw=0.6, zorder=7))


def panel_broader_soft_matter(ax: plt.Axes) -> None:
    style_panel(ax, "(d)", "beyond interfaces")
    draw_wrinkled_sheet_ridge(ax, 0.30, 0.55)
    draw_nematic_defect(ax, 0.74, 0.55)

    ax.plot([0.52, 0.52], [0.27, 0.78], color=FRAME, lw=0.55, ls=(0, (2, 3)), zorder=1)

    arrow(ax, (0.11, 0.77), (0.20, 0.70), color=FORCING, lw=0.8, mutation_scale=7.0)
    arrow(ax, (0.49, 0.77), (0.40, 0.70), color=FORCING, lw=0.8, mutation_scale=7.0)
    label(ax, 0.30, 0.805, "compression", color=FORCING, fontsize=7.1)

    label(ax, 0.30, 0.275, "wrinkle/ridge", fontsize=7.0)
    label(ax, 0.30, 0.175, "stress focusing", color=MUTED, fontsize=6.8)
    arrow(ax, (0.36, 0.305), (0.315, 0.55), color=LIQUID_DARK, lw=0.6, mutation_scale=5.7)

    label(ax, 0.74, 0.275, "defect core", color=CUTOFF, fontsize=7.0)
    label(ax, 0.74, 0.175, "topological cutoff", color=MUTED, fontsize=6.8)
    arrow(ax, (0.74, 0.305), (0.74, 0.522), color=CUTOFF, lw=0.6, mutation_scale=5.7)


def build_figure(use_tex: bool = True) -> plt.Figure:
    configure_matplotlib(use_tex=use_tex)
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH),
        constrained_layout=False,
    )
    plt.subplots_adjust(left=0.025, right=0.985, bottom=0.045, top=0.97, wspace=0.075, hspace=0.11)

    panel_pinch_off(axes[0, 0])
    panel_contact_line(axes[0, 1])
    panel_cusp(axes[1, 0])
    panel_broader_soft_matter(axes[1, 1])

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
        here / "fig1_visual_dictionary.pdf",
        here / "fig1_visual_dictionary.png",
    )


if __name__ == "__main__":
    main()
