import numpy as np
import pandas as pd
import pytest
from src.analysis import *

def test_real_data_coverage_and_no_contact_fields():
    e,h,s=load_data()
    assert len(e)==878 and e.event_id.is_unique
    assert e.venue_matched.all() and e.mapped.sum()==812
    assert e.site_specific.sum()==837
    assert not {'email','enquiry','desce'} & set(e.columns)
    assert not h.duplicated(['period','Venue_Code']).any()

def test_missing_history_is_not_zero_and_complete_year_only():
    e,h,_=load_data();d,_=spatial_comparison(e,h,'2025')
    assert len(d)==14
    assert 'SWHCC' not in set(d.history_code)
    assert 'TPCC' not in set(d.history_code)
    assert (d.observations==4).all()
    assert np.isclose(d.current_share.sum(),100)
    assert np.isclose(d.historical_share.sum(),100)
    assert h.loc[h.Performance_raw.eq('-'),'Performance'].isna().all()

def test_bipartite_separates_disconnected_blocks():
    a=pd.DataFrame([[5,0],[0,7]])
    vl,cl,q=bipartite_communities(a)
    assert vl[0]==cl[0] and vl[1]==cl[1] and vl[0]!=vl[1]
    expected=1-((5/12)**2+(7/12)**2)
    assert np.isclose(q,expected)

def test_network_event_weight_conservation():
    e,_,_=load_data();m=incidence(e)
    assert m.sum().sum()==837
    vl,cl,q=bipartite_communities(m)
    a=m.to_numpy();b=a-np.outer(a.sum(1),a.sum(0))/a.sum()
    assert np.isclose(q,(b*(vl[:,None]==cl[None,:])).sum()/a.sum())
    assert np.array_equal(vl,bipartite_communities(m)[0])

def test_mode_inclusion_exclusion_and_ca_inertia():
    _,_,s=load_data();p=participation_modes(s)
    assert p.loc['Dance',MODES].tolist()==[3,13,6]
    assert (p[MODES].sum(1)==p.any_pct).all()
    a=p[MODES].to_numpy(dtype=float);ca=correspondence_analysis(a)
    prob=a/a.sum();r=prob.sum(1);c=prob.sum(0)
    direct=((prob-np.outer(r,c))**2/np.outer(r,c)).sum()
    assert np.isclose(ca['inertia'].sum(),direct)
    assert ca['rank']==2
    assert np.allclose(correspondence_analysis(a*100)['inertia'],ca['inertia'])
    assert np.allclose((ca['rows']*r[:,None]).sum(0),0)

def test_invalid_ca_and_single_dimension():
    with pytest.raises(ValueError):correspondence_analysis([[0,0],[1,2]])
    assert correspondence_analysis([[1,2],[3,1],[2,4]])['rank']==1

def test_dash_endpoints_and_filtered_callbacks():
    from app import server,update_spatial,update_network,EVENTS
    client=server.test_client()
    for path in ['/','/_dash-layout','/_dash-dependencies']:
        assert client.get(path).status_code==200
    for category in ['ALL',*EVENTS.category.unique()]:
        spatial=update_spatial(category,'2025','Performance','white-bg')
        network=update_network(category,1,'white-bg')
        for fig in [*spatial[:3],*network[:3]]:assert fig.to_json()
