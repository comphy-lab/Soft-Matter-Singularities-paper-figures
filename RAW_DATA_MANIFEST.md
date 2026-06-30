# Raw simulation-data manifest — Figures 3 & 4

Where the Basilisk snapshots behind the numerical panels actually live. The repo
keeps only the *rendered* tight panels (`fig3_drop_pinch/snapshots/`,
`fig4_drop_bubble/<case>/panels/`) and per-case `manifest.csv`/`scales.txt`. The
heavy raw dumps (`snapshot-*`, restart dumps, logs) are NOT in git — they sit on
HPC scratch/project storage, which is volatile, so each case is mirrored to a
local archive drive on `comphy-mac` (Taylor).

Provenance lives in each case `manifest.csv` (`snapshot` column = the path the
dump was read from at render time) and in the project trackers
`memory/projects/soft-matter-singularities.md` and
`memory/projects/elastic-bubble-pinchoff.md`.

Repo: simulations come from **comphy-lab/ElasticPinchOff**
(`LiquidInThinning.c` = drop / "-in", `LiquidOutThinning.c` = bubble / "-out").

## Case → raw-data location

| Case | Figure panel | Physics | Compute host | Raw run path (cluster) | Local archive | Archive status |
|---|---|---|---|---|---|---|
| `c1024-in` | Fig 3 (a/b; + c/d Oh=1e-2 curve); Fig 4 (a) | Newtonian drop, Oh=0.01 | Hamilton (Durham) | `hamilton:/nobackup/rlzy43/ElasticPinchOff/simulationCases/c1024-in` *(deleted from Hamilton 2026-06-27 after archiving)* | `comphy-mac:/Volumes/macOfficeV0/ElasticPinchOff/Hamilton-Newtonian-2026-06-27/simulationCases/c1024-in` (64 G) | **archived** |
| `c1023-in` | Fig 3 (c/d Oh=0 curve) | Newtonian drop, Oh=0 (inviscid limit) | Hamilton (Durham) | `hamilton:/nobackup/rlzy43/ElasticPinchOff/simulationCases/c1023-in` *(deleted from Hamilton 2026-06-27 after archiving)* | `comphy-mac:/Volumes/macOfficeV0/ElasticPinchOff/Hamilton-Newtonian-2026-06-27/simulationCases/c1023-in` (65 G) | **archived** |
| `c1030-out` | Fig 4 (b) | Newtonian bubble, Oh=1e-2, De=0, Ec=0 | Snellius (SURF) | `snellius:/projects/0/nctt0620/vatsal/2026-06-27-Elastic-Pinch-Off/simulationCases/c1030-out` (2.7 G) | `comphy-mac:/Volumes/macOfficeV0/ElasticPinchOff/Snellius-2026-06-27-Elastic-Pinch-Off/simulationCases/c1030-out` | archived 2026-06-28 |
| `c1032-in` | Fig 4 (c) | Elastic drop, Oh=1, Ec=0.1, De=∞, lvl16 | Snellius (SURF) | `snellius:/projects/0/nctt0620/vatsal/2026-06-27-Elastic-Pinch-Off/simulationCases/c1032-in` (22 G) | `…/Snellius-2026-06-27-Elastic-Pinch-Off/simulationCases/c1032-in` | archived 2026-06-28 |
| `c1031-out` | Fig 4 (d) | Elastic bubble, Oh=1e-2, De=∞, Ec=0.1 | Snellius (SURF) | `snellius:/projects/0/nctt0620/vatsal/2026-06-27-Elastic-Pinch-Off/simulationCases/c1031-out` (4.5 G) | `…/Snellius-2026-06-27-Elastic-Pinch-Off/simulationCases/c1031-out` | archived 2026-06-28 |
| `c1033-out` | Fig 4 (d) | Elastic bubble (companion) | Snellius (SURF) | `snellius:/projects/0/nctt0620/vatsal/2026-06-27-Elastic-Pinch-Off/simulationCases/c1033-out` (31 M) | `…/Snellius-2026-06-27-Elastic-Pinch-Off/simulationCases/c1033-out` | archived 2026-06-28 |

Pending (not yet in a figure): `c1025-in` — Oh=1 **Newtonian** drop, MAXlevel=16,
continuation on Hamilton (Slurm 17663345), intended for the planned Oh=1 addition
to Figure 3. Archived at
`comphy-mac:/Volumes/macOfficeV0/ElasticPinchOff/Hamilton-Newtonian-2026-06-27/simulationCases/c1025-in`;
live run on `hamilton:/nobackup/rlzy43/ElasticPinchOff/simulationCases/c1025-in`.

## Storage hosts

- **macOfficeV0** — `comphy-mac:/Volumes/macOfficeV0` (11 TiB, ~10 TiB free). EPO
  cluster archives: `ElasticPinchOff/Hamilton-Newtonian-2026-06-27/`,
  `ElasticPinchOff/Snellius-2026-06-27-Elastic-Pinch-Off/`.
- **macOfficeV1** — `comphy-mac:/Volumes/macOfficeV1` (1.8 TiB, tighter). Holds the
  older DropsVsBubble high-Oh + low-Oh sweeps.
- **Hamilton scratch** — `hamilton:/nobackup/rlzy43/...` (600 G quota, purgeable).
- **Snellius project** — `snellius:/projects/0/nctt0620/vatsal/...` (`vsanjay@snellius.surf.nl`,
  allocation `nctt0620`; expires with the allocation — not a permanent archive).
- **Synology (published / final archive)** — `synosync:/volume1/CoMPhy-Archive/Projects/2026-2030/BubbleVsDropPinchOff`
  (`vatsal@synosync`, 3.7 G). The durable published-data archive for the broader
  BubbleVsDropPinchOff / Elastic Pinch-Off project: `finalResults/` figure outputs,
  pinch-off videos, and `ListOfSimulations_ElasticPinchOff.xlsx` master case-index.
  CoMPhy-Archive is a non-Dropbox Synology shared folder with snapshot protection — the
  most permanent location (macOfficeV0 is a single local drive; the Snellius/Hamilton
  paths are volatile). Moved here from `Dropbox/0-Projects/BubbleVsDropPinchOff` on
  2026-06-29 and the Dropbox copy deleted (a temporary fallback survives in
  `synosync:/volume1/Dropbox/#recycle`). Carries its own `README.md` (provenance);
  cross-referenced from the `elastic-bubble-pinchoff` tracker (`## Archives`).

## How the Snellius archive was made (2026-06-28)

```bash
rsync -a --partial --human-readable --stats --exclude='basilisk/' -e ssh \
  snellius:/projects/0/nctt0620/vatsal/2026-06-27-Elastic-Pinch-Off/ \
  /Volumes/macOfficeV0/ElasticPinchOff/Snellius-2026-06-27-Elastic-Pinch-Off/
```

The reproducible `basilisk/` install is excluded (rebuild via the repo's
`do_install_epo.sh` / `reset_install_basilisk-ref-locked.sh`); everything else
(`simulationCases/`, sbatch scripts, `*.params`, `postProcess/`, slurm logs,
`src-local/`) is mirrored. Log: `…/ElasticPinchOff/snellius-epo-archive.log`.

## Re-rendering the panels from raw data

All renderers and the decimation/compositing helpers live in the repo:

| Step | Script |
|---|---|
| Fig-4 panel (velocity, mirror) | `figures/fig4_drop_bubble/render_panel.py` |
| Fig-4 driver (all strips, from manifests) | `figures/fig4_drop_bubble/render_all_panels.py` |
| Fig-3 panel (split log10Φ / \|u\|) + driver | `figures/fig3_drop_pinch/render_fig3_panels.py --from-manifest` |
| Interface decimation (chain + Douglas-Peucker) | `figures/facet_simplify.py` |
| Composite vector-stamp (PDF over imshow footprint) | `figures/pdf_vector_stamp.py` |

The Basilisk field/facet helpers are built once with qcc (see `render_panel.py`
docstring for the build lines and the short-path SIGTRAP caveat):

```bash
export BASILISK=~/CMP-codes/basilisk/src; export PATH=$BASILISK:$PATH
mkdir -p /tmp/figbuild
qcc -O2 -w postProcess/getFacet.c -o /tmp/figbuild/getFacet -lm
qcc -O2 -w -disable-dimensions -I<src-local> postProcess/getData-elastic.c \
    -o /tmp/figbuild/getData-elastic -lm                       # Fig 4
qcc -O2 -w -disable-dimensions figures/fig3_drop_pinch/getData-c1024-diss.c \
    -o /tmp/figbuild/getData-c1024-diss -lm                    # Fig 3
```

Then `render_all_panels.py` / `render_fig3_panels.py --from-manifest` regenerate
the tight panels (rasterised field + **vector, decimated** interface), and
`make_fig{3,4}_*.py` vector-stamp them into the composites. `getFacet` emits the
interface as ~10^5 per-cell PLIC segments near pinch-off; `facet_simplify` chains
them into connected polylines and RDP-simplifies at a sub-cell tolerance, keeping
the curve vector + crisp while cutting the panel PDFs ~25x (Fig 4: 24 MB -> ~3.7 MB).

Raw-data roots are overridable via `EPO_HAMILTON_ROOT` / `EPO_SNELLIUS_ROOT`.
