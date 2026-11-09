"""
Additional robustness analyses for:
Regulation, Demand Shocks, and Renter Cost Burdens (2013-2024)

Run after build_panel.py. Reuses the estimators in analysis.py and writes
results_extra.json. Four sets of checks:

  1. Precision of the null: 90% confidence intervals (two one-sided tests at
     the 5% level) and the minimum detectable effect at 80% power for every
     regulation interaction in Tables 3 and 4.
  2. Inference: standard errors clustered by state instead of by metro.
  3. Shift-share diagnostics (Goldsmith-Pinkham, Sorkin & Swift, 2020):
     sector weights that decompose the shock x regulation coefficient into
     sector-specific estimates, and leave-one-sector-out estimates.
  4. Pre-trends in the remote-work event study: a linear pre-trend fitted to
     the 2013-2018 interaction coefficients, extrapolated to 2021-2024.
     (The Rambachan-Roth sensitivity analysis is run in R, script 04.)
"""
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')

# Reuse the data preparation and estimators from analysis.py (everything before the results section)
src = open('analysis.py', encoding='utf-8').read().split('OUT = {}')[0]
exec(src)

Z90, Z95, POWER = 1.645, 1.96, 0.8416
OUT = {}

def ols_full(y, X, cl):
    """OLS with CR1 cluster-robust covariance; returns coefficients, covariance, n, clusters."""
    Xv = X.values.astype(float); yv = y.values.astype(float)
    XtX_inv = np.linalg.pinv(Xv.T @ Xv); b = XtX_inv @ Xv.T @ yv; e = yv - Xv @ b
    meat = np.zeros((Xv.shape[1],) * 2)
    groups = pd.Series(np.arange(len(e))).groupby(cl.values).groups
    for idx in groups.values():
        s = Xv[idx].T @ e[idx]; meat += np.outer(s, s)
    n, k = Xv.shape; ng = len(groups)
    V = (ng / (ng - 1)) * ((n - 1) / (n - k)) * XtX_inv @ meat @ XtX_inv
    return pd.Series(b, X.columns), pd.DataFrame(V, X.columns, X.columns), n, ng

def design_A(d, y, mod='wrluri_z', shock='bartik', min_resp=3):
    """Same sample and regressors as panel_A in analysis.py, returned after the metro within-transform."""
    d = d.dropna(subset=[y, shock, mod, 'real_inc13', 'ba_share13', 'division']).copy()
    d = d[d.n_resp >= min_resp].reset_index(drop=True)
    d['D'] = d[shock]; d['DxR'] = d[shock] * d[mod]
    dy = pd.get_dummies(d.division.astype(int).astype(str) + '_' + d.year.astype(str), prefix='dy', drop_first=True, dtype=float)
    yr = pd.get_dummies(d.year, prefix='y', drop_first=True, dtype=float)
    ctrl = pd.concat([yr.mul(np.log(d.real_inc13), axis=0).add_prefix('inc_'),
                      yr.mul(d.ba_share13, axis=0).add_prefix('ba_')], axis=1)
    X = pd.concat([d[['D', 'DxR']], dy, ctrl], axis=1); X = X.loc[:, X.std() > 0]
    Z = pd.concat([d[[y]], X], axis=1); Z['cbsa'] = d.cbsa
    W = demean(Z, [y] + list(X.columns), 'cbsa')
    return d, W[y], W[list(X.columns)]

def ci_row(b, se):
    return {'b': round(b, 3), 'se': round(se, 3),
            'ci90': [round(b - Z90 * se, 3), round(b + Z90 * se, 3)],
            'ci95': [round(b - Z95 * se, 3), round(b + Z95 * se, 3)],
            'mde80': round((Z95 + POWER) * se, 3)}

OUTCOMES = ['ln_permits', 'burden30', 'burden50', 'ln_rent', 'burden_lt35k', 'burden_35_75k', 'burden_75kp']

# ---- 1. Precision of the null --------------------------------------------------
OUT['equiv_A'] = {}
for y in OUTCOMES:
    r, n, ng, r2 = panel_A(a, y)
    row = ci_row(float(r.loc['DxR', 'b']), float(r.loc['DxR', 'se']))
    row['main_D'] = round(float(r.loc['D', 'b']), 3)
    OUT['equiv_A'][y] = row
OUT['equiv_B'] = {}
for y in OUTCOMES:
    r, n, r2 = long_diff(a, y)
    row = ci_row(float(r.loc['WxR', 'b']), float(r.loc['WxR', 'se']))
    row['main_W'] = round(float(r.loc['W', 'b']), 3)
    OUT['equiv_B'][y] = row

# ---- 2. Standard errors clustered by state -----------------------------------
OUT['state_cluster'] = {}
for y in ['burden30', 'ln_permits', 'ln_rent']:
    d, yy, X = design_A(a, y)
    b, V, n, ng = ols_full(yy, X, d.state)
    OUT['state_cluster'][y] = {'DxR': round(b['DxR'], 3), 'se_state': round(float(np.sqrt(V.loc['DxR', 'DxR'])), 3), 'states': ng}

# ---- 3. Shift-share diagnostics -----------------------------------------------
# Rebuild sector contributions to the shock exactly as in build_panel.py
contrib = pd.read_csv('data/bartik_sector_contrib.csv', dtype={'cbsa': str, 'ind': str})   # written by build_panel.py
SECTORS = {'11': 'Agriculture', '21': 'Mining', '22': 'Utilities', '23': 'Construction', '31-33': 'Manufacturing',
           '42': 'Wholesale trade', '44-45': 'Retail trade', '48-49': 'Transportation and warehousing', '51': 'Information',
           '52': 'Finance and insurance', '53': 'Real estate', '54': 'Professional services', '55': 'Management of companies',
           '56': 'Administrative services', '61': 'Educational services', '62': 'Health care', '71': 'Arts and recreation',
           '72': 'Accommodation and food', '81': 'Other services'}
OUT['sectors'] = {}
for y in ['burden30', 'ln_permits', 'ln_rent']:
    d, yy, X = design_A(a, y)
    # FWL: residualize each sector's piece of DxR on all other regressors
    others = X.drop(columns='DxR')
    P = np.linalg.pinv(others.values.T @ others.values) @ others.values.T
    resid = lambda v: v - others.values @ (P @ v)
    dxr_t = resid(X['DxR'].values); y_t = resid(yy.values)
    cw = contrib.pivot_table(index=['cbsa', 'year'], columns='ind', values='contrib').reset_index()
    m = d[['cbsa', 'year', 'wrluri_z', 'cbsa']].iloc[:, :3].merge(cw, on=['cbsa', 'year'], how='left').fillna(0)
    m = m.set_index(d.index)
    # Within-metro transform of each sector piece (same as the main design), then residualize
    rows = []
    for k in [c for c in cw.columns if c not in ('cbsa', 'year')]:
        zk = m[k] * m['wrluri_z']
        zk = zk - zk.groupby(d.cbsa.values).transform('mean')
        zt = resid(zk.values)
        w = (zt @ dxr_t) / (dxr_t @ dxr_t)
        bk = (zt @ y_t) / (zt @ dxr_t) if abs(zt @ dxr_t) > 1e-12 else np.nan
        rows.append({'sector': SECTORS.get(k, k), 'naics': k, 'weight': w, 'beta_k': bk})
    sw = pd.DataFrame(rows)
    total = float((sw.weight * sw.beta_k).sum())
    full = float((dxr_t @ y_t) / (dxr_t @ dxr_t))
    top = sw.reindex(sw.weight.abs().sort_values(ascending=False).index).head(5)
    OUT['sectors'][y] = {'check_sum_equals_estimate': [round(total, 4), round(full, 4)],
                         'weight_sum': round(float(sw.weight.sum()), 3),
                         'negative_weight_share': round(float(-sw.weight[sw.weight < 0].sum()), 3),
                         'top5': [{'sector': r.sector, 'weight': round(r.weight, 3), 'beta_k': round(r.beta_k, 3)} for r in top.itertuples()]}

    # Leave-one-sector-out: drop sector k from the shock and re-estimate
    loo_est = []
    for k in [c for c in cw.columns if c not in ('cbsa', 'year')]:
        dk = a.merge(cw[['cbsa', 'year', k]], on=['cbsa', 'year'], how='left')
        dk['bartik_x'] = dk.bartik - dk[k].fillna(0)
        r, n, ng, r2 = panel_A(dk, y, shock='bartik_x')
        loo_est.append({'sector': SECTORS.get(k, k), 'DxR': round(float(r.loc['DxR', 'b']), 3), 'se': round(float(r.loc['DxR', 'se']), 3)})
    le = pd.DataFrame(loo_est)
    OUT['sectors'][y]['loo_range'] = [float(le.DxR.min()), float(le.DxR.max())]
    OUT['sectors'][y]['loo_any_significant'] = bool(((le.DxR / le.se).abs() > Z95).any())
    OUT['sectors'][y]['loo'] = loo_est

# ---- 4. Linear pre-trend in the remote-work event study ----------------------
def es_design(d, y, mod='wrluri_z', min_resp=3):
    d = d.dropna(subset=[y, 'wfh2019', mod, 'real_inc13', 'ba_share13', 'division']).copy()
    d = d[d.n_resp >= min_resp].reset_index(drop=True)
    Wc = d.wfh2019 - d.wfh2019.mean(); cols = {}
    for t in YEARS:
        if t == 2019: continue
        ind = (d.year == t).astype(float)
        cols[f'W_{t}'] = Wc * ind; cols[f'WR_{t}'] = Wc * d[mod] * ind; cols[f'R_{t}'] = d[mod] * ind
    E = pd.DataFrame(cols)
    dy = pd.get_dummies(d.division.astype(int).astype(str) + '_' + d.year.astype(str), prefix='dy', drop_first=True, dtype=float)
    yr = pd.get_dummies(d.year, prefix='y', drop_first=True, dtype=float)
    ctrl = pd.concat([yr.mul(np.log(d.real_inc13), axis=0).add_prefix('inc_'), yr.mul(d.ba_share13, axis=0).add_prefix('ba_')], axis=1)
    X = pd.concat([E, dy, ctrl], axis=1); X = X.loc[:, X.std() > 0]
    Z = pd.concat([d[[y]], X], axis=1); Z['cbsa'] = d.cbsa
    Wd = demean(Z, [y] + list(X.columns), 'cbsa')
    return d, Wd[y], Wd[list(X.columns)]

def chi2_sf_even(x, df):
    """Upper-tail chi-square probability for an even number of degrees of freedom (exact formula, no SciPy needed)."""
    assert df % 2 == 0
    term, total = 1.0, 1.0
    for i in range(1, df // 2):
        term *= (x / 2) / i; total += term
    return float(np.exp(-x / 2) * total)

OUT['pretrend'] = {}
PRE, POST = [2013, 2014, 2015, 2016, 2017, 2018], [2021, 2022, 2023, 2024]
for y in ['burden30', 'ln_rent', 'ln_permits']:
    d, yy, X = es_design(a, y)
    b, V, n, ng = ols_full(yy, X, d.cbsa)
    names = [f'WR_{t}' for t in PRE + POST]
    beta = b[names].values; S = V.loc[names, names].values
    # Joint Wald test that all pre-period interactions are zero
    bp = b[[f'WR_{t}' for t in PRE]].values; Sp = V.loc[[f'WR_{t}' for t in PRE], [f'WR_{t}' for t in PRE]].values
    wald = float(bp @ np.linalg.solve(Sp, bp))
    p_pre = chi2_sf_even(wald, len(PRE))
    # Linear trend through the pre-period coefficients and the 2019 reference (=0), by GLS-free OLS on years
    yrs = np.array(PRE + [2019], float); coef = np.append(bp, 0.0)
    A = np.column_stack([np.ones_like(yrs), yrs - 2019])
    L = np.linalg.pinv(A.T @ A) @ A.T                      # maps coefficients to (intercept, slope)
    # Average post effect minus the extrapolated trend, as a linear combination of the betas
    k = len(PRE)
    wpre = np.zeros(len(names)); wpost = np.zeros(len(names))
    for j, t in enumerate(POST):
        wpost[k + j] += 1 / len(POST)
        trend_t = L[0] + L[1] * (t - 2019)                 # weights on (pre coefficients, 2019=0)
        wpre[:k] -= trend_t[:k] / len(POST)
    w = wpost + wpre
    est = float(w @ beta); se = float(np.sqrt(w @ S @ w))
    avg_post = float(beta[k:].mean()); se_post = float(np.sqrt(np.ones(len(POST)) @ S[k:, k:] @ np.ones(len(POST)) / len(POST) ** 2))
    OUT['pretrend'][y] = {'joint_pre_test_chi2': round(wald, 2), 'df': len(PRE), 'p': round(p_pre, 3),
                          'avg_post': round(avg_post, 3), 'avg_post_se': round(se_post, 3),
                          'detrended_avg_post': round(est, 3), 'detrended_se': round(se, 3)}

json.dump(OUT, open('results_extra.json', 'w'), indent=1, default=float)
print(json.dumps({k: OUT[k] for k in ['equiv_A', 'equiv_B', 'state_cluster', 'pretrend']}, indent=1))
for y in OUT['sectors']:
    s = OUT['sectors'][y]
    print(y, 'sum check', s['check_sum_equals_estimate'], 'weight sum', s['weight_sum'], 'neg share', s['negative_weight_share'],
          'LOO range', s['loo_range'], 'any sig', s['loo_any_significant'])
    for t in s['top5']: print('   ', t)
