# Figure 3 Drop Pinch-Off Inputs

This directory is intentionally empty except for this manifest. Add real data or
image assets here, then extend `../make_fig3_drop_pinch.py` panel loaders.

Expected placeholders:

- `fig3a_neck_sequence.png` or `fig3a_neck_sequence.pdf` — experimental or
  simulation snapshots/masks of a thinning liquid filament.
- `fig3b_hmin_timeseries.csv` — columns: `tau`, `h_min`, optional `regime` or
  `run`.
- `fig3c_regime_map.csv` — columns such as `Oh`, `aspect_ratio` or
  `h_min_over_R`, and observed regime/transition.
- `fig3d_memory_outputs.csv` or `fig3d_satellite_images.png` — matched
  cases testing whether equal `h_min` still leaves history-dependent profiles
  or satellite outcomes.

Do not commit raw third-party images unless licensing is clear. Prefer derived
data, permission-cleared panels, or our own simulations.
