# PAPI × DTI × provincial merger (Viet Nam)

Replication package for:

**Digital government readiness and citizen experience under changing provincial boundaries: Measurement evidence from Viet Nam**

Authors: Hien Bui Ngoc, Thong Cao Văn, Hieu Le Ngoc (corresponding)

This repository reproduces the revised analysis (seed `20261009`): component audit of PAPI e-governance, variance/Theil aggregation under the 2025 63→34 groups, geographically connected sensitivity partitions, TWFE / wild-cluster checks, and nested province-grouped ridge prediction.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
python P3_analysis_final.py
```

`P3_analysis_final.py` runs, in order:

1. `P3_analysis_upgrade.py` — main analysis → `results_upgrade/`, `figures_upgrade/`
2. `verify_sources_upgrade.py` — independent raw-source checks
3. `build_manuscript_upgrade.py` — regenerate LaTeX under `manuscript/`
4. `check_upgrade.py` / `check_visual_upgrade.py` — consistency checks

Local sources only; no network calls. Missing inputs fail explicitly.

## Layout

| Path | Contents |
|---|---|
| `DataPaper3/data/` | Analysis-ready CSVs + `SOURCES.txt` + geo JSON |
| `DataPaper3/raw/` | Archived official workbooks / portal JS / NSO JSON |
| `results_upgrade/` | Tables + `KEY_RESULTS.json` + `VALIDATION_REPORT.json` |
| `figures_upgrade/` | PNG/SVG exports |
| `manuscript/` | Main `.tex`, title page, `REPLICATION.md` |
| `scripts/` | Package builder and GitHub publish helpers |

## Key validated findings (precomputed)

See `results_upgrade/KEY_RESULTS.json` and `VALIDATION_REPORT.json` (`status: passed`).

- Panel: 315 province-years; 307 observed full-PAPI rows
- TWFE (e-governance): coef ≈ 0.235, 95% CI [0.060, 0.409], wild-cluster *p* ≈ 0.008
- 2024 within-group variance share: full PAPI 14.1%; service sum 44.7%; DTI-gov 45.5%
- Connected geographic benchmark places full-PAPI within-share inside the simulated range (unlike unrestricted random grouping)
- Controls-only ridge often matches or beats Controls+DTI for concurrent prediction

## Interpretation limits

- Pre-reform measurement / aggregation study — **not** a causal estimate of the 2025 reform
- Service sum and five-item averages are diagnostic constructions, not official replacement indices
- Connected partitions are sensitivity references, not exact uniform randomisation of legal mergers
- Maps use stored generalised 2008 geoBoundaries geometry + merger crosswalk

## Publish this package to GitHub

```powershell
# 1) Refresh files from the parent project (optional if already current)
python build_public_package.py

# 2) Create remote + push (requires git; GitHub CLI optional)
python scripts/init_and_push_github.py --repo papi-dti-merger --public
```

If `gh` is not installed, the script initialises git and prints manual `git remote` / web UI steps.

## Citation

Please cite the manuscript and this repository (add DOI after Zenodo/OSF deposit). Source provenance: `DataPaper3/data/SOURCES.txt`.

## License

Code: MIT (see `LICENSE`). Upstream data remain under their original public-release terms.
