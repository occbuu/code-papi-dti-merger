"""Enhance the existing manuscript in place; also callable by its generator."""
from pathlib import Path
import json
import re
ROOT=Path(__file__).resolve().parent
MAN=ROOT/'Paper3_DeTaiThayHien/P3_PAPI_DTI_Merger.tex'

def enhance_text(tex):
    figures=json.loads((ROOT/'results_upgrade/visual_inline_tikz.json').read_text(encoding='utf-8'))
    if '% VISUAL_LITERATURE_REVISION_2026_10_09' in tex:
        def update_figure(match):
            block=match.group(0)
            for key,value in figures.items():
                if r'\label{fig:'+key+'}' in block:
                    return value
            return block
        return re.sub(r'\\begin\{figure\}\[p\].*?\\end\{figure\}',update_figure,tex,flags=re.S)
    tex=tex.replace(r'\usepackage{tikz}',r'\usepackage{tikz}'+'\n'+r'\usepackage{graphicx}'+'\n'+r'\usepackage{placeins}')
    moved=[]
    pattern=r'\\begin\{table\}\[htbp\].*?\\end\{table\}'
    for block in re.findall(pattern,tex,re.S):
        label=re.search(r'\\label\{([^}]+)\}',block).group(1)
        if label in ['tab:alignment','tab:aggregation','tab:gaps','tab:panel','tab:lag']:
            moved.append(block)
            replacement=figures['scatter'] if label=='tab:alignment' else figures['coefficients'] if label=='tab:panel' else ''
            tex=tex.replace(block,replacement,1)
    # Replace the former single bar figure with the complete simulation comparison.
    tex=re.sub(r'\\begin\{figure\}\[htbp\].*?\\end\{figure\}',lambda _:figures['aggregation'],tex,count=1,flags=re.S)
    tex=tex.replace(r'\section{Conceptual framework and institutional setting}',
        figures['reformmap']+'\n'+r'\FloatBarrier'+'\n'+r'\section{Conceptual framework and institutional setting}',1)
    tex=tex.replace(r'\section{Data and analytical design}',
        r'\section{Data and analytical design}'+'\n\n'+r'Figure~\ref{fig:workflow} provides an overview of the four analytical phases, separating construct interpretation from statistical validation.'+'\n'+figures['workflow'],1)
    tex=tex.replace(r'\subsection{An observable measurement audit}',figures['scoremap']+'\n'+r'\FloatBarrier'+'\n'+r'\subsection{An observable measurement audit}',1)
    tex=tex.replace(r'\section{Measurement audit and sensitivity outputs}',
        r'\section{Detailed estimates, measurement audit and sensitivity outputs}'+'\n\n'+'\n\n'.join(moved)+'\n'+r'\FloatBarrier',1)
    # Explicit references to figures establish their argumentative role.
    tex=tex.replace('The country has two relevant measurement systems.',r'Figure~\ref{fig:reformmap} locates the study units and distinguishes the mapped merger groups from unchanged provinces. The country has two relevant measurement systems.',1)
    tex=tex.replace('There are eight missing full-PAPI province-years,',r'Figure~\ref{fig:scoremap} maps the three principal measures in their original units. There are eight missing full-PAPI province-years,',1)
    tex=tex.replace(r'\subsection{Alignment and supporting panel models}',r'\subsection{Alignment and supporting panel models}'+'\n\n'+r'Figure~\ref{fig:scatter} visualises matched endpoint alignment, and Figure~\ref{fig:coefficients} summarises the principal conditional estimates; detailed numeric tables are retained in the appendix.',1)
    for lab in ['alignment','aggregation','gaps','panel','lag']:
        tex=re.sub(r'(?<!Appendix )Table~\\ref\{tab:'+lab+r'\}',lambda _:r'Appendix Table~\ref{tab:'+lab+'}',tex)
    theory=r'''
\subsection{Adoption, information-system success and benchmark validity}

Technology acceptance and information-system success address different stages of the readiness-to-experience sequence. TAM links acceptance to perceived usefulness and ease of use (Davis, 1989), while UTAUT distinguishes performance and effort expectations from social influence and facilitating conditions (Venkatesh et al., 2003). In public services, citizen trust also shapes adoption (Carter \& Bélanger, 2005). The DeLone--McLean framework separates system, information and service quality from use, satisfaction and net benefits (DeLone \& McLean, 2003). These distinctions imply that counting readiness or connectivity cannot establish successful completion. They do not license estimating individual acceptance mechanisms with provincial aggregate scores. PAPI contains selected access and response indicators, but does not supply a full TAM or IS-success measurement model here.

The e-government paradox literature identifies barriers between service investment and adoption (Savoldelli et al., 2014). Public-value research further separates organisational efficiencies from the outcomes valued by citizens (Cordella \& Bonina, 2012). Digital transformation therefore involves organisational processes and relationships rather than simply putting existing forms online (Mergel et al., 2019); a recent systematic review documents the wider forms of public-sector change involved (Haug et al., 2024). Our component audit asks a prior question: whether the citizen-side criterion is sufficiently aligned with the administrative performance being evaluated. It cannot adjudicate between trust, usability or organisational mechanisms without individual or transaction data.

Benchmarking frameworks themselves illustrate why interpretation needs to follow purpose. The OECD Digital Government Index assesses foundations for coherent, human-centred transformation (OECD, 2024). The UN survey combines online services, telecommunications infrastructure and human capital and also assesses local portals (UN DESA, 2024). These are related constructs, not direct observations of citizens' completed transactions. Research on EU benchmarking warns that indicator prominence may persist despite weak impact-evaluation value (Codagnone et al., 2015). This concern is consistent with treating composite construction as an analytical and normative choice rather than a neutral summary (Saltelli, 2007). It does not imply that DTI or PAPI is invalid for its stated purpose.
'''
    tex=tex.replace(r'\subsection{Territorial resolution and information loss}',theory+'\n'+r'\subsection{Territorial resolution and information loss}',1)
    spatial=r'''
Scale and zoning are distinct sources of MAUP: coarser reporting absorbs constituent variation, whereas alternative arrangements at the same number of units change the grouping. Our 63-to-34 decomposition describes the first issue, and the size-preserving alternative partitions diagnose the second. Contemporary work treats uncertainty in spatial inference as a substantive feature of measurement (Franklin, 2022). The uncertain geographic context problem adds that administrative units may differ from the places where citizens actually encounter services (Kwan, 2012). Thus a justified reporting unit need not be the correct individual exposure unit. We make no claim about users' service catchments or individual disadvantage from provincial polygons.

Comparative amalgamation evidence also distinguishes average outcomes from territorial distribution. Danish expenditure research evaluates jurisdiction size through an identified reform setting (Blom-Hansen et al., 2016). In Finland, geocoded evidence shows that political representation and local public employment can change unevenly across constituent municipalities (Harjunen et al., 2021). Japanese waste-management evidence finds cost responses contingent on municipal size and prior service arrangements (Li \& Takeuchi, 2023). A systematic review stresses the diversity of economic results and research designs (Gendźwiłł et al., 2021), while a recent cross-European comparison shows that reform strategies and policy instruments differ substantially (Klausen, 2026; first published online in 2024). These studies motivate attention to constituents and institutions; they do not establish that amalgamation universally improves averages, conceals individual inequality or yields the same effects for Vietnamese provinces.
'''
    tex=tex.replace(r'\subsection{Indices and reform in Viet Nam}',spatial+'\n'+r'\subsection{Indices and reform in Viet Nam}',1)
    tex=tex.replace('These procedures address within-province dependence,',
        r'Cluster-robust inference follows the dependence-aware logic discussed by Cameron and Miller (2015) and MacKinnon et al.\ (2023). These procedures address within-province dependence,',1)
    tex=tex.replace('Moran statistics provide a separate diagnostic of clustering on the same graph.',
        r'The boundary database is described by Runfola et al.\ (2020); its historical vintage remains an explicit limitation here. Moran statistics provide a separate global diagnostic of clustering on the same graph. Choropleth colours alone do not identify statistically significant local clusters; that would require local statistics and multiple-testing treatment (Anselin, 1995).',1)
    tex=tex.replace('The accompanying tables retain year-specific SD, IQR and CV.',
        r'Nested tuning separates model selection from evaluation to avoid optimistic validation (Varma \& Simon, 2006). Province grouping respects repeated observations, consistent with structured-data validation principles (Roberts et al., 2017), but does not constitute geographically buffered cross-validation. Nearby training and test provinces can share unmeasured context. The accompanying tables retain year-specific SD, IQR and CV.',1)
    tex=tex.replace('under the conventional convergence model,',r'under the conventional convergence model (Barro \& Sala-i-Martin, 1992),',1)
    # Add verified references and retain alphabetical ordering.
    additions=json.loads((ROOT/'literature_visual_revision.json').read_text(encoding='utf-8'))
    start=tex.index(r'\section*{References}');end=tex.index(r'\clearpage',start)
    old=tex[start:end];head,*entries=old.split(r'\refitem')
    for author,journal,url in additions:
        entry=author.replace('&',r'\&')+r' \emph{'+journal.replace('&',r'\&')+r'}. \url{'+url+r'}.\par'+'\n'
        entries.append(' '+entry)
    # Ø needs an explicit TeX glyph with the document's T5 setup.
    entries=[entry.replace('Ø',r'{\O}') for entry in entries]
    refs=head+''.join(r'\refitem'+e for e in sorted(entries,key=lambda s:s.strip().casefold()))
    tex=tex[:start]+refs+tex[end:]
    tex=tex.replace(r'\section*{Declarations}',r'\FloatBarrier'+'\n'+r'\section*{Declarations}',1)
    return '% VISUAL_LITERATURE_REVISION_2026_10_09\n'+tex

def main():
    tex=MAN.read_text(encoding='utf-8')
    backup=ROOT/'archive/pre_visual_revision_2026-10-09'
    backup.mkdir(exist_ok=True)
    if not (backup/MAN.name).exists(): (backup/MAN.name).write_text(tex,encoding='utf-8')
    revised=enhance_text(tex)
    MAN.write_text(revised,encoding='utf-8')
    report={'main_figures':len(re.findall(r'\\begin\{figure\}',revised[:revised.index(r'\appendix')])),'main_tables':len(re.findall(r'\\begin\{table\}',revised[:revised.index(r'\appendix')])),'references':revised.count(r'\refitem')-1,'source_bytes':len(revised.encode('utf-8'))}
    (ROOT/'results_upgrade/EDITORIAL_REVISION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
