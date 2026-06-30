#!/usr/bin/env python3
"""Generate Figure 7 from experimental images.

Layout: a left block stacks a square colour cusp (a) and a 2x2 set of
air-entrainment frames (b) over the FC-84 sheet-fragmentation hero sequence (c),
while a tall jet-eruption image (d) runs the full height on the right.

(c) is the focus: six high-speed frames of a drop spreading on a superheated
substrate into a thin sheet that ruptures and fragments into a spray of droplets,
laid out as a 2x3 block so each frame reads large.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpecFromSubplotSpec
from PIL import Image, ImageOps


WIDTH_MM = 135.0
HEIGHT_MM = 112.0
MM_TO_INCH = 1.0 / 25.4

RAW_DIR = Path(__file__).resolve().parent / "fig7_rawimages"

INK = "#111111"
FRAME = "#222222"
PANEL_FACE = "#FFFFFF"
LABEL_FACE = "#FFFFFF"

# (a) is a wide cusp image; crop a square centred on the cusp tip.
A_CROP = (392, 0, 1422, 1030)
# (b) is a 2x3 montage of an air-entraining plunging jet (frames i..vi in time).
# Keep the four corners -- i, iii, iv, vi -- dropping the redundant middle column.
B_FRAMES = {
    "i": (0, 0, 162, 244),
    "iii": (340, 0, 500, 244),
    "iv": (0, 252, 162, 496),
    "vi": (340, 252, 500, 496),
}
# (d) is a pair of jet images side by side; keep only the left one.
D_CROP = (0, 0, 242, 600)


def configure_matplotlib(use_tex: bool = True) -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman", "CMU Serif", "DejaVu Serif"],
            "font.size": 7.6,
            "axes.linewidth": 0.55,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "text.usetex": use_tex,
        }
    )
    if use_tex:
        matplotlib.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
    else:
        matplotlib.rcParams["mathtext.fontset"] = "cm"


def load_image(name: str, crop: tuple[int, int, int, int] | None = None) -> np.ndarray:
    img = Image.open(RAW_DIR / name)
    img = ImageOps.exif_transpose(img).convert("RGB")
    if crop is not None:
        img = img.crop(crop)
    return np.asarray(img)


def style_image_axis(ax: plt.Axes) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor(PANEL_FACE)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.55)
        spine.set_color(FRAME)


def show_image(ax: plt.Axes, image: np.ndarray) -> None:
    ax.imshow(image, interpolation="lanczos")
    ax.set_xlim(0, image.shape[1])
    ax.set_ylim(image.shape[0], 0)
    ax.set_aspect("equal", adjustable="box")
    style_image_axis(ax)


def panel_label(ax: plt.Axes, label: str, title: str | None = None) -> None:
    text = label if title is None else f"{label} {title}"
    ax.text(
        0.025,
        0.965,
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.4,
        color=INK,
        bbox={
            "facecolor": LABEL_FACE,
            "edgecolor": "none",
            "alpha": 0.88,
            "boxstyle": "round,pad=0.18",
        },
        zorder=10,
    )


def stage_label(ax: plt.Axes, text: str) -> None:
    ax.text(
        0.965,
        0.945,
        text,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.0,
        color=INK,
        bbox={
            "facecolor": LABEL_FACE,
            "edgecolor": "none",
            "alpha": 0.82,
            "boxstyle": "round,pad=0.14",
        },
        zorder=10,
    )


def build_figure(use_tex: bool = True) -> plt.Figure:
    configure_matplotlib(use_tex=use_tex)

    fig = plt.figure(
        figsize=(WIDTH_MM * MM_TO_INCH, HEIGHT_MM * MM_TO_INCH),
        facecolor="white",
        constrained_layout=False,
    )
    # Outer split: a left block (a + b stacked over the c hero strip) and a tall
    # jet-eruption panel (d) running the full height on the right.
    outer = fig.add_gridspec(
        1, 2,
        left=0.008, right=0.992, bottom=0.012, top=0.988,
        wspace=0.045, width_ratios=[1.66, 0.85],
    )
    left = GridSpecFromSubplotSpec(
        2, 1, subplot_spec=outer[0, 0], hspace=0.07, height_ratios=[1.0, 1.12],
    )

    # Top of the left block: (a) square cusp beside the (b) 2x2 air-entrainment set.
    top = GridSpecFromSubplotSpec(
        1, 2, subplot_spec=left[0], wspace=0.05, width_ratios=[1.0, 0.7],
    )
    ax_a = fig.add_subplot(top[0, 0])
    show_image(ax_a, load_image("a-PhysRevFluids.4.110502.png", crop=A_CROP))
    panel_label(ax_a, "(a)", "viscous cusp")

    # (b) Four corner frames of the plunging-jet montage (i, iii, iv, vi), in time
    # order across the 2x2: incipient dimple -> thinning neck -> pinch-off spray.
    # Draw the (b) label after all four frames so it is not overpainted by a
    # later-drawn neighbour.
    b_grid = GridSpecFromSubplotSpec(2, 2, subplot_spec=top[0, 1], wspace=0.05, hspace=0.05)
    b_axes = {}
    for key, (r, c) in (("i", (0, 0)), ("iii", (0, 1)), ("iv", (1, 0)), ("vi", (1, 1))):
        ax = fig.add_subplot(b_grid[r, c])
        show_image(ax, load_image("b-PhysRevLett.93.png", crop=B_FRAMES[key]))
        b_axes[key] = ax
    # Raise the labelled top-left frame so its label (which spans the block top)
    # is drawn after the neighbouring frame instead of being overpainted by it.
    b_axes["i"].set_zorder(5)
    panel_label(b_axes["i"], "(b)", "air entrainment")

    # (c) FC-84 sheet-fragmentation hero strip: six time-ordered high-speed frames
    # in a 2x3 (three over three).  A drop strikes a 340 C superheated substrate,
    # spreads into a thin sheet, which ruptures into a spray of drops.  A "time"
    # arrow gives the direction; absolute times are deliberately not printed -- the
    # source AVI is a slowed playback export, so the frame->time mapping cannot be
    # verified without the raw high-speed capture.
    c_grid = GridSpecFromSubplotSpec(
        3, 6, subplot_spec=left[1], wspace=0.03, hspace=0.05,
        height_ratios=[0.1, 1.0, 1.0],
    )
    ax_time = fig.add_subplot(c_grid[0, :])
    ax_time.axis("off")
    ax_time.annotate(
        "", xy=(0.99, 0.18), xytext=(0.01, 0.18), xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 0.9},
    )
    ax_time.text(0.5, 0.3, "time", transform=ax_time.transAxes,
                 ha="center", va="bottom", fontsize=7.0, color=INK)
    # Three frames per row, each spanning two of the six columns.
    c_label_ax = None
    for i, (c0, c1) in enumerate([(0, 2), (2, 4), (4, 6)]):
        ax = fig.add_subplot(c_grid[1, c0:c1])
        show_image(ax, load_image(f"fc84_frames/frame_{i:02d}.png"))
        if i == 0:
            c_label_ax = ax
    for j, (c0, c1) in enumerate([(0, 2), (2, 4), (4, 6)]):
        ax = fig.add_subplot(c_grid[2, c0:c1])
        show_image(ax, load_image(f"fc84_frames/frame_{j + 3:02d}.png"))
    # Label the top-left frame last (raised zorder) so the spanning descriptor is
    # not overpainted by the neighbouring frame.
    c_label_ax.set_zorder(5)
    panel_label(c_label_ax, "(c)", "Marangoni rupture")

    # (d) Tall jet eruption (left image of the pair), full height on the right.
    ax_d = fig.add_subplot(outer[0, 1])
    show_image(ax_d, load_image("d-Nature-jet-35000151.png", crop=D_CROP))
    panel_label(ax_d, "(d)", "jet eruption")

    return fig


def save_with_fallback(out_pdf: Path, out_png: Path) -> None:
    try:
        fig = build_figure(use_tex=True)
        fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.01)
        fig.savefig(out_png, dpi=450, bbox_inches="tight", pad_inches=0.01)
        plt.close(fig)
    except RuntimeError:
        plt.close("all")
        fig = build_figure(use_tex=False)
        fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.01)
        fig.savefig(out_png, dpi=450, bbox_inches="tight", pad_inches=0.01)
        plt.close(fig)


def main() -> None:
    here = Path(__file__).resolve().parent
    save_with_fallback(
        here / "fig7_focusing_output.pdf",
        here / "fig7_focusing_output.png",
    )
    print("Saved fig7_focusing_output.pdf and fig7_focusing_output.png")


if __name__ == "__main__":
    main()
