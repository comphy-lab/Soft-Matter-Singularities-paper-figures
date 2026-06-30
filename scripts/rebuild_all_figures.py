#!/usr/bin/env python3
"""Rebuild the eight publication figures from inside the figures repository."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class FigureJob:
    number: int
    name: str
    command: tuple[str, ...]
    outputs: tuple[Path, Path]


JOBS = (
    FigureJob(
        1,
        "visual dictionary",
        ("make_fig1_visual_dictionary.py",),
        (ROOT / "fig1_visual_dictionary.pdf", ROOT / "fig1_visual_dictionary.png"),
    ),
    FigureJob(
        2,
        "conceptual toolkit",
        ("make_fig2_conceptual_toolkit.py",),
        (ROOT / "fig2_conceptual_toolkit.pdf", ROOT / "fig2_conceptual_toolkit.png"),
    ),
    FigureJob(
        3,
        "drop pinch-off",
        ("make_fig3_drop_pinch.py",),
        (ROOT / "fig3_drop_pinch.pdf", ROOT / "fig3_drop_pinch.png"),
    ),
    FigureJob(
        4,
        "drop and bubble pinch-off",
        ("make_fig4_drop_bubble.py",),
        (ROOT / "fig4_drop_bubble.pdf", ROOT / "fig4_drop_bubble.png"),
    ),
    FigureJob(
        5,
        "coalescence",
        ("fig5_coalescence_src/make_fig5_coalescence.py",),
        (ROOT / "fig5_coalescence.pdf", ROOT / "fig5_coalescence.png"),
    ),
    FigureJob(
        6,
        "contact line",
        ("make_fig6_contact_line.py",),
        (ROOT / "fig6_contact_line.pdf", ROOT / "fig6_contact_line.png"),
    ),
    FigureJob(
        7,
        "focusing and output",
        ("make_fig7_focusing_output.py",),
        (ROOT / "fig7_focusing_output.pdf", ROOT / "fig7_focusing_output.png"),
    ),
    FigureJob(
        8,
        "broad family",
        ("make_fig8_broad_family.py",),
        (ROOT / "fig8_broad_family.pdf", ROOT / "fig8_broad_family.png"),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild all eight Soft Matter Singularities figures."
    )
    parser.add_argument(
        "figures",
        nargs="*",
        type=int,
        metavar="N",
        help="optional figure number(s) to rebuild; defaults to all eight",
    )
    args = parser.parse_args()
    invalid = [number for number in args.figures if number < 1 or number > 8]
    if invalid:
        parser.error(f"figure numbers must be between 1 and 8: {invalid}")
    return args


def require_binary(name: str, *, optional: bool = False) -> None:
    if shutil.which(name):
        return
    message = f"Required executable not found on PATH: {name}"
    if optional:
        print(f"[warn] {message}", file=sys.stderr)
        return
    raise SystemExit(message)


def run_job(job: FigureJob) -> None:
    start = time.monotonic()
    command = (sys.executable, *job.command)
    print(f"[fig {job.number}] {job.name}: {' '.join(job.command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    missing = [path for path in job.outputs if not path.exists()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise SystemExit(f"Figure {job.number} did not produce expected output(s): {names}")
    elapsed = time.monotonic() - start
    print(f"[fig {job.number}] done in {elapsed:.1f}s", flush=True)


def main() -> int:
    args = parse_args()
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"Run this from the figures repository root: {ROOT}")

    require_binary("pdftoppm")
    selected = set(args.figures) if args.figures else {job.number for job in JOBS}
    for job in JOBS:
        if job.number in selected:
            run_job(job)

    print("Rebuilt figure PDFs and PNG previews.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
