# Soft Matter Singularities Paper Figures

Figure assets, source scripts, and supporting data for the review paper
*Singularities in Soft Matter Systems*.

This repository is intended to be used as the `figures/` submodule of
[`VatsalSy/Soft-Matter-Singularities_paper`](https://github.com/VatsalSy/Soft-Matter-Singularities_paper).

## Contents

- `fig1_visual_dictionary.*` through `fig8_broad_family.*`: compiled figure exports used by the paper.
- `make_fig*.py`: figure-generation scripts.
- `fig3_drop_pinch/`, `fig4_drop_bubble/`, `fig5_coalescence_data/`, and related folders: curated panel data and intermediate assets needed to rebuild the figures.
- `RAW_DATA_MANIFEST.md`: provenance notes for raw simulation and image sources that are too large or external to this repository.

## Regeneration

Run the relevant Python generator from the repository root, for example:

```bash
python make_fig1_visual_dictionary.py
python fig5_coalescence_src/make_fig5_coalescence.py
```

The parent paper repository builds the manuscript with:

```bash
make check-citations
make
```

## Notes

This repository deliberately tracks publication-facing figure PDFs/PNGs and the curated data needed to reproduce them. Operating-system files, Python caches, local environments, and temporary previews are ignored.
