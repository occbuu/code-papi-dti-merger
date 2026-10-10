"""Independent checks of cleaned values against immutable local raw downloads."""
from pathlib import Path
import json
import re
import sys
import numpy as np
import pandas as pd
import openpyxl
from P3_analysis_upgrade import norm, ROOT, RAW, DATA, OUT

DIM={1:'participation',2:'transparency',3:'accountability',4:'anticorruption',
     5:'admin_procedures',6:'public_services',7:'environment',8:'egovernance'}

def papi_check():
    rows=[]
    for year in range(2020,2025):
        f=next((RAW/'papi_official').glob(f'*{year}*'))
        b=openpyxl.load_workbook(f,read_only=True,data_only=True);s=b.worksheets[0]
        data=list(s.iter_rows(values_only=True));names=data[1];codes=data[0]
        for row_number,r in enumerate(data,1):
            match=re.match(r'Dimension (\d):',str(r[0]))
            dim=DIM[int(match[1])] if match else ('total' if r[0]=='Unweighted PAPI Score' else None)
            if not dim:continue
            for j,name in enumerate(names):
                if j<3 or not isinstance(codes[j],(int,float)) or not name:continue
                v=r[j];value=float(v) if isinstance(v,(int,float)) and v>0 else np.nan
                rows.append(dict(key=norm(name),year=year,dimension=dim,raw_score=value,source=f.name,sheet=s.title,row=row_number,column=j+1))
        b.close()
    raw=pd.DataFrame(rows);assert not raw.duplicated(['key','year','dimension']).any()
    cleaned=pd.read_csv(DATA/'papi_long.csv');cleaned=cleaned[cleaned.year.ge(2020)].copy();cleaned['key']=cleaned.province.map(norm)
    joined=cleaned.merge(raw,on=['key','year','dimension'],validate='one_to_one',how='outer',indicator=True)
    assert joined['_merge'].eq('both').all()
    assert joined.score.isna().equals(joined.raw_score.isna())
    joined['absolute_difference']=(joined.score-joined.raw_score).abs()
    assert joined.absolute_difference.max()<1e-9
    joined.drop(columns='_merge').to_csv(OUT/'T0_raw_PAPI_validation.csv',index=False,encoding='utf-8-sig')
    raw.to_csv(OUT/'T0_PAPI_rebuilt_2020_2024.csv',index=False,encoding='utf-8-sig')
    return dict(rows=len(raw),observed=int(raw.raw_score.notna().sum()),max_difference=float(joined.absolute_difference.max()))

def dti_check():
    # Parse static Vue table row text, never execute downloaded JavaScript.
    candidates=[]
    for f in (RAW/'dti').glob('*.js'):
        text=f.read_text(encoding='utf-8')
        starts=list(re.finditer(r'\w\("tr",',text))
        for i,m in enumerate(starts):
            block=text[m.start():starts[i+1].start() if i+1<len(starts) else len(text)]
            scores=re.findall(r'\(0,(\d+)\)',block)
            strings=re.findall(r'\._v\(("(?:\\.|[^"\\])*")\)',block)
            labels=[]
            for string in strings:
                value=json.loads(string).strip()
                if any(ch.isalpha() for ch in value) and '(' not in value:
                    labels.append(value)
            if len(scores)>=4 and labels:
                candidates.append(dict(key=norm(labels[0]),values=np.array([float('0.'+s) for s in scores[:4]]),source=f.name,offset=m.start()))
    cleaned=pd.concat([pd.read_csv(DATA/'dti.csv'),pd.read_csv(DATA/'dti_2024_63.csv')],ignore_index=True)
    rows=[]
    for r in cleaned.itertuples():
        value=np.array([r.dti_total,r.dti_gov,r.dti_econ,r.dti_soc]);key=norm(r.province)
        matches=[s for s in candidates if s['key']==key and np.max(np.abs(s['values']-value))<1e-9]
        rows.append(dict(key=key,year=r.year,matched_raw_row=bool(matches),matches=len(matches),
                         sources='; '.join(sorted({s['source'] for s in matches}))))
    checked=pd.DataFrame(rows);checked.to_csv(OUT/'T0_raw_DTI_validation.csv',index=False,encoding='utf-8-sig')
    assert checked.matched_raw_row.all(),checked[~checked.matched_raw_row]
    return dict(rows=len(checked),matched=int(checked.matched_raw_row.sum()),note='Scores and province labels checked; year assignment follows source inventory, not inferred from equal values.')

def controls_check():
    population=json.loads((RAW/'nso/V02.03-07_population_urban.json').read_text(encoding='utf-8'))
    maps=[dict(zip(v['values'],v['valueTexts'])) for v in population['meta']['variables']]
    rec=[]
    for d in population['data']['data']:
        k=d['key'];labels=[maps[i][code] for i,code in enumerate(k)]
        try:value=float(d['values'][0]);year=int(labels[-1])
        except (ValueError,TypeError):continue
        rec.append(dict(key=norm(labels[0].replace('Ð','Đ')),category=labels[1],year=year,value=value))
    pop=pd.DataFrame(rec)
    # JSON-stat raw response contains trailing transport text; decode first JSON object.
    text=(RAW/'nso/V03.12_grdp_per_capita.json').read_text(encoding='utf-8')
    dataset=json.JSONDecoder().raw_decode(text)[0]['dataset'];dims=dataset['dimension']
    ids=dataset.get('id',dims.get('id'));sizes=dataset.get('size',dims.get('size'))
    if ids is None: raise ValueError(f'JSON-stat dimension metadata missing: {list(dims)}')
    labels=[]
    for name in ids:
        cat=dims[name]['category'];index=cat['index'];inv={i:cat['label'][k] for k,i in index.items()}
        labels.append(inv)
    values=dataset['value'];grdp=[]
    for flat,value in (values.items() if isinstance(values,dict) else enumerate(values)):
        if value is None:continue
        coord=np.unravel_index(int(flat),sizes);label=[labels[i][c] for i,c in enumerate(coord)]
        years=[int(match.group()) for s in label if (match:=re.search(r'20\d{2}',str(s)))]
        if len(years)!=1:continue
        grdp.append(dict(key=norm(label[0].replace('Ð','Đ')),year=years[0],raw_grdp=float(value)))
    grdp=pd.DataFrame(grdp)
    cleaned=pd.read_csv(DATA/'controls.csv');cleaned=cleaned[cleaned.year.between(2020,2024)].copy();cleaned['key']=cleaned.province.map(norm)
    # Locate categories by official labels, not numerical category positions.
    print('Population categories:',sorted(pop.category.unique()))
    totals=pop[pop.category.str.contains('Tổng số',case=False)].rename(columns={'value':'raw_pop'})
    urban=pop[pop.category.str.contains('Thành thị',case=False)].rename(columns={'value':'raw_urban_pop'})
    joined=cleaned.merge(totals[['key','year','raw_pop']],on=['key','year'],validate='one_to_one')
    joined=joined.merge(urban[['key','year','raw_urban_pop']],on=['key','year'],validate='one_to_one')
    joined=joined.merge(grdp,on=['key','year'],validate='one_to_one')
    if len(joined)!=315:
        missing=cleaned[['key','year']].merge(joined[['key','year']],on=['key','year'],how='left',indicator=True)
        raise ValueError(f'Raw control coverage {len(joined)}; missing {missing[missing._merge.eq("left_only")].to_dict("records")}')
    joined['raw_urban_share']=joined.raw_urban_pop/joined.raw_pop
    for clean,raw,tolerance in [('pop','raw_pop',1e-8),('urban_share','raw_urban_share',5e-5),('grdp_pc','raw_grdp',1e-8)]:
        joined[clean+'_abs_difference']=(joined[clean]-joined[raw]).abs()
        assert joined[clean+'_abs_difference'].max()<tolerance,(clean,joined[clean+'_abs_difference'].max())
    joined.to_csv(OUT/'T0_raw_controls_validation.csv',index=False,encoding='utf-8-sig')
    return dict(rows=len(joined),max_population_difference=float(joined.pop_abs_difference.max()),
                max_urban_share_difference=float(joined.urban_share_abs_difference.max()),max_grdp_difference=float(joined.grdp_pc_abs_difference.max()))

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    result=dict(PAPI=papi_check(),DTI=dti_check(),controls=controls_check())
    (OUT/'SOURCE_VALIDATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
