"""Data-driven scientific figures: PNG/SVG for inspection, inline TikZ for the editor.

Uses the stored historical geometry; never represents it as a certified 2025 map.
All coordinates, points and intervals in the manuscript are embedded, without inputs.
"""
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch
from matplotlib.colors import Normalize, to_hex
from P3_analysis_upgrade import norm

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results_upgrade'; FIG=ROOT/'figures_upgrade'
BLUE='#0072B2'; ORANGE='#D55E00'; GRAY='#707070'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})

def read(name): return pd.read_csv(OUT/(name+'.csv'))
def color(c): return '{rgb,255:red,%d;green,%d;blue,%d}'%tuple(round(float(v)*255) for v in matplotlib.colors.to_rgb(c))
def node(x,y,s,size='scriptsize',anchor='center'):
    return f'\\node[font=\\{size},anchor={anchor},align=center] at ({x:.4f},{y:.4f}) {{{s}}};'
def line(x1,y1,x2,y2,c=GRAY,opts=''):
    return f'\\draw[color={color(c)},line width=.45pt{opts}] ({x1:.4f},{y1:.4f})--({x2:.4f},{y2:.4f});'
def dot(x,y,c=BLUE,r=.035):
    return f'\\fill[{color(c)}] ({x:.4f},{y:.4f}) circle ({r}cm);'
def wrap(body,caption,label):
    return '\n'.join([r'\begin{figure}[p]',r'\centering',r'\resizebox{\linewidth}{!}{%',r'\begin{tikzpicture}[x=1cm,y=1cm]',body,r'\end{tikzpicture}}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{figure}'])
def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=220,bbox_inches='tight')
    fig.savefig(FIG/(name+'.svg'),bbox_inches='tight');plt.close(fig)
def geometry(p):
    geo=json.loads((ROOT/'DataPaper3/data/geo/geoBoundaries-VNM-ADM1_simplified.geojson').read_text(encoding='utf-8'))
    polys=[]
    for f in geo['features']:
        k=norm(f['properties']['shapeName'])
        assert k in set(p.key),k
        g=f['geometry']
        for rings in (g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]):
            polys.append((k,[np.asarray(r)[:,:2] for r in rings]))
    assert set(k for k,_ in polys)==set(p.key)
    return polys
def maps(p,polys,reform):
    count=2 if reform else 3
    fig,axs=plt.subplots(1,count,figsize=(11,7.2),layout='constrained')
    data=p.set_index('key'); group=data.new_key.to_dict(); groups=sorted(set(group.values()))
    palette=[to_hex(plt.get_cmap('tab20')(i)) for i in range(20)]+[to_hex(plt.get_cmap('tab20b')(i)) for i in range(14)]
    fields=['old','new'] if reform else ['dti_gov','egovernance','service_facing']
    titles=['(a) 63 former provinces','(b) 34 mapped provincial groups'] if reform else ['(a) DTI government','(b) Full PAPI e-governance','(c) Portal access + response']
    body=[]; coverage=[]
    # Equirectangular display at 16 degrees N, matching both renderings.
    project=lambda a: np.column_stack([(a[:,0]-102)*np.cos(np.deg2rad(16)),a[:,1]-8])
    for j,(ax,field,title) in enumerate(zip(axs,fields,titles)):
        base=j*5.0; scale=.42
        body.append(node(base+2,7.45,title,'small'))
        values=data[field] if not reform else None
        lo,hi=(float(values.min()),float(values.max())) if values is not None else (0,1)
        cmap=plt.get_cmap('viridis'); nn=Normalize(lo,hi)
        boundaries=defaultdict(list)
        for k,rings in polys:
            if field=='old': c='#E69F00' if data.loc[k,'merged'] else '#CACACA'
            elif field=='new': c=palette[groups.index(group[k])]
            else: c=to_hex(cmap(nn(values[k]))) if pd.notna(values[k]) else '#D0D0D0'
            for idx,r in enumerate(rings):
                q=project(r)
                ax.add_patch(Polygon(q,facecolor=c if idx==0 else 'white',edgecolor='white' if field!='new' else c,linewidth=.35))
                coords='--'.join(f'({base+scale*x:.4f},{scale*y:.4f})' for x,y in q)
                body.append(f'\\path[fill={color(c if idx==0 else "white")},draw={color("white" if field!="new" else c)},line width=.12pt] {coords}--cycle;')
                for a,b in zip(r[:-1],r[1:]):
                    edge=tuple(sorted([tuple(a),tuple(b)]));boundaries[edge].append(k)
        if field=='new':
            for edge,keys in boundaries.items():
                if len(keys)==1 or len({group[k] for k in keys})>1:
                    q=project(np.asarray(edge)); ax.plot(q[:,0],q[:,1],color='#555555',lw=.3)
                    body.append(line(base+scale*q[0,0],scale*q[0,1],base+scale*q[1,0],scale*q[1,1],GRAY))
        ax.set(xlim=(-.2,8.5),ylim=(-.5,16.4)); ax.set_aspect('equal');ax.axis('off');ax.set_title(title,fontsize=11)
        if values is not None:
            cb=fig.colorbar(plt.cm.ScalarMappable(norm=nn,cmap=cmap),ax=ax,orientation='horizontal',fraction=.045,pad=.025)
            cb.set_label('Published 2024 score' if field!='service_facing' else 'Sum of two published components')
            for i in range(60):
                xx=base+.15+i*3.0/60
                body.append(f'\\fill[{color(cmap(i/59))}] ({xx:.4f},-.45) rectangle ({xx+3/60:.4f},-.23);')
            body += [node(base+.15,-.65,f'{lo:.2f}'),node(base+3.15,-.65,f'{hi:.2f}'),node(base+1.65,-.98,'Score in original units')]
            coverage.append(dict(field=field,matched_geometry_keys=63,observed_scores=int(values.notna().sum()),min=lo,max=hi))
        else:
            body.append(node(base+1.7,-.5,'Merged: orange; unchanged: grey' if field=='old' else 'Colour identifies mapped groups'))
            if field=='old':
                for key,label in [('ha noi','Ha Noi'),('da nang','Da Nang'),('gia lai','Gia Lai'),('ho chi minh','Ho Chi Minh City')]:
                    rings=max((r for k,rr in polys if k==key for r in rr),key=len)
                    centre=project(rings).mean(axis=0); ax.annotate(label,centre,fontsize=7,xytext=(4,2),textcoords='offset points')
                    body.append(node(base+scale*centre[0]+.04,scale*centre[1]+.02,label,'tiny','west'))
        body.append(line(base+3.6,6.2,base+3.6,6.7,GRAY,',->'));body.append(node(base+3.6,6.9,'N'))
    foot='Generalised historical geometry; mapped groups, not an official 2025 boundary survey.'
    fig.suptitle(foot,fontsize=9)
    name='F1_reform_maps' if reform else 'F3_score_maps'
    save(fig,name)
    caption=('Study geography and the 2025 provincial grouping. Orange indicates the 52 former provinces assigned to 23 merged groups; grey indicates 11 unchanged provinces. Right: 34 groups reconstructed by removing internal edges of mapped constituent polygons; colours are identifiers, not scores. Labels orient readers to selected places. '
             if reform else 'Spatial distributions on the former provincial units, 2024. Each panel uses its own original score scale; colours are not directly comparable across measures. Grey denotes missing PAPI scores (two provinces); DTI is shown for all 63. This descriptive map does not identify significant local clusters or a numerical gap between differently scaled indices. ')
    caption+='Both figures use the stored generalised 2008 geoBoundaries geometry, with Hue relabelled and Con Dao assigned to Ba Ria--Vung Tau. They illustrate the analytical crosswalk and omit features absent from the source; they are not official contemporary boundary maps. Coordinates are displayed equirectangularly at 16 degrees N.'
    return wrap('\n'.join(body),caption,'fig:reformmap' if reform else 'fig:scoremap'),coverage

def workflow():
    boxes=[('1. Source integration','DTI + PAPI + NSO controls\\63 provinces; 2020--2024\\Keys, missingness, raw-source checks'),
           ('2. Measurement audit','Full e-governance = Internet + service sum\\Service sum = portal access + response\\Five recurring percentages: diagnostic only'),
           ('3. Territorial sensitivity','63 units mapped to 34 groups\\Variance + Theil; common observed sample\\5,000 unrestricted assignments\\4 connected chains: 50,000 burn-in each\\1,000 retained draws per chain; thinning 500'),
           ('4. Association and prediction','Province/year effects; matched lags; wild tests\\Ridge: 5 repeats of 5 province-grouped folds\\4 inner folds; controls-only baseline\\Pre-reform associations, not reform effects')]
    fig,ax=plt.subplots(figsize=(11,6));ax.set(xlim=(0,12),ylim=(0,8));ax.axis('off');body=[]
    for i,(title,txt) in enumerate(boxes):
        x=.2+(i%2)*6; y=4.3 if i<2 else .3
        ax.add_patch(FancyBboxPatch((x,y),5.4,3.2,boxstyle='round,pad=.13',fc='#EDF4F8',ec=BLUE))
        ax.text(x+2.7,y+2.65,title,ha='center',weight='bold',fontsize=11)
        ax.text(x+2.7,y+1.25,txt.replace('\\','\n'),ha='center',va='center',fontsize=9,linespacing=1.6)
        body.append(f'\\draw[rounded corners=4pt,draw={color(BLUE)},fill=blue!4] ({x},{y}) rectangle ({x+5.4},{y+3.2});')
        body.append(node(x+2.7,y+2.65,r'\textbf{'+title+'}','small'))
        body.append(node(x+2.7,y+1.25,txt))
    for a,b in [((5.7,5.9),(6.1,5.9)),((8.9,4.15),(2.9,3.65)),((5.7,1.9),(6.1,1.9))]:
        ax.annotate('',b,a,arrowprops={'arrowstyle':'->','color':BLUE}); body.append(line(*a,*b,BLUE,',->'))
    save(fig,'F2_workflow')
    return wrap('\n'.join(body),'Analytical workflow. The four phases distinguish data checks, construct composition, territorial aggregation and supporting validation. Connected simulation uses 50,000 burn-in proposals per chain, followed by 500,000 sampling proposals per chain, retaining one partition every 500 proposals. The workflow does not imply a causal pathway or measure a post-reform effect.','fig:workflow')

def scatter(p):
    keys=set(p[p.year.eq(2020)&p.egovernance.notna()].key)&set(p[p.year.eq(2024)&p.egovernance.notna()].key)
    fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained');body=[];checks=[]
    for i,out in enumerate(['egovernance','service_facing']):
        for j,year in enumerate([2020,2024]):
            s=p[p.year.eq(year)&p.key.isin(keys)].dropna(subset=[out,'dti_gov']);x=s.dti_gov.to_numpy();y=s[out].to_numpy()
            ax=axs[i,j];ax.scatter(x,y,color=BLUE,alpha=.75,s=22,edgecolors='white',lw=.4)
            fit=np.polyfit(x,y,1);xx=np.array([x.min(),x.max()]);ax.plot(xx,np.polyval(fit,xx),color=ORANGE,lw=1.2)
            title=f'{year}: '+('Full e-governance' if i==0 else 'Portal access + response')
            ax.set(title=title,xlabel='DTI government',ylabel='PAPI score / component sum')
            from scipy.stats import spearmanr
            rho=float(spearmanr(x,y).statistic);ax.text(.03,.94,f'n = {len(s)}; Spearman ρ = {rho:.3f}',transform=ax.transAxes,va='top',fontsize=9)
            bx=j*7;by=(1-i)*4.5
            xmin,xmax=.2,.95; ymin,ymax=(2.,4.5) if i==0 else (.6,1.35)
            assert np.all((x>=xmin)&(x<=xmax)&(y>=ymin)&(y<=ymax))
            ax.set(xlim=(xmin,xmax),ylim=(ymin,ymax))
            tx=lambda a:bx+(a-xmin)/(xmax-xmin)*5.6
            ty=lambda a:by+(a-ymin)/(ymax-ymin)*3.1
            body += [node(bx+2.8,by+3.65,title,'small'),line(bx,by,bx+5.6,by),line(bx,by,bx,by+3.1)]
            for a,b in zip(x,y):body.append(dot(tx(a),ty(b)))
            yy=np.polyval(fit,xx);body.append(line(tx(xx[0]),ty(yy[0]),tx(xx[1]),ty(yy[1]),ORANGE))
            for a in [.3,.5,.7,.9]:body += [line(tx(a),by,tx(a),by-.06),node(tx(a),by-.25,f'{a:.1f}')]
            for a in ([2.5,3,3.5,4] if i==0 else [.6,.8,1,1.2]):body += [node(bx-.12,ty(a),f'{a:.1f}',anchor='east')]
            body += [node(bx+2.8,by-.62,'DTI government'),node(bx+2.8,by+3.25,f'$n={len(s)}$; Spearman $\\rho={rho:.3f}$')]
            checks.append(dict(figure='scatter',outcome=out,year=year,n=len(s),rho=rho,slope=fit[0],intercept=fit[1]))
    save(fig,'F4_alignment_scatter')
    return wrap('\n'.join(body),'Readiness and citizen-side scores on the same 61 matched provinces, 2020 and 2024. Points are provinces; orange lines are unweighted descriptive least-squares fits in original score units. Axes are held fixed between years within each outcome; changes in published score levels remain subject to changing assessment frameworks. Spearman statistics summarise rank alignment and are not the slopes of those lines. No causal interpretation or change significance follows from the visual comparison; paired endpoint uncertainty is reported in Appendix Table~\\ref{tab:alignment}.','fig:scatter'),checks

def coefficients(models):
    configs=[('All outcomes, 2020--2024',[(o,'TWFE controls',l) for o,l in [('egovernance','Full e-governance'),('service_facing','Portal + response'),('internet_access','Internet access'),('common_service_items','Five service items')]]),
             ('Full score: sample / specification', [('egovernance',m,l) for m,l in [('TWFE common lag sample','Current: matched sample'),('Lag common sample','Lag: matched sample'),('Adjacent first differences + year FE','Adjacent differences'),('TWFE 2022-2024','2022--2024 only')]])]
    fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained');body=[];checks=[]
    for j,(title,rows) in enumerate(configs):
        ax=axs[j];ax.axvline(0,color=GRAY,ls='--',lw=.8);bx=j*8.5
        tx=lambda v:bx+3+(v+.4)/1.0*4.2
        body += [node(bx+4.8,4.35,title,'small'),line(tx(0),.3,tx(0),3.9,GRAY,',dashed'),line(tx(-.4),.3,tx(.6),.3)]
        for i,(o,m,label) in enumerate(rows):
            term='lag_dti' if m=='Lag common sample' else 'z_dti_gov'
            r=models[models.outcome.eq(o)&models.model.eq(m)&models.term.eq(term)].iloc[0];y=3.5-i*.8
            ax.errorbar(r.coef,y,xerr=[[r.coef-r.ci_low],[r.ci_high-r.coef]],fmt='o',color=BLUE,capsize=3)
            body += [line(tx(r.ci_low),y,tx(r.ci_high),y,BLUE),line(tx(r.ci_low),y-.07,tx(r.ci_low),y+.07,BLUE),line(tx(r.ci_high),y-.07,tx(r.ci_high),y+.07,BLUE),dot(tx(r.coef),y,BLUE,.05),node(bx+2.85,y,label,anchor='east')]
            checks.append(dict(figure='coefficient',outcome=o,model=m,coef=r.coef,ci_low=r.ci_low,ci_high=r.ci_high,n=int(r.n)))
        ax.set(yticks=[3.5-i*.8 for i in range(4)],yticklabels=[r[2] for r in rows],xlim=(-.4,.6),xlabel='DTI government coefficient (95% CI)',title=title)
        for x in [-.4,-.2,0,.2,.4,.6]:body.append(node(tx(x),0,f'{x:.1f}'))
        body.append(node(bx+5,-.4,'DTI coefficient; 95\\% CI'))
    save(fig,'F5_coefficient_plots')
    return wrap('\n'.join(body),'Conditional DTI associations and sensitivity to sample/specification. Left: four outcomes in the fully controlled province/year fixed-effects model. Right: full e-governance in matched current/lag samples, adjacent first differences and the restricted period. Intervals are province-clustered 95\\% intervals, not wild-bootstrap intervals. Right-hand specifications differ in samples and estimands and are not coefficient equality tests. Service-specific lag/difference results and wild-test probabilities remain in Appendix Tables~\\ref{tab:panel} and~\\ref{tab:lag}.','fig:coefficients'),checks

def aggregation(disp,bench):
    fields=['egovernance','internet_access','service_facing','dti_gov'];labels=['Full e-governance','Internet access','Portal + response','DTI government']
    fig,ax=plt.subplots(figsize=(10,4.7),layout='constrained');body=[];checks=[]
    tx=lambda v:3.8+v*10
    for i,(v,label) in enumerate(zip(fields,labels)):
        y=3.5-i
        a=disp[disp.year.eq(2024)&disp['var'].eq(v)&disp.metric.eq('variance')].iloc[0]
        c=bench[bench.year.eq(2024)&bench['var'].eq(v)&bench.metric.eq('variance')&bench.scheme.eq('connected_local_chains')].iloc[0]
        u=bench[bench.year.eq(2024)&bench['var'].eq(v)&bench.metric.eq('variance')&bench.scheme.eq('unrestricted')].iloc[0]
        ax.plot([c.q05,c.q95],[y,y],color=BLUE,lw=5,alpha=.35);ax.scatter(c['mean'],y,color=BLUE,s=40,marker='s');ax.scatter(u['mean'],y+.18,color=GRAY,s=38,marker='^');ax.scatter(a.within_share,y-.18,color=ORANGE,s=48)
        body += [node(3.55,y,label,anchor='east'),line(tx(c.q05),y,tx(c.q95),y,BLUE,',line width=3pt,opacity=.35'),dot(tx(c['mean']),y,BLUE,.06),dot(tx(u['mean']),y+.18,GRAY,.06),dot(tx(a.within_share),y-.18,ORANGE,.065)]
        checks.append(dict(outcome=v,actual=a.within_share,connected_mean=c['mean'],connected_q05=c.q05,connected_q95=c.q95,unrestricted_mean=u['mean']))
    ax.set(yticks=[3.5-i for i in range(4)],yticklabels=labels,xlim=(0,.75),xlabel='Fraction of population-weighted variance within mapped groups')
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([],[],color=ORANGE,marker='o',ls='',label='Actual grouping'),Line2D([],[],color=BLUE,marker='s',ls='-',label='Connected: mean and 5–95% range'),Line2D([],[],color=GRAY,marker='^',ls='',label='Unrestricted mean')],loc='lower center',bbox_to_anchor=(.48,1.03),ncol=3,frameon=False,fontsize=9)
    body.append(line(tx(0),-.1,tx(.75),-.1))
    for x in [0,.15,.3,.45,.6,.75]:body.append(node(tx(x),-.35,f'{x:.2f}'))
    body += [node(7.5,-.8,'Fraction of population-weighted variance within groups'),node(7.5,4.35,'Orange: actual; blue: connected mean / range; grey: unrestricted mean')]
    save(fig,'F6_aggregation_reference')
    return wrap('\n'.join(body),'Territorial aggregation compared with alternative grouping references, 2024. Orange denotes actual within-group variance shares; blue denotes connected-chain means and 5--95\\% simulated reference ranges; grey denotes unrestricted means. All measures use the same 61 observed provinces and population weights. Connected ranges are not confidence intervals and do not establish a reform-selection mechanism.','fig:aggregation'),checks

def main():
    FIG.mkdir(exist_ok=True);p=read('T0_panel');polys=geometry(p[p.year.eq(2024)])
    reform,_=maps(p[p.year.eq(2024)],polys,True);heat,coverage=maps(p[p.year.eq(2024)],polys,False)
    scat,sc=scatter(p);coef,cc=coefficients(read('T3_panel'));agg,aa=aggregation(read('T6_dispersion'),read('T6_benchmarks'))
    figures={'reformmap':reform,'workflow':workflow(),'scoremap':heat,'scatter':scat,'coefficients':coef,'aggregation':agg}
    (OUT/'visual_inline_tikz.json').write_text(json.dumps(figures,ensure_ascii=False),encoding='utf-8')
    (OUT/'VISUAL_VALIDATION.json').write_text(json.dumps({'geometry_keys':63,'mapped_groups':34,'choropleths':coverage,'scatter':sc,'coefficient_points':cc,'aggregation':aa,'geometry_note':'Stored historical 2008 geometry; not an official 2025 survey.'},indent=2),encoding='utf-8')
    print('Six figure families exported; inline TikZ stored for the existing manuscript.')

if __name__=='__main__':main()
