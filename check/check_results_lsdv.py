"""Independent Python cross-check using explicit dummy variables (LSDV).

analysis.py removes metro fixed effects by subtracting metro means. This script
instead puts a dummy variable for every metro into the regression and solves it
with a different routine (numpy lstsq), so an error in the demeaning step would
show up as a mismatch. Run from the housing_research_data folder:
    python check_results_lsdv.py
"""
import numpy as np, pandas as pd

d = pd.read_csv('data/panel_full.csv', dtype={'cbsa': str})
YEARS = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]
d = d[d.year.isin(YEARS)]
d = d[d.cbsa.isin(d.groupby('cbsa').year.nunique().loc[lambda s: s == 11].index)].copy()
d['ln_permits'] = np.log(d.permits_per_1k.clip(lower=0.1))
d['ln_rent'] = np.log(d.real_rent)
cs = d[d.year == 2019]
d['R'] = (d.wrluri - cs.wrluri.mean()) / cs.wrluri.std()

REF = {'ln_permits': (0.002, 0.009), 'burden30': (-0.009, 0.099), 'burden50': (-0.017, 0.073),
       'ln_rent': (-0.001, 0.001), 'burden_lt35k': (-0.255, 0.124), 'burden_35_75k': (-0.021, 0.171),
       'burden_75kp': (-0.041, 0.082)}

s = d[(d.n_resp >= 3)].dropna(subset=['bartik', 'R', 'real_inc13', 'ba_share13', 'division']).copy()
print(f"{'outcome':15s} {'LSDV coef':>10s} {'paper':>8s} {'LSDV se':>9s} {'paper':>8s} {'N':>6s}")
for y, (rb, rse) in REF.items():
    t = s.dropna(subset=[y]).reset_index(drop=True)
    X = pd.concat([
        t.bartik.rename('D'), (t.bartik * t.R).rename('DxR'),
        pd.get_dummies(t.cbsa, prefix='m', dtype=float),                                   # all metro dummies
        pd.get_dummies(t.division.astype(int).astype(str) + '_' + t.year.astype(str), prefix='dy',
                       dtype=float).iloc[:, 1:],                                          # division x year
        pd.get_dummies(t.year, dtype=float).iloc[:, 1:].mul(np.log(t.real_inc13), axis=0).add_prefix('inc'),
        pd.get_dummies(t.year, dtype=float).iloc[:, 1:].mul(t.ba_share13, axis=0).add_prefix('ba'),
    ], axis=1)
    Xv, yv = X.values, t[y].values
    b, *_ = np.linalg.lstsq(Xv, yv, rcond=None)
    e = yv - Xv @ b
    rank = np.linalg.matrix_rank(Xv)
    XtXi = np.linalg.pinv(Xv.T @ Xv)
    meat = sum(np.outer(Xv[i].T @ e[i], Xv[i].T @ e[i]) for i in t.groupby('cbsa').indices.values())
    G, n = t.cbsa.nunique(), len(t)
    k = rank - G  # metro dummies are nested in clusters and are not counted (fixest/reghdfe convention)
    V = (G / (G - 1)) * ((n - 1) / (n - k)) * XtXi @ meat @ XtXi
    j = list(X.columns).index('DxR')
    print(f"{y:15s} {b[j]:10.3f} {rb:8.3f} {np.sqrt(V[j, j]):9.3f} {rse:8.3f} {n:6d}")
