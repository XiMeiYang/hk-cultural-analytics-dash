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
app=Dash(__name__,title='Hong Kong Cultural Participation | Space, Networks and Modes')
server=app.server
app.layout=html.Div([
    html.Header([html.H1('Multidimensional Visual Analytics of Cultural Consumption in Hong Kong')]),
    html.Div([html.Div([html.Strong('878'),html.Span('Event records')],className='stat'),
        html.Div([html.Strong('812 / 878'),html.Span('Events with coordinates')],className='stat'),
        html.Div([html.Strong('25'),html.Span('Identifiable facilities')],className='stat'),
        html.Div([html.Strong('9 × 3'),html.Span('Art forms × exclusive participation modes')],className='stat')],className='stats'),
    dcc.Tabs(id='tab',value='s4',children=[
        dcc.Tab(label='Spatial Dimension · Q4',value='s4'),
        dcc.Tab(label='Spatial Dimension · Q5',value='s5'),
        dcc.Tab(label='Category Dimension · Q5',value='c5')]),
    html.Div([html.Div([html.Label('Event category (spatial analyses only)'),
        dcc.Dropdown(id='category',options=[{'label':'All categories','value':'ALL'}]+[{'label':x,'value':x} for x in sorted(EVENTS.category.unique())],value='ALL',clearable=False)],className='control'),
        html.Div([html.Label('Map background'),dcc.Dropdown(id='map-style',options=[{'label':'Light basemap (internet required)','value':'carto-positron'},{'label':'Blank background (offline coordinates)','value':'white-bg'}],value='carto-positron',clearable=False)],className='control')],id='global-controls',className='controls'),
    html.Section([
        html.Div('01 / SPATIAL COMPARISON',className='eyebrow'),
        html.H2('Spatial Dimension · Question 4: Comparing Current Events with Historical Spatial Patterns'),
        html.P('Compare relative shares across common facilities. This is a descriptive comparison, not a like-for-like test of historical trends.'),
        html.Div([html.Div([html.Label('Historical reference period'),dcc.Dropdown(id='period',options=[{'label':x,'value':x} for x in ['2024','2025']+sorted(HISTORY.period.unique())],value='2025',clearable=False)],className='control'),
            html.Div([html.Label('Historical measure'),dcc.Dropdown(id='metric',options=[{'label':'Performances','value':'Performance'},{'label':'Attendances','value':'Attendance'}],value='Performance',clearable=False)],className='control')],className='controls'),
        html.Div(id='spatial-summary',className='notice'),
        html.Div([dcc.Graph(id='density'),dcc.Graph(id='bivariate')],className='grid'),
        html.Div([dcc.Graph(id='comparison'),html.Div([dcc.Graph(figure=bivariate_legend()),html.P('Horizontal: historical share. Vertical: current event share. Tertiles are computed on common facilities; boundary values enter the lower group. Filtering recalculates thresholds.'),html.P('Points represent facilities, not audience residences. The source archive contains no district boundaries, so this version does not draw unverified district polygons.')],className='card')],className='grid'),
        html.Button('Download comparison CSV',id='download-spatial-btn',n_clicks=0),dcc.Download(id='download-spatial'),
        html.P('Historical figures exclude hirer programmes; the current snapshot is not a full-year total. Only common facilities with complete historical observations are compared. Missing records are not zeros. Category filters affect current events only; historical figures retain all categories. The density map uses screen-space smoothing, not events per square kilometre.',className='footnote')
    ],id='panel-s4',className='panel'),
    html.Section([
        html.Div('02 / BIPARTITE NETWORK',className='eyebrow'),
        html.H2('Spatial Dimension · Question 5: Venue–Category Bipartite Communities'),
        html.P('Observed events connect facilities and categories. Rooms within a facility are combined; edge weights count event records.'),
        html.Div([html.Label('Community resolution γ (higher values generally favour finer partitions)'),dcc.Slider(id='resolution',min=.5,max=1.5,step=.25,value=1,marks={.5:'0.5',1:'1.0',1.5:'1.5'})],className='slider'),
        html.Div(id='network-summary',className='notice'),dcc.Graph(id='network'),
        html.Div([dcc.Graph(id='community-heatmap'),dcc.Graph(id='community-map')],className='grid'),
        html.Button('Download venue communities CSV',id='download-network-btn',n_clicks=0),dcc.Download(id='download-network'),
        html.P('A deterministic greedy heuristic optimizes Barber bipartite modularity while retaining both node types. Communities are algorithmic groupings, not verified collaborations. Facilities without coordinates remain in the network.',className='footnote')
    ],id='panel-s5',className='panel'),
    html.Section([
        html.Div('03 / PARTICIPATION SPACE',className='eyebrow'),
        html.H2('Category Dimension · Question 5: Correspondence Analysis and Digital Participation Space'),
        html.Div('Space refers to statistical feature space. The proposal title is retained, but the data support alternative-mode participation as a proxy only: television, radio and DVD/CD are included. This is not a purely online participation rate.',className='notice'),
        dcc.Graph(figure=ca_biplot(MODES_DATA,CA)),
        html.Div([dcc.Graph(figure=participation_bar(MODES_DATA)),dcc.Graph(figure=modes_heatmap(MODES_DATA))],className='grid'),
        html.P('From any-mode U, physical P and alternative A rates: physical only = U−A; alternative only = U−P; both = P+A−U. The nine art forms use weighted population percentages and may overlap. CA describes structure; percentages are not converted into respondent counts, and no chi-square significance is claimed.'),
        html.P('The biplot displays row and column principal coordinates. Compare relationships within each point type; direct distances between art forms and modes do not measure association strength. Interpret the plot alongside the mode matrix.'),
        html.Button('Download participation modes and CA coordinates CSV',id='download-ca-btn',n_clicks=0),dcc.Download(id='download-ca')
    ],id='panel-c5',className='panel'),
    html.Footer('Reproducible descriptive analysis · Python / Plotly / Dash')
],className='shell')

def subset(category):
    return EVENTS if category=='ALL' else EVENTS[EVENTS.category.eq(category)]

@callback([Output('panel-'+x,'style') for x in ['s4','s5','c5']]+[Output('global-controls','style')],Input('tab','value'))
def switch_tab(value):
    return [dict(display='block' if x==value else 'none') for x in ['s4','s5','c5']]+[dict(display='flex' if value in ['s4','s5'] else 'none')]

@callback(Output('density','figure'),Output('bivariate','figure'),Output('comparison','figure'),Output('spatial-summary','children'),
          Input('category','value'),Input('period','value'),Input('metric','value'),Input('map-style','value'))
def update_spatial(category,period,metric,style):
    e=subset(category);d,rho=spatial_comparison(e,HISTORY,period,metric)
    r=f'{rho:.3f}' if np.isfinite(rho) else 'not available'
    summary=f'Selected events: {len(e)}; geocoded: {int(e.mapped.sum())}. Common complete facilities: {len(d)}; mapped: {int(d.latitude.notna().sum()) if not d.empty else 0}. Spearman ρ={r} (descriptive only; not evidence of recovery or statistical significance).'
    return density_map(e,style),bivariate_map(d,style),comparison_scatter(d),summary

@callback(Output('network','figure'),Output('community-heatmap','figure'),Output('community-map','figure'),Output('network-summary','children'),
          Input('category','value'),Input('resolution','value'),Input('map-style','value'))
def update_network(category,resolution,style):
    e=subset(category);m=incidence(e)
    if m.empty:return empty('No identifiable facilities'),empty('No data'),empty('No data'),'No venue–category associations for this selection.'
    vl,cl,q=bipartite_communities(m,resolution)
    msg=f'{len(m)} facilities × {m.shape[1]} categories; {int((m>0).sum().sum())} edges, {int(m.sum().sum())} events; {len(set(vl)|set(cl))} communities; bipartite modularity Q={q:.3f}. Excluded area-aggregate events: {int((~e.site_specific).sum())}.'
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
