"""Checks on revised scientific outputs, source verification and manuscript linkage."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
from P3_analysis_upgrade import ROOT,OUT,DATA,prepare,residualize,dispersion,adjacency,connected,ridge_predict

def main():
    p,merger=prepare();p2=pd.read_csv(OUT/'T0_panel.csv')
    assert len(p2)==315 and not p2.duplicated(['key','year']).any()
    assert p2.egovernance.notna().sum()==307
    assert p2.loc[p2.egovernance.isna(),'common_service_items'].isna().all()
    eligible=p2.dropna(subset=['service_facing','internet_access','egovernance'])
    assert np.max(np.abs(eligible.service_facing+eligible.internet_access-eligible.egovernance))<1e-5
    models=pd.read_csv(OUT/'T3_panel.csv');m=models[(models.model.eq('TWFE controls'))&models.outcome.eq('egovernance')].iloc[0]
    # Independent explicit-dummy least squares on actual unbalanced panel.
    d=p.copy();d['y']=d.groupby('year').egovernance.transform(lambda x:(x-x.mean())/x.std());d['x']=d.groupby('year').dti_gov.transform(lambda x:(x-x.mean())/x.std())
    controls=['ln_grdp_pc','urban_pp','ln_pop'];d=d.dropna(subset=['y','x']+controls)
    effects=pd.get_dummies(d[['key','year']].astype(str),drop_first=True,dtype=float)
    X=np.column_stack([np.ones(len(d)),d[['x']+controls].to_numpy(),effects.to_numpy()]);b=np.linalg.lstsq(X,d.y,rcond=None)[0][1]
    assert abs(b-m.coef)<1e-10
    keys,adj=adjacency(merger);assignments=np.load(OUT/'T6_spatial_partitions.npy')
    initial=pd.factorize(merger.set_index('key').loc[keys].new_key)[0];sizes=np.bincount(initial)
    for draw in assignments:
        assert np.array_equal(np.bincount(draw,minlength=len(sizes)),sizes)
        assert all(connected(list(np.flatnonzero(draw==g)),adj) for g in np.unique(draw))
    shares=pd.read_csv(OUT/'T6_dispersion.csv')
    assert np.max(np.abs(shares.total-shares.between-shares.within))<1e-10
    assert shares.within_share.between(0,1).all()
    shifts=pd.read_csv(OUT/'T6_scale_sensitivity.csv');vs=shifts[shifts.metric.eq('variance')].within_share
    assert vs.max()-vs.min()<1e-10
    preds=pd.read_csv(OUT/'T5_oof_predictions.csv');assert preds.prediction.notna().all()
    assert not preds.duplicated(['outcome','model','repeat','key','year']).any()
    # Recompute all reported CV metrics from saved out-of-fold predictions.
    reports=pd.read_csv(OUT/'T5_prediction_repeats.csv')
    for r in reports.itertuples():
        d=preds[preds.outcome.eq(r.outcome)&preds.model.eq(r.model)&preds['repeat'].eq(r.repeat)]
        err=d.observed-d.prediction
        r2=1-np.sum(err**2)/np.sum((d.observed-d.observed.mean())**2)
        assert abs(r2-r.r2)<1e-10
    source=json.loads((OUT/'SOURCE_VALIDATION.json').read_text(encoding='utf-8'))
    assert source['PAPI']['observed']==2762 and source['DTI']['matched']==315 and source['controls']['rows']==315
    tex=(ROOT/'Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger.tex').read_text(encoding='utf-8')
    assert not re.search(r'@@[A-Z]+@@',tex)
    labels=set(re.findall(r'\\label\{([^}]+)\}',tex));refs=set(re.findall(r'\\ref\{([^}]+)\}',tex));assert refs<=labels,(refs-labels)
    stack=[]
    for action,env in re.findall(r'\\(begin|end)\{([^}]+)\}',tex):
        if action=='begin':stack.append(env)
        else:assert stack and stack.pop()==env,(action,env)
    assert not stack
    assert r'\includegraphics' not in tex and r'\input{' not in tex
    anonymous=(ROOT/'Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger_anonymous.tex').read_text(encoding='utf-8')
    assert 'b.nhien@' not in anonymous and 'lnhieu@' not in anonymous and 'B.22-33' not in anonymous
    report=dict(status='passed',panel_rows=315,egovernance_observed=307,raw_source_verification=source,
                explicit_dummy_coefficient=b,validated_connected_partitions=len(assignments),
                cross_validation_metric_rows=len(reports),latex_static_checks='passed',latex_compilation='unverified: built-in compiler environment unavailable')
    (OUT/'VALIDATION_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
