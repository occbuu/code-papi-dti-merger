"""Build self-contained LaTeX with every reported result taken from revised CSVs."""
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results_upgrade'
MAN=ROOT/'Paper3_DeTaiThayHien'
ARCH=ROOT/'archive/pre_revision_2026-10-09'

def read(name): return pd.read_csv(OUT/(name+'.csv'))
def esc(x):
    return str(x).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%')
def num(x,d=3): return '--' if pd.isna(x) else f'{x:.{d}f}'
def pval(x): return '$<0.001$' if x<.001 else f'{x:.3f}'
def ci(r): return f'[{r.ci_low:.3f}, {r.ci_high:.3f}]'
def table(caption,label,heads,rows,fmt,note):
    # Flexible text columns prevent long outcome/specification labels overflowing.
    fmt=fmt.replace('l',r'>{\raggedright\arraybackslash}X')
    lines=[r'\begin{table}[htbp]',r'\centering\footnotesize',r'\setlength{\tabcolsep}{3pt}',f'\\caption{{{caption}}}\\label{{{label}}}',f'\\begin{{tabularx}}{{\\linewidth}}{{@{{}}{fmt}@{{}}}}',r'\toprule',' & '.join(heads)+r' \\',r'\midrule']
    lines+=[' & '.join(map(str,row))+r' \\' for row in rows]
    lines += [r'\bottomrule',r'\end{tabularx}',r'\par\smallskip',r'\begin{minipage}{\linewidth}\footnotesize '+note+r'\end{minipage}',r'\end{table}']
    return '\n'.join(lines)

LABEL={'egovernance':'Full e-governance','service_facing':'Portal access + response',
       'internet_access':'Internet access','common_service_items':'Five common service items',
       'dti_gov':'DTI government','dti_total':'DTI total'}

def main():
    p=read('T0_panel');delta=read('T2_endpoint_change');corr=read('T2_alignment');models=read('T3_panel');wild=read('T3_wild_cluster')
    disp=read('T6_dispersion');bench=read('T6_benchmarks');pred=read('T5_prediction_summary');increment=read('T5_incremental_validation')
    moran=read('T6_moran');chains=read('T6_spatial_chain_diagnostics');diag=read('T6_chain_statistic_diagnostics');gaps=read('T6_constituent_gaps')
    desc=read('T1_descriptive');sens=read('T6_scale_sensitivity');missing=read('T6_missing_scenarios')
    d=p[p.year.eq(2024)].dropna(subset=['egovernance','internet_access','service_facing']);w=d['pop'].to_numpy();w=w/w.sum()
    a=d.internet_access.to_numpy();b=d.service_facing.to_numpy();y=a+b
    v=lambda x:np.sum(w*(x-w@x)**2)
    internet_share=v(a)/v(y); service_share=v(b)/v(y);cov_share=2*np.sum(w*(a-w@a)*(b-w@b))/v(y)
    cover=[]
    for year,s in p.groupby('year'):
        cover.append([str(year),str(s.egovernance.notna().sum()),str(s.service_facing.notna().sum()),str(s.common_service_items.notna().sum()),str(s.dti_gov.notna().sum())])
    coverage=table('Coverage of the revised panel','tab:coverage',['Year','Full PAPI','Service sum','Common items','DTI'],cover,'lrrrr',
        'Potential observations: 63 provinces per year. Service sum is portal access plus responsiveness. Common items require all five percentages. Blank or suppressed province-years are never replaced with zero.')
    changes=table('Endpoint rank alignment on matched provinces','tab:alignment',['Citizen-side measure','$N$','$\\rho_{2020}$','$\\rho_{2024}$','$\\Delta\\rho$','95\\% CI'],
        [[LABEL[r.outcome],str(r.n),num(r.rho2020),num(r.rho2024),num(r.delta),ci(r)] for r in delta.itertuples()], 'lrrrrl',
        'Supply measure: DTI government. Percentile intervals use 10,000 paired province resamples. The same province and both years enter each draw. Intervals describe uncertainty across provinces conditional on published scores; they do not include survey design uncertainty or spatial dependence.')
    aggregation=[]
    for vname in ['egovernance','internet_access','service_facing','dti_gov','dti_total']:
        r=disp[(disp.year.eq(2024))&disp['var'].eq(vname)&disp.metric.eq('variance')].iloc[0]
        u=bench[(bench.year.eq(2024))&bench['var'].eq(vname)&bench.metric.eq('variance')&bench.scheme.eq('unrestricted')].iloc[0]
        c=bench[(bench.year.eq(2024))&bench['var'].eq(vname)&bench.metric.eq('variance')&bench.scheme.eq('connected_local_chains')].iloc[0]
        aggregation.append([LABEL[vname],num(r.within_share),num(u['mean']),num(c['mean']),f'{c.q05:.3f}--{c.q95:.3f}'])
    aggregation=table('Pre-reform variance under the 2025 provincial groups, 2024','tab:aggregation',
        ['Measure','Within share','Random mean','Connected mean','Connected 5--95\\%'],aggregation,'lrrrl',
        'All measures use the same 61 observed provinces and 2024 population weights. Random benchmark: 5,000 unrestricted 63-slot assignments. Connected sensitivity: four local swap chains, 4,000 retained partitions on the stored 2008 queen-contiguity graph. Full group sizes are preserved before masking missing scores. The connected interval is a simulated reference range, not a confidence interval or causal randomisation test.')
    panelrows=[]
    for vname in ['egovernance','service_facing','internet_access','common_service_items']:
        r=models[(models.outcome.eq(vname))&models.model.eq('TWFE controls')].iloc[0];wi=wild[wild.outcome.eq(vname)].iloc[0]
        panelrows.append([LABEL[vname],num(r.coef),ci(r),pval(r.p),pval(wi.p_wild),num(r.partial_r2_first_regressor)])
    paneltab=table('Supporting within-province associations, 2020--2024','tab:panel',
        ['Outcome','DTI coef.','95\\% CI','$p_{cluster}$','$p_{wild}$','Partial $R^2$'],panelrows,'lrlrrr',
        'Outcome and DTI government are within-year z-scores. All four fits have 307 observations and 63 province clusters, province/year effects and log GRDP per capita, urban share and log population controls. PanelOLS cluster intervals use residual degrees of freedom. Wild tests are restricted Rademacher province bootstrap-t tests with 4,999 draws. Partial R-squared compares models with and without DTI after exactly absorbing both effects. These are conditional associations.')
    lagrows=[]
    for vname in ['egovernance','service_facing']:
        for model,label in [('TWFE common lag sample','Current, matched sample'),('Lag common sample','Lag, matched sample'),('Adjacent first differences + year FE','Adjacent differences')]:
            r=models[(models.outcome.eq(vname))&models.model.eq(model)].iloc[0]
            lagrows.append([LABEL[vname],label,num(r.coef),ci(r),str(r.n),pval(r.p)])
    lagtab=table('Lag and difference checks with explicit sample definitions','tab:lag',
        ['Outcome','Specification','Coef.','95\\% CI','$N$','$p$'],lagrows,'llrlrr',
        'The current-only and lag-only estimates use identical 244-observation samples. First differences use only adjacent observed year pairs, all three differenced controls, year effects and province-clustered inference. The larger 307-observation current model is not the comparator for the lag model.')
    predictionrows=[]
    for vname in ['egovernance','service_facing']:
        for model in ['Controls','DTI','Controls + DTI']:
            r=pred[pred.outcome.eq(vname)&pred.model.eq(model)].iloc[0]
            predictionrows.append([LABEL[vname],model,num(r.r2_mean),num(r.r2_split_sd),num(r.rmse_mean)])
    predictiontab=table('Concurrent-year prediction for held-out provinces, 2022--2024','tab:prediction',
        ['Outcome','Predictors','Mean $R^2$','Split SD','RMSE'],predictionrows,'llrrr',
        'Raw score outcomes; 184 province-years per task. All specifications include year indicators. Five repetitions of five province-grouped outer folds; ridge penalty selected in four province-grouped inner folds from seven log-spaced candidates, 0.01--1,000. Predictor scaling and target centring are fitted on each training fold. Split SD is split variability, not an inferential SE. This validates contemporaneous prediction in other provinces, not forecasting future years.')
    g=gaps[gaps.n_old.gt(1)].sort_values('egovernance_range',ascending=False).head(8)
    gaprows=[[esc(r.province_new),str(r.n_old),f'{r.egovernance_n}/{r.n_old}',num(r.egovernance_range),num(r.service_facing_range),num(r.dti_gov_range)] for r in g.itertuples()]
    gaptab=table('Constituent score ranges in selected merged groups, 2024','tab:gaps',
        ['New province','Members','PAPI observed','Full PAPI','Service sum','DTI gov.'],gaprows,'lrrrrr',
        'Selected by the largest full-PAPI ranges, not by inferred integration costs. Ranges are in the original score units. A missing member leaves the reported range incomplete. These are gaps between provincial means, not inequalities between individual citizens.')
    # Self-contained native vector figure. No external image/project dependency.
    bars=[]
    for i,vname in enumerate(['egovernance','internet_access','service_facing','dti_gov']):
        r=disp[disp.year.eq(2024)&disp['var'].eq(vname)&disp.metric.eq('variance')].iloc[0]
        yy=3-i
        bars += [f'\\node[anchor=east,font=\\small] at (0,{yy}) {{{LABEL[vname]}}};',
                 f'\\fill[blue!55] (0.1,{yy-.16}) rectangle ({.1+8*r.within_share:.4f},{yy+.16});',
                 f'\\node[anchor=west,font=\\small] at ({.2+8*r.within_share:.4f},{yy}) {{{100*r.within_share:.1f}\\%}};']
    fig=r'''\begin{figure}[htbp]
\centering
\begin{tikzpicture}[x=1cm,y=.8cm]
@@BARS@@
\draw[->] (0.1,-.55) -- (4.5,-.55);
\foreach \x/\lab in {0.1/0,1.7/20,3.3/40} {\draw (\x,-.5)--(\x,-.6);\node[below,font=\small] at (\x,-.6) {\lab};}
\node[below,font=\small] at (2.3,-1.0) {Variance within the new provincial groups (\%)};
\end{tikzpicture}
\caption{What the new provincial averages absorb depends on the citizen-side measure. Population-weighted 2024 variance shares on the same 61 former provinces.}
\label{fig:aggregation}
\end{figure}'''.replace('@@BARS@@','\n'.join(bars))
    pre=(ARCH/'P3_PAPI_DTI_Merger.tex').read_text(encoding='utf-8')
    author=pre[pre.index(r'\author{'):pre.index(r'\date{}')]
    refs=pre[pre.index(r'\section*{References}'):pre.index(r'\clearpage\n\appendix') if r'\clearpage\n\appendix' in pre else pre.index('\\clearpage\n\\appendix')]
    # Keep only literature actually cited by the revised argument.
    remove=['Athey, S., Tibshirani','Bui, N. H.','Chernozhukov','Driscoll','Ke, G.','Lundberg','Wager, S.']
    refs='\n'.join(line for line in refs.splitlines() if not any(s in line for s in remove))
    refs=refs.replace('CECODES, VFF-CRT, RTA \\& UNDP. (2025)','CECODES, RTA \\& UNDP. (2025)')
    refs += r'''
\refitem Fotheringham, A. S., \& Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. \emph{Environment and Planning A, 23}(7), 1025--1044. \url{https://doi.org/10.1068/a231025}.\par
\refitem OECD, European Union \& EC-JRC. (2008). \emph{Handbook on constructing composite indicators: Methodology and user guide}. Paris: OECD Publishing. \url{https://doi.org/10.1787/9789264043466-en}.\par
\refitem Ministry of Information and Communications. (2020). \emph{Decision 1726/QD-BTTTT on the digital transformation assessment framework}, 12 October 2020.\par
\refitem Ministry of Information and Communications. (2022). \emph{Decision 922/QD-BTTTT on the digital transformation assessment framework}, 20 May 2022.\par
\refitem CECODES, VFF-CRT, RTA \& UNDP. (2021). \emph{The 2020 Viet Nam Provincial Governance and Public Administration Performance Index (PAPI)}. Hanoi: UNDP.\par
\refitem Buyannemekh, B., Picazo-Vela, S., Luna, D. E., \& Luna-Reyes, L. F. (2024). Understanding value of digital service delivery by governments in Mexico. \emph{Government Information Quarterly, 41}(2), 101936. \url{https://doi.org/10.1016/j.giq.2024.101936}.\par
\refitem Lee, D. W., Rogers, M., \& Soifer, H. D. (2025). The modifiable areal unit problem in political science. \emph{Political Analysis, 33}(4), 412--424. \url{https://doi.org/10.1017/pan.2025.2}.\par
\refitem Skargren, F., Lagsten, J., Hatakka, M., \& Garc\'ia Ambrosiani, K. (2026). Learning by assessing digital government: A case study of the digital index framework. \emph{Transforming Government: People, Process and Policy, 20}(3), 595--615. \url{https://doi.org/10.1108/TG-06-2025-0182}.\par
'''
    header, *entries = refs.split(r'\refitem')
    refs = header + ''.join(r'\refitem'+entry for entry in sorted(entries, key=lambda x:x.strip().casefold()))
    template=r'''\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage{lmodern}
\usepackage{amsmath,amssymb,booktabs,array,tabularx}
\usepackage{tikz}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\usepackage{microtype}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{xurl}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.55\baselineskip}
\setlist{nosep,leftmargin=*}
\emergencystretch=2em
\newcommand{\refitem}{\hangindent=1.5em\hangafter=1 }
\title{Digital government readiness and citizen experience under changing provincial boundaries: Measurement evidence from Viet Nam}
@@AUTHOR@@
\date{}
\begin{document}
\maketitle
@@CONTACT@@

\begin{abstract}
Digital-government rankings combine administrative capacity and citizen-facing performance, yet their interpretation also depends on what citizen surveys measure and where reporting boundaries are drawn. We link Viet Nam's Digital Transformation Index (DTI) to the Provincial Governance and Public Administration Performance Index (PAPI) for 2020--2024 and reclassify pre-reform scores under the 2025 consolidation from 63 to 34 provinces. An audit of the source workbooks separates PAPI's Internet-access component from portal access and government responsiveness. In 2024, @@FULLSHARE@@\% of population-weighted variance in full e-governance scores lies within the new provincial groups, compared with @@SERVICESHARE@@\% for portal access plus responsiveness and @@DTISHARE@@\% for DTI government, on the same 61 provinces. The apparent homogeneity of the full citizen-side index falls within the reference range of geographically connected grouping simulations. DTI--PAPI rank alignment is limited, but paired bootstrap intervals do not establish a decline between 2020 and 2024. Supporting province/year fixed-effects models show positive contemporaneous associations, while nested province-grouped validation finds no clear predictive improvement from adding DTI to socioeconomic controls. The results identify two distinct limits of benchmarking: composite citizen-side measures can obscure differences between connectivity and service interaction, and new provincial averages absorb variation among their constituent administrations. This is a baseline measurement study, not an estimate of the reform's effects or of individual welfare inequality.
\end{abstract}

\textbf{Keywords:} digital government; performance measurement; citizen experience; composite indicators; territorial aggregation; Viet Nam

\section{Introduction}

Digital-government performance is often judged through rankings of administrative readiness. These rankings inform comparisons between places, guide investment and communicate progress. Their practical value depends on two links that are easy to overlook: a supply-side score must convey something about citizens' interaction with government, and the unit being ranked must retain the variation relevant to managing services. A high score may reflect organisational preparation without widespread use. A favourable provincial average may combine administrations with very different profiles. Neither issue can be resolved by treating an administrative index as a direct measure of citizen experience.

Viet Nam's territorial reform makes both questions visible. Resolution 202/2025/QH15, adopted on 12 June 2025, consolidated 63 provinces into 34. Fifty-two former provinces were grouped into 23 new provinces, while 11 remained unchanged. From July 2025, the reform of local government also removed the district tier and reorganised administrative service delivery around provinces and communes (National Assembly of Viet Nam, 2025; Government of Viet Nam, 2025). Measurements referring to 2024 therefore offer a baseline on the former units. Reclassifying those measurements under the new boundaries reveals what disappears from view when constituent scores are replaced by larger-area averages. It does not reveal whether the reform improves services.

The country has two relevant measurement systems. The Digital Transformation Index (DTI) assesses provincial digital transformation from the administrative side. The Provincial Governance and Public Administration Performance Index (PAPI) uses citizen surveys and includes an e-governance dimension. Their distinct reporting perspectives permit triangulation, but do not make the two constructs interchangeable. Crucially, PAPI e-governance combines portal access, Internet access and government responsiveness. Connectivity is an enabling condition for digital interaction, whereas the other components concern aspects of the interaction itself. Comparing DTI only with the full PAPI dimension risks conflating these stages.

Research distinguishes the availability of digital services from adoption and the public outcomes they produce (Gil-Garcia et al., 2018; Lindgren et al., 2019). Design--reality gaps and inequalities in connectivity, skills and trust can interrupt the connection between administrative effort and citizen use (Heeks, 2002; Helbig et al., 2009; van Dijk, 2020). Composite-indicator research adds that conclusions depend on indicator selection, weighting and aggregation (OECD et al., 2008). Spatial research shows that changing the units of analysis can alter the patterns one observes (Fotheringham \& Wong, 1991). These perspectives suggest that digital-government benchmarking should be evaluated jointly as a question of construct composition and territorial resolution.

We make three contributions. First, we audit the citizen-side measure and distinguish an Internet-access component, a portal-and-response sum, and a diagnostic average of five service-related percentages available under consistent labels. Second, we quantify the dispersion of published provincial mean scores absorbed within the new provincial groups, using a variance decomposition and a geographically connected sensitivity benchmark. Third, we examine the practical information in DTI through matched-sample rank comparisons, parsimonious panel models and predictive validation against socioeconomic baselines. The combination shows why neither a low aggregate association nor a homogeneous aggregate citizen-side score can be read directly as evidence of administrative failure or successful territorial design.

The analysis addresses three questions. How does the comparison between supply and citizen-side scores change when connectivity is separated from service interaction? How much dispersion in each measure lies within the 2025 provincial groups, and how sensitive is the interpretation to geographical constraints? Does DTI add information beyond provincial socioeconomic characteristics? These questions concern the interpretation and usefulness of benchmarks. Causal effects of digital investment and post-reform service delivery remain outside the design.

\section{Conceptual framework and institutional setting}

\subsection{From readiness to citizen interaction}

A useful sequence is administrative readiness, functioning service availability, citizen awareness and access, actual use, and completion or responsiveness. Organisational readiness can support subsequent stages, but no stage guarantees the next. Digital-era governance emphasises the reintegration of processes around citizens' needs (Dunleavy et al., 2006). The digital-divide literature highlights resources outside the administration that shape access and use (Helbig et al., 2009; van Dijk, 2020). These arguments motivate a positive association between readiness and service interaction, without assuming a one-to-one relationship.

Three explanations can produce weak alignment. First, administrative scores may respond to revisions in scoring rules or reporting requirements. Second, conversion constraints may prevent available services from being used effectively. Third, a citizen-side composite may be dominated empirically by connectivity, making it an imperfect criterion for assessing administrative service provision. The present data can distinguish some implications of the third explanation, but cannot establish reporting manipulation or identify the causal mechanism behind conversion constraints. We therefore use those explanations to organise interpretation rather than to claim that one has been proven.

The measurement question is consequential even when each component is legitimate. An index intended to describe the broad environment for e-governance may appropriately include Internet access. The same index may be less suitable as a criterion for validating the performance of government portals. The problem is the mismatch between the purpose of a composite and the inference drawn from it. Separating the components makes that mismatch observable without treating either index as inherently defective.

\subsection{Territorial resolution and information loss}

Recent methodological work emphasises that spatial units need substantive justification rather than selection according to favourable results (Lee et al., 2025). Provinces are meaningful here because they delimit administrative responsibility and published assessment scores. Alternative groupings diagnose sensitivity to reporting geography; they do not validate a boundary design merely because a particular indicator becomes more homogeneous.

Administrative consolidation changes the level at which performance is reported. A new provincial mean absorbs differences between constituent provinces. Those differences become invisible in a league table of new provinces, even though they may remain relevant to targeting support. This is a reporting effect that can be calculated before the organisational consequences of the reform are known. It is related to the modifiable areal unit problem: statistical patterns depend on the scale and configuration of the areas being analysed (Fotheringham \& Wong, 1991).

The amalgamation literature evaluates efficiency, expenditure, administrative performance and democratic participation (Blom-Hansen et al., 2016; Tavares, 2018; Ebinger et al., 2019; Roesel, 2017). Our contribution concerns a narrower issue within that conversation: the information retained in performance reporting when units are consolidated. Previous Vietnamese evidence on restructuring local government addresses public-service effects using a different reform and an identification strategy (Malesky et al., 2014). We do not transfer that causal interpretation to an exercise that merely regroups pre-reform scores.

Geography matters for the benchmark. If neighbouring provinces have similar connectivity, merging neighbours will tend to produce more homogeneous citizen-side scores than merging arbitrary provinces nationally. Comparing the actual groups with unrestricted random groups can therefore exaggerate how unusual the actual arrangement is. Conversely, differences in service interaction may persist among neighbours. The empirical questions are whether component composition explains the difference and whether the conclusion survives a benchmark that requires connected groups.

\subsection{Indices and reform in Viet Nam}

PAPI's e-governance dimension has three subdimensions: access to government portals, access to the Internet and the responsiveness of provincial authorities. Published provincial workbooks contain both these scores and selected underlying percentages. PAPI's 2020 report describes refinements to the dimension (CECODES et al., 2021), which rules out assuming a continuous unchanged scale back to 2018. We begin in 2020 and document the observable labels and availability each year. These records do not establish invariant denominators or item weights.

DTI includes digital-government, digital-economy and digital-society pillars. Its administrative framework was introduced through Decision 1726/QD-BTTTT in 2020 and revised through Decision 922/QD-BTTTT in 2022. Three pillar scores and group-level indicators can be observed in the local replication inputs, but an item-by-item invariant DTI-government score cannot be reconstructed from those inputs. We therefore assess published within-year comparisons and treat changes over time as conditional on changing measurement rules.

The 2025 territorial consolidation coincided with changes in administrative service delivery and the National Public Service Portal (Government of Viet Nam, 2025). User-perspective reviews provide a relevant context for concerns about online completion and support (IPS \& UNDP, 2025). They do not establish that a measured DTI gap between two former provinces translates into a particular integration cost. Our group-level comparisons identify places where baseline profiles differ, which can guide subsequent service audits.

\section{Data and analytical design}

\subsection{Sources, coverage and provenance}

The analytical grid contains 63 former provinces over 2020--2024. PAPI dimensional scores are taken from the accompanying provincial data files. DTI scores come from the official portal snapshots recorded in the source inventory. Population, urban share and GRDP per capita come from National Statistics Office tables. The merger map follows Resolution 202/2025/QH15. Inputs were assembled in September 2026; the reference years of the scores remain 2020--2024. Later publication or retrieval dates do not make these post-reform observations.

The revised extraction reads the first annual sheet of each official PAPI workbook and records the file, sheet, row, column, label and province code for every component value. It retains genuine zero percentages within eligible observations. Cells associated with province-years whose e-governance dimension is unavailable are excluded, including zero-filled suppressed records. Province names are normalised, keys are checked for duplicates, and joins enforce their expected cardinality. Every input file has a recorded SHA-256 hash.

An independent source check reconstructs all 2,835 dimensional/total PAPI records in the study period from those workbooks, matching 2,762 observed scores and the original missingness pattern. All 315 DTI province-year score vectors match province-labelled static rows in the archived portal JavaScript, which is parsed as text rather than executed. Population and GRDP match all 315 provincial control records; the cleaned urban shares agree with the raw population ratios within their four-decimal rounding tolerance. These checks validate the stored values, while source-year assignment and the legal merger map retain their documented provenance.

@@COVERAGE@@

There are eight missing full-PAPI province-years, leaving 307 panel observations. These are treated as missing rather than imputed in regressions. In 2024, Tiền Giang and Vĩnh Phúc are unavailable, so comparative dispersion analyses use the same 61-province sample for every measure. Their constituent groups are incompletely observed. We also report sensitivity scenarios filling those two scores at the observed 2024 minimum or maximum. These are explicit scenarios, not identified bounds or a missing-at-random correction.

\subsection{An observable measurement audit}

Let $E$ denote the full PAPI e-governance score, $I$ the Internet-access subdimension and $S$ the sum of portal access and responsiveness. The workbook data satisfy $E=I+S$ up to floating-point precision. The service sum $S$ excludes connectivity but retains the published component scales and weights. It remains a broad service-facing measure, not a measure of end-to-end completion or satisfaction. Its nominal range is approximately 0.66--6.66, subject to the published scoring conventions.

We also calculate $C$, the unweighted mean of five published percentages with recurring labels: adequate certification information, adequate land-procedure information, portal use for personal procedures, website user-friendliness and awareness of online draft-policy comments. All five must be observed. This diagnostic avoids changes in the composition of the official portal subdimension, including the construction-information item that appears in 2020 but not subsequent annual sheets. Additional portal-use and online-payment labels appear in 2023--2024 and are inventoried but not backfilled. $C$ is a transparent sensitivity construction, not an official index or a validated latent scale. Equal weighting is a choice tested alongside the original components.

We do not infer full measurement invariance from recurring labels. Questionnaire routing, eligible respondents, denominators and weights may differ. Nor do within-year z-scores repair a change in construct composition. The principal findings consequently concern comparisons of published scores and the observable components, especially the final pre-reform cross-section. Temporal models support those comparisons, with explicit qualifications.

\subsection{Alignment and supporting panel models}

We report annual Spearman correlations and percentile intervals from 5,000 province resamples, supplemented by Kendall and Pearson coefficients. For the 2020--2024 change we restrict to provinces observed at both endpoints and resample province pairs 10,000 times. The interval is calculated directly for the difference in correlations. These resamples do not propagate within-province survey design uncertainty or adjust for spatial dependence. A difference in individual-year significance levels is not treated as evidence of a change.

Supporting models relate within-year standardised citizen-side scores to standardised DTI-government scores:
\begin{equation}
 z(Y)_{it}=\beta z(DTI^{gov})_{it}+\gamma'X_{it}+\alpha_i+\lambda_t+\varepsilon_{it},
\end{equation}
where $X$ includes log GRDP per capita, urban share and log population. Province and year effects absorb time-invariant provincial characteristics and common year shocks. Province-clustered uncertainty and restricted wild cluster bootstrap-t tests are reported. The latter use 4,999 Rademacher sign draws at the province level and retain covariates and the observed missingness pattern. These procedures address within-province dependence, not time-varying confounding or every form of spatial dependence.

All numerical residualisation uses an exact absorbed-effects projection or iterative demeaning to convergence on the unbalanced estimation sample. Current and lagged models are compared on identical samples. First differences are calculated before deleting missing observations so only adjacent observed year pairs enter; they include all three differenced controls and year indicators. A within/between sensitivity decomposition separates every time-varying regressor on the same complete-case sample (Mundlak, 1978). A 2022--2024 fit restricts the period around the revised DTI framework, while still making no claim of item-level DTI invariance.

We report partial $R^2$ for DTI after absorbing both sets of effects and conditioning on controls. Other PAPI dimensions are exploratory specificity comparisons, not automatically valid negative controls. Their associations may legitimately respond to digital government. The supplementary outcome family is stated explicitly and includes Holm-adjusted results. Machine-learning effect estimates and independent within-year treatment permutations are not used to strengthen causal claims.

\subsection{Dispersion under the new boundaries}

Our main aggregation statistic is the population-weighted variance of published provincial mean scores. With normalised population weights $w_i$, group weights $W_g$ and constituent-weighted means $\mu_g$,
\begin{align}
 V &= \sum_i w_i(y_i-\mu)^2,\\
 V_B &= \sum_g W_g(\mu_g-\mu)^2,\\
 V_W &= \sum_g\sum_{i\in g}w_i(y_i-\mu_g)^2,\qquad V=V_B+V_W.
\end{align}
The share $V_W/V$ is the variation among former provincial means absorbed inside the new reporting groups. It is unchanged by a common translation or nonzero linear rescaling of a given score. It does not measure variation among individual residents. Population weights describe the geographical exposure represented by each provincial mean, rather than turning the score into an individual observation.

We retain Theil decomposition as a supplementary scale-sensitive diagnostic (Theil, 1967; Shorrocks, 1980), including shifts of the PAPI scale. Composite scores have no established ratio-scale interpretation, making Theil an insufficient sole basis for an inequality claim. The variance analysis avoids that particular dependence on the score's origin.

Two grouping references are calculated on the same province-year sample. An unrestricted reference randomly reassigns all 63 slots while preserving actual group sizes, with 5,000 draws. Missing-score slots are masked after assignment. A connected sensitivity reference uses a queen-contiguity graph extracted from exact shared vertices in the stored geoBoundaries 2008 geometry, with Côn Đảo assigned to Bà Rịa--Vũng Tàu. All actual groups are connected on this graph. This is a historical geometry approximation, not a certification of contemporary legal boundaries.

Four local chains start from the actual grouping and swap two province assignments if both resulting groups remain connected. Proposals mix fixed graph-edge pairs and unrestricted pairs with equal probability, preserving proposal symmetry and group sizes. Each chain discards 50,000 proposals and retains one partition every 500 further proposals, for 1,000 draws per chain. We record acceptance, unique partitions, chain means and lag-one dependence. We have not established irreducibility across every feasible partition, so these draws provide a geographical sensitivity reference, not a certified exact randomisation distribution. We report empirical reference ranges rather than causal $p$-values for territorial selection. Moran statistics provide a separate diagnostic of clustering on the same graph.

\subsection{Does DTI add predictive information?}

We compare ridge models with socioeconomic controls, DTI government, and both, each including year indicators, for 2022--2024. Outcomes are raw full-PAPI and service-sum scores. Five repeated five-fold outer partitions hold out all years of each province. Four province-grouped inner folds choose the ridge penalty. Scaling and target centring are estimated within training folds. This avoids treating target-province observations as independent validation cases and avoids using their outcomes to standardise the target.

Performance is assessed through pooled out-of-fold $R^2$ and RMSE. Split variability is descriptive. To compare the combined and controls-only models we bootstrap province-level mean squared-error differences conditional on the fitted validation models. That interval does not account for refitting uncertainty. The task concerns concurrent-year prediction for other provinces, not forecasting future years or selecting a causal model.

\section{Results}

\subsection{Component composition changes the diagnosis}

The source audit reveals that full e-governance and the narrower service sum describe different provincial patterns. In the 2024 common sample, the variance of Internet access accounts for @@INTERNETVAR@@\% of full-score variance, the variance of the service sum for @@SERVICEVAR@@\%, and their covariance term for @@COVVAR@@\%. These are components of the identity $\operatorname{Var}(I+S)=\operatorname{Var}(I)+\operatorname{Var}(S)+2\operatorname{Cov}(I,S)$, not mutually independent causal contributions. The connectivity component therefore has substantial influence on the full score's geographical dispersion.

DTI government correlates with the full e-governance score at 0.213 in 2024, but with the service sum at @@RHOSERVICE@@. On matched endpoint provinces, full-score alignment falls while service-sum alignment rises in point estimates (Table~\ref{tab:alignment}). Both changes have intervals containing zero. The five-item diagnostic is also imprecise. The evidence supports limited, measure-dependent alignment; it does not establish progressive decoupling or progressive coupling. The direction itself depends on which citizen-side construct is chosen.

@@CHANGES@@

This difference matters for interpretation. A weak DTI--full-PAPI relationship cannot alone establish that readiness fails to reach citizens. Part of the discrepancy concerns comparison with connectivity, which also reflects household resources and the wider digital environment. Conversely, a stronger association with the service sum does not establish successful completion of public services. The stable-label percentage diagnostic provides a more cautious check and does not reproduce every relationship seen in the official subdimension sum.

\subsection{What is absorbed by provincial aggregation?}

On the same 61 provinces, only @@FULLSHARE@@\% of full-PAPI variance is within the new groups. Internet access has a similarly low share of @@INTERNETSHARE@@\%. The service sum has a much larger share, @@SERVICESHARE@@\%, close to the @@DTISHARE@@\% for DTI government (Table~\ref{tab:aggregation}; Figure~\ref{fig:aggregation}). Thus the full citizen-side composite can suggest considerable similarity among constituent provinces even when its service-facing components differ. The original contrast between homogeneous citizen experience and heterogeneous administrative readiness depends strongly on index composition.

@@AGGREGATION@@

@@FIGURE@@

The geographical reference changes the comparison further. For full PAPI, the actual variance share of @@FULLPROP@@ is below the unrestricted random mean of @@RANDOMMEAN@@, but lies within the connected reference range, @@CONNECTEDLOW@@--@@CONNECTEDHIGH@@. The connected mean is @@CONNECTEDMEAN@@. We therefore cannot attribute the apparent similarity to unusual choices in territorial design. This reference is imperfect, but it exposes the consequence of allowing implausibly distant provinces to merge in the unrestricted benchmark.

On the stored graph, Moran's $I$ in 2024 is @@MORANFULL@@ for full PAPI and @@MORANINTERNET@@ for Internet access, compared with @@MORANSERVICE@@ for the service sum and @@MORANDTI@@ for DTI government. Connectivity and the full composite are more spatially clustered. Spatial structure provides a plausible statistical explanation for their low within-group shares without requiring evidence that the reform selected provinces for digital similarity. The service sum and DTI government both remain within their connected reference ranges; neither is shown to be unusually heterogeneous relative to that reference.

The connected chains accept approximately @@ACCEPTLOW@@--@@ACCEPTHIGH@@\% of proposals, and each retains 1,000 distinct partitions. Full-PAPI chain means range from @@CHAINLOW@@ to @@CHAINHIGH@@; the accompanying diagnostics disclose remaining serial dependence. These checks support the sensitivity comparison, while falling short of proving globally uniform sampling. Missing-score scenarios place the full-PAPI variance share between @@MISSLOW@@ and @@MISSHIGH@@ under the four observed-range endpoint fills. More extreme unobserved scores remain possible.

Constituent ranges show where the new averages combine distinct profiles (Table~\ref{tab:gaps}). Đà Nẵng--Quảng Nam and Gia Lai--Bình Định have conspicuous baseline gaps, but this does not identify platform incompatibility or the cost of integrating administrations. Published DTI totals for the new provinces closely match simple constituent averages. Our population-weighted group summaries answer a different question from those official equally weighted totals, and the match is not extended to the government pillar without an official pillar-level aggregation check.

@@GAPS@@

\subsection{Supporting associations are modest and specification-dependent}

The full-score TWFE coefficient is @@BETAFULL@@, with interval @@CIFULL@@ and wild bootstrap $p=@@WILDFULL@@$. For the service sum it is @@BETASERVICE@@, with interval @@CISERVICE@@ and wild bootstrap $p=@@WILDSERVICE@@$. The Internet-access estimate is less precise, and the five-item diagnostic does not show a clear association (Table~\ref{tab:panel}). Partial $R^2$ is small for every outcome, so positive coefficients do not imply that DTI explains most within-province movement.

@@PANEL@@

Sample matching is important. In the 244-observation lag-eligible sample, the current full-score coefficient is smaller and less precise than in the 307-observation model. The lagged coefficients remain inconclusive (Table~\ref{tab:lag}). The service-sum association persists in adjacent first differences, whereas the full score and the five-item diagnostic are less stable. These differences reinforce the measurement qualification rather than establishing rapid causal pass-through. Contemporaneous provincial shocks, changing measurement rules and time-varying omitted factors remain possible explanations.

In the 2022--2024 restricted-period specification, the full-score coefficient is approximately @@RESTRICTFULL@@ and the service-sum coefficient approximately @@RESTRICTSERVICE@@, both with intervals spanning zero (Appendix Table~\ref{tab:additional}). The entire-period associations are therefore not robust evidence of a stable relationship within the later framework. The restricted sample is shorter and offers less precision, so this result cannot isolate a measurement break from a changing substantive relationship. It further limits claims about general pass-through from readiness to citizen outcomes.

@@LAG@@

The component analysis is a revision prompted by the measurement audit, not a preregistered confirmatory design. The supplementary family contains all reported outcome comparisons. Holm adjustment across that family weakens conventional significance, and the full-PAPI and service-sum results should be read alongside it. Other dimensions are not assumed to be unaffected by digital transformation. Direct common-sample outcome contrasts are provided in the replication outputs to avoid treating separate significance decisions as evidence that two associations differ.

\subsection{Limited incremental predictive value}

For full e-governance, the controls-only ridge model has mean out-of-fold $R^2=@@R2CONTROLS@@$, compared with @@R2COMBINED@@ when DTI is added. For the service sum the corresponding values are @@R2SERVICECONTROLS@@ and @@R2SERVICECOMBINED@@ (Table~\ref{tab:prediction}). The DTI-only specification provides some signal, especially for the service sum, but its contribution does not translate into a clear improvement over the controls baseline when combined.

@@PREDICTION@@

The province-bootstrap interval for the combined-minus-controls mean squared-error difference spans zero for both outcomes. This is evidence against relying on the apparent precision of an in-sample relationship as proof that the index provides additional targeting information. It is not evidence that DTI is useless for every administrative purpose: the benchmark may inform organisational assessment even when it adds little to this particular citizen-side prediction task. The conclusion is deliberately task-specific.

\section{Discussion}

\subsection{Benchmark validity depends on the inference being made}

The results refine the familiar concern that digital capacity and citizen outcomes can diverge. A comparison of two composite indices can combine a substantive conversion problem with a measurement problem. Once connectivity is separated, the apparent contrast between supply-side dispersion and citizen-side homogeneity becomes much smaller for the portal-and-response sum. A stable-label percentage diagnostic is less closely associated with DTI in the panel. These findings favour inspecting the components and their denominators before attributing an aggregate pattern to implementation failure.

This does not discredit connectivity as a governance concern. Access is necessary for inclusive digital government, and including it in a broad e-governance index has a clear substantive purpose. The distinction is between measuring the enabling environment and validating administrative service interaction. Policymakers need both, with labels that communicate which stage is being assessed. A single number is less useful when its interpretation shifts between those purposes.

The panel and predictive findings add a separate caution. DTI can have a positive conditional association with a service-facing measure without improving prediction beyond socioeconomic characteristics. Association, measurement validity and predictive utility are distinct properties. The same empirical exercise should not be used to claim all three merely because one coefficient is significant. The revised design makes each question observable with a corresponding statistic.

\subsection{Territorial consolidation and performance visibility}

Citizen research in Mexico separates digital-system quality, use, satisfaction and perceived public value (Buyannemekh et al., 2024). Those distinctions reinforce the need to avoid treating access as completed service delivery. Our aggregate measures cannot test that individual-level pathway. Research on assessment practice likewise treats digital indices as tools for organisational learning (Skargren et al., 2026). Component and constituent reporting could support that role, but the present study does not evaluate whether agencies actually learn from the scores.

Boundary consolidation absorbs considerable dispersion in the service sum and DTI government. That is an arithmetical consequence of reporting larger-area means, but it has a practical implication: management systems that retain only new-province league tables lose information about constituent profiles. The policy response is to preserve geographically disaggregated baselines and inspect the service-facing components. It does not require concluding that consolidation is harmful.

For the transition, a provincial dashboard could show its mean, constituent ranges, missingness and separate access/use/response measures. Differences should trigger service audits, not automatic labels of integration failure. Follow-up measurement at communes or other consistent service catchments would help determine whether the baseline gaps persist, narrow or widen. Linking old and new geographical identifiers is essential to distinguish actual change from reclassification.

The connected sensitivity also changes the standard for interpreting territorial comparisons. Unrestricted random aggregation can be a useful mathematical illustration, but geographic restrictions substantially change its reference distribution. This lesson generalises to digital benchmarking in other settings where administrative boundaries are redrawn: a counterfactual reporting geography must be plausible for the question being asked, and computational diagnostics must accompany simulations.

\subsection{Limits and next empirical tests}

Several limitations constrain the conclusions. Published provincial means conceal citizen-level heterogeneity and contain survey error. Component-level design-based uncertainty and respondent denominators are not available in the analytical inputs. Recurring labels do not establish invariant measurement, particularly for percentage items with selective eligibility. The diagnostic service sum and equal-weight common-item mean are sensitivity constructions rather than newly validated indices. DTI lacks an invariant item-level series, and the short panel limits temporal inference.

The graph uses historical simplified geometry and exact shared vertices. It may omit or misrepresent contemporary adjacencies. Local chains preserve connectivity and sizes, but do not reproduce legal, population, fiscal or political constraints on the actual reform and have not been shown to reach every feasible partition. The simulated comparison therefore qualifies an unrestricted benchmark rather than identifying a reform-selection mechanism. Province resampling and clustered regression also leave spatially correlated uncertainty incompletely addressed.

All measures precede the reform. A future evaluation needs compatible post-reform citizen and service data, preferably with respondent or service-location geography that can be mapped to stable catchments. The 11 unchanged provinces also underwent the wider local-government and portal reforms, so a simple merged-versus-unchanged comparison would target an incremental amalgamation effect rather than the whole reform package. Identification would require addressing selection and spillovers. Interviews, transaction-level completion data and portal audits would be needed to test conversion constraints or integration costs directly.

\section{Conclusion}

Digital-government benchmarking loses precision when a broad citizen-side composite is treated as a direct measure of service interaction or when territorial averages replace constituent profiles. In Viet Nam's pre-reform baseline, the full PAPI e-governance dimension and its service-facing sum yield substantially different pictures of the variation absorbed by the new provincial groups. Geographic restrictions also qualify the apparent exceptional homogeneity of the full composite. Rank-change intervals and predictive checks support restrained conclusions about the information in DTI.

The practical implication is to retain component-level and constituent-level reporting alongside provincial rankings. The empirical contribution is a measurement and aggregation assessment that can be repeated when compatible post-reform data become available. The present evidence establishes neither reform effects nor individual welfare inequality, and it does not validate readiness rankings as substitutes for observed citizen interaction.

@@DECLARATIONS@@
@@REFERENCES@@
\clearpage
\appendix
\section{Measurement audit and sensitivity outputs}

The replication crosswalk records all 13 inspected PAPI component/item labels for each year, including absent items, original scale labels and eligible observation counts. The portal-access score, Internet-access score and responsiveness score are separated from the ten percentage indicators. Construction-procedure information is available in 2020 but not the subsequent annual sheets; general portal use and online payment appear only in the later sheets. The latter items are inventoried rather than silently substituted for earlier indicators. Five recurring service labels form the diagnostic average, conditional on all five being observed. Item-specific inference requires confirmation of questionnaire denominators.

The stored DTI series spans two documented assessment frameworks, introduced in 2020 and revised in 2022. The eight indicator groups available for 2022--2024 are not an item-level bridge across those frameworks. No common-core DTI-government index is asserted. The measurement limitation is therefore handled through qualified interpretation and a restricted-period sensitivity, rather than by describing z-standardisation as harmonisation.

The accompanying tables retain year-specific SD, IQR and CV. Exploratory convergence coefficients are preserved outside the main argument. If an annual-growth coefficient $b$ from a horizon $T$ is translated under the conventional convergence model, the rate is $\lambda=-\ln(1+Tb)/T$ and the half-life is $\ln(2)/\lambda$, when that mapping is defined. We do not interpret this as a structural half-life for indices with changing scoring rules.

Theil shares are compared after common translations of the PAPI score. Variance shares remain unchanged, as required by the decomposition. Both outcomes and DTI use a shared observed sample in the territorial analysis. The saved partition assignments allow replication of the paired measure comparisons without regenerating different groupings for different scores. Missingness scenarios and graph/chain diagnostics are separate from inferential regression results.

@@APPENDIXTABLE@@

The production pipeline intentionally excludes the earlier DML, causal-forest, SHAP and independent-year treatment-permutation results. Those outputs are retained as historical exploratory material, but do not support the revised claims. The revised notebook calls the same script used to produce the revised tables and figures. Inputs are hashed, package versions are recorded, and missing required files cause failure rather than simulated-data fallback.

\end{document}
'''
    # Numeric tokens all resolved from current output tables.
    full=disp[disp.year.eq(2024)&disp['var'].eq('egovernance')&disp.metric.eq('variance')].iloc[0]
    service=disp[disp.year.eq(2024)&disp['var'].eq('service_facing')&disp.metric.eq('variance')].iloc[0]
    internet=disp[disp.year.eq(2024)&disp['var'].eq('internet_access')&disp.metric.eq('variance')].iloc[0]
    supply=disp[disp.year.eq(2024)&disp['var'].eq('dti_gov')&disp.metric.eq('variance')].iloc[0]
    un=bench[bench.year.eq(2024)&bench['var'].eq('egovernance')&bench.metric.eq('variance')&bench.scheme.eq('unrestricted')].iloc[0]
    con=bench[bench.year.eq(2024)&bench['var'].eq('egovernance')&bench.metric.eq('variance')&bench.scheme.eq('connected_local_chains')].iloc[0]
    mf=models[models.outcome.eq('egovernance')&models.model.eq('TWFE controls')].iloc[0]
    ms=models[models.outcome.eq('service_facing')&models.model.eq('TWFE controls')].iloc[0]
    dd=diag[diag.year.eq(2024)&diag['var'].eq('egovernance')&diag.metric.eq('variance')]
    def pv(outcome,model): return pred[pred.outcome.eq(outcome)&pred.model.eq(model)].iloc[0].r2_mean
    tokens={'COVERAGE':coverage,'CHANGES':changes,'AGGREGATION':aggregation,'FIGURE':fig,'GAPS':gaptab,'PANEL':paneltab,'LAG':lagtab,'PREDICTION':predictiontab,
        'FULLSHARE':f'{100*full.within_share:.1f}','SERVICESHARE':f'{100*service.within_share:.1f}','INTERNETSHARE':f'{100*internet.within_share:.1f}','DTISHARE':f'{100*supply.within_share:.1f}',
        'INTERNETVAR':f'{100*internet_share:.1f}','SERVICEVAR':f'{100*service_share:.1f}','COVVAR':f'{100*cov_share:.1f}',
        'RHOSERVICE':num(corr[corr.year.eq(2024)&corr.outcome.eq('service_facing')&corr.supply.eq('dti_gov')].iloc[0].rho),
        'FULLPROP':num(full.within_share),'RANDOMMEAN':num(un['mean']),'CONNECTEDMEAN':num(con['mean']),'CONNECTEDLOW':num(con.q05),'CONNECTEDHIGH':num(con.q95),
        'BETAFULL':num(mf.coef),'BETASERVICE':num(ms.coef),'CIFULL':ci(mf),'CISERVICE':ci(ms),
        'WILDFULL':num(wild[wild.outcome.eq('egovernance')].iloc[0].p_wild),'WILDSERVICE':num(wild[wild.outcome.eq('service_facing')].iloc[0].p_wild),
        'ACCEPTLOW':f'{100*chains.acceptance_rate.min():.1f}','ACCEPTHIGH':f'{100*chains.acceptance_rate.max():.1f}',
        'CHAINLOW':num(dd['mean'].min()),'CHAINHIGH':num(dd['mean'].max()),'MISSLOW':num(missing.variance_within_share.min()),'MISSHIGH':num(missing.variance_within_share.max()),
        'R2CONTROLS':num(pv('egovernance','Controls')),'R2COMBINED':num(pv('egovernance','Controls + DTI')),
        'R2SERVICECONTROLS':num(pv('service_facing','Controls')),'R2SERVICECOMBINED':num(pv('service_facing','Controls + DTI')),
        'AUTHOR':author,'REFERENCES':refs}
    for vname,key in [('egovernance','RESTRICTFULL'),('service_facing','RESTRICTSERVICE')]:
        tokens[key]=num(models[models.outcome.eq(vname)&models.model.eq('TWFE 2022-2024')&models.term.eq('z_dti_gov')].iloc[0].coef)
    for vname,key in [('egovernance','MORANFULL'),('internet_access','MORANINTERNET'),('service_facing','MORANSERVICE'),('dti_gov','MORANDTI')]:
        tokens[key]=num(moran[moran.year.eq(2024)&moran['var'].eq(vname)].iloc[0].moran_I)
    app=[]
    for vname in ['egovernance','service_facing','internet_access','common_service_items']:
        for model in ['Balanced provinces','TWFE 2022-2024','Three pillars']:
            r=models[models.outcome.eq(vname)&models.model.eq(model)&models.term.eq('z_dti_gov')].iloc[0]
            app.append([LABEL[vname],model,num(r.coef),ci(r),str(r.n)])
    tokens['APPENDIXTABLE']=table('Additional conditional-association specifications','tab:additional',
        ['Outcome','Specification','DTI coefficient','95\\% CI','$N$'],app,'llrlr',
        'Balanced provinces requires all five outcome/DTI/control observations. The restricted period does not guarantee item-level comparability. Three pillars estimates condition on all three DTI pillar scores. All models absorb province/year effects and use province-clustered inference.')
    contact=r'''\begin{center}\small
Hien Bui Ngoc: \href{mailto:b.nhien@hcmca.edu.vn}{b.nhien@hcmca.edu.vn}; ORCID 0000-0003-3339-976X.\\
Thong Cao Văn: \href{mailto:c.vthong@hcmca.edu.vn}{c.vthong@hcmca.edu.vn}.\\
Corresponding author: Hieu Le Ngoc; \href{mailto:lnhieu@ptit.edu.vn}{lnhieu@ptit.edu.vn}; ORCID 0000-0002-1133-1433.
\end{center}'''
    declarations=r'''\section*{Declarations}
\textbf{Data and code availability.} The accompanying replication package contains the analysis-ready inputs, the revised extraction and analysis scripts, input hashes, environment versions and all revised result tables. Source provenance is documented alongside the data. The script reproduces the revised results from the supplied analytical inputs and extracts the new PAPI components from the original workbooks. End-to-end recreation of every earlier cleaned input from raw sources has not been certified. A public repository DOI is not yet assigned.

\textbf{Ethics.} The analysis uses publicly released aggregated provincial statistics and does not collect participant-level data.

\textbf{Funding.} This article is an output of ministerial-level research project B.22-33 hosted by the Ho Chi Minh City Cadre Academy and led by Dr.\ Bùi Ngọc Hiền. The funder had no role in study design, analysis or the decision to submit.

\textbf{Use of AI tools.} AI assistants were used for code drafting, methodological auditing, manuscript revision and language editing, including Claude (Anthropic; Cursor) in the earlier workflow and Codex (OpenAI) in this revision. The authors retain responsibility for validating the analyses and the submitted manuscript.

\textbf{CRediT authorship.} Hien Bui Ngoc: Conceptualization; Funding acquisition; Project administration; Writing -- review \& editing. Thong Cao Văn: Conceptualization; Investigation; Writing -- review \& editing. Hieu Le Ngoc: Conceptualization; Data curation; Formal analysis; Methodology; Software; Visualization; Writing -- original draft; Writing -- review \& editing.

\textbf{Conflicts of interest:} none declared.
'''
    tokens.update(CONTACT=contact,DECLARATIONS=declarations)
    tex=template
    for key,value in tokens.items(): tex=tex.replace('@@'+key+'@@',value)
    unresolved=re.findall(r'@@[A-Z]+@@',tex);assert not unresolved,unresolved
    from build_visual_upgrade import main as build_visuals
    from enhance_manuscript_visual import enhance_text
    build_visuals()
    tex=enhance_text(tex)
    (MAN/'P3_PAPI_DTI_Merger.tex').write_text(tex,encoding='utf-8')
    anonymous=tex.replace(author,r'\author{}').replace(contact,'').replace(declarations,
        r'''\section*{Declarations}
The study uses publicly released aggregated provincial statistics. Data provenance and analysis code accompany the manuscript. Identifying funding, authorship and repository details are supplied separately for anonymous review. AI assistance in code drafting and manuscript revision is disclosed in the separate title-page file.
''')
    (MAN/'P3_PAPI_DTI_Merger_anonymous.tex').write_text(anonymous,encoding='utf-8')
    title=tex[:tex.index(r'\begin{document}')]+r'\begin{document}\maketitle'+'\n'+contact+'\n'+declarations+'\n'+r'\end{document}'
    (MAN/'P3_title_page.tex').write_text(title,encoding='utf-8')
    words=len(re.findall(r'\b[\w-]+\b',tex[tex.index(r'\section{Introduction}'):tex.index(r'\section*{Declarations}')]))
    (OUT/'manuscript_build_info.txt').write_text(f'LaTeX-source token count for main sections (includes commands/tables): {words}\nAll numeric tokens and tables generated from results_upgrade.\n',encoding='utf-8')
    print('Updated self-contained main manuscript, anonymous version and title page.')

if __name__=='__main__':main()
