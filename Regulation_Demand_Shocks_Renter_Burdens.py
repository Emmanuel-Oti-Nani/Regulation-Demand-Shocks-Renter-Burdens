"""
Regulation, Demand Shocks, and Renter Cost Burdens (2013-2024)
MAIN PYTHON SCRIPT - runs the whole analysis from the raw data.

Run from this folder:   python Regulation_Demand_Shocks_Renter_Burdens.py
(or double-click run_analysis_python.bat)

  data/raw/        source data
  build_panel.py   step 1: builds data/panel_full.csv
  analysis.py      step 2: estimates every model -> results.json
  figures.py       step 3: Figures 1 and 2
  robustness_extra.py  step 4: precision of the null, state-clustered SEs,
                   shift-share sector diagnostics, pre-trend tests (Table 6)
Outputs go to output_python/: tables (CSV), figures (PNG), and an HTML report
with every table and figure.
"""
import os, sys, json, runpy, shutil, base64, datetime, warnings
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = os.path.join('output_python'); os.makedirs(os.path.join(OUT, 'tables'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'figures'), exist_ok=True)

for step, script in [('Step 1: building the panel', 'build_panel.py'),
                     ('Step 2: estimating the models', 'analysis.py'),
                     ('Step 3: drawing the figures', 'figures.py'),
                     ('Step 4: additional robustness', 'robustness_extra.py')]:
    print(f'\n== {step} ({script}) ==', flush=True)
    runpy.run_path(script, run_name='__main__')

import pandas as pd
o = json.load(open('results.json'))
shutil.copy('fig1_trends.png', os.path.join(OUT, 'figures', 'figure1_trends.png'))
shutil.copy('fig2_event.png', os.path.join(OUT, 'figures', 'figure2_event_study.png'))

LAB = {'ln_permits': 'Log permits per 1,000 households', 'burden30': 'Renters paying >30% of income',
       'burden50': 'Renters paying >50% of income', 'ln_rent': 'Log real median gross rent',
       'burden_lt35k': 'Burden, renters under $35,000', 'burden_35_75k': 'Burden, renters $35,000-$74,999',
       'burden_75kp': 'Burden, renters $75,000 or more'}
from math import erf, sqrt
def p(b, se): return 2 * (1 - 0.5 * (1 + erf(abs(b / se) / sqrt(2)))) if se else 1
def cell(r, stars=True):
    s = '**' if p(r['b'], r['se']) < 0.01 else '*' if p(r['b'], r['se']) < 0.05 else ''
    return f"{r['b']:.3f} ({r['se']:.3f}){s if stars else ''}"

DESC = {'burden30': 'Renters paying >30% of income (%)', 'burden50': 'Renters paying >50% of income (%)',
        'burden_lt35k': 'Burden, renters under $35,000 (%)', 'burden_35_75k': 'Burden, renters $35,000-$74,999 (%)',
        'burden_75kp': 'Burden, renters $75,000 or more (%)', 'real_rent': 'Real median gross rent (2024 $)',
        'permits_per_1k': 'Permits per 1,000 households', 'bartik': 'Predicted employment growth (%)',
        'wfh2019': 'Worked from home, 2019 (%)', 'wrluri': 'WRLURI 2018 (unstandardized)',
        'real_inc13': 'Real median household income, 2013 (2024 $)', 'ba_share13': "Bachelor's degree or higher, 2013 (%)"}
t2 = pd.DataFrame([{'Variable': DESC[k], 'Mean': v['mean'], 'SD': v['sd'], 'Min': v['min'], 'Max': v['max']}
                   for k, v in o['desc'].items()])
t3 = pd.DataFrame([{'Outcome': LAB[k], 'Shock (D)': cell(v['D']), 'D x regulation': cell(v['DxR']),
                    'Observations': v['n'], 'Metros': v['metros']} for k, v in o['A'].items()])
t4 = pd.DataFrame([{'Outcome': LAB[k], 'Remote work (W)': cell(v['W']), 'W x regulation': cell(v['WxR']),
                    'Regulation': cell(v['R']), 'R2': v['r2'], 'N': v['n']} for k, v in o['B'].items()])
t5 = pd.DataFrame([{'Specification': s, 'Metros': v['burden30']['metros'],
                    'Burden >30%': cell(v['burden30']['DxR'], False), 'Log permits': cell(v['ln_permits']['DxR'], False),
                    'Log real rent': cell(v['ln_rent']['DxR'], False)} for s, v in o['robust'].items()])
t5b = pd.DataFrame([{'Specification': s, 'W x regulation (burden >30%)': cell(v['burden30']['WxR'], False),
                     'N': v['burden30']['n']} for s, v in o['robustB'].items()])
paper3 = [0.002, -0.009, -0.017, -0.001, -0.255, -0.021, -0.041]
paper4 = [-0.027, -0.345, -0.078, -0.006, -0.262, -0.879, -0.326]
chk = pd.DataFrame(
    [{'Table': 'Table 3: D x regulation', 'Outcome': LAB[k], 'Manuscript': pc, 'This run': round(o['A'][k]['DxR']['b'], 3)}
     for k, pc in zip(LAB, paper3)] +
    [{'Table': 'Table 4: W x regulation', 'Outcome': LAB[k], 'Manuscript': pc, 'This run': round(o['B'][k]['WxR']['b'], 3)}
     for k, pc in zip(LAB, paper4)])
chk['Match'] = ['yes' if abs(a - b) < 0.0015 else 'CHECK' for a, b in zip(chk['Manuscript'], chk['This run'])]

ox = json.load(open('results_extra.json'))
t6a = pd.DataFrame([{'Outcome': LAB[k], 'D x regulation': v['b'], 'SE': v['se'], '90% CI low': v['ci90'][0],
                     '90% CI high': v['ci90'][1], 'MDE (80% power)': v['mde80']} for k, v in ox['equiv_A'].items()])
t6b = pd.DataFrame([{'Outcome': LAB[k], 'W x regulation': v['b'], 'SE': v['se'], '90% CI low': v['ci90'][0],
                     '90% CI high': v['ci90'][1], 'MDE (80% power)': v['mde80']} for k, v in ox['equiv_B'].items()])
t6c = pd.DataFrame([{'Outcome': LAB[k], 'D x regulation': v['DxR'], 'SE clustered by state': v['se_state'], 'States': v['states']}
                    for k, v in ox['state_cluster'].items()])
t6d = pd.DataFrame([{'Outcome': LAB[y], **w} for y, s in ox['sectors'].items() for w in s['top5']])
t6e = pd.DataFrame([{'Outcome': LAB[y], **w} for y, s in ox['sectors'].items() for w in s['loo']])
t6f = pd.DataFrame([{'Outcome': LAB[k], **v} for k, v in ox['pretrend'].items()])
for name, t in [('table6a_precision_annual_panel', t6a), ('table6b_precision_long_difference', t6b),
                ('table6c_state_clustered_se', t6c), ('table6d_sector_weights_top5', t6d),
                ('table6e_leave_one_sector_out', t6e), ('table6f_pretrend_tests', t6f)]:
    t.to_csv(os.path.join(OUT, 'tables', name + '.csv'), index=False)

for name, t in [('table2_descriptives', t2), ('table3_annual_panel', t3), ('table4_long_difference', t4),
                ('table5_robustness', t5), ('robustness_long_difference', t5b), ('check_against_manuscript', chk)]:
    t.to_csv(os.path.join(OUT, 'tables', name + '.csv'), index=False)

pd.set_option('display.width', 200); pd.set_option('display.max_columns', 10)
print('\nTable 3. Annual panel: shift-share shock x regulation\n', t3.to_string(index=False))
print('\nTable 4. Long difference 2019-2024: remote work x regulation\n', t4.to_string(index=False))
print('\nTable 5. Robustness of the shock x regulation interaction\n', t5.to_string(index=False))
print('\nCheck against the manuscript\n', chk.to_string(index=False))

# ---- HTML report -------------------------------------------------------------
def img(path): return '<img src="data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode() + '">'
fs = o['first_stage']['D']
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Regulation, Demand Shocks, and Renter Cost Burdens</title>
<style>body{{font-family:Georgia,serif;max-width:960px;margin:2em auto;padding:0 1em;color:#111;line-height:1.5}}
h1{{font-size:1.6em}} h2{{font-size:1.2em;margin-top:2em;border-bottom:1px solid #ddd}}
table{{border-collapse:collapse;font-size:.9em;margin:.5em 0}} th,td{{border:1px solid #ccc;padding:4px 8px;text-align:left}}
th{{background:#f0efec}} img{{max-width:100%}} .note{{color:#555;font-size:.85em}}</style></head><body>
<h1>Regulation, Demand Shocks, and Renter Cost Burdens, 2013&ndash;2024</h1>
<p class="note">Analysis report generated with Python {sys.version.split()[0]} on {datetime.date.today():%B %d, %Y}.
Main sample: <b>{o['n_main_metros']} metropolitan areas</b> with at least three Wharton survey responses.</p>
<h2>Table 2. Descriptive statistics</h2>{t2.to_html(index=False)}
<h2>Figure 1. Trends by tercile of land-use restrictiveness</h2>{img('fig1_trends.png')}
<h2>Table 3. Annual panel: shift-share employment shock &times; regulation</h2>{t3.to_html(index=False)}
<p class="note">Metro fixed effects, division-by-year effects, 2013 log real income and college share interacted with year.
Standard errors clustered by metro. * p &lt; 0.05; ** p &lt; 0.01. First stage: {fs['b']:.2f} ({fs['se']:.2f}).</p>
<h2>Table 4. Long difference, 2019&ndash;2024: remote work &times; regulation</h2>{t4.to_html(index=False)}
<p class="note">Robust standard errors. * p &lt; 0.05; ** p &lt; 0.01.</p>
<h2>Figure 2. Event study: remote work &times; regulation</h2>{img('fig2_event.png')}
<h2>Table 5. Robustness of the shock &times; regulation interaction</h2>{t5.to_html(index=False)}
<h3>Long-difference robustness</h3>{t5b.to_html(index=False)}
<h2>Table 6. Additional robustness</h2>
<h3>Precision of the regulation interactions, annual panel</h3>{t6a.to_html(index=False)}
<h3>Precision of the regulation interactions, long difference</h3>{t6b.to_html(index=False)}
<h3>Standard errors clustered by state</h3>{t6c.to_html(index=False)}
<h3>Shift-share sector weights (five largest)</h3>{t6d.to_html(index=False)}
<h3>Pre-trend tests, remote-work event study</h3>{t6f.to_html(index=False)}
<p class="note">The Rambachan&ndash;Roth sensitivity analysis is in the R output (table6g).</p>
<h2>Check against the manuscript</h2>{chk.to_html(index=False)}
</body></html>"""
rep = os.path.join(OUT, 'Regulation_Demand_Shocks_Renter_Burdens_report_python.html')
open(rep, 'w', encoding='utf-8').write(html)
print(f"\nManuscript check: {(chk['Match'] == 'yes').sum()} of {len(chk)} estimates match.")
print('Report written to', rep)
