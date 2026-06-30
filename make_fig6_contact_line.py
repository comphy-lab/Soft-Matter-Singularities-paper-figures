#!/usr/bin/env python3
"""Generate Figure 6: moving contact-line singularity and slip regularisation."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Arc, Circle, FancyArrowPatch, Polygon
from matplotlib.ticker import FuncFormatter, FixedLocator, LogLocator, NullFormatter

WIDTH_MM = 170.0
HEIGHT_MM = 99.0
MM_TO_INCH = 1.0 / 25.4
SCHEMATIC_SCALE = 1.13

CA = 0.01
X_MIN = 1.0e-3
X_MAX = 1.0e5
SLIP_LENGTH = 1.0

INK = "#161616"
MUTED = "#686868"
GRID = "#D4D4D4"
LIQUID = "#6DBBE7"
LIQUID_EDGE = "#176C98"
SOLID = "#777777"
DRIVE = "#C95D2B"
SLIP = "#2B7C59"
ANGLE = "#0F6FA7"
CURVATURE = "#C7322B"
THEORY = "#111111"
GAS = "#FFFFFF"


def configure_matplotlib(use_tex: bool) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 7.8,
            "axes.linewidth": 0.62,
            "axes.labelsize": 7.8,
            "xtick.labelsize": 6.8,
            "ytick.labelsize": 6.8,
            "legend.fontsize": 6.5,
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


def cumulative_trapezoid(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    out = np.zeros_like(y)
    out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out


def contact_line_data() -> dict[str, np.ndarray]:
    """Integrate the Voinov-limit angle equation on a log-spaced grid.

    Cox-Voinov gives d(theta^3)/d(ln X) = 9 Ca for the no-slip wedge, so the
    interface curvature is kappa = dtheta/dX = 3 Ca / (X theta^2). The slip
    cutoff multiplies the forcing by X/(X+ell_s)."""
    x = np.geomspace(X_MIN, X_MAX, 1800)
    logx = np.log(x)

    rhs_no_slip = np.full_like(x, 9.0 * CA)
    theta3_start = 1.0 + 9.0 * CA * np.log(np.e * X_MIN)
    theta3_no_slip = theta3_start + cumulative_trapezoid(rhs_no_slip, logx)
    theta_no_slip = theta3_no_slip ** (1.0 / 3.0)
    kappa_no_slip = 3.0 * CA / (x * theta_no_slip**2)

    rhs_slip = 9.0 * CA * x / (x + SLIP_LENGTH)
    theta3_slip = 1.0 + cumulative_trapezoid(rhs_slip, logx)
    theta_slip = theta3_slip ** (1.0 / 3.0)
    kappa_slip = 3.0 * CA / ((x + SLIP_LENGTH) * theta_slip**2)

    x_theory = np.geomspace(1.0, X_MAX, 600)
    theta3_theory_no_slip = 1.0 + 9.0 * CA * np.log(np.e * x_theory)
    theta_theory_no_slip = theta3_theory_no_slip ** (1.0 / 3.0)
    kappa_theory_no_slip = 3.0 * CA / (x_theory * theta_theory_no_slip**2)

    theta3_base = 1.0 + 9.0 * CA * np.log(np.e * x_theory)
    offset = theta3_slip[-1] - (1.0 + 9.0 * CA * np.log(np.e * X_MAX))
    theta3_theory_slip = theta3_base + offset
    theta_theory_slip = theta3_theory_slip ** (1.0 / 3.0)
    kappa_theory_slip = 3.0 * CA / (x_theory * theta_theory_slip**2)

    return {
        "x": x,
        "theta3_no_slip": theta3_no_slip,
        "kappa_no_slip": kappa_no_slip,
        "theta3_slip": theta3_slip,
        "kappa_slip": kappa_slip,
        "x_theory": x_theory,
        "theta3_theory_no_slip": theta3_theory_no_slip,
        "kappa_theory_no_slip": kappa_theory_no_slip,
        "theta3_theory_slip": theta3_theory_slip,
        "kappa_theory_slip": kappa_theory_slip,
    }


def panel_label(ax, label: str) -> None:
    ax.text(
        0.015,
        0.975,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.6,
        fontweight="bold",
        color=INK,
        bbox=dict(boxstyle="round,pad=0.14", facecolor=GAS, edgecolor="none", alpha=0.82),
        zorder=20,
    )


def arrow(ax, start, end, color=INK, lw=0.8, ms=8.0, zorder=6) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=ms,
            lw=lw,
            color=color,
            zorder=zorder,
        )
    )


def double_arrow(ax, start, end, color=INK, lw=0.7, ms=7.0, zorder=6) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="<->",
            mutation_scale=ms,
            lw=lw,
            color=color,
            zorder=zorder,
        )
    )


def setup_schematic(ax) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_schematic(ax, regularised: bool) -> None:
    setup_schematic(ax)
    panel_label(ax, "(a)" if not regularised else "(d)")

    y_wall = 0.22
    x0 = 0.16
    s = SCHEMATIC_SCALE
    ax.plot([0.045, 0.97], [y_wall, y_wall], color=SOLID, lw=2.05, solid_capstyle="round")

    if regularised:
        xs = np.linspace(0.0, 0.62, 180)
        ys = y_wall + s * (0.045 * (1.0 - np.exp(-xs / 0.095)) + 0.45 * xs)
        poly = [(x0, y_wall), *[(x0 + s * x, y) for x, y in zip(xs, ys)], (x0 + s * xs[-1], y_wall)]
        contact_angle = 32.0
    else:
        interface_tip = (x0 + s * 0.59, y_wall + s * 0.32)
        poly = [(x0, y_wall), (interface_tip[0], y_wall), interface_tip]
        contact_angle = np.degrees(np.arctan2(interface_tip[1] - y_wall, interface_tip[0] - x0))

    ax.add_patch(
        Polygon(poly, closed=True, facecolor=LIQUID, edgecolor=LIQUID_EDGE, lw=0.85, alpha=0.92)
    )

    dot_color = SLIP if regularised else INK
    ax.plot([x0], [y_wall], "o", color=dot_color, ms=3.4, zorder=8)
    ax.add_patch(Arc((x0, y_wall), 0.23 * s, 0.23 * s, theta1=0, theta2=contact_angle, color=INK, lw=0.76))
    if regularised:
        ax.text(x0 + s * 0.145, y_wall + s * 0.035, r"$\theta$", color=INK, ha="left", va="bottom")
    else:
        ax.text(x0 + s * 0.15, y_wall + s * 0.145, r"$\theta$", color=INK, ha="center", va="center")

    arrow(ax, (0.10, 0.085), (0.45, 0.085), color=DRIVE, lw=1.0, ms=9.1)
    ax.text(0.49, 0.085, r"$U$", color=DRIVE, va="center", ha="left")

    if regularised:
        ax.add_patch(Circle((x0, y_wall), 0.087 * s, facecolor=SLIP, edgecolor="none", alpha=0.16))
        double_arrow(ax, (x0 - s * 0.075, y_wall + s * 0.13), (x0 + s * 0.075, y_wall + s * 0.13), color=SLIP, lw=0.78)
        ax.text(x0, y_wall + s * 0.17, r"$\ell_s$", color=SLIP, ha="center", va="bottom")
        ax.text(0.58, 0.75, "slip cutoff", color=MUTED, ha="center", va="center")
        ax.text(0.58, 0.63, "finite inner\nmotion", color=MUTED, ha="center", va="center", linespacing=1.05)
    else:
        arrow(ax, (x0, y_wall), (x0 + s * 0.39, y_wall + s * 0.065), color=MUTED, lw=0.68, ms=7.4)
        ax.text(x0 + s * 0.30, y_wall + s * 0.115, r"$r$", color=MUTED, ha="center", va="center")
        ax.text(0.58, 0.80, "no slip", color=MUTED, ha="center", va="center")
        ax.text(0.57, 0.68, "wedge stress\nkeeps growing", color=MUTED, ha="center", va="center", linespacing=1.05)


def style_log_axis(ax) -> None:
    ax.grid(True, which="major", color=GRID, lw=0.45, alpha=0.72)
    ax.grid(True, which="minor", color=GRID, lw=0.25, alpha=0.42)
    ax.tick_params(which="major", direction="out", width=0.72, length=3.6, pad=2.2)
    ax.tick_params(which="minor", direction="out", width=0.52, length=2.0)
    for spine in ax.spines.values():
        spine.set_linewidth(0.72)


def format_theta_axis(ax) -> None:
    ax.set_yscale("log")
    ticks = [0.5, 1.0, 1.5, 2.0]
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:g}"))
    ax.yaxis.set_minor_formatter(NullFormatter())


def plot_theta_panel(ax, data: dict[str, np.ndarray], regularised: bool) -> None:
    x = data["x"]
    key = "theta3_slip" if regularised else "theta3_no_slip"
    theory_key = "theta3_theory_slip" if regularised else "theta3_theory_no_slip"
    label = "(e)" if regularised else "(b)"

    panel_label(ax, label)
    ax.set_xscale("log")
    format_theta_axis(ax)
    ax.plot(x, data[key], color=ANGLE, lw=1.7, label="numerical")
    ax.plot(data["x_theory"], data[theory_key], color=THEORY, lw=1.15, ls=(0, (4, 2)), label="large-$X$ theory")
    ax.axvspan(X_MIN, SLIP_LENGTH, color=SLIP if regularised else MUTED, alpha=0.075, lw=0)
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(0.44 if not regularised else 0.95, 2.3)
    ax.set_ylabel(r"$\theta^3$")
    if regularised:
        ax.set_xlabel(r"$X/\ell_s$")
    else:
        ax.set_xlabel(r"$X$")
    ax.text(
        0.98,
        0.34,
        r"$Ca=0.01$",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color=MUTED,
        fontsize=6.8,
    )
    if regularised:
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(0.19, 0.995),
            frameon=True,
            framealpha=0.95,
            borderpad=0.32,
        )
    else:
        ax.legend(
            loc="lower right",
            bbox_to_anchor=(0.985, 0.08),
            frameon=True,
            framealpha=0.95,
            borderpad=0.32,
        )
    style_log_axis(ax)


def plot_curvature_panel(ax, data: dict[str, np.ndarray], regularised: bool) -> None:
    x = data["x"]
    key = "kappa_slip" if regularised else "kappa_no_slip"
    theory_key = "kappa_theory_slip" if regularised else "kappa_theory_no_slip"
    label = "(f)" if regularised else "(c)"

    panel_label(ax, label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.plot(x, data[key], color=CURVATURE, lw=1.7, label="numerical")
    ax.plot(data["x_theory"], data[theory_key], color=THEORY, lw=1.15, ls=(0, (4, 2)), label="large-$X$ theory")
    ax.axvspan(X_MIN, SLIP_LENGTH, color=SLIP if regularised else MUTED, alpha=0.075, lw=0)
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(1.0e-8, 1.0e2)
    ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=6))
    ax.set_ylabel(r"$|\kappa|$")
    if regularised:
        ax.set_xlabel(r"$X/\ell_s$")
    else:
        ax.set_xlabel(r"$X$")
    if regularised:
        label_x, label_y = 0.06, 0.86
        label_text = "finite cutoff"
    else:
        label_x, label_y = 0.09, 0.60
        label_text = "blows up\nas $X\\to0$"
    ax.text(
        label_x,
        label_y,
        label_text,
        transform=ax.transAxes,
        color=SLIP if regularised else CURVATURE,
        ha="left",
        va="top",
        fontsize=6.8,
    )
    ax.legend(loc="upper right", frameon=True, framealpha=0.95, borderpad=0.32)
    style_log_axis(ax)


def build_figure(use_tex: bool = True):
    data = contact_line_data()
    fig = plt.figure(figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH))
    fig.patch.set_facecolor(GAS)
    gs = GridSpec(
        2,
        3,
        figure=fig,
        width_ratios=[0.78, 1.30, 1.30],
        height_ratios=[1.0, 1.0],
        left=0.024,
        right=0.992,
        bottom=0.105,
        top=0.965,
        wspace=0.36,
        hspace=0.42,
    )

    axes = np.array([[fig.add_subplot(gs[i, j]) for j in range(3)] for i in range(2)])
    draw_schematic(axes[0, 0], regularised=False)
    plot_theta_panel(axes[0, 1], data, regularised=False)
    plot_curvature_panel(axes[0, 2], data, regularised=False)
    draw_schematic(axes[1, 0], regularised=True)
    plot_theta_panel(axes[1, 1], data, regularised=True)
    plot_curvature_panel(axes[1, 2], data, regularised=True)

    axes[0, 1].set_title("no-slip calculation", fontsize=7.8, pad=2.5)
    axes[1, 1].set_title("slip-regularised calculation", fontsize=7.8, pad=2.5)
    return fig


def save_with_fallback(out_pdf: Path, out_png: Path) -> None:
    try:
        configure_matplotlib(use_tex=True)
        fig = build_figure(use_tex=True)
    except Exception as exc:
        print(f"[warn] TeX render failed ({exc}); falling back to mathtext")
        plt.close("all")
        configure_matplotlib(use_tex=False)
        fig = build_figure(use_tex=False)

    fig.savefig(out_pdf, dpi=300)
    fig.savefig(out_png, dpi=240)
    plt.close(fig)
    print(f"Saved {out_pdf}")
    print(f"Saved {out_png}")


def main() -> None:
    here = Path(__file__).parent
    save_with_fallback(here / "fig6_contact_line.pdf", here / "fig6_contact_line.png")


if __name__ == "__main__":
    main()
