"""Rebuild minimal source extracts from the user's original ZIP; never publish PDFs/contacts."""
import argparse
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import zipfile
import pandas as pd

FIELDS={'events_current_flat.csv':['event_id','cat1','cat2','venueid'],
        'venues_current_flat.csv':['venue_id','venuee','venuec','latitude','longitude'],
        'event_category_codebook.csv':None,'lcsd_cultural_programmes_by_venue.csv':None,
        'stage3_participation_by_art_form.csv':None}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('archive',type=Path)
    args=parser.parse_args();out=Path(__file__).resolve().parents[1]/'data/source';out.mkdir(parents=True,exist_ok=True)
    manifest=[]
    with zipfile.ZipFile(args.archive) as z:
        for name,cols in FIELDS.items():
            matches=[x for x in z.infolist() if PurePosixPath(x.filename).name==name and not x.filename.startswith('__MACOSX/')]
            if len(matches)!=1:raise ValueError(f'Expected exactly one {name}, found {len(matches)}')
            if matches[0].file_size>20_000_000:raise ValueError('Unexpected extract size')
            b=z.read(matches[0]);d=pd.read_csv(io.BytesIO(b),dtype=str)
            if cols:d=d[cols]
            d.to_csv(out/name,index=False)
            manifest.append({'file':name,'rows':len(d),'archive_original_sha256':hashlib.sha256(b).hexdigest(),
                'published_columns':list(d.columns),'published_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
    (out/'manifest.json').write_text(json.dumps({'snapshot_date':'2026-10-02','files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
