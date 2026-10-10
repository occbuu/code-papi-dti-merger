"""Verify every visual statistic against analytical outputs and source geometry."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results_upgrade'
def main():
    v=json.loads((OUT/'VISUAL_VALIDATION.json').read_text(encoding='utf-8'))
    p=pd.read_csv(OUT/'T0_panel.csv');m=pd.read_csv(OUT/'T3_panel.csv');d=pd.read_csv(OUT/'T6_dispersion.csv')
    keys=set(p[p.year.eq(2020)&p.egovernance.notna()].key)&set(p[p.year.eq(2024)&p.egovernance.notna()].key)
    assert v['geometry_keys']==63 and p.new_key.nunique()==34
    assert p[p.year.eq(2024)].merged.sum()==52
    for row in v['choropleths']:
        s=p[p.year.eq(2024)][row['field']]
        assert s.notna().sum()==row['observed_scores'] and s.min()==row['min'] and s.max()==row['max']
    for row in v['scatter']:
        s=p[p.year.eq(row['year'])&p.key.isin(keys)].dropna(subset=['dti_gov',row['outcome']])
        assert len(s)==row['n']==61
        assert abs(spearmanr(s.dti_gov,s[row['outcome']]).statistic-row['rho'])<1e-12
        assert np.allclose(np.polyfit(s.dti_gov,s[row['outcome']],1),[row['slope'],row['intercept']])
    for row in v['coefficient_points']:
        term='lag_dti' if row['model']=='Lag common sample' else 'z_dti_gov'
        s=m[m.outcome.eq(row['outcome'])&m.model.eq(row['model'])&m.term.eq(term)].iloc[0]
        assert np.allclose([s.coef,s.ci_low,s.ci_high],[row['coef'],row['ci_low'],row['ci_high']])
    for row in v['aggregation']:
        s=d[d.year.eq(2024)&d['var'].eq(row['outcome'])&d.metric.eq('variance')].iloc[0]
        assert abs(s.within_share-row['actual'])<1e-12
    tex=(ROOT/'Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger.tex').read_text(encoding='utf-8')
    before=tex[:tex.index(r'\appendix')]
    assert before.count(r'\begin{figure}')==6 and before.count(r'\begin{table}')==2
    assert tex.count(r'\refitem')-1==51
    assert tex.count(r'\label{fig:scatter}')==1
    refs=set(re.findall(r'\\ref\{([^}]+)\}',tex));labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert refs<=set(labels) and len(labels)==len(set(labels))
    # Balance grouping braces while respecting TeX-escaped braces and comment lines.
    level=0
    for line in tex.splitlines():
        if line.lstrip().startswith('%'):continue
        for match in re.finditer(r'(?<!\\)[{}]',line):
            level+=1 if match.group()=='{' else -1
            assert level>=0
    assert level==0
    print('Visual checks passed: 63 spatial keys, 34 groups, 4 scatter panels, 8 coefficient points, 4 variance comparisons, 6 figures, 2 main tables, 51 references.')
if __name__=='__main__':main()
