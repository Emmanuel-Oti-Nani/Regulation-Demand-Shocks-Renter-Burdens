"""Estimation for: Regulation, demand shocks, and renter cost burdens (2013-2024)."""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
a = pd.read_csv('data/panel_full.csv', dtype={'cbsa':str})
YEARS = [2013,2014,2015,2016,2017,2018,2019,2021,2022,2023,2024]
cnt = a.groupby('cbsa').year.nunique(); bal = cnt[cnt==len(YEARS)].index
a = a[a.cbsa.isin(bal)].copy()
a['ln_permits'] = np.log(a.permits_per_1k.clip(lower=0.1))
a['ln_rent'] = np.log(a.real_rent)

def ols_cluster(y, X, cl):
    """OLS with CR1 cluster-robust SEs. X: DataFrame (no constant added)."""
    Xv = X.values.astype(float); yv = y.values.astype(float)
    XtX_inv = np.linalg.pinv(Xv.T@Xv); b = XtX_inv@Xv.T@yv; e = yv - Xv@b
    G = pd.Series(e).groupby(cl.values)
    meat = np.zeros((Xv.shape[1],)*2)
    for g, idx in G.groups.items():
        s = Xv[idx].T@e[idx]; meat += np.outer(s,s)
    n,k = Xv.shape; ng = len(G.groups)
    V = (ng/(ng-1))*((n-1)/(n-k))*XtX_inv@meat@XtX_inv
    se = np.sqrt(np.diag(V)); r2 = 1 - (e@e)/((yv-yv.mean())@(yv-yv.mean()))
    return pd.DataFrame({'b':b,'se':se}, index=X.columns), n, ng, r2

def demean(df, cols, by):
    return df[cols] - df.groupby(by)[cols].transform('mean')

def panel_A(d, y, mod='wrluri_z', shock='bartik', min_resp=3, extra_drop=None, wcol=None):
    d = d.dropna(subset=[y, shock, mod, 'real_inc13','ba_share13','division']).copy()
    if min_resp: d = d[d.n_resp>=min_resp] if mod.startswith('wrluri') else d
    if extra_drop is not None: d = d[~extra_drop(d)]
    d = d.reset_index(drop=True)
    d['D'] = d[shock]; d['DxR'] = d[shock]*d[mod]
    # division-by-year FE and baseline controls x year
    dy = pd.get_dummies(d.division.astype(int).astype(str)+'_'+d.year.astype(str), prefix='dy', drop_first=True, dtype=float)
    yr = pd.get_dummies(d.year, prefix='y', drop_first=True, dtype=float)
    ctrl = pd.concat([yr.mul(np.log(d.real_inc13),axis=0).add_prefix('inc_'), yr.mul(d.ba_share13,axis=0).add_prefix('ba_')], axis=1)
    X = pd.concat([d[['D','DxR']], dy, ctrl], axis=1)
    X = X.loc[:, X.std()>0]
    Z = pd.concat([d[[y]], X], axis=1); Z['cbsa']=d.cbsa
    W = demean(Z, [y]+list(X.columns), 'cbsa')   # metro FE via within transform
    res, n, ng, r2 = ols_cluster(W[y], W[list(X.columns)], d.cbsa)
    return res.loc[['D','DxR']], n, ng, r2

def long_diff(d, y, mod='wrluri_z', y0=2019, y1=2024, min_resp=3):
    w = d.pivot_table(index='cbsa', columns='year', values=y)
    base = d[d.year==y0].set_index('cbsa')[['wfh2019',mod,'real_inc13','ba_share13','renter_share13','division','n_resp']]
    base['dY'] = w[y1]-w[y0]
    base = base.dropna()
    if min_resp and mod.startswith('wrluri'): base = base[base.n_resp>=min_resp]
    base = base.reset_index()
    base['W'] = base.wfh2019 - base.wfh2019.mean()
    base['WxR'] = base.W*base[mod]
    dv = pd.get_dummies(base.division.astype(int), prefix='div', drop_first=True, dtype=float)
    X = pd.concat([pd.Series(1.0,index=base.index,name='const'), base[['W','WxR',mod]], np.log(base.real_inc13).rename('ln_inc13'),
                   base[['ba_share13','renter_share13']], dv], axis=1)
    res, n, ng, r2 = ols_cluster(base.dY, X, base.cbsa)  # cluster = metro -> HC1
    return res.loc[['W','WxR',mod]], n, r2

def event_study(d, y, mod='wrluri_z', min_resp=3):
    d = d.dropna(subset=[y,'wfh2019',mod,'real_inc13','ba_share13','division']).copy()
    d = d[d.n_resp>=min_resp].reset_index(drop=True)
    Wc = d.wfh2019 - d.wfh2019.mean()
    cols = {}
    for t in YEARS:
        if t==2019: continue
        ind = (d.year==t).astype(float)
        cols[f'W_{t}'] = Wc*ind; cols[f'WR_{t}'] = Wc*d[mod]*ind; cols[f'R_{t}'] = d[mod]*ind
    E = pd.DataFrame(cols)
    dy = pd.get_dummies(d.division.astype(int).astype(str)+'_'+d.year.astype(str), prefix='dy', drop_first=True, dtype=float)
    yr = pd.get_dummies(d.year, prefix='y', drop_first=True, dtype=float)
    ctrl = pd.concat([yr.mul(np.log(d.real_inc13),axis=0).add_prefix('inc_'), yr.mul(d.ba_share13,axis=0).add_prefix('ba_')], axis=1)
    X = pd.concat([E, dy, ctrl], axis=1); X = X.loc[:, X.std()>0]
    Z = pd.concat([d[[y]], X], axis=1); Z['cbsa']=d.cbsa
    Wd = demean(Z, [y]+list(X.columns), 'cbsa')
    res, n, ng, r2 = ols_cluster(Wd[y], Wd[list(X.columns)], d.cbsa)
    return res.loc[[c for c in res.index if c.startswith('WR_')]], n, ng

# Standardize moderators on the metro cross-section (one value per metro)
cs = a[a.year==2019]
for m,src in [('wrluri_z','wrluri'),('zri_z','zri')]:
    mu, sd = cs[src].mean(), cs[src].std(); a[m] = (a[src]-mu)/sd
a['wrluri_unw_z'] = (a.wrluri_unw - cs.wrluri_unw.mean())/cs.wrluri_unw.std()

OUT = {}
outcomes = [('ln_permits','Log permits per 1,000 households'),('burden30','Renter cost burden >30% (pct.)'),
            ('burden50','Severe burden >50% (pct.)'),('ln_rent','Log real median gross rent'),
            ('burden_lt35k','Burden, renters < $35k'),('burden_35_75k','Burden, renters $35k–$75k'),('burden_75kp','Burden, renters $75k+')]
fmt = lambda r: {'b':round(float(r.b),3),'se':round(float(r.se),3)}
OUT['A'] = {}
for y,lab in outcomes:
    r,n,ng,r2 = panel_A(a, y); OUT['A'][y] = {'D':fmt(r.loc['D']),'DxR':fmt(r.loc['DxR']),'n':n,'metros':ng}
OUT['B'] = {}
for y,lab in outcomes:
    r,n,r2 = long_diff(a, y); OUT['B'][y] = {'W':fmt(r.loc['W']),'WxR':fmt(r.loc['WxR']),'R':fmt(r.loc['wrluri_z']),'n':n,'r2':round(r2,3)}
OUT['ES'] = {}
for y in ['burden30','ln_rent','ln_permits']:
    r,n,ng = event_study(a, y); OUT['ES'][y] = {k:fmt(v) for k,v in r.iterrows()}
# Robustness for main outcome burden30 and permits
rob = {}
specs = {
 'main (WRLURI, >=3 responses)': dict(),
 'WRLURI, >=1 response': dict(min_resp=1),
 'WRLURI, >=5 responses': dict(min_resp=5),
 'WRLURI unweighted mean': dict(mod='wrluri_unw_z'),
 'Zoning Restrictiveness Index': dict(mod='zri_z', min_resp=0),
 'Lagged Bartik shock': dict(shock='bartik_lag'),
 'Drop 2013': dict(extra_drop=lambda d: d.year==2013),
 'Drop 2021': dict(extra_drop=lambda d: d.year==2021),
 'Drop California': dict(extra_drop=lambda d: d.state=='CA'),
 'Drop New England (CT boundary change)': dict(extra_drop=lambda d: d.division==1),
}
for name,kw in specs.items():
    rob[name] = {}
    for y in ['burden30','ln_permits','ln_rent']:
        r,n,ng,r2 = panel_A(a, y, **kw); rob[name][y] = {'DxR':fmt(r.loc['DxR']),'n':n,'metros':ng}
OUT['robust'] = rob
robB = {}
for name,kw in {'main':{}, '>=1 response':{'min_resp':1}, '>=5 responses':{'min_resp':5}, 'ZRI':{'mod':'zri_z','min_resp':0}, '2019->2023':{'y1':2023}}.items():
    robB[name] = {}
    for y in ['burden30','ln_rent','ln_permits']:
        r,n,r2 = long_diff(a, y, **kw); robB[name][y] = {'WxR':fmt(r.loc['WxR']),'n':n}
OUT['robustB'] = robB
# Descriptives
main = a[(a.n_resp>=3)]
desc = {}
for v in ['burden30','burden50','burden_lt35k','burden_35_75k','burden_75kp','real_rent','permits_per_1k','bartik','wfh2019','wrluri','real_inc13','ba_share13']:
    s = main[v]; desc[v] = {'mean':round(s.mean(),2),'sd':round(s.std(),2),'min':round(s.min(),2),'max':round(s.max(),2)}
OUT['desc'] = desc
OUT['n_main_metros'] = int(main.cbsa.nunique())
# Trends by regulation tercile (for figure)
m19 = main[main.year==2019][['cbsa','wrluri']]
m19['tercile'] = pd.qcut(m19.wrluri, 3, labels=['Least restrictive','Middle','Most restrictive'])
tt = main.merge(m19[['cbsa','tercile']], on='cbsa')
OUT['trends'] = {v: tt.groupby(['tercile','year'],observed=True)[v].mean().round(2).unstack(0).to_dict() for v in ['burden30','real_rent','permits_per_1k','burden_lt35k']}
OUT['terc_desc'] = tt[tt.year==2019].groupby('tercile',observed=True)[['wrluri','burden30','real_rent','permits_per_1k','wfh2019','real_inc13']].mean().round(2).to_dict()
json.dump(OUT, open('results.json','w'), indent=1, default=str)
print(json.dumps({k:OUT[k] for k in ['A','B','n_main_metros']}, indent=1))

# First stage: does the shift-share shock predict actual private employment growth?
fs = a.dropna(subset=['g']).copy(); fs = fs[fs.g.abs()<30]
r,n,ng,r2 = panel_A(fs, 'g')
OUT['first_stage'] = {'D':fmt(r.loc['D']),'DxR':fmt(r.loc['DxR']),'n':n,'metros':ng}
json.dump(OUT, open('results.json','w'), indent=1, default=str)
print('first stage', OUT['first_stage'])
