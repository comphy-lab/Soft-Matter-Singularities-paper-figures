#!/usr/bin/env python3
"""Generate Figure 5: sessile-drop coalescence as a constructive singularity.

Panels:
  (a) initiation: two spherical caps near contact on a substrate (schematic).
  (b) bridge time history h(x,t) from the clean lubrication simulation.
  (c) neck height collapsed by the similarity law: h0/(0.272 theta^4) vs t for
      several contact angles falls on the single line h0 = 0.272 theta^4 t.
  (d) self-similar collapse h/h0(t) vs theta x/h0(t): snapshots from several
      contact angles fall on one master shape -> loss of memory / universality.

The hydrodynamics are the clean (surfactant-free, beta=Pe=0) limit of the
sessile-drop lubrication model of Talukdar et al.; the early-time viscous
similarity law and the constant 0.272 are from Hernandez-Sanchez et al. (2012).

Data bundles (produced on the compute host by reduce_fig5.py) live in
  fig5_coalescence_data/fig5_data_theta{20,10,5,1}.npz
theta=20 is required for panels (a)/(b); the others are optional and are added
to panels (c)/(d) automatically when present.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from matplotlib.colors import Normalize, LogNorm, ListedColormap
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle, Arc

WIDTH_MM = 160.0
HEIGHT_MM = 132.0
MM_TO_INCH = 1.0 / 25.4

LIQUID = "#58B7E6"
LIQUID_DARK = "#156D9A"
SUBSTRATE = "#9A9A9A"
GAS = "#FFFFFF"
INK = "#171717"
MUTED = "#6A6A6A"
FRAME = "#B9B9B9"
FORCING = "#C95F2D"
CUTOFF = "#2F7D59"
THEORY = "#171717"

V_STAR = 0.272  # clean viscous coalescence constant (Hernandez-Sanchez 2012)
HP = 1e-4       # precursor-film thickness used in the simulations

# distinct hue + marker per contact angle, shared across panels (c) and (d).
# theta=10 is a warm blue and theta=5 a warm red so the two collapse sets in (c)
# read clearly against each other.
ANGLE_COLOR = {20: "#E08214", 10: "#1F6FA8", 5: "#C0392B", 3: "#1B9E77",
               2: "#7D3C98", 1: "#D81B7A"}
ANGLE_MARK = {20: "o", 10: "s", 5: "^", 3: "D", 2: "v", 1: "P"}
COLLAPSE_ANGLES = (10, 5)   # panel (c): two angles is enough to show universality
COLLAPSE_NCURVES = 8        # panel (c): overlay only this many times per angle
HISTORY_ANGLE = 10          # panel (b): bridge time sequence shown for this angle

SRC = Path(__file__).resolve().parent           # figures/fig5_coalescence_src/
FIGDIR = SRC.parent                              # figures/
DATA = FIGDIR / "fig5_coalescence_data"          # simulation data bundles
MASTER_CSV = SRC / "similarity_master.csv"       # theory curve (similarity_solution.py)

LABEL_BOX = {"facecolor": GAS, "edgecolor": "none", "pad": 0.4, "alpha": 0.95}


def configure_matplotlib(use_tex: bool = True) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 8.5,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.usetex": use_tex,
            # use an ASCII minus so usetex renders the sign (the unicode minus
            # U+2212 is dropped by LaTeX, which hides negative tick labels)
            "axes.unicode_minus": False,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
        }
    )
    if use_tex:
        matplotlib.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
    else:
        matplotlib.rcParams["mathtext.fontset"] = "cm"


def panel_label(ax: plt.Axes, label: str, title: str) -> None:
    ax.text(0.03, 0.965, label, transform=ax.transAxes, ha="left", va="top",
            fontsize=10, fontweight="bold", color=INK, bbox=LABEL_BOX, zorder=20)
    ax.text(0.135, 0.965, title, transform=ax.transAxes, ha="left", va="top",
            fontsize=8.5, color=INK, bbox=LABEL_BOX, zorder=20)


def style_data_axis(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_edgecolor(INK)
        spine.set_linewidth(0.8)
    ax.tick_params(labelsize=7.5, which="both", color=INK)


# --------------------------------------------------------------------------- #
# Panel (a): sessile initiation schematic
# --------------------------------------------------------------------------- #
def _cap(ax, x_c, a, theta_deg, base_y, **kw):
    th = np.deg2rad(theta_deg)
    R = a / np.sin(th)
    cy = base_y - R * np.cos(th)
    xs = np.linspace(x_c - a, x_c + a, 240)
    ys = cy + np.sqrt(np.clip(R * R - (xs - x_c) ** 2, 0, None))
    verts = np.column_stack([xs, ys])
    verts = np.vstack([verts, [x_c + a, base_y], [x_c - a, base_y]])
    poly = Polygon(verts, closed=True, **kw)
    ax.add_patch(poly)
    return poly


def panel_initiation(ax: plt.Axes) -> None:
    # crop the vertical extent so the schematic fills the panel instead of
    # floating in empty space; keep equal aspect so the drops stay circular.
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.56)
    ax.set_aspect("equal")
    ax.axis("off")
    panel_label(ax, "(a)", "initiation on a substrate")

    base_y = 0.13
    a = 0.235
    theta_d = 72.0
    gap = 0.010
    x_l = 0.5 - gap - a
    x_r = 0.5 + gap + a
    apex_y = base_y + a * (1 - np.cos(np.deg2rad(theta_d))) / np.sin(np.deg2rad(theta_d))

    ax.add_patch(Rectangle((0.0, 0.0), 1.0, base_y,
                           facecolor=SUBSTRATE, edgecolor="none", zorder=1))
    ax.text(0.5, base_y / 2, "substrate", ha="center", va="center", fontsize=7,
            color=GAS, zorder=2)

    capkw = dict(facecolor=LIQUID, edgecolor=LIQUID_DARK, linewidth=1.1, zorder=3)
    _cap(ax, x_l, a, theta_d, base_y, **capkw)
    cap_b = _cap(ax, x_r, a, theta_d, base_y, **capkw)

    # drop labels sit just above each apex
    ax.text(x_l, apex_y + 0.03, "drop A", ha="center", va="bottom",
            fontsize=7.5, color=MUTED, zorder=6)
    ax.text(x_r, apex_y + 0.03, "drop B", ha="center", va="bottom",
            fontsize=7.5, color=MUTED, zorder=6)

    # microscopic-contact marker with a short callout just above the neck
    ax.add_patch(plt.Circle((0.5, base_y + 0.010), 0.014, facecolor=CUTOFF,
                            edgecolor=GAS, linewidth=0.7, zorder=6))
    ax.annotate("microscopic contact", xy=(0.5, base_y + 0.024),
                xytext=(0.5, apex_y + 0.085), ha="center", va="bottom",
                fontsize=6.8, color=CUTOFF,
                arrowprops=dict(arrowstyle="-|>", color=CUTOFF, lw=0.8,
                                mutation_scale=7, shrinkA=1, shrinkB=2),
                bbox={"facecolor": GAS, "edgecolor": "none", "pad": 0.3,
                      "alpha": 0.9}, zorder=8)

    # contact-angle wedge on the inner side of the right drop; clip it to the
    # drop so the arc can never poke through the curved interface.
    xcl = 0.5 + gap
    arc = Arc((xcl, base_y), 0.12, 0.12, angle=0, theta1=0, theta2=theta_d,
              color=INK, lw=1.0, zorder=7)
    ax.add_patch(arc)
    arc.set_clip_path(cap_b)
    ax.text(xcl + 0.062, base_y + 0.040, r"$\theta$", fontsize=8.5, color=INK,
            ha="left", va="center", zorder=8,
            bbox={"facecolor": LIQUID, "edgecolor": "none", "pad": 0.1,
                  "alpha": 0.0})


# --------------------------------------------------------------------------- #
# Panel (b): bridge time history (single representative angle)
# --------------------------------------------------------------------------- #
def panel_history(ax: plt.Axes, d) -> None:
    style_data_axis(ax)
    th = int(round(float(d["theta_deg"])))
    panel_label(ax, "(b)", rf"bridge growth ($\theta={th}^\circ$)")

    prof_t = d["prof_t"]
    prof_x = d["prof_x"]
    prof_h = d["prof_h"]
    norm = LogNorm(vmin=prof_t.min(), vmax=prof_t.max())
    cmap = cm.viridis
    xwin = 1.8
    hmax = 0.0
    for t, x, h in zip(prof_t, prof_x, prof_h):
        m = np.abs(x) <= xwin
        ax.plot(x[m], h[m], color=cmap(norm(t)), lw=1.3, zorder=3)
        hmax = max(hmax, float(h[m].max()))
    ax.set_xlim(-xwin, xwin)
    ax.set_ylim(0, 1.15 * hmax)
    ax.set_xlabel(r"$x/L$", fontsize=9, labelpad=1)
    ax.set_ylabel(r"$h/L$", fontsize=9, labelpad=1)

    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cb = ax.figure.colorbar(sm, ax=ax, pad=0.03, fraction=0.046)
    cb.set_ticks(list(prof_t))
    cb.set_ticklabels([f"{v:g}" for v in prof_t])
    cb.ax.tick_params(labelsize=6.5)
    cb.ax.minorticks_off()
    cb.ax.set_title(r"$t$", fontsize=9, pad=3)
    ax.annotate("growing neck", xy=(0.0, 0.16 * hmax), xytext=(0.60, 0.62),
                textcoords="axes fraction", ha="center", va="center",
                fontsize=6.8, color=INK,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7,
                                mutation_scale=6, shrinkA=1, shrinkB=3),
                bbox=LABEL_BOX, zorder=10)


# --------------------------------------------------------------------------- #
# Panel (d): self-similar collapse across contact angles
# --------------------------------------------------------------------------- #
def _draw_collapse(ax, bundles, lw_scale=1.0, theory_lw=1.4):
    """Plot the time-shaded collapse curves + theory onto ``ax``; return legend
    handles. Each contact angle gets one hue family (Blues for 10, Reds for 5),
    shaded dark -> light from early -> late (log-time), matching panel (b)."""
    CMAPS = {10: cm.Blues, 5: cm.Reds}
    angles = [a for a in sorted(COLLAPSE_ANGLES, reverse=True) if a in bundles]
    handles = []
    for k, th in enumerate(angles):
        d = bundles[th]
        cmap = CMAPS.get(th, cm.Greys)
        n = len(d["coll_t"])
        idx = np.unique(np.linspace(0, n - 1, min(n, COLLAPSE_NCURVES)).astype(int))
        tlog = np.log10(d["coll_t"][idx])
        span = tlog.max() - tlog.min()
        frac = (tlog - tlog.min()) / span if span > 0 else np.zeros_like(tlog)
        lw, ls = (2.0 * lw_scale, "-") if k == 0 else (1.5 * lw_scale, (0, (4, 2.2)))
        for j, i in enumerate(idx):
            cval = 1.0 - 0.72 * frac[j]             # darkest (early) -> lightest (late)
            ax.plot(d["coll_xi"][i], d["coll_H"][i], color=cmap(cval), lw=lw, ls=ls,
                    alpha=1.0, solid_capstyle="round", zorder=4 + k)
        handles.append(plt.Line2D([], [], color=cmap(0.8), lw=2.4 if k == 0 else 1.8,
                                  ls=ls, label=rf"$\theta={th}^\circ$"))
    if MASTER_CSV.exists():
        m = np.loadtxt(MASTER_CSV, delimiter=",")
        ax.plot(m[:, 0], m[:, 1], color=THEORY, lw=theory_lw, zorder=8)
        handles.append(plt.Line2D([], [], color=THEORY, lw=1.4, label="theory"))
    return handles


def _time_gradient_legend(ax, bundles):
    """Bottom-of-(d) key: one small horizontal colourbar per angle (Blues for
    10, Reds for 5) shaded dark->light = early->late and ticked with that
    angle's lowest and highest time, plus a theory-line entry."""
    CMAPS = {10: cm.Blues, 5: cm.Reds}
    angles = [a for a in sorted(COLLAPSE_ANGLES, reverse=True) if a in bundles]
    bx, bw, bh = 0.19, 0.20, 0.028
    ys = [0.13, 0.055]
    for th, y in zip(angles, ys):
        d = bundles[th]
        tmin, tmax = float(d["coll_t"].min()), float(d["coll_t"].max())
        # darkest (early) -> lightest (late): full-contrast hue family
        tc = ListedColormap(CMAPS.get(th, cm.Greys)(np.linspace(1.0, 0.28, 256)))
        cax = ax.inset_axes([bx, y, bw, bh])
        sm = cm.ScalarMappable(norm=LogNorm(tmin, tmax), cmap=tc)
        sm.set_array([])
        cb = ax.figure.colorbar(sm, cax=cax, orientation="horizontal")
        cb.set_ticks([tmin, tmax])
        cb.set_ticklabels([f"{tmin:.0f}" if tmax >= 10 else f"{tmin:g}", f"{tmax:.0f}"])
        cb.minorticks_off()
        cb.ax.tick_params(labelsize=6, length=2, pad=1.2, color=MUTED)
        cb.outline.set_edgecolor(MUTED)
        cb.outline.set_linewidth(0.5)
        ax.text(bx - 0.015, y + bh / 2, rf"$\theta={th}^\circ$", transform=ax.transAxes,
                ha="right", va="center", fontsize=7, color=INK)
    ax.text(bx + bw / 2, ys[0] + bh + 0.012, r"time $t$", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=6.5, color=MUTED)
    # theory entry just right of the bars
    tx = bx + bw + 0.05
    ax.plot([tx, tx + 0.07], [0.095, 0.095], transform=ax.transAxes,
            color=THEORY, lw=1.6, clip_on=False)
    ax.text(tx + 0.085, 0.095, "theory", transform=ax.transAxes, ha="left",
            va="center", fontsize=7, color=INK)


def panel_collapse(ax: plt.Axes, bundles: dict) -> None:
    style_data_axis(ax)
    panel_label(ax, "(d)", "self-similar collapse")

    _draw_collapse(ax, bundles, lw_scale=1.0, theory_lw=1.4)
    ax.set_xlim(-5, 5)
    ax.set_ylim(0, 5)
    ax.set_xlabel(r"$\xi = \theta x / h_0(t)$", fontsize=9, labelpad=1)
    ax.set_ylabel(r"$\mathcal{H} = h / h_0(t)$", fontsize=9, labelpad=1)
    _time_gradient_legend(ax, bundles)

    # inset: strong zoom on the neck |xi| < 1, enlarged to fill the empty upper
    # wedge. No tick labels: the indicated box + connectors show the magnified
    # region, same time-shaded curves + theory.
    axins = ax.inset_axes([0.24, 0.55, 0.52, 0.35])
    _draw_collapse(axins, bundles, lw_scale=0.8, theory_lw=1.0)
    axins.set_xlim(-1, 1)
    axins.set_ylim(0.97, 1.34)
    axins.set_xticks([])
    axins.set_yticks([])
    for sp in axins.spines.values():
        sp.set_edgecolor(MUTED)
        sp.set_linewidth(0.8)
    ax.indicate_inset_zoom(axins, edgecolor=MUTED, lw=0.7, alpha=0.8)


# --------------------------------------------------------------------------- #
# Panel (c): neck height compared with the similarity law
# --------------------------------------------------------------------------- #
def _subsample_log(t, y, n=30):
    m = t > 0
    t, y = t[m], y[m]
    if len(t) == 0:
        return t, y
    targ = np.logspace(np.log10(t.min()), np.log10(t.max()), n)
    idx = np.unique([int(np.argmin(np.abs(t - tt))) for tt in targ])
    return t[idx], y[idx]


def panel_neck(ax: plt.Axes, bundles: dict) -> None:
    style_data_axis(ax)
    panel_label(ax, "(c)", "neck height vs theory")
    ax.set_xscale("log")
    ax.set_yscale("log")

    tmax = 1.0
    handles = []
    for th in sorted(bundles, reverse=True):
        d = bundles[th]
        thr = np.deg2rad(th)
        color = ANGLE_COLOR.get(th, INK)
        mk = ANGLE_MARK.get(th, "o")
        h0t = d["h0t"]
        t, h = h0t[:, 0], h0t[:, 1]
        keep = h > 1.5 * HP            # drop precursor-dominated floor
        t, h = t[keep], h[keep]
        y = h / (V_STAR * thr ** 4)    # compensate by the similarity prefactor
        ts, ys = _subsample_log(t, y, n=24)
        ax.plot(ts, ys, mk, ms=5.4, mfc=color, mec="white", mew=0.3, alpha=0.92,
                ls="none", zorder=4)
        tmax = max(tmax, t.max())
        handles.append(plt.Line2D([], [], color=color, marker=mk, ls="none",
                                  ms=5.4, mec="white", mew=0.3,
                                  label=rf"$\theta={th}^\circ$"))

    tref = np.logspace(np.log10(0.2), np.log10(tmax * 1.3), 100)
    ax.plot(tref, tref, color=THEORY, lw=1.7, zorder=6)   # prediction on top
    handles.append(plt.Line2D([], [], color=THEORY, lw=1.7,
                              label=r"$h_0=0.272\,\theta^4 t$"))

    ax.set_xlim(0.2, tmax * 2)
    ax.set_ylim(0.02, tmax * 2)
    ax.set_xlabel(r"$t$", fontsize=9, labelpad=1)
    ax.set_ylabel(r"$h_0\,/\,(0.272\,\theta^4)$", fontsize=9, labelpad=1)
    leg = ax.legend(handles=handles, loc="lower right", fontsize=6.6,
                    frameon=True, handletextpad=0.3, borderpad=0.4,
                    labelspacing=0.3, columnspacing=0.8, ncol=2,
                    bbox_to_anchor=(0.99, 0.03))
    leg.get_frame().set_facecolor(GAS)
    leg.get_frame().set_edgecolor(FRAME)
    leg.get_frame().set_linewidth(0.6)
    leg.get_frame().set_alpha(0.95)


# --------------------------------------------------------------------------- #
def _load_bundles() -> dict:
    bundles = {}
    for th in (20, 10, 5, 3, 2, 1):
        p = DATA / f"fig5_data_theta{th}.npz"
        if p.exists():
            bundles[th] = np.load(p, allow_pickle=True)
    return bundles


def build_figure(use_tex: bool = True) -> plt.Figure:
    configure_matplotlib(use_tex=use_tex)
    bundles = _load_bundles()
    if 20 not in bundles:
        raise FileNotFoundError("fig5_data_theta20.npz is required")

    W = WIDTH_MM * MM_TO_INCH
    H = HEIGHT_MM * MM_TO_INCH
    fig, axes = plt.subplots(2, 2, figsize=(W, H))
    fig.subplots_adjust(left=0.075, right=0.95, bottom=0.085, top=0.965,
                        wspace=0.30, hspace=0.30)

    hist = bundles.get(HISTORY_ANGLE, bundles[20])
    panel_initiation(axes[0, 0])
    panel_history(axes[0, 1], hist)
    panel_neck(axes[1, 0], bundles)
    panel_collapse(axes[1, 1], bundles)
    return fig


def save_with_fallback(out_pdf: Path, out_png: Path) -> None:
    try:
        fig = build_figure(use_tex=True)
    except (RuntimeError, FileNotFoundError) as exc:
        if isinstance(exc, FileNotFoundError):
            raise
        plt.close("all")
        fig = build_figure(use_tex=False)
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=450)
    plt.close(fig)


def main() -> None:
    save_with_fallback(FIGDIR / "fig5_coalescence.pdf", FIGDIR / "fig5_coalescence.png")
    print("Saved fig5_coalescence.pdf and fig5_coalescence.png")


if __name__ == "__main__":
    main()
