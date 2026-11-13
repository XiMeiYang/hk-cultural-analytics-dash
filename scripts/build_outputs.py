"""Regenerate all published analysis tables from the bundled source extracts."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.analysis import *

def main():
    out=ROOT/'data/processed';out.mkdir(parents=True,exist_ok=True)
    e,h,s=load_data()
    e.to_csv(out/'events_clean.csv',index=False)
    h.to_csv(out/'history_clean.csv',index=False)
    e[['venueid','venuee','venuec','facility','facility_zh','history_code','latitude','longitude','site_specific']].drop_duplicates().to_csv(out/'venue_mapping.csv',index=False)
    e.loc[~e.mapped,['event_id','venueid','venuee','category']].to_csv(out/'unmapped_events.csv',index=False)
    e.loc[~e.site_specific,['event_id','venueid','venuee','category']].to_csv(out/'non_specific_venues.csv',index=False)
    d,rho=spatial_comparison(e,h)
    d.to_csv(out/'spatial_2025_performance.csv',index=False)
    m=incidence(e);vl,cl,q=bipartite_communities(m)
    m.to_csv(out/'venue_category_matrix.csv')
    pd.DataFrame({'facility':m.index,'community':vl,'events':m.sum(axis=1).to_numpy()}).to_csv(out/'venue_communities.csv',index=False)
    pd.DataFrame({'category':m.columns,'community':cl}).to_csv(out/'category_communities.csv',index=False)
    sensitivity=[]
    for gamma in [.5,.75,1,1.25,1.5]:
        rv,cv,rq=bipartite_communities(m,gamma)
        sensitivity.append({'resolution':gamma,'communities':len(set(rv)|set(cv)),'modularity':rq})
    pd.DataFrame(sensitivity).to_csv(out/'community_sensitivity.csv',index=False)
    p=participation_modes(s);ca=correspondence_analysis(p[MODES])
    p.to_csv(out/'participation_modes.csv')
    pd.DataFrame(ca['rows'],index=p.index,columns=['CA1','CA2']).to_csv(out/'ca_art_coordinates.csv')
    pd.DataFrame(ca['columns'],index=MODES,columns=['CA1','CA2']).to_csv(out/'ca_mode_coordinates.csv')
    audit={'snapshot_date':'2026-10-02','event_rows':len(e),'event_ids_unique':bool(e.event_id.is_unique),
        'matched_venue_rows':int(e.venue_matched.sum()),'mapped_events':int(e.mapped.sum()),
        'unmapped_events':int((~e.mapped).sum()),'specific_site_events':int(e.site_specific.sum()),
        'excluded_area_aggregate_events':int((~e.site_specific).sum()),'network_facilities':len(m),
        'network_categories':m.shape[1],'network_edges':int((m>0).sum().sum()),'communities':len(set(vl)|set(cl)),
        'bipartite_modularity_gamma_1':q,'history_missing_performance':int(h.Performance.isna().sum()),
        'comparison_default_facilities':len(d),'comparison_default_spearman':rho,
        'ca_rank':ca['rank'],'ca_inertia':ca['inertia'].tolist(),'ca_explained':ca['explained'].tolist()}
    (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
