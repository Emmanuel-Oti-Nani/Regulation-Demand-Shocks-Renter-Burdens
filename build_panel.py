"""Build the metro-year analysis panel, 2013-2024 (2020 excluded).
Run from the project folder: python build_panel.py  (reads data/raw/, writes data/panel_full.csv)"""
import pandas as pd, numpy as np
R = 'data/raw/'
YEARS = [2013,2014,2015,2016,2017,2018,2019,2021,2022,2023,2024]

# ---------------- ACS ----------------
a = pd.read_csv(R+'acs1_metro_2013_2024.csv', dtype={'cbsa':str})
num = [c for c in a.columns if c.endswith('E')]
a[num] = a[num].apply(pd.to_numeric, errors='coerce')
a['rent_computed'] = a.B25070_001E - a.B25070_011E
a['burden30'] = 100*(a.B25070_007E+a.B25070_008E+a.B25070_009E+a.B25070_010E)/a.rent_computed
a['burden50'] = 100*a.B25070_010E/a.rent_computed
# income tiers (nominal brackets in B25106)
a['burden_lt35k'] = 100*(a.B25106_028E+a.B25106_032E)/(a.B25106_025E+a.B25106_029E)
a['burden_35_75k'] = 100*(a.B25106_036E+a.B25106_040E)/(a.B25106_033E+a.B25106_037E)
a['burden_75kp'] = 100*a.B25106_044E/a.B25106_041E
a['renter_share'] = 100*a.B25003_003E/a.B25003_001E
wf = pd.read_csv(R+'acs1_S0801_wfh_2013_2024.csv', dtype={'cbsa':str})
wf['wfh_share'] = wf.S0801_C01_013E.where(wf.S0801_C01_013E>=0)
a = a.merge(wf[['year','cbsa','wfh_share']], on=['year','cbsa'], how='left')
a['ba_share'] = 100*(a.B15003_022E+a.B15003_023E+a.B15003_024E+a.B15003_025E)/a.B15003_001E
a['households'] = a.B25003_001E
a['med_rent'] = a.B25064_001E
a['med_inc'] = a.B19013_001E
a['pop'] = a.B01003_001E
a['state'] = a.name.str.extract(r', ([A-Z]{2})')[0]
cpi = pd.read_csv(R+'cpi_less_shelter_CUUR0000SA0L2_annual.csv').set_index('year').cpi_u_less_shelter
a['real_rent'] = a.med_rent * cpi[2024] / a.year.map(cpi)
a['real_inc'] = a.med_inc * cpi[2024] / a.year.map(cpi)
a['rent_to_inc'] = 100*12*a.med_rent/a.med_inc

# ---------------- Delineations: county -> CBSA by vintage ----------------
def delin(f):
    d = pd.read_csv(R+f, skiprows=2, dtype=str)
    d = d[d['FIPS State Code'].notna() & d['CBSA Code'].str.match(r'^\d{5}$', na=False)]
    d['fips'] = d['FIPS State Code'].str.zfill(2)+d['FIPS County Code'].str.zfill(3)
    return d[['fips','CBSA Code']].rename(columns={'CBSA Code':'cbsa'})
D = {2013:delin('delin2013.csv'), 2018:delin('delin2018.csv'), 2020:delin('delin2020.csv'), 2023:delin('delin2023.csv')}
def vint(y): return 2013 if y<=2017 else 2018 if y<=2019 else 2020 if y<=2022 else 2023

# ---------------- Building permits ----------------
b = pd.read_csv(R+'bps_county_2012_2024.csv', dtype={'st':str,'cty':str})
b['fips'] = b.st.str.zfill(2)+b.cty.str.zfill(3)
b['units'] = b[['u1','u2','u34','u5']].sum(axis=1)
rows=[]
for y in YEARS:
    bb = b[b.year==y].merge(D[vint(y)], on='fips')
    g = bb.groupby('cbsa')[['units','u5']].sum().reset_index(); g['year']=y; rows.append(g)
perm = pd.concat(rows)
a = a.merge(perm, on=['cbsa','year'], how='left')
a['permits_per_1k'] = 1000*a.units/a.households
a['mf_share'] = 100*a.u5/a.units

# ---------------- Wharton index and NZLUD ZRI -> CBSA (2018 codes) ----------------
# The Wharton file has no redistribution license, so the public repository ships only the
# metro-level averages built here (data/derived/wharton_zri_cbsa.csv). If the original file is
# in data/raw (see data/raw/README_WHARTON.md), the averages are rebuilt from it.
import os
WH = R+'WHARTON_LAND_REGULATION_DATA_01_15_2020.dta'; DER = 'data/derived/wharton_zri_cbsa.csv'
if os.path.exists(WH):
    w = pd.read_stata(WH)
    w = w[w.cbsacode18.notna() & w.WRLURI18.notna()].copy()
    w['cbsa'] = w.cbsacode18.astype(int).astype(str).str.zfill(5)
    w['wt'] = w.weight_cbsa.fillna(w.weight_metro).fillna(1.0)
    wr = w.groupby('cbsa').apply(lambda g: pd.Series({'wrluri': np.average(g.WRLURI18, weights=g.wt), 'n_resp': len(g),
          'wrluri_unw': g.WRLURI18.mean()}), include_groups=False).reset_index()
    # NZLUD Zoning Restrictiveness Index, linked to CBSAs through the Wharton place codes
    z = pd.read_csv(R+'nzlud_muni.csv', encoding='latin-1')
    z['geoid7'] = z.GEOID.astype(int).astype(str).str.zfill(7)
    wp = w[w.fipsplacecode18.notna()].copy()
    wp['geoid7'] = wp.statecode.astype(int).astype(str).str.zfill(2)+wp.fipsplacecode18.astype(int).astype(str).str.zfill(5)
    zz = z.merge(wp[['geoid7','cbsa']].drop_duplicates('geoid7'), on='geoid7')
    zr = zz.groupby('cbsa').agg(zri=('zri','mean'), n_zri=('zri','size')).reset_index()
    os.makedirs('data/derived', exist_ok=True)
    wr.merge(zr, on='cbsa', how='outer').sort_values('cbsa').to_csv(DER, index=False)
else:
    dz = pd.read_csv(DER, dtype={'cbsa': str})
    wr = dz[dz.wrluri.notna()][['cbsa','wrluri','n_resp','wrluri_unw']].copy()
    zr = dz[dz.zri.notna()][['cbsa','zri','n_zri']].copy()

# ---------------- Bartik shock from QCEW ----------------
q = pd.read_csv(R+'qcew_msa_sector_2012_2024.csv', dtype={'area':str,'ind':str,'disc':str})
sec = q[(q.own==5)&(q['agg']==44)].copy()          # MSA x NAICS sector, private
tot = q[(q.own==5)&(q['agg']==41)&(q.ind=='10')][['area','year','emp']].rename(columns={'emp':'priv_tot'})
nat = q[(q.area=='US000')&(q.own==5)&(q['agg']==14)][['ind','year','emp']].rename(columns={'emp':'nat'})
# impute suppressed MSA-sector cells: allocate residual private employment by national sector shares
sec = sec.merge(tot, on=['area','year']).merge(nat, on=['ind','year'])
sec['emp'] = sec.emp.astype(float)
sec['supp'] = sec.disc.eq('N')
disc_sum = sec[~sec.supp].groupby(['area','year']).emp.sum().rename('disc_sum')
supp_nat = sec[sec.supp].groupby(['area','year']).nat.sum().rename('supp_nat')
sec = sec.join(disc_sum, on=['area','year']).join(supp_nat, on=['area','year'])
sec['disc_sum'] = sec.disc_sum.fillna(0)
resid = (sec.priv_tot - sec.disc_sum).clip(lower=0)
sec.loc[sec.supp,'emp'] = (resid*sec.nat/sec.supp_nat)[sec.supp]
sec['cbsa'] = sec.area.str[1:]+'0'
base = sec[sec.year==2012].copy()
base['share'] = base.emp/base.groupby('cbsa').emp.transform('sum')
# leave-one-out national growth by sector and year
natsum = sec.groupby(['ind','year']).emp.sum().rename('msa_sum').reset_index()
natq = nat.merge(natsum, on=['ind','year'])
own = sec[['cbsa','ind','year','emp']]
loo = own.merge(nat, on=['ind','year'])
loo['nat_loo'] = loo.nat - loo.emp
loo = loo.sort_values(['cbsa','ind','year'])
loo['g'] = loo.groupby(['cbsa','ind']).nat_loo.pct_change()
bt = loo.merge(base[['cbsa','ind','share']], on=['cbsa','ind'])
bt['contrib'] = bt.share*bt.g
bartik = bt.groupby(['cbsa','year']).contrib.sum(min_count=1).mul(100).rename('bartik').reset_index()
# Each sector's contribution to the shock (used by the shift-share diagnostics in robustness_extra.py)
sc = bt.dropna(subset=['g'])[['cbsa','ind','year']].assign(contrib=100*bt.dropna(subset=['g']).contrib.values)
sc.sort_values(['cbsa','ind','year']).to_csv('data/bartik_sector_contrib.csv', index=False)

# Actual private employment growth (for the first-stage check)
tg = tot.copy(); tg['cbsa'] = tg.area.str[1:]+'0'; tg = tg.sort_values(['cbsa','year'])
tg['g'] = 100*tg.groupby('cbsa').priv_tot.pct_change()
a = a.merge(tg[['cbsa','year','g']], on=['cbsa','year'], how='left')
a = a.merge(bartik, on=['cbsa','year'], how='left')
bartik['year'] = bartik.year+1
a = a.merge(bartik.rename(columns={'bartik':'bartik_lag'}), on=['cbsa','year'], how='left')

# ---------------- Merge moderators, baseline covariates ----------------
a = a.merge(wr, on='cbsa', how='left').merge(zr, on='cbsa', how='left')
b19 = a[a.year==2019][['cbsa','wfh_share']].rename(columns={'wfh_share':'wfh2019'})
b13 = a[a.year==2013][['cbsa','real_inc','ba_share','renter_share']].rename(columns=lambda c: c if c=='cbsa' else c+'13')
a = a.merge(b19, on='cbsa', how='left').merge(b13, on='cbsa', how='left')
div = {'CT':1,'ME':1,'MA':1,'NH':1,'RI':1,'VT':1,'NJ':2,'NY':2,'PA':2,'IL':3,'IN':3,'MI':3,'OH':3,'WI':3,
 'IA':4,'KS':4,'MN':4,'MO':4,'NE':4,'ND':4,'SD':4,'DE':5,'DC':5,'FL':5,'GA':5,'MD':5,'NC':5,'SC':5,'VA':5,'WV':5,
 'AL':6,'KY':6,'MS':6,'TN':6,'AR':7,'LA':7,'OK':7,'TX':7,'AZ':8,'CO':8,'ID':8,'MT':8,'NV':8,'NM':8,'UT':8,'WY':8,
 'AK':9,'CA':9,'HI':9,'OR':9,'WA':9,'PR':0}
a['division'] = a.state.map(div)
a = a[a.state!='PR']
a.to_csv('data/panel_full.csv', index=False)

# Analysis sample: CBSAs observed in all 11 years with Wharton coverage
cnt = a.groupby('cbsa').year.nunique()
bal = cnt[cnt==len(YEARS)].index
s = a[a.cbsa.isin(bal)]
print('metros total', a.cbsa.nunique(), '| balanced', len(bal), '| balanced w/ WRLURI', s[s.wrluri.notna()].cbsa.nunique(),
      '| n_resp>=5', s[s.n_resp>=5].cbsa.nunique(), '| n_resp>=10', s[s.n_resp>=10].cbsa.nunique(), '| with ZRI', s[s.zri.notna()].cbsa.nunique())
print(s[['burden30','burden50','burden_lt35k','burden_35_75k','burden_75kp','real_rent','permits_per_1k','bartik','bartik_lag','wfh2019','wrluri']].describe().T.round(2))
