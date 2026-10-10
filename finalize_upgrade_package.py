"""Write the canonical entry point, notebook and replication documentation."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parent
wrapper = '''"""Revised entry point; legacy implementation is archived."""
from pathlib import Path
import subprocess
import sys
def main():
    root = Path(__file__).resolve().parent
    for script in ['P3_analysis_upgrade.py', 'verify_sources_upgrade.py', 'build_manuscript_upgrade.py', 'check_upgrade.py', 'check_visual_upgrade.py']:
        print(f'Running {script}', flush=True)
        subprocess.run([sys.executable, str(root / script)], cwd=root, check=True)
if __name__ == '__main__':
    main()
'''
(ROOT/'P3_analysis_final.py').write_text(wrapper, encoding='utf-8')
readme = '''# Paper 3 — revised 9 October 2026

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
'''
(ROOT/'README.md').write_text(readme, encoding='utf-8')
(ROOT/'Paper3_DeTaiThayHien'/'REPLICATION.md').write_text(readme, encoding='utf-8')
code = '''from pathlib import Path
import subprocess
import sys
here = Path.cwd().resolve()
candidates = [here, *here.parents]
root = next((p for p in candidates if (p / 'P3_analysis_final.py').exists()), None)
if root is None:
    relative = Path('Paper2026_Upgrade/P3_Provincial_Panel_PAPI_DTI_Merger')
    root = next((p / relative for p in candidates if (p / relative / 'P3_analysis_final.py').exists()), None)
if root is None:
    raise FileNotFoundError('Open this notebook from the project or parent workspace.')
subprocess.run([sys.executable, str(root / 'P3_analysis_final.py')], cwd=root, check=True)
'''
nb = {'cells': [
    {'cell_type': 'markdown', 'metadata': {}, 'source': ['# Paper 3: revised reproducible analysis\n', 'Runs the canonical pipeline, raw-source verifier, manuscript builder and consistency checks. No automatic package installation. PDF compilation is separate.']},
    {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': code.splitlines(keepends=True)}],
    'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
(ROOT/'P3_analysis_final.ipynb').write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding='utf-8')
pdf = ROOT/'Paper3_DeTaiThayHien'/'P3_PAPI_DTI_Merger.pdf'
if pdf.exists():
    destination = pdf.with_name('P3_PAPI_DTI_Merger_PRE_REVISION_2026-10-09.pdf')
    if not destination.exists():
        pdf.rename(destination)
print('Entry point, notebook, documentation and historical PDF naming updated.')
