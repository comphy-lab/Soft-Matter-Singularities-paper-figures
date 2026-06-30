#!/usr/bin/env python3
"""Vector-stamp standalone snapshot PDFs over their imshow raster footprints.

matplotlib cannot place a PDF *inside* an Axes, so a simulation snapshot is first
drawn as a raster (``imshow`` of the ``.png``) to lock the composite layout, then
the ``.pdf`` sibling — which carries a rasterised colour field plus a genuinely
*vector* interface (see ``fig4_drop_bubble/render_panel.py``: field via ``imshow``,
interface via a ``LineCollection``) — is painted over the identical footprint with
pypdf. The colour field has to stay raster, but the interface line becomes vector,
so it no longer pixelates when the reader zooms in.

Mapping is anchored to matplotlib's own tight bounding box, so the stamped output
crops exactly like ``bbox_inches="tight"`` would. A panel whose vector PDF is
missing is silently left as the raster imshow already drew.

Usage from a figure script::

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pdf_vector_stamp import save_vector_composite

    panels = []                                   # (vector_pdf, AxesImage)
    im = ax.imshow(plt.imread(png))
    panels.append((png.with_suffix(".pdf"), im))
    ...
    save_vector_composite(fig, out_pdf, out_png, panels, pad_in=0.015)
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from matplotlib.transforms import Bbox
from pypdf import PdfReader, PdfWriter, Transformation

POINTS_PER_INCH = 72.0


def _pdftocairo() -> str:
    exe = shutil.which("pdftocairo") or "/opt/homebrew/bin/pdftocairo"
    if not Path(exe).exists():
        raise FileNotFoundError(
            "pdftocairo not found; it is needed to rasterise the .png sibling "
            "from the final vector PDF. Install poppler (brew install poppler)."
        )
    return exe


def save_vector_composite(
    fig,
    out_pdf: str | Path,
    out_png: str | Path,
    panels,
    pad_in: float = 0.015,
    raster_dpi: int = 300,
) -> None:
    """Save ``fig`` to ``out_pdf`` with each panel's raster footprint overstamped
    by its vector PDF, then rasterise ``out_png`` from the final vector PDF.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The fully-assembled composite. Its snapshot panels must already contain
        the raster ``imshow`` whose extent fixes each stamp's footprint.
    out_pdf, out_png : path-like
        Final outputs. ``out_png`` is rasterised from ``out_pdf`` so the two
        always agree.
    panels : iterable of (path-like, matplotlib.image.AxesImage)
        Each pair is a vector snapshot PDF and the ``imshow`` artist that marks
        where it belongs. Missing PDFs are skipped (panel stays raster).
    pad_in : float
        White padding (inches) added around the tight bbox; match the figure's
        previous ``pad_inches`` so the crop is unchanged.
    raster_dpi : int
        Resolution for the embedded colour-field raster and the .png preview.
    """
    out_pdf = Path(out_pdf)
    out_png = Path(out_png)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    fig.canvas.draw()
    dpi = fig.get_dpi()  # display px -> inches uses the *draw* dpi
    renderer = fig.canvas.get_renderer()
    tight = fig.get_tightbbox(renderer)  # inches, figure-relative
    bb = Bbox.from_extents(
        tight.x0 - pad_in, tight.y0 - pad_in, tight.x1 + pad_in, tight.y1 + pad_in
    )

    # Footprint of each panel in PDF points, relative to the cropped MediaBox.
    stamps = []
    for vector_pdf, image in panels:
        vector_pdf = Path(vector_pdf)
        if not vector_pdf.exists():
            continue
        ext = image.get_window_extent()  # display px, bottom-left origin (== PDF)
        x0 = (ext.x0 / dpi - bb.x0) * POINTS_PER_INCH
        y0 = (ext.y0 / dpi - bb.y0) * POINTS_PER_INCH
        w = ext.width / dpi * POINTS_PER_INCH
        h = ext.height / dpi * POINTS_PER_INCH
        stamps.append((vector_pdf, (x0, y0, w, h)))

    tmp_pdf = out_pdf.with_name(out_pdf.stem + ".raster-tmp.pdf")
    fig.savefig(tmp_pdf, bbox_inches=bb, dpi=raster_dpi)

    target = PdfReader(str(tmp_pdf)).pages[0]
    for vector_pdf, (x0, y0, w, h) in stamps:
        src = PdfReader(str(vector_pdf)).pages[0]
        sw = float(src.mediabox.width)
        sh = float(src.mediabox.height)
        op = Transformation().scale(w / sw, h / sh).translate(x0, y0)
        target.merge_transformed_page(src, op, over=True)
    writer = PdfWriter()
    writer.add_page(target)
    with open(out_pdf, "wb") as fh:
        writer.write(fh)
    tmp_pdf.unlink(missing_ok=True)

    subprocess.run(
        [
            _pdftocairo(),
            "-png",
            "-r",
            str(raster_dpi),
            "-singlefile",
            str(out_pdf),
            str(out_png.with_suffix("")),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"Saved (vector interface): {out_pdf}")
    print(f"Saved (raster preview):   {out_png}")
