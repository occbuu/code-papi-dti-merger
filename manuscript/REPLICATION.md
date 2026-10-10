# Paper 3 — revised 9 October 2026

**Digital government readiness and citizen experience under changing provincial boundaries: Measurement evidence from Viet Nam**

Main manuscript: `Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger.tex`. Anonymous manuscript and separate title page are in the same directory. Originals are preserved in `archive/pre_revision_2026-10-09/`. Files under `results/`, `figures/`, the draft Word file and `P3_analysis.py` are historical and do not support the revised manuscript.

## Reproduce

Use Python with packages in `requirements-upgrade.txt`, which records the verified environment. No packages are installed automatically. From any working directory:

```powershell
python "C:/OccBuu/Paper2026/19_HVCB/DeTaiCapBo_09Apr23/Paper2026_Upgrade/P3_Provincial_Panel_PAPI_DTI_Merger/P3_analysis_final.py"
```

Alternatively run all cells of `P3_analysis_final.ipynb` from this project or its parent workspace. The entry point runs revised analysis, independent raw-source verification, manuscript generation and consistency checks. Missing files fail explicitly. Seed: 20261009. Local sources only; no network requests. Results are regenerated in `results_upgrade/` and `figures_upgrade/`.

## Evidence and interpretation

`T0_panel.csv` contains the keyed 63-province × 5-year grid, with 307 observed full-PAPI province-years. T0 files record source labels, extraction locations and measurement coverage. `SOURCE_VALIDATION.json` records independent raw-source comparisons: PAPI dimensions/total; all 315 DTI province-year score vectors; all 315 control vectors. Archived DTI years follow documented source assignments, rather than being inferred from matching scores. Components are extracted from original workbooks. This does not certify recreation of every historical cleaning step or legal mapping.

`VALIDATION_REPORT.json` records independent regression, variance, partition connectivity, prediction and LaTeX static checks. `KEY_RESULTS.json`, input hashes and environment records accompany scientific result tables. T2, T3, T5 and T6 files contain revised alignment, panel, grouped prediction and geographic decomposition outputs.

The study assesses pre-reform measurement composition and territorial aggregation. It does not identify a post-reform causal effect. Service sums and five-item averages are diagnostic constructions, not validated replacement indices. Connected simulations are sensitivity references, not exact randomisation tests.

## Manuscript status

`build_manuscript_upgrade.py` generates all three LaTeX files from revised tables. Make durable text edits in the generator; rerunning replaces generated sources. The built-in compiler returned `Unable to find standard directories for platform`. No revised PDF has been verified. The historical PDF is named PRE_REVISION. Static checks passed; page layout awaits successful compilation.

Before submission: compile and inspect the PDF; verify author/funding/CRediT declarations; deposit a permitted public replication package and assign a DOI; select a journal and apply its template. Causal or individual-level claims require additional data. See `REVISION_LOG_2026-10-09.md` for completed revisions and remaining limits.

## Visual and literature revision

The existing main manuscript now contains six figure families, two main tables and 51 references. Detailed tables are retained in the appendix. PNG/SVG exports are in `figures_upgrade/`; inline TikZ keeps the manuscript self-contained. Historical geometry and the merger crosswalk are explicitly distinguished from official contemporary boundaries. The generator now rebuilds figures and applies `enhance_manuscript_visual.py`; `check_visual_upgrade.py` verifies visual values against scientific outputs. See the project-root `VISUAL_LITERATURE_REVISION_2026-10-09.md`. Latest built-in compilation status is unknown; the anonymous manuscript from the previous revision has not been refreshed during this in-place editor revision.
