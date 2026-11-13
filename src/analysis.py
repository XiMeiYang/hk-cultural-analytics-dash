"""Descriptive analysis; no synthetic observations or inferential survey tests."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
FACILITIES = {
    'HKCC': 'Hong Kong Cultural Centre', 'HKCH': 'Hong Kong City Hall',
    'SWHCC': 'Sai Wan Ho Civic Centre', 'SWCC': 'Sheung Wan Civic Centre',
    'KST': 'Ko Shan Theatre', 'NCWCC': 'Ngau Chi Wan Civic Centre',
    'YMTT': 'Yau Ma Tei Theatre', 'TWTH': 'Tsuen Wan Town Hall',
    'TMTH': 'Tuen Mun Town Hall', 'STTH': 'Sha Tin Town Hall',
    'EKCC': 'East Kowloon Cultural Centre', 'KTT': 'Kwai Tsing Theatre',
    'YLT': 'Yuen Long Theatre', 'TPCC': 'Tai Po Civic Centre',
    'NDTH': 'North District Town Hall', 'HKFA': 'Hong Kong Film Archive',
    'HKC': 'Hong Kong Coliseum', 'QES': 'Queen Elizabeth Stadium',
    'HKScM': 'Hong Kong Science Museum', 'HKSpM': 'Hong Kong Space Museum',
}
ART_ZH = {'Dance':'舞蹈','Theatre':'戏剧','Music':'音乐','Xiqu':'戏曲',
          'Multi-arts':'跨媒体艺术','Visual Arts':'视觉艺术','Film Arts':'电影艺术',
          'Literary Reading':'文学阅读','Literary Activities':'文学活动'}
MODES = ['Physical only', 'Alternative only', 'Both']

def load_data(root=ROOT / 'data/source'):
    events = pd.read_csv(root / 'events_current_flat.csv', dtype=str)
    venues = pd.read_csv(root / 'venues_current_flat.csv', dtype={'venue_id':str})
    categories = pd.read_csv(root / 'event_category_codebook.csv')
    history = pd.read_csv(root / 'lcsd_cultural_programmes_by_venue.csv')
    survey = pd.read_csv(root / 'stage3_participation_by_art_form.csv')
    if events.event_id.duplicated().any() or venues.venue_id.duplicated().any():
        raise ValueError('Duplicate event or venue primary key')
    for col in ['cat1', 'cat2']:
        events[col] = events[col].str.strip().str.upper()
    names = categories.set_index('code').name_en.to_dict()
    events['category'] = events.cat2.map(names).fillna(events.cat2).fillna('Unclassified')
    # Prefix distinguishes equally named categories across different service families.
    events['category'] = events.cat1.map(names).fillna('Unclassified') + ' / ' + events.category
    events = events.merge(venues, left_on='venueid', right_on='venue_id', how='left', validate='many_to_one', indicator=True)
    events['venue_matched'] = events['_merge'].eq('both')
    events = events.drop(columns='_merge')
    events['facility'] = events.venuee.str.split(' (', regex=False).str[0].str.strip()
    events['facility_zh'] = events.venuec.str.split(' (', regex=False).str[0].str.strip()
    events['site_specific'] = events.venue_matched & ~events.venuee.fillna('').str.startswith('Venues in ')
    events['mapped'] = events.latitude.between(22,22.6) & events.longitude.between(113.8,114.5)
    inverse = {name:code for code,name in FACILITIES.items()}
    events['history_code'] = events.facility.map(inverse)
    history['Venue_Code'] = history.Venue_Code.str.strip()
    history['period'] = history.Year.astype(str) + history.Quarter
    if history.duplicated(['period','Venue_Code']).any():
        raise ValueError('Duplicate historical facility-quarter keys')
    for col in ['Performance','Attendance']:
        history[col+'_raw'] = history[col].astype(str)
        history[col] = pd.to_numeric(history[col], errors='coerce')
    return events, history, survey

def facility_table(events):
    e = events[events.site_specific]
    return e.groupby('facility',as_index=False).agg(
        facility_zh=('facility_zh','first'), events=('event_id','nunique'),
        latitude=('latitude','median'),longitude=('longitude','median'),
        history_code=('history_code','first'))

def spatial_comparison(events, history, period='2025', metric='Performance'):
    selected = history[history.Year.astype(str).eq(period)] if len(period)==4 else history[history.period.eq(period)]
    expected = 4 if len(period)==4 else 1
    h = selected[selected.Venue_Code.isin(FACILITIES)].groupby('Venue_Code').agg(
        historical=(metric, lambda s:s.sum(min_count=expected)), observations=(metric,'count'),rows=(metric,'size'))
    # Only observed full periods, no converting '-' into zero.
    h = h[(h.observations==expected) & (h.rows==expected)].reset_index()
    c = facility_table(events)
    c = c[c.history_code.notna()]
    d = c.merge(h,left_on='history_code',right_on='Venue_Code',validate='one_to_one')
    # Both source populations must explicitly observe the facility.
    if d.empty: return d, float('nan')
    d['historical_share'] = d.historical / d.historical.sum() * 100
    d['current_share'] = d.events / d.events.sum() * 100
    # Three empirical quantile bins, ties stay together; thresholds may collapse.
    for col in ['historical_share','current_share']:
        q = d[col].quantile([1/3,2/3]).to_numpy()
        d[col+'_class'] = np.searchsorted(q,d[col].to_numpy(),side='left')
    d['bivariate'] = d.historical_share_class.astype(str) + '-' + d.current_share_class.astype(str)
    rho = spearmanr(d.historical_share,d.current_share).statistic if len(d)>2 and d.historical_share.nunique()>1 and d.current_share.nunique()>1 else float('nan')
    return d, float(rho)

def incidence(events):
    e = events[events.site_specific]
    return pd.crosstab(e.facility,e.category).astype(float)

def bipartite_communities(matrix, resolution=1.0):
    """Deterministic greedy agglomeration for Barber bipartite modularity.

    Q = sum_ij (Aij - gamma*ki*dj/m) [gi=gj] / m.
    This is a heuristic, not a claim of a global maximum. No one-mode projection.
    """
    a = np.asarray(matrix,dtype=float)
    if a.ndim!=2 or (a<0).any() or a.sum()<=0: raise ValueError('Empty or invalid incidence matrix')
    n,k = a.shape; m=a.sum()
    b = (a - resolution*np.outer(a.sum(axis=1),a.sum(axis=0))/m)/m
    scores=np.block([[np.zeros((n,n)),b],[b.T,np.zeros((k,k))]])
    groups=[{i} for i in range(n+k)]
    while len(groups)>1:
        np.fill_diagonal(scores,-np.inf)
        i,j=np.unravel_index(np.argmax(scores),scores.shape)
        if scores[i,j]<=1e-12: break
        if i>j: i,j=j,i
        groups[i] |= groups[j]
        scores[i,:] += scores[j,:]; scores[:,i] += scores[:,j]
        scores=np.delete(np.delete(scores,j,axis=0),j,axis=1)
        groups.pop(j)
    # Stable display order: most event-weight first, with deterministic tiebreak.
    groups.sort(key=lambda g:(-sum(a[v,:].sum() for v in g if v<n),min(g)))
    labels=np.empty(n+k,dtype=int)
    for c,g in enumerate(groups):
        for v in g: labels[v]=c+1
    q=float((b*(labels[:n,None]==labels[None,n:])).sum())
    return labels[:n],labels[n:],q

def participation_modes(survey):
    p=survey[survey.group.ne('Any Art Form')].pivot(index='group',columns='metric',values='value_pct')
    u=p['any_mode_participation_pct']; a=p['alternative_mode_participation_pct']; ph=p['physical_mode_participation_pct']
    out=pd.DataFrame({'Physical only':u-a,'Alternative only':u-ph,'Both':ph+a-u})
    if (out<0).any().any() or not np.allclose(out.sum(axis=1),u):
        raise ValueError('Rounded source rates do not support consistent mutually exclusive modes')
    out['any_pct']=u;out['alternative_pct']=a;out['alternative_share']=a/u*100
    out['label']=out.index
    return out

def correspondence_analysis(values):
    a=np.asarray(values,dtype=float)
    if a.ndim!=2 or not np.isfinite(a).all() or (a<0).any() or a.sum()<=0:
        raise ValueError('CA needs a nonnegative finite table')
    p=a/a.sum();r=p.sum(axis=1);c=p.sum(axis=0)
    if (r==0).any() or (c==0).any(): raise ValueError('Zero mass row/column')
    s=(p-np.outer(r,c))/np.sqrt(np.outer(r,c))
    u,d,vt=np.linalg.svd(s,full_matrices=False)
    keep=d>1e-10;d=d[keep];u=u[:,keep];v=vt.T[:,keep]
    # Stable orientation for reproducible plots.
    for j in range(len(d)):
        sign=1 if u[np.argmax(np.abs(u[:,j])),j]>=0 else -1
        u[:,j]*=sign;v[:,j]*=sign
    rows=u*d/np.sqrt(r[:,None]);cols=v*d/np.sqrt(c[:,None])
    eig=d*d;ratio=eig/eig.sum() if eig.sum()>0 else eig
    return {'rows':rows,'columns':cols,'inertia':eig,'explained':ratio,'rank':len(d)}
