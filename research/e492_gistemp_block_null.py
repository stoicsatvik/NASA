"""E492: exact five-year-block permutation sensitivity on pinned NASA GISTEMP zonal annual anomalies.
The block permutation is a deliberately limited conditional null, NOT a climate-model null.
No raw NASA file download or planetary analogue inference is performed.
"""
from __future__ import annotations
import csv, hashlib, itertools, json, math
from pathlib import Path
import numpy as np
from scipy.stats import theilslopes
import statsmodels.api as sm

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'gistemp_zonal_2001_2025_snapshot.csv'
FIELDS={'global':'global_centi_c','tropics':'tropics_24S_24N_centi_c','arctic':'arctic_64N_90N_centi_c'}

def trend(y, x):
    x=np.asarray(x,dtype=float); y=np.asarray(y,dtype=float)
    return float(np.dot(x-x.mean(),y-y.mean())/np.dot(x-x.mean(),x-x.mean())*10)

def block_permutation_test(y):
    assert len(y)==25
    blocks=np.asarray(y,dtype=float).reshape(5,5)
    observed=trend(y,np.arange(25))
    null=np.array([trend(blocks[list(order)].reshape(-1),np.arange(25)) for order in itertools.permutations(range(5))])
    # Exact inclusive conditional randomization p; observed order is one of 120 permutations.
    p_two=float(np.count_nonzero(np.abs(null)>=abs(observed)-1e-12)/len(null))
    p_pos=float(np.count_nonzero(null>=observed-1e-12)/len(null))
    return {'observed_c_per_decade':round(observed,8),'n_permutations':len(null),
            'two_sided_p':round(p_two,8),'one_sided_positive_p':round(p_pos,8),
            'null_min_max_c_per_decade':[round(float(null.min()),8),round(float(null.max()),8)],
            'null_median_c_per_decade':round(float(np.median(null)),8)}

def diagnostic(y, years):
    x=years-years.mean()
    h={}
    for lag in (1,3,5):
        r=sm.OLS(y,sm.add_constant(x)).fit(cov_type='HAC',cov_kwds={'maxlags':lag})
        b=10*r.params[1];se=10*r.bse[1]
        h[str(lag)]=[round(float(b-1.96*se),6),round(float(b+1.96*se),6)]
    ts=theilslopes(y,years,alpha=0.95)
    # Delete each consecutive five-year window and refit with original years, not compacted indices.
    drops=[]
    for start in range(21):
        keep=np.ones(25,dtype=bool);keep[start:start+5]=False
        drops.append(trend(y[keep],years[keep]))
    return {'ols_c_per_decade':round(trend(y,years),8),
            'theil_sen_c_per_decade':round(float(10*ts.slope),8),
            'theil_sen_95_interval':[round(float(10*ts.low_slope),8),round(float(10*ts.high_slope),8)],
            'hac_95_intervals_by_lag':h,
            'delete_five_year_window_range':[round(min(drops),8),round(max(drops),8)],
            'exact_five_year_block_order_null':block_permutation_test(y)}

def run():
    with DATA.open(newline='') as f: rows=list(csv.DictReader(f))
    years=np.array([int(r['year']) for r in rows],dtype=float)
    assert np.array_equal(years,np.arange(2001,2026))
    y={k:np.array([int(r[v]) for r in rows],dtype=float)/100 for k,v in FIELDS.items()}
    y['arctic_minus_tropics']=y['arctic']-y['tropics']
    out={'schema':'nasa/e492/gistemp-conditional-block-order-null/v1',
         'source_url':'https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt',
         'source_git_blob':'0f8109a63a1e3b683a67d83bbb6ef8840ccfad45',
         'input_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
         'source_note':'Manual 2026-10-10 transcription, not independently re-downloaded this run; 1951–1980 anomaly baseline.',
         'null_note':'Five contiguous five-year blocks permuted exhaustively (5!=120), preserving order inside each block; exchangeability of block order is NOT established, so p values are conditional diagnostics, not physical climate attribution.',
         'series':{k:diagnostic(v,years) for k,v in y.items()}}
    return out

if __name__=='__main__':
    out=run(); print(json.dumps(out,indent=2,sort_keys=True))
