import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from .analysis import facility_table, MODES

PALETTE=['#216869','#d99b42','#5368a6','#b9556b','#6d9472','#9a6aab','#ba7746','#5e879d','#7d7852','#967e7e']
BIVARIATE={'0-0':'#e8e8e8','0-1':'#ace4e4','0-2':'#5ac8c8','1-0':'#dfb0d6','1-1':'#a5add3','1-2':'#5698b9','2-0':'#be64ac','2-1':'#8c62aa','2-2':'#3b4994'}

def finish(fig, title=None, height=460):
    fig.update_layout(template='plotly_white',height=height,
        font=dict(family='Arial, Microsoft YaHei, sans-serif',color='#243d49'),
        paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=45,r=30,t=60,b=45),
        title=dict(text=title or '',font=dict(size=16)),legend_title_text='',
        colorway=PALETTE)
    return fig

def empty(message):
    f=go.Figure(); f.add_annotation(text=message,x=.5,y=.5,xref='paper',yref='paper',showarrow=False)
    f.update_xaxes(visible=False);f.update_yaxes(visible=False)
    return finish(f,height=400)

def density_map(events,style):
    e=events[events.mapped & events.site_specific]
    if e.empty:return empty('No valid coordinates for this selection')
    d=facility_table(e)
    f=px.density_map(d,lat='latitude',lon='longitude',z='events',radius=26,
        center={'lat':22.36,'lon':114.14},zoom=9,map_style=style,
        hover_name='facility',hover_data={'events':True,'latitude':False,'longitude':False},
        color_continuous_scale='Teal',labels={'events':'Event records'})
    return finish(f,'Current event density',510)

def bivariate_map(d,style):
    if d.empty:return empty('No comparable facilities in this period')
    p=d.dropna(subset=['latitude','longitude']).copy()
    f=px.scatter_map(p,lat='latitude',lon='longitude',color='bivariate',
        color_discrete_map=BIVARIATE,size_max=20,
        hover_name='facility',zoom=9,center={'lat':22.36,'lon':114.14},map_style=style,
        hover_data={'historical_share':':.2f','current_share':':.2f','events':True,'historical':True,'bivariate':False,'latitude':False,'longitude':False},
        labels={'historical_share':'Historical share (%)','current_share':'Current share (%)','events':'Current events','historical':'Historical value'})
    f.update_traces(marker_size=19);f.update_layout(showlegend=False)
    return finish(f,'Historical × current event shares',510)

def bivariate_legend():
    f=go.Figure()
    for h in range(3):
        for c in range(3):
            f.add_trace(go.Scatter(x=[h],y=[c],mode='markers',marker=dict(symbol='square',size=48,color=BIVARIATE[f'{h}-{c}']),showlegend=False,hoverinfo='skip'))
    f.update_xaxes(tickvals=[0,1,2],ticktext=['Low','Medium','High'],title='Historical share →',range=[-.5,2.5],showgrid=False,zeroline=False)
    f.update_yaxes(tickvals=[0,1,2],ticktext=['Low','Medium','High'],title='Current share →',range=[-.5,2.5],showgrid=False,zeroline=False)
    return finish(f,'Tertile colour key (ties kept together)',260)

def comparison_scatter(d):
    if d.empty:return empty('No common facilities')
    f=px.scatter(d,x='historical_share',y='current_share',hover_name='facility',
        size='events',color_discrete_sequence=[PALETTE[0]],labels={'historical_share':'Historical share (%)','current_share':'Current event share (%)'})
    lim=max(d.historical_share.max(),d.current_share.max())*1.1
    f.add_shape(type='line',x0=0,y0=0,x1=lim,y1=lim,line=dict(color='#b8c6cc',dash='dot'))
    return finish(f,'Relative shares across common facilities')

def network_fig(matrix,vl,cl):
    g=nx.Graph()
    names=list(matrix.index)+list(matrix.columns); n=len(matrix)
    for i in range(len(names)):g.add_node(i)
    for i in range(n):
        for j in range(matrix.shape[1]):
            if matrix.iloc[i,j]>0:g.add_edge(i,n+j,weight=float(matrix.iloc[i,j]))
    pos=nx.spring_layout(g,seed=42,weight='weight',iterations=120)
    f=go.Figure()
    for i,j,attr in g.edges(data=True):
        f.add_trace(go.Scatter(x=[pos[i][0],pos[j][0]],y=[pos[i][1],pos[j][1]],mode='lines',
            line=dict(width=.4+np.log1p(attr['weight'])/2,color='rgba(112,137,147,.3)'),hoverinfo='skip',showlegend=False))
    labels=np.r_[vl,cl]
    for ids,symbol,label in [(range(n),'circle','Facilities'),(range(n,len(names)),'diamond','Categories')]:
        ids=list(ids)
        f.add_trace(go.Scatter(x=[pos[i][0] for i in ids],y=[pos[i][1] for i in ids],mode='markers',name=label,
            text=[names[i] for i in ids],customdata=[[int(labels[i]),g.degree(i,weight='weight')] for i in ids],
            marker=dict(symbol=symbol,size=[12+2*np.log1p(g.degree(i,weight='weight')) for i in ids],
                color=[PALETTE[(labels[i]-1)%len(PALETTE)] for i in ids],line=dict(width=1,color='white')),
            hovertemplate='%{text}<br>Community %{customdata[0]}<br>Event weight %{customdata[1]}<extra></extra>'))
    f.update_xaxes(visible=False);f.update_yaxes(visible=False)
    return finish(f,'Venue–category bipartite network',580)

def community_heatmap(matrix,vl):
    z=matrix.groupby(pd.Index(vl,name='community')).sum()
    z=z.div(z.sum(axis=1),axis=0)*100
    names=[x.split(' / ')[-1]+' ['+str(i+1)+']' for i,x in enumerate(z.columns)]
    f=px.imshow(z.to_numpy(),x=names,y=[f'Community {x}' for x in z.index],aspect='auto',color_continuous_scale='Teal',labels={'color':'Within-community %'})
    f.update_traces(customdata=np.tile(np.array(z.columns),(len(z),1)),
        hovertemplate='%{y}<br>%{customdata}<br>Within-community share %{z:.2f}%<extra></extra>')
    f.update_xaxes(tickangle=-40)
    return finish(f,'Category composition (rows sum to 100%)',510)

def community_map(events,matrix,vl,style):
    d=facility_table(events).set_index('facility').reindex(matrix.index).reset_index()
    d['community']=[f'Community {x}' for x in vl]
    d=d.dropna(subset=['latitude','longitude'])
    if d.empty:return empty('No coordinates available; facilities remain in the network')
    colors={f'Community {i+1}':PALETTE[i%len(PALETTE)] for i in range(max(vl))}
    f=px.scatter_map(d,lat='latitude',lon='longitude',size='events',color='community',color_discrete_map=colors,
        hover_name='facility',map_style=style,zoom=9,center={'lat':22.36,'lon':114.14},size_max=35,
        labels={'events':'Events','community':'Community'})
    return finish(f,'Community locations',500)

def ca_biplot(modes,ca):
    if ca['rank']<2:return empty('Fewer than two active dimensions; a 2D CA plot is unavailable')
    f=go.Figure()
    for xy,text,symbol,color,name in [(ca['rows'],modes.label,'circle',PALETTE[0],'Art forms'),(ca['columns'],MODES,'diamond',PALETTE[1],'Participation modes')]:
        f.add_trace(go.Scatter(x=xy[:,0],y=xy[:,1],mode='markers+text',text=list(text),textposition='top center',
            marker=dict(size=12,symbol=symbol,color=color),name=name,cliponaxis=False,
            hovertemplate='%{text}<br>Dimension 1: %{x:.3f}<br>Dimension 2: %{y:.3f}<extra></extra>'))
    f.add_hline(y=0,line_dash='dot',line_color='#c5d1d6');f.add_vline(x=0,line_dash='dot',line_color='#c5d1d6')
    f.update_xaxes(title=f'Dimension 1 ({ca["explained"][0]:.1%} inertia)',zeroline=False)
    f.update_yaxes(title=f'Dimension 2 ({ca["explained"][1]:.1%} inertia)',zeroline=False,scaleanchor='x',scaleratio=1)
    return finish(f,'CA biplot · symmetric principal coordinates',560)

def participation_bar(modes):
    d=modes.sort_values('alternative_share')
    f=px.bar(d,x='alternative_share',y='label',orientation='h',color_discrete_sequence=[PALETTE[0]],
        labels={'alternative_share':'Alternative / any-mode participation (%)','label':''},hover_data={'alternative_pct':True,'any_pct':True})
    f.update_xaxes(range=[0,100]);return finish(f,'Alternative-mode participation share',470)

def modes_heatmap(modes):
    f=px.imshow(modes[MODES].to_numpy(),x=MODES,y=modes.label,aspect='auto',text_auto=True,color_continuous_scale='Teal',labels={'color':'Full-sample %'})
    return finish(f,'Exclusive participation modes (%)',470)
