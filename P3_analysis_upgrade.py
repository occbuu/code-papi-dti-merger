"""Paper 3 revision: explicit measurement checks and reproducible descriptive inference.

Run from any working directory. Inputs are immutable; revised outputs are isolated.
No network access, automatic installations, synthetic data, DML or causal forests.
"""
from pathlib import Path
import collections
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
import unicodedata

import numpy as np
import pandas as pd
import openpyxl
from scipy import stats
from linearmodels.panel import PanelOLS
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'DataPaper3/data'
RAW = ROOT / 'DataPaper3/raw'
OUT = ROOT / 'results_upgrade'
FIG = ROOT / 'figures_upgrade'
for path in [OUT, FIG]:
    path.mkdir(exist_ok=True)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
SEED = 20261009
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                     'axes.spines.right': False, 'figure.dpi': 120})

def save(df, name):
    df.to_csv(OUT / (name + '.csv'), index=False, encoding='utf-8-sig')

def norm(s):
    s = unicodedata.normalize('NFD', str(s).replace('đ','d').replace('Đ','D').replace('–',' ').replace('—',' ').replace('-',' '))
    s = s.encode('ascii','ignore').decode().lower()
    s = re.sub(r'^\s*(tp\.\s*|tp\s+|thanh pho\s+|tinh\s+)', '', s)
    s = re.sub(r'\s+(city|province)\s*$', '', s)
    s = re.sub(r'[^a-z ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return {'thua thien hue':'hue','tt hue':'hue','con dao':'ba ria vung tau'}.get(s,s)

def unique(df, cols):
    if df.duplicated(cols).any():
        raise ValueError(f'Duplicate keys {cols}: {df.loc[df.duplicated(cols,keep=False),cols]}')

def prepare():
    papi = pd.read_csv(DATA/'papi_long.csv')
    dti = pd.concat([pd.read_csv(DATA/'dti.csv'),pd.read_csv(DATA/'dti_2024_63.csv')],ignore_index=True)
    controls = pd.read_csv(DATA/'controls.csv')
    merger = pd.read_csv(DATA/'province_merger_map_63_to_34.csv')
    for df in [papi,dti,controls,merger]:
        df['key'] = df['province' if 'province' in df else 'province_old'].map(norm)
    code = papi[papi.year.eq(2020)].drop_duplicates('province_code_pre2025').set_index('province_code_pre2025').key
    papi['key'] = papi.province_code_pre2025.map(code)
    merger['new_key'] = merger.province_new.map(norm)
    for df,cols in [(papi,['key','year','dimension']),(dti,['key','year']),
                    (controls,['key','year']),(merger,['key'])]: unique(df,cols)
    assert merger.key.nunique()==63 and merger.new_key.nunique()==34
    for df in [papi,dti,controls]: assert set(df.key)<=set(merger.key)
    grid = pd.MultiIndex.from_product([sorted(merger.key),range(2020,2025)],names=['key','year']).to_frame(index=False)
    p = grid.merge(papi.pivot(index=['key','year'],columns='dimension',values='score').reset_index(),on=['key','year'],how='left',validate='one_to_one')
    p = p.merge(dti[['key','year','dti_total','dti_gov','dti_soc','dti_econ']],on=['key','year'],how='left',validate='one_to_one')
    p = p.merge(controls[['key','year','pop','urban_share','grdp_pc']],on=['key','year'],how='left',validate='one_to_one')
    p = p.merge(merger[['key','province_old','province_new','new_key','merged']],on='key',validate='many_to_one')
    assert len(p)==315
    p['ln_grdp_pc']=np.log(p.grdp_pc); p['ln_pop']=np.log(p['pop']); p['urban_pp']=100*p.urban_share
    return p,merger

# Exact labels from annual official workbooks. These are label-consistent indicators,
# not a claim that questionnaires, denominators and scoring are invariant.
ITEMS = {
 'portal_access':'Access to E-Government Portals',
 'internet_access':'Access to the Internet',
 'responsiveness':'E-Reponsiveness of Provincial Authorities',
 'info_certification':'Access to Adequate Information about Certification Procedures Online',
 'info_land':'Access to Adequate Information about Land Use Rights Certification Procedures On',
 'internet_news':'Proportion of Respondents that Get Access to Information from the Internet',
 'internet_home':'Proportion of Respondents that Get Access to the Internet at Home',
 'portal_personal_papers':'Proportion of Respondents Who Used Local Government E-Service Portal',
 'portal_user_friendly':'Proportion of Respondents that Knows Provincial Website and Thinks It is User-Friendly',
 'draft_comments':'Proportion of Respondents Aware that Province Posted Draft Regulation for Comments',
 'portal_general_use':'Used Online Government Service Portal',
 'online_payment':'Able to Pay for Service Online',
 'construction_info':'Access to Adequate Information about Construction Permit Procedures Online',
}

def extract_items(p):
    rows=[]; cross=[]
    for year in range(2020,2025):
        files=list((RAW/'papi_official').glob(f'*{year}*'))
        assert len(files)==1,files
        f=files[0]; book=openpyxl.load_workbook(f,read_only=True,data_only=True)
        sheet=book.worksheets[0]; cells=list(sheet.iter_rows(values_only=True))
        names=cells[1]; codes=cells[0]
        for item,label in ITEMS.items():
            found=[(i,r) for i,r in enumerate(cells,1) if str(r[0]).rstrip('*').strip()==label]
            assert len(found)<=1,(year,item,found)
            if not found:
                cross.append(dict(year=year,item=item,label=label,available=False,source=f.name,sheet=sheet.title,row=None,scale=None,observed_n=0))
                continue
            i,r=found[0]; count=0
            for j,name in enumerate(names):
                if j<3 or not isinstance(codes[j],(int,float)) or not name: continue
                value=r[j]
                score=isinstance(value,(int,float)) and np.isfinite(value)
                # Composite scores cannot be zero; genuine zero percentages are valid.
                if item in ['portal_access','internet_access','responsiveness'] and score and value<=0: score=False
                value=float(value) if score else np.nan
                count+=int(score)
                rows.append(dict(key=norm(name),year=year,item=item,value=value,
                                 source=f.name,sheet=sheet.title,row=i,column=j+1,province_code=int(codes[j])))
            cross.append(dict(year=year,item=item,label=r[0],available=True,source=f.name,
                              sheet=sheet.title,row=i,scale=r[2],observed_n=count))
        book.close()
    items=pd.DataFrame(rows); unique(items,['key','year','item'])
    items=items.merge(p[['key','year','egovernance']],on=['key','year'],validate='many_to_one')
    items['raw_extracted_value']=items.value
    items['province_dimension_available']=items.egovernance.notna()
    # Zero-filled cells in suppressed province-years are not valid zero percentages.
    items.loc[~items.province_dimension_available,'value']=np.nan
    items=items.drop(columns='egovernance')
    cross=pd.DataFrame(cross)
    eligible=items.groupby(['year','item']).value.count()
    cross['eligible_observed_n']=[int(eligible.get((r.year,r.item),0)) for r in cross.itertuples()]
    save(items,'T0_item_provenance'); save(cross,'T0_measurement_crosswalk')
    p=p.merge(items.pivot(index=['key','year'],columns='item',values='value').reset_index(),on=['key','year'],how='left',validate='one_to_one')
    p['service_facing']=p.portal_access+p.responsiveness
    check=p.dropna(subset=['egovernance','internet_access','service_facing'])
    diff=(check.egovernance-check.internet_access-check.service_facing).abs().max()
    assert diff<1e-5,diff
    # Equally weighted raw percentage diagnostic; not an official or psychometric score.
    p['common_service_items']=p[['info_certification','info_land','portal_personal_papers','portal_user_friendly','draft_comments']].mean(axis=1,skipna=False)
    save(p,'T0_panel'); save(p[p.egovernance.isna()][['key','year','province_old']],'T0_missing_egovernance')
    return p,float(diff)

def descriptive(p):
    cols=['egovernance','service_facing','internet_access','dti_gov']
    out=[]
    for year,d in p.groupby('year'):
        for v in cols:
            x=d[v].dropna()
            out.append(dict(year=year,var=v,n=len(x),mean=x.mean(),sd=x.std(),cv=x.std()/x.mean(),iqr=x.quantile(.75)-x.quantile(.25)))
    save(pd.DataFrame(out),'T1_descriptive')
    # Optional legacy convergence diagnostic, correct finite-interval mapping.
    out=[]
    for v in ['egovernance','dti_gov','dti_total']:
        w=p.pivot(index='key',columns='year',values=v)[[2020,2024]].dropna()
        b=pd.DataFrame({'g':np.log(w[2024]/w[2020])/4,'l0':np.log(w[2020])})
        fit=smf.ols('g ~ l0',b).fit(cov_type='HC3'); beta=fit.params['l0']
        speed=-np.log1p(4*beta)/4 if 0<1+4*beta<1 else np.nan
        out.append(dict(var=v,n=len(w),beta=beta,se=fit.bse['l0'],p=fit.pvalues['l0'],half_life_diagnostic=np.log(2)/speed))
    save(pd.DataFrame(out),'T1_convergence_diagnostic')

def bootstrap_corr(a,b,rng,B=5000):
    # Vectorized row-wise rank bootstrap, retaining ties in resampled provinces.
    idx=rng.integers(0,len(a),(B,len(a)))
    aa=stats.rankdata(a[idx],axis=1); bb=stats.rankdata(b[idx],axis=1)
    aa-=aa.mean(axis=1,keepdims=True); bb-=bb.mean(axis=1,keepdims=True)
    return (aa*bb).sum(axis=1)/np.sqrt((aa**2).sum(axis=1)*(bb**2).sum(axis=1))

def alignment(p):
    rng=np.random.default_rng(SEED+1); rows=[]; delta=[]
    for outcome in ['egovernance','service_facing','internet_access','common_service_items']:
        for supply in ['dti_gov','dti_total','dti_soc']:
            for year,d in p.groupby('year'):
                d=d.dropna(subset=[outcome,supply]); sims=bootstrap_corr(d[supply].to_numpy(),d[outcome].to_numpy(),rng)
                rows.append(dict(year=year,outcome=outcome,supply=supply,n=len(d),rho=stats.spearmanr(d[supply],d[outcome]).statistic,
                                 ci_low=np.quantile(sims,.025),ci_high=np.quantile(sims,.975),
                                 kendall=stats.kendalltau(d[supply],d[outcome]).statistic,pearson=stats.pearsonr(d[supply],d[outcome]).statistic))
        w=p.pivot(index='key',columns='year',values=[outcome,'dti_gov'])
        w=w.loc[:,[(outcome,2020),(outcome,2024),('dti_gov',2020),('dti_gov',2024)]].dropna()
        a=w.to_numpy(); idx=rng.integers(0,len(a),(10000,len(a)))
        def rb(i,j):
            x=stats.rankdata(a[idx,i],axis=1); y=stats.rankdata(a[idx,j],axis=1)
            x-=x.mean(axis=1,keepdims=True); y-=y.mean(axis=1,keepdims=True)
            return (x*y).sum(1)/np.sqrt((x*x).sum(1)*(y*y).sum(1))
        sims=rb(1,3)-rb(0,2)
        r0=stats.spearmanr(a[:,0],a[:,2]).statistic; r1=stats.spearmanr(a[:,1],a[:,3]).statistic
        delta.append(dict(outcome=outcome,n=len(a),rho2020=r0,rho2024=r1,delta=r1-r0,
                          ci_low=np.quantile(sims,.025),ci_high=np.quantile(sims,.975),bootstrap_draws=10000))
    save(pd.DataFrame(rows),'T2_alignment'); save(pd.DataFrame(delta),'T2_endpoint_change')
    fig,ax=plt.subplots(figsize=(7,3.8))
    for v,label in [('egovernance','Full PAPI e-governance'),('service_facing','Portal access + responsiveness'),('internet_access','Internet access')]:
        d=pd.DataFrame(rows).query('outcome==@v and supply=="dti_gov"')
        ax.errorbar(d.year,d.rho,yerr=[d.rho-d.ci_low,d.ci_high-d.rho],marker='o',capsize=3,label=label)
    ax.axhline(0,color='grey',lw=.7); ax.set_xticks(range(2020,2025)); ax.set_ylabel('Spearman correlation with DTI government'); ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(FIG/'F2_alignment.png',dpi=300);plt.close(fig)
    return pd.DataFrame(rows),pd.DataFrame(delta)

def residualize(d,cols):
    arr=d[cols].astype(float).copy()
    for _ in range(2000):
        old=arr.to_numpy().copy()
        arr-=arr.groupby(d.key).transform('mean'); arr-=arr.groupby(d.year).transform('mean')
        if np.max(np.abs(arr.to_numpy()-old))<1e-11: break
    else: raise RuntimeError('FE projection did not converge')
    assert arr.groupby(d.key).mean().abs().to_numpy().max()<1e-9
    return arr

CTRL=['ln_grdp_pc','urban_pp','ln_pop']
def fe(d,outcome,x):
    d=d.dropna(subset=[outcome]+x).copy(); pan=d.set_index(['key','year'])
    fit=PanelOLS(pan[outcome],pan[x],entity_effects=True,time_effects=True,drop_absorbed=True).fit(cov_type='clustered',cluster_entity=True)
    w=residualize(d,[outcome]+x)
    y=w[outcome].to_numpy(); X=w[x].to_numpy(); err=y-X@fit.params.reindex(x).to_numpy()
    r2=1-err@err/(y@y)
    without=X[:,1:]; e0=y-without@np.linalg.lstsq(without,y,rcond=None)[0] if without.shape[1] else y
    partial=1-err@err/(e0@e0)
    rows=[]
    for t in x:
        if 'dti' not in t: continue
        lo,hi=fit.conf_int().loc[t]
        rows.append(dict(term=t,coef=fit.params[t],se=fit.std_errors[t],p=fit.pvalues[t],ci_low=lo,ci_high=hi,
                         n=len(d),clusters=d.key.nunique(),r2_twfe=r2,partial_r2_first_regressor=partial))
    return rows,fit,d

def wild_cluster(d,outcome,x,B=4999):
    # Restricted wild cluster bootstrap-t; fixed covariates, Rademacher province signs.
    y=d[outcome].to_numpy()
    F=pd.get_dummies(d[['key','year']].astype(str),drop_first=True,dtype=float)
    base=np.column_stack([np.ones(len(d)),F.to_numpy(),d[x[1:]].to_numpy()])
    full=np.column_stack([base,d[x[0]].to_numpy()])
    q0=np.linalg.qr(base,mode='reduced')[0]; q=np.linalg.qr(full,mode='reduced')[0]
    xr=d[x[0]].to_numpy()-q0@(q0.T@d[x[0]].to_numpy()); xx=xr@xr
    e0=y-q0@(q0.T@y); er=y-q@(q.T@y); b=xr@y/xx
    codes=pd.factorize(d.key)[0]; G=codes.max()+1
    indicator=np.eye(G)[codes]
    factor=G/(G-1)*(len(d)-1)/(len(d)-np.linalg.matrix_rank(full))
    def se(e): return np.sqrt(factor*np.sum((indicator.T@(xr[:,None]*e))**2,axis=0))/xx
    t_obs=b/se(er[:,None])[0]; rng=np.random.default_rng(SEED+2); ts=[]
    for start in range(0,B,250):
        signs=rng.choice([-1.,1.],(G,min(250,B-start)))
        ystar=e0[:,None]*signs[codes]
        est=xr@ystar/xx; residual=ystar-q@(q.T@ystar)
        ts.extend(est/se(residual))
    return dict(coef=b,t_stat=t_obs,p_wild=(1+np.sum(np.abs(ts)>=abs(t_obs)))/(B+1),draws=B,clusters=G)

def panel(p):
    z=p.sort_values(['key','year']).copy()
    outcomes=['egovernance','service_facing','internet_access','common_service_items','portal_personal_papers','portal_user_friendly',
              'admin_procedures','public_services','transparency','participation','accountability','anticorruption','environment','total']
    for c in outcomes+['dti_gov','dti_total','dti_econ','dti_soc']:
        z['z_'+c]=z.groupby('year')[c].transform(lambda x:(x-x.mean())/x.std())
    z['lag_dti']=z.groupby('key').z_dti_gov.shift(1)
    rows=[]; wild=[]
    for outcome in ['egovernance','service_facing','internet_access','common_service_items']:
        y='z_'+outcome
        lag=z.dropna(subset=[y,'lag_dti','z_dti_gov']+CTRL)
        specs=[('TWFE',z,['z_dti_gov']),('TWFE controls',z,['z_dti_gov']+CTRL),
               ('TWFE common lag sample',lag,['z_dti_gov']+CTRL),('Lag common sample',lag,['lag_dti']+CTRL),
               ('Current and lag',lag,['z_dti_gov','lag_dti']+CTRL),
               ('Three pillars',z,['z_dti_gov','z_dti_econ','z_dti_soc']+CTRL),
               ('TWFE 2022-2024',z[z.year.ge(2022)],['z_dti_gov']+CTRL)]
        complete=z.dropna(subset=[y,'z_dti_gov']+CTRL).groupby('key').year.count()
        balanced=z[z.key.isin(complete[complete.eq(5)].index)]
        specs.append(('Balanced provinces',balanced,['z_dti_gov']+CTRL))
        for model,d,x in specs:
            result,fit,used=fe(d,y,x)
            for r in result: rows.append(dict(outcome=outcome,model=model,**r))
            if model=='TWFE controls': wild.append(dict(outcome=outcome,**wild_cluster(used,y,x)))
        # Differences are constructed on the full year grid before dropping missing pairs.
        fd=z[['key','year',y,'z_dti_gov']+CTRL].copy()
        for c in [y,'z_dti_gov']+CTRL: fd[c]=fd.groupby('key')[c].diff()
        fd=fd.dropna(); formula=y+' ~ z_dti_gov + '+' + '.join(CTRL)+' + C(year)'
        fit=smf.ols(formula,fd).fit(cov_type='cluster',cov_kwds={'groups':fd.key},use_t=True)
        lo,hi=fit.conf_int().loc['z_dti_gov']
        rows.append(dict(outcome=outcome,model='Adjacent first differences + year FE',term='z_dti_gov',coef=fit.params['z_dti_gov'],se=fit.bse['z_dti_gov'],p=fit.pvalues['z_dti_gov'],ci_low=lo,ci_high=hi,n=len(fd),clusters=fd.key.nunique(),r2_twfe=np.nan,partial_r2_first_regressor=np.nan))
    save(pd.DataFrame(rows),'T3_panel');save(pd.DataFrame(wild),'T3_wild_cluster')
    # Full within/between decomposition of every time-varying regressor, same sample.
    d=z.dropna(subset=['z_egovernance','z_dti_gov']+CTRL).copy()
    for c in ['z_dti_gov']+CTRL:
        d[c+'_bar']=d.groupby('key')[c].transform('mean'); d[c+'_dev']=d[c]-d[c+'_bar']
    terms=[c+s for c in ['z_dti_gov']+CTRL for s in ['_bar','_dev']]
    fit=smf.ols('z_egovernance ~ '+' + '.join(terms)+' + C(year)',d).fit(cov_type='cluster',cov_kwds={'groups':d.key},use_t=True)
    save(pd.DataFrame([dict(term=t,coef=fit.params[t],se=fit.bse[t],p=fit.pvalues[t]) for t in terms]),'T3_within_between')
    # Exploratory outcome family; do not reinterpret other dimensions as negative controls.
    specs=[]
    for v in outcomes:
        r,_,_=fe(z,'z_'+v,['z_dti_gov']+CTRL);specs.append(dict(outcome=v,**r[0]))
    family=pd.DataFrame(specs); family['p_holm_all_reported_outcomes']=multipletests(family.p,method='holm')[1]
    save(family,'T3_specificity_exploratory')
    # Common-sample difference in associations, accounting for shared outcome covariance.
    comps=[]
    for v in ['internet_access','service_facing','accountability','transparency']:
        zz=z.copy(); zz['contrast']=zz.z_egovernance-zz['z_'+v]
        r,_,_=fe(zz,'contrast',['z_dti_gov']+CTRL);comps.append(dict(comparison='full minus '+v,**r[0]))
    save(pd.DataFrame(comps),'T3_outcome_contrasts')
    return pd.DataFrame(rows),pd.DataFrame(wild)

def dispersion(x,w,c,kind='variance'):
    w=np.asarray(w)/np.sum(w); mu=w@x; k=max(c)+1
    wg=np.bincount(c,weights=w,minlength=k); sx=np.bincount(c,weights=w*x,minlength=k)
    mask=wg>0; mg=sx[mask]/wg[mask]
    if kind=='variance':
        total=w@((x-mu)**2); between=wg[mask]@((mg-mu)**2)
    else:
        assert np.all(x>0)
        total=w@((x/mu)*np.log(x/mu));between=wg[mask]@((mg/mu)*np.log(mg/mu))
    return total,between,total-between,(total-between)/total

def adjacency(merger):
    # Reproducible queen contiguity from exact shared vertices of stored 2008 geometry.
    geo=json.loads((DATA/'geo/geoBoundaries-VNM-ADM1_simplified.geojson').read_text(encoding='utf-8'))
    vertices=collections.defaultdict(set)
    for f in geo['features']:
        name=norm(f['properties']['shapeName']); geom=f['geometry']
        for poly in (geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]):
            for ring in poly:
                for pt in ring: vertices[tuple(pt)].add(name)
    keys=sorted(merger.key); lookup={s:i for i,s in enumerate(keys)}; adj=[set() for _ in keys]; edges=set()
    for names in vertices.values():
        for a in names:
            for b in names:
                if a!=b:
                    adj[lookup[a]].add(lookup[b]); edges.add(tuple(sorted([a,b])))
    save(pd.DataFrame(sorted(edges),columns=['key_a','key_b']),'T6_adjacency_2008')
    assert all(adj), 'Isolated graph nodes'
    return keys,adj

def connected(members,adj):
    if len(members)<2: return True
    seen={members[0]}; todo=list(seen); allowed=set(members)
    while todo:
        u=todo.pop()
        for v in adj[u]&allowed-seen: seen.add(v);todo.append(v)
    return len(seen)==len(members)

def spatial_draws(c0,adj,B=4000):
    # Symmetric all-node swap proposals preserving sizes; conditioned on connected groups.
    # Four local chains. Their empirical output is a sensitivity distribution, not a
    # certified uniform draw from every feasible administrative partition.
    all_draws=[];diag=[]
    edges=np.array([(i,j) for i,neighbors in enumerate(adj) for j in neighbors if i<j])
    for chain in range(4):
        rng=np.random.default_rng(SEED+100+chain); c=c0.copy(); accepted=0; sampled=[]; proposals=0
        groups={g:list(np.where(c==g)[0]) for g in np.unique(c)}
        assert all(connected(m,adj) for m in groups.values()), 'Actual group not connected in stored graph'
        burn=50000;thin=500
        for step in range(burn+(B//4)*thin):
            # Fixed mixture of graph-edge and all-node proposals is symmetric,
            # with more local moves and retained support for distant exchanges.
            if rng.random()<.5: i,j=edges[rng.integers(len(edges))]
            else: i,j=rng.choice(len(c),2,replace=False)
            a,b=c[i],c[j]; proposals+=1
            if a!=b:
                ga=[j if u==i else u for u in groups[a]];gb=[i if u==j else u for u in groups[b]]
                if connected(ga,adj) and connected(gb,adj):
                    c[i],c[j]=b,a;groups[a]=ga;groups[b]=gb;accepted+=1
            if step>=burn and (step-burn)%thin==0: sampled.append(c.copy())
        all_draws.extend(sampled)
        signatures={tuple(sorted(tuple(sorted(np.where(s==g)[0])) for g in np.unique(s))) for s in sampled}
        diag.append(dict(chain=chain,proposals=proposals,accepted=accepted,acceptance_rate=accepted/proposals,sampled=len(sampled),unique_partitions=len(signatures),burn=burn,thin=thin))
    save(pd.DataFrame(diag),'T6_spatial_chain_diagnostics')
    np.save(OUT/'T6_spatial_partitions.npy',np.array(all_draws))
    return np.array(all_draws)

def aggregation(p,merger):
    keys,adj=adjacency(merger); map_sorted=merger.set_index('key').loc[keys]
    codes=pd.factorize(map_sorted.new_key)[0]; draws=spatial_draws(codes,adj)
    rng=np.random.default_rng(SEED+3); unrestricted=np.array([rng.permutation(codes) for _ in range(5000)])
    rows=[];bench=[];moran=[];chainstats=[]
    for year in [2022,2023,2024]:
        full=p[p.year.eq(year)].set_index('key').loc[keys].reset_index()
        # Joint sample for every variable: fixed full 63-slot partitions, then mask.
        mask=full[['egovernance','service_facing','internet_access','dti_gov','dti_total','pop']].notna().all(axis=1).to_numpy()
        w=full.loc[mask,'pop'].to_numpy(); c=codes[mask]
        for v in ['egovernance','service_facing','internet_access','dti_gov','dti_total']:
            x=full.loc[mask,v].to_numpy()
            for kind in ['variance','theil']:
                total,between,within,share=dispersion(x,w,c,kind)
                rows.append(dict(year=year,var=v,metric=kind,n=len(x),total=total,between=between,within=within,within_share=share))
                for scheme,assignments in [('unrestricted',unrestricted),('connected_local_chains',draws)]:
                    sims=np.array([dispersion(x,w,a[mask],kind)[3] for a in assignments])
                    bench.append(dict(year=year,var=v,metric=kind,scheme=scheme,n=len(x),observed=share,mean=sims.mean(),q05=np.quantile(sims,.05),q95=np.quantile(sims,.95),p_lower_mc=(1+(sims<=share).sum())/(len(sims)+1),p_upper_mc=(1+(sims>=share).sum())/(len(sims)+1),draws=len(sims)))
                    if scheme=='connected_local_chains':
                        for chain,s in enumerate(np.array_split(sims,4)):
                            chainstats.append(dict(year=year,var=v,metric=kind,chain=chain,mean=s.mean(),lag1_correlation=np.corrcoef(s[:-1],s[1:])[0,1]))
            # Moran statistic on common observed nodes, binary queen adjacency.
            indices=np.flatnonzero(mask); W=np.array([[int(j in adj[i]) for j in indices] for i in indices],float)
            centered=x-x.mean()
            I=len(x)/W.sum()*(centered@W@centered)/(centered@centered)
            sims=[]
            for _ in range(1999):
                t=rng.permutation(centered); sims.append(len(x)/W.sum()*(t@W@t)/(t@t))
            expected=-1/(len(x)-1)
            moran.append(dict(year=year,var=v,n=len(x),moran_I=I,expected_I=expected,p_two_sided_mc=(1+sum(abs(s-expected)>=abs(I-expected) for s in sims))/2000))
    save(pd.DataFrame(rows),'T6_dispersion');save(pd.DataFrame(bench),'T6_benchmarks');save(pd.DataFrame(moran),'T6_moran');save(pd.DataFrame(chainstats),'T6_chain_statistic_diagnostics')
    # Translation invariance of variance is checked; Theil scale sensitivity disclosed.
    full=p[p.year.eq(2024)].set_index('key').loc[keys].reset_index();mask=full.egovernance.notna().to_numpy()
    x=full.loc[mask,'egovernance'].to_numpy(); w=full.loc[mask,'pop'].to_numpy(); c=codes[mask]
    sens=[]
    for offset in [-1,0,1,5]:
        for kind in ['variance','theil']:
            sens.append(dict(outcome='egovernance',offset=offset,metric=kind,within_share=dispersion(x+offset,w,c,kind)[3]))
    save(pd.DataFrame(sens),'T6_scale_sensitivity')
    # Missing PAPI endpoint sensitivity: observed-range imputations, scenario only.
    missing=full.egovernance.isna(); low=full.egovernance.min();high=full.egovernance.max();sc=[]
    import itertools
    for vals in itertools.product([low,high],repeat=int(missing.sum())):
        x=full.egovernance.to_numpy().copy();x[missing]=vals
        sc.append(dict(imputed_keys=';'.join(full.loc[missing,'key']),imputed_values=';'.join(map(str,vals)),variance_within_share=dispersion(x,full['pop'].to_numpy(),codes)[3],scenario='observed-range endpoints, not identified bounds'))
    save(pd.DataFrame(sc),'T6_missing_scenarios')
    gaps=[]
    for name,d in p[p.year.eq(2024)].groupby('province_new'):
        row=dict(province_new=name,n_old=len(d),members='; '.join(d.province_old))
        for v in ['egovernance','service_facing','dti_gov']:
            s=d.dropna(subset=[v]);row[v+'_n']=len(s)
            row[v+'_range']=s[v].max()-s[v].min() if len(s)>1 else np.nan
            row[v+'_wmean']=np.average(s[v],weights=s['pop']) if len(s) else np.nan
        gaps.append(row)
    gap=pd.DataFrame(gaps);save(gap,'T6_constituent_gaps')
    # Official aggregation is total DTI only; do not extend to government pillar.
    off=pd.read_csv(DATA/'dti_2024_34.csv');off['new_key']=off.province.map(norm)
    mean=p[p.year.eq(2024)].groupby('new_key').dti_total.mean().rename('simple_mean').reset_index()
    off=off.merge(mean,on='new_key',validate='one_to_one');off['absolute_difference']=(off.dti_total-off.simple_mean).abs();save(off,'T6_official34_check')
    # Published range figure, with missing observations explicitly marked.
    display=gap[gap.n_old.gt(1)].sort_values('egovernance_range');fig,axs=plt.subplots(1,2,figsize=(8.6,6),sharey=True)
    for i,row in enumerate(display.itertuples()):
        d=p[(p.year.eq(2024))&p.province_new.eq(row.province_new)]
        for ax,v in zip(axs,['egovernance','dti_gov']):
            s=d[v].dropna().sort_values();ax.plot(s,[i]*len(s),color='grey',lw=1);ax.scatter(s,[i]*len(s),s=18)
    axs[0].set_yticks(range(len(display)));axs[0].set_yticklabels([r.province_new+(' *' if r.egovernance_n<r.n_old else '') for r in display.itertuples()],fontsize=8)
    axs[0].set_xlabel('PAPI e-governance, 2024');axs[1].set_xlabel('DTI government, 2024');fig.tight_layout();fig.savefig(FIG/'F5_constituent_gaps.png',dpi=300);plt.close(fig)
    return pd.DataFrame(rows),pd.DataFrame(bench),gap

def ridge_predict(X,y,Xtest,alpha):
    mean=X.mean(axis=0);sd=X.std(axis=0);sd[sd<1e-12]=1
    a=(X-mean)/sd;b=(Xtest-mean)/sd;center=y.mean()
    coef=np.linalg.solve(a.T@a+alpha*np.eye(a.shape[1]),a.T@(y-center))
    return center+b@coef

def predictive(p):
    # Concurrent-year cross-province validation on raw targets: every target province
    # is held out in both outer and inner folds; all scaling fitted on training data.
    rows=[];preds=[];rng=np.random.default_rng(SEED+4)
    for outcome in ['egovernance','service_facing']:
        d=p[p.year.ge(2022)].dropna(subset=[outcome,'dti_gov']+CTRL).reset_index(drop=True)
        year=pd.get_dummies(d.year,prefix='year',dtype=float)
        specs={'Controls':CTRL,'DTI':['dti_gov'],'Controls + DTI':CTRL+['dti_gov']}
        for rep in range(5):
            groups=sorted(d.key.unique());rng.shuffle(groups);fid={g:i%5 for i,g in enumerate(groups)}
            f=d.key.map(fid).to_numpy()
            for label,cols in specs.items():
                X=pd.concat([d[cols],year],axis=1).to_numpy(); y=d[outcome].to_numpy();pr=np.empty(len(d))
                for fold in range(5):
                    tr=np.flatnonzero(f!=fold);te=np.flatnonzero(f==fold)
                    # Explicit small ridge implementation avoids opaque library CV defaults.
                    train_groups=sorted(d.key.iloc[tr].unique())
                    inner_map={g:i%4 for i,g in enumerate(train_groups)}
                    inner=d.key.iloc[tr].map(inner_map).to_numpy()
                    losses=[];alphas=np.logspace(-2,3,7)
                    for alpha in alphas:
                        error=[]
                        for inner_fold in range(4):
                            a=tr[inner!=inner_fold];b=tr[inner==inner_fold]
                            fitted=ridge_predict(X[a],y[a],X[b],alpha)
                            error.extend((y[b]-fitted)**2)
                        losses.append(np.mean(error))
                    alpha=alphas[np.argmin(losses)]
                    pr[te]=ridge_predict(X[tr],y[tr],X[te],alpha)
                r2=1-np.sum((y-pr)**2)/np.sum((y-y.mean())**2)
                rows.append(dict(outcome=outcome,model=label,repeat=rep,n=len(d),r2=r2,rmse=np.sqrt(np.mean((y-pr)**2))))
                for i in range(len(d)):preds.append(dict(outcome=outcome,model=label,repeat=rep,key=d.key[i],year=int(d.year[i]),observed=y[i],prediction=pr[i]))
    out=pd.DataFrame(rows);pred=pd.DataFrame(preds);save(out,'T5_prediction_repeats');save(pred,'T5_oof_predictions')
    summary=out.groupby(['outcome','model']).agg(r2_mean=('r2','mean'),r2_split_sd=('r2','std'),rmse_mean=('rmse','mean'),n=('n','first')).reset_index();save(summary,'T5_prediction_summary')
    contrasts=[]
    for outcome in ['egovernance','service_facing']:
        d=pred[pred.outcome.eq(outcome)].copy();d['se']=(d.observed-d.prediction)**2
        w=d.groupby(['key','model']).se.mean().unstack()
        diff=(w['Controls + DTI']-w['Controls']).to_numpy();idx=rng.integers(0,len(diff),(10000,len(diff)))
        sims=diff[idx].mean(axis=1)
        contrasts.append(dict(outcome=outcome,delta_mse_combined_minus_controls=diff.mean(),ci_low=np.quantile(sims,.025),ci_high=np.quantile(sims,.975),clusters=len(diff),interpretation='equal-province mean loss, conditional on fitted CV models'))
    save(pd.DataFrame(contrasts),'T5_incremental_validation')
    return summary,pd.DataFrame(contrasts)

def manifest():
    rows=[]
    for path in sorted((ROOT/'DataPaper3').rglob('*')):
        if path.is_file(): rows.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
    save(pd.DataFrame(rows),'INPUT_SHA256')
    packages=['numpy','pandas','scipy','statsmodels','linearmodels','matplotlib','openpyxl']
    versions={p:importlib.metadata.version(p) for p in packages}
    (OUT/'environment.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),seed=SEED,packages=versions),indent=2),encoding='utf-8')
    (ROOT/'requirements-upgrade.txt').write_text('\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n',encoding='utf-8')

def main():
    print('Preparing validated inputs',flush=True);p,merger=prepare();p,component_error=extract_items(p);descriptive(p)
    print('Bootstrapping alignment and endpoint changes',flush=True);corr,change=alignment(p)
    print('Refitting matched-sample panel models and wild cluster tests',flush=True);models,wild=panel(p)
    print('Sampling geographically connected sensitivity partitions',flush=True);disp,bench,gaps=aggregation(p,merger)
    print('Nested province-grouped prediction with controls-only baseline',flush=True);prediction,increment=predictive(p)
    manifest()
    key=dict(component_reconstruction_max_error=component_error,
             endpoint_changes=change.to_dict('records'),wild_cluster=wild.to_dict('records'),prediction=prediction.to_dict('records'),incremental_validation=increment.to_dict('records'),
             main_models=models[models.model.eq('TWFE controls')].to_dict('records'),
             dispersion2024=disp[disp.year.eq(2024)].to_dict('records'),benchmarks2024=bench[bench.year.eq(2024)&bench.metric.eq('variance')].to_dict('records'))
    (OUT/'KEY_RESULTS.json').write_text(json.dumps(key,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Complete:',OUT,flush=True)

if __name__=='__main__': main()
