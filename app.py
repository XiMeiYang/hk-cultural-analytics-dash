"""Run: python app.py. All analyses use the bundled, documented snapshot."""
import os
import numpy as np
from dash import Dash, html, dcc, Input, Output, State, callback
from src.analysis import (load_data, spatial_comparison, incidence, bipartite_communities,
                          participation_modes, correspondence_analysis, MODES)
from src.charts import (density_map,bivariate_map,bivariate_legend,comparison_scatter,
                        network_fig,community_heatmap,community_map,ca_biplot,
                        participation_bar,modes_heatmap,empty)

EVENTS,HISTORY,SURVEY=load_data()
MODES_DATA=participation_modes(SURVEY)
CA=correspondence_analysis(MODES_DATA[MODES])
app=Dash(__name__,title='香港文化参与 | 空间 · 网络 · 模式')
server=app.server
app.layout=html.Div([
    html.Header([html.Div('COMP7507  /  MEMBER 04',className='eyebrow'),
        html.H1('香港公共文化消费的多维可视分析'),
        html.P('从活动在哪里，到场地如何连接，再到观众如何参与。',className='subtitle'),
        html.Div('事件快照 2026-10-02  ·  历史 2023Q2—2026Q1  ·  问卷参与期 2021/07—2022/07',className='tag')]),
    html.Div([html.Div([html.Strong('878'),html.Span('事件记录')],className='stat'),
        html.Div([html.Strong('812 / 878'),html.Span('事件坐标覆盖')],className='stat'),
        html.Div([html.Strong('25'),html.Span('可识别的具体设施')],className='stat'),
        html.Div([html.Strong('9 × 3'),html.Span('艺术类别 × 互斥参与模式')],className='stat')],className='stats'),
    dcc.Tabs(id='tab',value='s4',children=[
        dcc.Tab(label='空间维度 · 问题4',value='s4'),
        dcc.Tab(label='空间维度 · 问题5',value='s5'),
        dcc.Tab(label='类别维度 · 问题5',value='c5'),
        dcc.Tab(label='数据与方法',value='methods')]),
    html.Div([html.Div([html.Label('事件类别（仅作用于两个空间问题）'),
        dcc.Dropdown(id='category',options=[{'label':'全部类别','value':'ALL'}]+[{'label':x,'value':x} for x in sorted(EVENTS.category.unique())],value='ALL',clearable=False)],className='control'),
        html.Div([html.Label('地图底图'),dcc.Dropdown(id='map-style',options=[{'label':'浅色底图（需联网）','value':'carto-positron'},{'label':'空白底图（离线坐标）','value':'white-bg'}],value='carto-positron',clearable=False)],className='control')],id='global-controls',className='controls'),
    html.Section([
        html.Div('01 / SPATIAL COMPARISON',className='eyebrow'),
        html.H2('空间维度 · 问题4：用当前事件级场地坐标验证历史空间格局'),
        html.P('比较共同设施的相对份额，观察当前活动是否仍集中于历史上的主要场地。这里的“验证”是描述性对照，不是同口径趋势检验。'),
        html.Div([html.Div([html.Label('历史对照期'),dcc.Dropdown(id='period',options=[{'label':x,'value':x} for x in ['2024','2025']+sorted(HISTORY.period.unique())],value='2025',clearable=False)],className='control'),
            html.Div([html.Label('历史指标'),dcc.Dropdown(id='metric',options=[{'label':'表演场次','value':'Performance'},{'label':'入场人次','value':'Attendance'}],value='Performance',clearable=False)],className='control')],className='controls'),
        html.Div(id='spatial-summary',className='notice'),
        html.Div([dcc.Graph(id='density'),dcc.Graph(id='bivariate')],className='grid'),
        html.Div([dcc.Graph(id='comparison'),html.Div([dcc.Graph(figure=bivariate_legend()),html.P('横轴：历史份额；纵轴：当前事件份额。按共同样本的三分位分组，边界值归入较低组。筛选后阈值会重新计算。'),html.P('这是场地点图，没有将场地坐标误当作观众居住地。原包不含行政区边界，本版本不绘制未经核验的18区填色图。')],className='card')],className='grid'),
        html.Button('下载当前比较表 CSV',id='download-spatial-btn',n_clicks=0),dcc.Download(id='download-spatial'),
        html.P('历史指标不含租用者举办的节目；当前快照不是全年活动总量。只保留当前出现、历史期间数据完整的共同设施；没有记录不等于零。筛选类别只作用于当前事件，历史侧仍是全部类别。密度图是屏幕空间平滑，不是每平方公里密度。',className='footnote')
    ],id='panel-s4',className='panel'),
    html.Section([
        html.Div('02 / BIPARTITE NETWORK',className='eyebrow'),
        html.H2('空间维度 · 问题5：场地与类别二部图社区检测'),
        html.P('用真实事件连接场地与类别。场地内的不同厅室合并为同一设施；连线权重是事件记录数。'),
        html.Div([html.Label('社区分辨率 γ（较高通常倾向更细的划分；属于敏感性检查）'),dcc.Slider(id='resolution',min=.5,max=1.5,step=.25,value=1,marks={.5:'0.5',1:'1.0',1.5:'1.5'})],className='slider'),
        html.Div(id='network-summary',className='notice'),dcc.Graph(id='network'),
        html.Div([dcc.Graph(id='community-heatmap'),dcc.Graph(id='community-map')],className='grid'),
        html.Button('下载场地社区表 CSV',id='download-network-btn',n_clicks=0),dcc.Download(id='download-network'),
        html.P('采用 Barber 二部模块度的确定性贪心合并启发式，保留两类节点，不使用普通单模投影代替二部图。社区是算法划分，不代表真实合作组织；地图没有坐标的场地仍参与网络。',className='footnote')
    ],id='panel-s5',className='panel'),
    html.Section([
        html.Div('03 / PARTICIPATION SPACE',className='eyebrow'),
        html.H2('类别维度 · 问题5：对应分析与数字化参与空间'),
        html.Div('“空间”指统计特征空间。此处保留提案题名，但数据只支持非实体参与代理：电视、广播、DVD/CD 也包括在内，不能称为纯线上参与率。',className='notice'),
        dcc.Graph(figure=ca_biplot(MODES_DATA,CA)),
        html.Div([dcc.Graph(figure=participation_bar(MODES_DATA)),dcc.Graph(figure=modes_heatmap(MODES_DATA))],className='grid'),
        html.P('从报告的任一模式 U、实体 P、非实体 A 推导：仅实体=U−A；仅非实体=U−P；两者皆有=P+A−U。9类分别为总体加权百分比，类别之间可重叠。CA仅描述结构，不把百分比乘3017伪造人数，也不报告卡方显著性。'),
        html.P('双标图使用行列主坐标。可比较同类点的相对关系；艺术点与模式点的直接欧氏距离不等于关联强度，需要结合模式矩阵解释。'),
        html.Button('下载参与模式与 CA 坐标 CSV',id='download-ca-btn',n_clicks=0),dcc.Download(id='download-ca')
    ],id='panel-c5',className='panel'),
    html.Section([
        html.H2('数据来源、清洗与边界'),
        dcc.Markdown('''### 这三个问题如何串起来？
先看**文化活动在哪里**（双变量地图），再看**哪些场地与类别形成组合**（二部网络），最后看**不同类别偏向怎样的参与模式**（CA）。三套分析有不同观察单位，不能硬拼为个人记录。

### 清洗与可复现性
1. event_id、venue_id 唯一性检查；类别代码统一大写；按场地键进行多对一连接。
2. 同一设施的厅室通过英文名称的 ` (` 前缀合并；映射表和缺失清单见 data/processed。
3. “Venues in … district” 是区域集合，排除出具体设施网络；坐标缺失不补猜测点。
4. 历史场地代码去首尾空格，剔除 Total/Other/Non-LCSD；`-` 保留为缺失。全年只使用四季度数值完整的设施。
5. 问卷从官方报告第36页的展示值转录；排除 Any Art Form 总计，检查互斥模式非负与加总关系。

### 来源
- [LCSD 事件 XML](https://www.lcsd.gov.hk/datagovhk/event/events.xml) · [场地 XML](https://www.lcsd.gov.hk/datagovhk/event/venues.xml) · [事件字典](https://www.lcsd.gov.hk/datagovhk/event/data_dictionary.pdf)
- [LCSD 统计开放数据入口](https://www.lcsd.gov.hk/datagovhk/)：使用用户原包内场地季度 CSV；原包未保存该表的直接下载地址。
- [HKADC Stage 3 报告](https://www.hkadc.org.hk/en/research/behavioural-study-on-arts-participants-stage-3-survey-report-on-patterns-of-arts-participation_3004)：2022年调查，参与参考期2021年7月至2022年7月；n=3017；报告百分比已加权并四舍五入。

页面使用的是 **2026-10-02 保存的历史快照**，不会自动更新为今天的活动。实时下载链接可能已变化。

### 不能据此得出的结论
- 当前事件数不是演出场次、观众数或完整年度供给；历史入场人次不是去重人数。
- 设施地图不代表观众住址、可达性或18区人口公平性。
- 二部社区不证明场地合作关系；CA不证明数字化导致参与变化。
- 原包没有纯线上参与分项，因此不制作虚构的线上比例。
''')
    ],id='panel-methods',className='panel'),
    html.Footer('基于原始数据快照的可复现描述性分析 · Python / Plotly / Dash')
],className='shell')

def subset(category):
    return EVENTS if category=='ALL' else EVENTS[EVENTS.category.eq(category)]

@callback([Output('panel-'+x,'style') for x in ['s4','s5','c5','methods']]+[Output('global-controls','style')],Input('tab','value'))
def switch_tab(value):
    return [dict(display='block' if x==value else 'none') for x in ['s4','s5','c5','methods']]+[dict(display='flex' if value in ['s4','s5'] else 'none')]

@callback(Output('density','figure'),Output('bivariate','figure'),Output('comparison','figure'),Output('spatial-summary','children'),
          Input('category','value'),Input('period','value'),Input('metric','value'),Input('map-style','value'))
def update_spatial(category,period,metric,style):
    e=subset(category);d,rho=spatial_comparison(e,HISTORY,period,metric)
    r=f'{rho:.3f}' if np.isfinite(rho) else '不可计算'
    summary=f'筛选事件 {len(e)} 条；可定位 {int(e.mapped.sum())} 条。共同完整设施 {len(d)} 个；地图可定位 {int(d.latitude.notna().sum()) if not d.empty else 0} 个。Spearman ρ={r}（描述性；不作同口径恢复或显著性结论）。'
    return density_map(e,style),bivariate_map(d,style),comparison_scatter(d),summary

@callback(Output('network','figure'),Output('community-heatmap','figure'),Output('community-map','figure'),Output('network-summary','children'),
          Input('category','value'),Input('resolution','value'),Input('map-style','value'))
def update_network(category,resolution,style):
    e=subset(category);m=incidence(e)
    if m.empty:return empty('无具体设施'),empty('无数据'),empty('无数据'),'此筛选没有可用的场地—类别关联。'
    vl,cl,q=bipartite_communities(m,resolution)
    msg=f'{len(m)} 个设施 × {m.shape[1]} 类别；{int((m>0).sum().sum())} 条关联，{int(m.sum().sum())} 条事件；{len(set(vl)|set(cl))} 个社区；二部模块度 Q={q:.3f}。区域集合记录排除 {int((~e.site_specific).sum())} 条。'
    return network_fig(m,vl,cl),community_heatmap(m,vl),community_map(e,m,vl,style),msg

@callback(Output('download-spatial','data'),Input('download-spatial-btn','n_clicks'),State('category','value'),State('period','value'),State('metric','value'),prevent_initial_call=True)
def download_spatial(_,category,period,metric):
    d,_=spatial_comparison(subset(category),HISTORY,period,metric)
    return dcc.send_data_frame(d.to_csv,f'spatial_{period}_{metric}.csv',index=False)

@callback(Output('download-network','data'),Input('download-network-btn','n_clicks'),State('category','value'),State('resolution','value'),prevent_initial_call=True)
def download_network(_,category,resolution):
    m=incidence(subset(category))
    if m.empty:return None
    vl,_,_=bipartite_communities(m,resolution)
    d=m.copy();d['community']=vl
    return dcc.send_data_frame(d.to_csv,'venue_communities.csv')

@callback(Output('download-ca','data'),Input('download-ca-btn','n_clicks'),prevent_initial_call=True)
def download_ca(_):
    d=MODES_DATA.copy();d['CA1']=CA['rows'][:,0];d['CA2']=CA['rows'][:,1]
    return dcc.send_data_frame(d.to_csv,'participation_modes_ca.csv')

if __name__=='__main__':
    app.run(host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','8050')),debug=False)
