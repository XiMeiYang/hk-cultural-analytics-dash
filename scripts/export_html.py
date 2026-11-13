"""Export one standalone, offline report (embedded Plotly; maps use coordinate-only base)."""
import sys
from pathlib import Path
import plotly.io as pio
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.analysis import *
from src.charts import *

def main():
    e,h,s=load_data();d,r=spatial_comparison(e,h);m=incidence(e);vl,cl,q=bipartite_communities(m)
    p=participation_modes(s);ca=correspondence_analysis(p[MODES])
    figs=[density_map(e,'white-bg'),bivariate_map(d,'white-bg'),bivariate_legend(),comparison_scatter(d),
          network_fig(m,vl,cl),community_heatmap(m,vl),community_map(e,m,vl,'white-bg'),
          ca_biplot(p,ca),participation_bar(p),modes_heatmap(p)]
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Hong Kong Cultural Analytics</title><body style="max-width:1100px;margin:30px auto;font-family:sans-serif"><h1>Multidimensional Visual Analytics of Cultural Consumption in Hong Kong</h1>',
          '<p>Historical and current event shares have different coverage. Alternative participation includes television, radio and CD, not only online channels. CA is descriptive. Offline maps retain coordinates without a road basemap.</p>']
    for i,f in enumerate(figs):html.append(pio.to_html(f,full_html=False,include_plotlyjs=True if i==0 else False))
    html.append('</body></html>');out=ROOT/'exports';out.mkdir(exist_ok=True)
    (out/'member4_report.html').write_text('\n'.join(html),encoding='utf-8')
    print(out/'member4_report.html')

if __name__=='__main__':main()
