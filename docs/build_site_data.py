"""
Builds the data files for the interactive website in docs/.
Run from the repository root after the Python analysis:

    python docs/build_site_data.py [path/to/census_boundary_folder]

Inputs : data/panel_full.csv, results.json, results_extra.json (from the Python analysis),
         output/tables/table6g_honestdid_relative_magnitudes.csv (from the R analysis, optional),
         and, only when rebuilding the maps, the Census cartographic boundary shapefiles
         cb_2023_us_cbsa_20m and cb_2023_us_state_20m (https://www2.census.gov/geo/tiger/GENZ2023/shp/).
Outputs: docs/data/metros.json, docs/data/results.json, docs/data/cbsa.json, docs/data/states.json
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
OUTD = os.path.join('docs', 'data'); os.makedirs(OUTD, exist_ok=True)
YEARS = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]
SERIES = ['burden30', 'burden50', 'burden_lt35k', 'burden_35_75k', 'burden_75kp', 'real_rent', 'permits_per_1k']

a = pd.read_csv('data/panel_full.csv', dtype={'cbsa': str})
a = a[a.year.isin(YEARS)]
n = a.groupby('cbsa').year.nunique(); bal = n[n == len(YEARS)].index
a = a[a.cbsa.isin(bal)].copy()

cs = a[a.year == 2019].set_index('cbsa')
mu, sd = cs.wrluri.mean(), cs.wrluri.std()
main = cs[cs.n_resp >= 3]
terc = pd.qcut(main.wrluri, 3, labels=['Least restrictive', 'Middle', 'Most restrictive'])

def r(x, k=2):
    return None if pd.isna(x) else round(float(x), k)

metros = []
for code, g in a.sort_values('year').groupby('cbsa'):
    c = cs.loc[code]
    name = c['name'].replace(' Metro Area', '').replace(' Micro Area', '')
    m = {'id': code, 'name': name, 'state': c.state, 'main': bool(c.n_resp >= 3) if pd.notna(c.n_resp) else False,
         'wrluri': r(c.wrluri, 3), 'wrluri_z': r((c.wrluri - mu) / sd, 3) if pd.notna(c.wrluri) else None,
         'n_resp': None if pd.isna(c.n_resp) else int(c.n_resp), 'zri': r(c.zri, 3),
         'wfh2019': r(c.wfh2019, 1), 'tercile': terc.get(code) if code in terc.index else None,
         'households': int(g[g.year == 2024].households.iloc[0])}
    for s in SERIES:
        m[s] = [r(v, 1 if s != 'permits_per_1k' else 2) for v in g[s]]
    metros.append(m)
json.dump({'years': YEARS, 'metros': metros}, open(os.path.join(OUTD, 'metros.json'), 'w'), separators=(',', ':'))

# ---- Results for the charts ----------------------------------------------------
o = json.load(open('results.json')); ox = json.load(open('results_extra.json'))
LAB = {'ln_permits': 'Log permits per 1,000 households', 'burden30': 'Burden >30%', 'burden50': 'Severe burden >50%',
       'ln_rent': 'Log real rent', 'burden_lt35k': 'Burden, income < $35k', 'burden_35_75k': 'Burden, $35k–$75k',
       'burden_75kp': 'Burden, $75k+'}
res = {'interactions_A': [], 'interactions_B': [], 'event': {}, 'sectors': [], 'pretrend': ox['pretrend'],
       'n_main': o['n_main_metros'], 'first_stage': o['first_stage']['D']}
for k, lab in LAB.items():
    e = ox['equiv_A'][k]
    res['interactions_A'].append({'key': k, 'label': lab, 'b': e['b'], 'se': e['se'], 'lo': e['ci95'][0], 'hi': e['ci95'][1],
                                  'lo90': e['ci90'][0], 'hi90': e['ci90'][1], 'main': o['A'][k]['D']['b']})
    e = ox['equiv_B'][k]
    res['interactions_B'].append({'key': k, 'label': lab, 'b': e['b'], 'se': e['se'], 'lo': e['ci95'][0], 'hi': e['ci95'][1],
                                  'lo90': e['ci90'][0], 'hi90': e['ci90'][1], 'main': o['B'][k]['W']['b']})
for y in ['burden30', 'ln_rent', 'ln_permits']:
    pts = [{'year': 2019, 'b': 0.0, 'se': 0.0}]
    for k, v in o['ES'][y].items():
        pts.append({'year': int(k.split('_')[1]), 'b': v['b'], 'se': v['se']})
    res['event'][y] = sorted(pts, key=lambda p: p['year'])
res['sectors'] = ox['sectors']['burden30']['top5']
hd = os.path.join('output', 'tables', 'table6g_honestdid_relative_magnitudes.csv')
if os.path.exists(hd):
    h = pd.read_csv(hd)
    res['honestdid'] = [{'Mbar': None if pd.isna(x.Mbar) else float(x.Mbar), 'lb': round(float(x.lb), 3), 'ub': round(float(x.ub), 3),
                         'method': x.method} for x in h.itertuples()]
json.dump(res, open(os.path.join(OUTD, 'results.json'), 'w'), indent=1)

# ---- Boundaries (only when the shapefile folder is given) ------------------------
if len(sys.argv) > 1:
    sys.path.insert(0, os.path.join(ROOT, 'docs'))
    from shp2geo import convert
    shp = sys.argv[1]
    cb = convert(os.path.join(shp, 'cb_2023_us_cbsa_20m'), ['CBSAFP'])
    keep = set(bal)
    cb['features'] = [f for f in cb['features'] if f['properties']['CBSAFP'] in keep]
    st = convert(os.path.join(shp, 'cb_2023_us_state_20m'), ['STUSPS'])
    st['features'] = [f for f in st['features'] if f['properties']['STUSPS'] != 'PR']
    json.dump(cb, open(os.path.join(OUTD, 'cbsa.json'), 'w'), separators=(',', ':'))
    json.dump(st, open(os.path.join(OUTD, 'states.json'), 'w'), separators=(',', ':'))
print('site data written to', OUTD)
