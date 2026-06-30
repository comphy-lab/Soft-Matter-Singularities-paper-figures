# Soft Matter Singularities Figures

This repository contains the figure assets and generation scripts for the
*Singularities in Soft Matter Systems* review paper.

## Working Rules

- Keep generated publication assets and their source data together.
- Do not commit raw simulation dumps unless they are deliberately curated for a figure.
- Keep large or external raw-data provenance in `RAW_DATA_MANIFEST.md`.
- Preserve the filenames expected by the parent LaTeX manuscript.
- Run the relevant `make_fig*.py` script after editing a figure generator.
- Check fonts and visual output before claiming a figure is ready.
- Avoid committing OS files, Python caches, local environments, or temporary preview folders.

## Parent Manuscript

The parent manuscript repository is:

```text
git@github.com:VatsalSy/Soft-Matter-Singularities_paper.git
```

This repository is mounted there as the `figures/` submodule.
