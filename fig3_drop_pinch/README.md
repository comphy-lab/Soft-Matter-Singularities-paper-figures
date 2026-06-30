# Figure 3: Drop Pinch-Off

This folder contains the source assets for `../fig3_drop_pinch.pdf`.

- `../drop-water-only.pdf` is the remote/source experimental row used in row 0;
  `panels/drop-water-only.pdf` is the annotated rendered panel used by the
  composite.
- `snapshots/` contains the six tight c1024 simulation panel PDFs/PNGs generated
  on Hamilton from frame indices `0,5,6,7,8,9`.
- `panels/fig3_hmin_l16.pdf` and `panels/fig3_dhdt_l16.pdf` are the quantitative
  subpanels used in row 2.
- `data/fig3_l16_hmin_dhdt.csv` is reduced plotting data. The thinning-rate
  column is the analytic derivative of fits through `h_min(t)`, not a
  finite-difference derivative of the raw log. The quantitative panels plot the
  full reduced arrays stored here, without display subsampling. Both plotted
  cases use SciPy smoothing splines of the residual around their limiting
  asymptotes: `Oh=0` tends to `A tau^(2/3)` as `tau -> 0`, with `A` inferred
  from the original data, and `Oh=10^{-2}` tends to `(0.0709/Oh) tau`. The full
  Basilisk dump binaries are intentionally not stored here.

Regenerate with:

```sh
python3 ../make_fig3_drop_pinch.py
```
