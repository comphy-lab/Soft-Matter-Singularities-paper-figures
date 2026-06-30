#!/usr/bin/env python3
"""Generate Figure 4: drop vs bubble pinch-off, Newtonian vs elastic.

Three rows:
  Row 1  Newtonian drop (Oh=1e-2, c1024-in)    | Newtonian bubble (Oh=1e-2, c1030-out)
  Row 2  Elastic drop (Oh=1, Ec=0.1, c1032-in) | Elastic bubble (c1031/c1033-out)
  Row 3  Scaling-race schematics: drop (strong amplification, arrest)
                                  bubble (weak amplification, no arrest)

Rows 1-2 are strips of mirror cross-section snapshot panels in the Figure-3 style
(dissipation log10(Phi) on the left half, speed |u| on the right half). Those tight
panels are rendered separately by figures/fig4_drop_bubble/render_panel.py and read
here from figures/fig4_drop_bubble/<case>/panels via each case manifest.csv. When a
case has not been rendered yet, a labelled placeholder is drawn so the layout and the
finished Row 3 still compile.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

VEL_CMAP = "Blues"
VEL_VMIN = 0.0
DROP_VMAX = 3.0     # drop rows: |u| in [0, 3]
BUBBLE_VMAX = 10.0  # bubble rows: |u| in [0, 10]

WIDTH_MM = 135.0
# Trimmed from 162 so the figure's float box clears the top-fraction limit and
# sits at a page top with text below, rather than on a standalone float page.
HEIGHT_MM = 148.0
MM_TO_INCH = 1.0 / 25.4

HERE = Path(__file__).resolve().parent
PANEL_ROOT = HERE / "fig4_drop_bubble"

# Palette (shared with the rest of the figure set).
LIQUID = "#58B7E6"
INK = "#171717"
MUTED = "#6A6A6A"
FRAME = "#B9B9B9"
FORCING = "#C95F2D"   # capillary driving (drop)
SIMILARITY = "#2F6FA3"  # inertial driving (bubble)
CUTOFF = "#2F7D59"    # arrest marker
MEMORY = "#8C5A9E"    # elastic / polymer stress

# Font sizes (native pt). The figure is drawn 135 mm wide and printed at
# textwidth=34pc~143 mm, a ~1.06x upscale, so native ~8.5 pt prints ~9 pt and
# matches the 8 pt caption. These are deliberately larger than the old panel.
FS_PANEL = 11.0       # (e)/(f) bold panel letters
FS_TITLE = 9.5        # panel sub-title
FS_AXIS = 9.0         # axis labels
FS_CURVE = 9.0        # curve labels
FS_TICK = 8.0         # tick labels
FS_INSET = 8.5        # scaling-law inset box (one line; sized to fit the panel)
FS_NOTE = 8.5         # short annotations

LABEL_BOX = {"facecolor": "white", "edgecolor": "none", "pad": 0.4, "alpha": 0.95}


def configure_matplotlib(use_tex: bool = True) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": FS_AXIS,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "text.usetex": use_tex,
        }
    )
    if use_tex:
        matplotlib.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
    else:
        matplotlib.rcParams["mathtext.fontset"] = "cm"


def arrow(ax, xy0, xy1, color=INK, lw=0.8, style="-|>", mutation_scale=8.0, zorder=6):
    ax.add_patch(
        FancyArrowPatch(
            xy0, xy1, arrowstyle=style, mutation_scale=mutation_scale,
            lw=lw, color=color, shrinkA=0, shrinkB=0, zorder=zorder,
        )
    )


# --------------------------------------------------------------------------- #
# Row 3 : scaling-race schematics
# --------------------------------------------------------------------------- #
def _race_frame(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("white")
    # interior plotting window in axes coords
    return 0.155, 0.90, 0.165, 0.88


def _panel_letter(ax, letter, title):
    ax.text(0.02, 0.99, letter, transform=ax.transAxes, fontsize=FS_PANEL,
            fontweight="bold", color=INK, va="top", ha="left", zorder=12)
    ax.text(0.135, 0.985, title, transform=ax.transAxes, fontsize=FS_TITLE,
            color=INK, va="top", ha="left", zorder=12)


def _xticks(ax, x0, x1, y0):
    labels = ["$1$", "$10$", "$10^2$", "$10^3$"]
    for i, lab in enumerate(labels):
        xi = x0 + (i / 3.0) * (x1 - x0)
        ax.plot([xi, xi], [y0, y0 - 0.018], color=INK, lw=0.6, zorder=5)
        ax.text(xi, y0 - 0.03, lab, fontsize=FS_TICK, color=INK,
                ha="center", va="top", zorder=7)


def _axes_arrows(ax, x0, x1, y0, y1):
    arrow(ax, (x0, y0), (x1 + 0.03, y0), color=INK, lw=0.7, mutation_scale=7.0, zorder=5)
    arrow(ax, (x0, y0), (x0, y1 + 0.03), color=INK, lw=0.7, mutation_scale=7.0, zorder=5)


def _map(logr, slope, intercept):
    return slope * logr + intercept


def panel_drop_race(ax):
    """(e) drop: diverging slopes -> capillary is overtaken -> elastic arrest."""
    x0, x1, y0, y1 = _race_frame(ax)
    _panel_letter(ax, r"\textbf{(c)}", "drop: strong amplification")

    logr = np.linspace(0, 3, 400)
    forcing = _map(logr, 1.0, 0.30)    # capillary gamma/h  ~ (h0/h)^1
    elastic = _map(logr, 4.0, -3.6)    # sigma_zz ~ G (h0/h)^4
    lo = min(forcing.min(), elastic.min())
    hi = max(forcing.max(), elastic.max())

    def to_xy(arr):
        yn = y0 + (arr - lo) / (hi - lo) * (y1 - y0)
        xn = x0 + logr / 3.0 * (x1 - x0)
        return xn, yn

    fx, fy = to_xy(forcing)
    ex, ey = to_xy(elastic)
    vis = (fy <= y1) & (ey <= y1)

    # crossing
    d = elastic - forcing
    ic = int(np.where(np.diff(np.sign(d)))[0][0])
    xc = x0 + logr[ic] / 3.0 * (x1 - x0)
    yc = y0 + (forcing[ic] - lo) / (hi - lo) * (y1 - y0)

    ax.plot(fx[vis], fy[vis], color=FORCING, lw=1.6, ls="--", zorder=4)
    ax.plot(ex[vis], ey[vis], color=MEMORY, lw=1.8, zorder=5)

    # arrest marker
    ax.plot([xc, xc], [y0, yc], color=CUTOFF, lw=1.0, ls=":", zorder=4)
    ax.text(xc - 0.045, yc + 0.075, "arrest", fontsize=FS_NOTE, color=CUTOFF,
            ha="center", va="bottom", zorder=8)
    # arrow from the "arrest" label to the intersection (the arrest point)
    arrow(ax, (xc - 0.030, yc + 0.066), (xc - 0.004, yc + 0.008),
          color=CUTOFF, lw=0.7, mutation_scale=6.0, zorder=8)

    # curve labels in clear regions
    ax.text(x0 + 0.87 * (x1 - x0), y0 + 0.86 * (y1 - y0),
            r"$\sigma_{zz}\sim G(h_0/h)^4$", fontsize=FS_CURVE, color=MEMORY,
            ha="right", va="bottom", zorder=8, bbox=LABEL_BOX)
    ax.text(x1 - 0.01, y0 + 0.50 * (y1 - y0), r"$\gamma/h_{\min}$",
            fontsize=FS_CURVE, color=FORCING, ha="right", va="center",
            zorder=8, bbox=LABEL_BOX)

    # axis labels
    ax.text((x0 + x1) / 2, y0 - 0.085, r"thinning ratio $h_0/h$",
            fontsize=FS_AXIS, color=INK, ha="center", va="top", zorder=7)
    ax.text(x0 - 0.075, (y0 + y1) / 2, "stress", fontsize=FS_AXIS, color=MUTED,
            ha="center", va="center", rotation=90, zorder=7)

    _xticks(ax, x0, x1, y0)
    _axes_arrows(ax, x0, x1, y0, y1)

    ax.text(0.90, 0.255, r"$h_{\min}\sim h_0\,(Gh_0/\gamma)^{1/3}$",
            transform=ax.transAxes, fontsize=FS_INSET, color=INK,
            ha="right", va="bottom",
            bbox={"facecolor": "white", "edgecolor": FRAME, "lw": 0.6,
                  "boxstyle": "round,pad=0.3"}, zorder=9)


def panel_bubble_race(ax):
    """(f) bubble: parallel slopes -> memory stays subdominant -> no arrest."""
    x0, x1, y0, y1 = _race_frame(ax)
    _panel_letter(ax, r"\textbf{(f)}", "bubble: weak amplification")

    logr = np.linspace(0, 3, 400)
    forcing = _map(logr, 2.0, 0.55)    # inertia rho hdot^2 ~ (h0/h)^2
    elastic = _map(logr, 2.0, -0.95)   # sigma_rr ~ G (h0/h)^2 (parallel, below)
    lo = min(forcing.min(), elastic.min())
    hi = max(forcing.max(), elastic.max())

    def to_xy(arr):
        yn = y0 + (arr - lo) / (hi - lo) * (y1 - y0)
        xn = x0 + logr / 3.0 * (x1 - x0)
        return xn, yn

    fx, fy = to_xy(forcing)
    ex, ey = to_xy(elastic)
    vis = (fy <= y1) & (ey <= y1)

    ax.plot(fx[vis], fy[vis], color=SIMILARITY, lw=1.6, ls="--", zorder=4)
    ax.plot(ex[vis], ey[vis], color=MEMORY, lw=1.8, zorder=5)

    # fixed gap between parallel lines -> double arrow + label (kept clear of arrow)
    gfrac = 0.60
    xg = x0 + gfrac * (x1 - x0)
    ig = int(round(gfrac * (len(logr) - 1)))
    yg_f = y0 + (forcing[ig] - lo) / (hi - lo) * (y1 - y0)
    yg_e = y0 + (elastic[ig] - lo) / (hi - lo) * (y1 - y0)
    arrow(ax, (xg, yg_e), (xg, yg_f), color=CUTOFF, lw=0.8, style="<->",
          mutation_scale=5.5, zorder=7)
    ax.text(xg + 0.05, (yg_e + yg_f) / 2, "fixed\nratio", fontsize=FS_NOTE,
            color=CUTOFF, ha="left", va="center", linespacing=1.1, zorder=8,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3, "alpha": 0.95})

    # curve labels
    ax.text(x0 + 0.87 * (x1 - x0), y0 + 0.91 * (y1 - y0), r"$\rho\,\dot{h}^2$",
            fontsize=FS_CURVE, color=SIMILARITY, ha="right", va="bottom",
            zorder=8, bbox=LABEL_BOX)
    ax.text(x0 + 0.36 * (x1 - x0), y0 + 0.31 * (y1 - y0),
            r"$\sigma_{rr}\sim G(h_0/h)^2$", fontsize=FS_CURVE, color=MEMORY,
            ha="left", va="top", zorder=8, bbox=LABEL_BOX)

    # "no arrest" note in the empty upper-left wedge
    ax.text(x0 + 0.015, y1 - 0.01, "no arrest:\nmemory stays\nsubdominant",
            fontsize=FS_NOTE, color=INK, ha="left", va="top", linespacing=1.15,
            zorder=8)

    ax.text((x0 + x1) / 2, y0 - 0.085, r"collapse ratio $h_0/h$",
            fontsize=FS_AXIS, color=INK, ha="center", va="top", zorder=7)
    ax.text(x0 - 0.075, (y0 + y1) / 2, "stress", fontsize=FS_AXIS, color=MUTED,
            ha="center", va="center", rotation=90, zorder=7)

    _xticks(ax, x0, x1, y0)
    _axes_arrows(ax, x0, x1, y0, y1)

    ax.text(0.90, 0.215, r"$h_{\min}\sim h_0\,(t_0-t)^{1/2}$",
            transform=ax.transAxes, fontsize=FS_INSET, color=INK,
            ha="right", va="bottom",
            bbox={"facecolor": "white", "edgecolor": FRAME, "lw": 0.6,
                  "boxstyle": "round,pad=0.3"}, zorder=9)


# --------------------------------------------------------------------------- #
# Rows 1-2 : snapshot strips (placeholder-aware)
# --------------------------------------------------------------------------- #
def load_case_panels(case: str) -> list[dict[str, str]]:
    manifest = PANEL_ROOT / case / "manifest.csv"
    if not manifest.exists():
        return []
    with manifest.open() as f:
        rows = list(csv.DictReader(f))
    # Full-domain framing makes every frame informative (the t=0 baseline now shows
    # the intact object), so keep all frames.
    return rows


def frame_title(row: dict, mode: str) -> str:
    """Per-frame time label. mode='frac' -> t/t0, with the last pre/post-pinch
    frames labelled t0^- / t0^+ via the manifest label; mode='time' -> absolute t."""
    if mode == "time":
        try:
            t = float(row.get("snapshot_time") or row.get("target_time") or 0.0)
        except ValueError:
            return ""
        return rf"$t={t:.0f}$"
    lab = (row.get("label") or "").strip().lower()
    frac = (row.get("fraction") or "").strip()
    if lab in ("t0_minus", "t0minus"):
        return r"$t_0^{-}$"
    if lab in ("t0_plus", "t0plus", "near_t0"):
        return r"$t_0^{+}$"
    if not frac:
        return ""
    try:
        f = float(frac)
    except ValueError:
        return ""
    if f == 0:
        return r"$0$"
    return rf"${f:g}\,t_0$"


def draw_strip(fig, cell, case: str, letter: str, title: str, use_tex: bool,
               label_mode: str = "frac") -> list:
    """Draw one column: a horizontal strip of mirror panels, or a placeholder.

    Returns the (vector_pdf, AxesImage) pairs for the snapshot panels so the
    composite can stamp vector interfaces over their raster footprints."""
    rows = load_case_panels(case)
    if not rows:
        ax = fig.add_subplot(cell)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.02, 0.06), 0.96, 0.82,
                                    boxstyle="round,pad=0.01",
                                    facecolor="#F4F4F4", edgecolor=FRAME, lw=0.7))
        ax.text(0.02, 0.99, letter, transform=ax.transAxes, fontsize=FS_PANEL,
                fontweight="bold", color=INK, va="top", ha="left")
        ax.text(0.135, 0.985, title, transform=ax.transAxes, fontsize=FS_TITLE,
                color=INK, va="top", ha="left")
        ax.text(0.5, 0.46, f"{case}\nframes rendering", transform=ax.transAxes,
                fontsize=FS_NOTE, color=MUTED, ha="center", va="center",
                linespacing=1.3)
        return []

    n = len(rows)
    sub = cell.subgridspec(1, n, wspace=0.04)
    axes = []
    panels: list[tuple[Path, object]] = []
    for j, row in enumerate(rows):
        ax = fig.add_subplot(sub[0, j])
        png = Path(row.get("png", ""))
        if not png.exists():
            png = PANEL_ROOT / case / "panels" / png.name
        if png.exists():
            # imshow fixes the layout; the vector PDF sibling is stamped over
            # this footprint later so the interface stays vector on zoom.
            im = ax.imshow(plt.imread(png))
            panels.append((png.with_suffix(".pdf"), im))
        ax.axis("off")
        ttl = frame_title(row, label_mode)
        if ttl:
            ax.set_title(ttl, fontsize=FS_TICK, pad=2.5)
        axes.append(ax)
    fig.canvas.draw()
    pos0 = axes[0].get_position()
    title_y = pos0.y1 + 0.034
    fig.text(pos0.x0 - 0.006, title_y, letter, ha="left", va="bottom",
             fontsize=FS_PANEL, fontweight="bold", color=INK)
    fig.text(pos0.x0 + 0.046, title_y, title, ha="left", va="bottom",
             fontsize=FS_TITLE, color=INK)
    return panels


# --------------------------------------------------------------------------- #
# Composite
# --------------------------------------------------------------------------- #
def build_figure(use_tex: bool = True, row3_only: bool = False) -> tuple[plt.Figure, list]:
    configure_matplotlib(use_tex)
    if row3_only:
        fig, axes = plt.subplots(1, 2, figsize=(WIDTH_MM * MM_TO_INCH,
                                                0.46 * WIDTH_MM * MM_TO_INCH))
        fig.subplots_adjust(left=0.02, right=0.99, bottom=0.04, top=0.99, wspace=0.12)
        panel_drop_race(axes[0])
        panel_bubble_race(axes[1])
        return fig, []

    fig = plt.figure(figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH))
    gs = GridSpec(4, 1, figure=fig, height_ratios=[1.0, 1.0, 0.12, 1.5],
                  hspace=0.36, left=0.02, right=0.985, bottom=0.05, top=0.955)

    vector_panels: list = []
    row1 = gs[0, 0].subgridspec(1, 2, wspace=0.06)
    vector_panels += draw_strip(fig, row1[0, 0], "c1024-in", r"\textbf{(a)}", "Newtonian drop", use_tex, "frac")
    vector_panels += draw_strip(fig, row1[0, 1], "c1030-out", r"\textbf{(d)}", "Newtonian bubble", use_tex, "frac")

    row2 = gs[1, 0].subgridspec(1, 2, wspace=0.06)
    vector_panels += draw_strip(fig, row2[0, 0], "c1032-in", r"\textbf{(b)}", "Elastic drop", use_tex, "time")
    vector_panels += draw_strip(fig, row2[0, 1], "c1031-c1033-out", r"\textbf{(e)}", "Elastic bubble", use_tex, "frac")

    # Two velocity colourbars: drops [0,3] under the left column, bubbles [0,10] under the right.
    cbar_row = gs[2, 0].subgridspec(1, 2, wspace=0.10)
    cax_d = fig.add_subplot(cbar_row[0, 0])
    cb_d = fig.colorbar(ScalarMappable(norm=Normalize(VEL_VMIN, DROP_VMAX), cmap=VEL_CMAP),
                        cax=cax_d, orientation="horizontal", ticks=[0, 1, 2, 3])
    cb_d.set_label(r"drops: $|\boldsymbol{u}|$", fontsize=FS_TICK, labelpad=1.5)
    cax_b = fig.add_subplot(cbar_row[0, 1])
    cb_b = fig.colorbar(ScalarMappable(norm=Normalize(VEL_VMIN, BUBBLE_VMAX), cmap=VEL_CMAP),
                        cax=cax_b, orientation="horizontal", ticks=[0, 2, 4, 6, 8, 10])
    cb_b.set_label(r"bubbles: $|\boldsymbol{u}|$", fontsize=FS_TICK, labelpad=1.5)
    for cb in (cb_d, cb_b):
        cb.ax.tick_params(labelsize=FS_TICK - 0.5, length=2.0, width=0.5, pad=1.0)
        cb.outline.set_linewidth(0.5)
    fig.canvas.draw()
    for cax in (cax_d, cax_b):
        p = cax.get_position()
        cax.set_position([p.x0 + 0.16 * p.width, p.y0 + 0.52 * p.height,
                          0.68 * p.width, 0.30 * p.height])

    row3 = gs[3, 0].subgridspec(1, 2, wspace=0.16)
    panel_drop_race(fig.add_subplot(row3[0, 0]))
    panel_bubble_race(fig.add_subplot(row3[0, 1]))
    return fig, vector_panels


def save_with_fallback(out_pdf: Path, out_png: Path, row3_only: bool = False) -> None:
    try:
        fig, vector_panels = build_figure(use_tex=True, row3_only=row3_only)
    except RuntimeError as exc:
        print(f"LaTeX unavailable ({exc}); retrying with mathtext.")
        plt.close("all")
        fig, vector_panels = build_figure(use_tex=False, row3_only=row3_only)
    from pdf_vector_stamp import save_vector_composite

    # pad_in=0.1 reproduces the previous bbox_inches="tight" default padding.
    save_vector_composite(fig, out_pdf, out_png, vector_panels, pad_in=0.1)
    plt.close(fig)


def main() -> None:
    import sys
    base = HERE
    if "--inspect-row3" in sys.argv:
        save_with_fallback(base / "fig4_row3_preview.pdf",
                           base / "fig4_row3_preview.png", row3_only=True)
        return
    save_with_fallback(base / "fig4_drop_bubble.pdf",
                       base / "fig4_drop_bubble.png")


if __name__ == "__main__":
    main()
