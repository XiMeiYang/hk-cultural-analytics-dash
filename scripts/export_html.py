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
    html=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>香港文化分析</title><body style="max-width:1100px;margin:30px auto;font-family:sans-serif"><h1>香港公共文化消费的多维可视分析</h1>',
          '<p>2026-10-02事件快照；历史2025年；问卷参考期2021/07–2022/07。离线地图不含道路底图，保留真实经纬度。空间比较存在覆盖与主办方口径差异；非实体参与包含电视、广播和CD，并非纯线上参与。CA不作显著性推断。</p>']
    for i,f in enumerate(figs):html.append(pio.to_html(f,full_html=False,include_plotlyjs=True if i==0 else False))
    html.append('</body></html>');out=ROOT/'exports';out.mkdir(exist_ok=True)
    (out/'member4_report.html').write_text('\n'.join(html),encoding='utf-8')
    print(out/'member4_report.html')

if __name__=='__main__':main()
