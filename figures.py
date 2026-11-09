import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
o = json.load(open('results.json'))
C = ['#86b6ef', '#2a78d6', '#104281']; MK = ['o', 's', '^']
TER = ['Least restrictive', 'Middle', 'Most restrictive']
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False})

# Figure 1: trends by regulation tercile
fig, axs = plt.subplots(1, 3, figsize=(7.5, 3.2))
panels = [('burden30', 'A. Renters paying >30% of income (%)'), ('real_rent', 'B. Real median gross rent (2024 $)'),
          ('permits_per_1k', 'C. Permits per 1,000 households')]
for ax, (v, t) in zip(axs, panels):
    d = o['trends'][v]
    for i, k in enumerate(TER):
        ys = sorted((int(y), val) for y, val in d[k].items())
        x = [p[0] for p in ys]; y = [p[1] for p in ys]
        pre = [(a, b) for a, b in zip(x, y) if a <= 2019]; post = [(a, b) for a, b in zip(x, y) if a >= 2021]
        for seg in (pre, post):
            ax.plot([p[0] for p in seg], [p[1] for p in seg], color=C[i], lw=2, marker=MK[i], ms=4,
                    label=k if seg is pre else None)
    ax.axvspan(2019.5, 2020.5, color=GRID, lw=0)
    ax.set_title(t, fontsize=8.5, loc='left', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.6); ax.set_xticks([2013, 2016, 2019, 2022])
fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, fontsize=7.5, loc='lower center', ncol=3, bbox_to_anchor=(0.5, 0.06))
fig.text(0.01, 0.01, 'Note: Shaded band marks 2020 (no standard ACS 1-year estimates). Metros grouped by tercile of the 2018 WRLURI.',
         fontsize=7, color=MUTED)
fig.tight_layout(rect=(0, 0.14, 1, 1)); fig.savefig('fig1_trends.png', dpi=300); plt.close()

# Figure 2: event study, remote work x regulation on renter burden
es = o['ES']['burden30']
yrs = sorted(int(k.split('_')[1]) for k in es) + [2019]
pts = sorted([(int(k.split('_')[1]), v['b'], v['se']) for k, v in es.items()] + [(2019, 0.0, 0.0)])
fig, ax = plt.subplots(figsize=(6, 3))
ax.axhline(0, color=MUTED, lw=0.8)
ax.axvline(2020, color=GRID, lw=6, zorder=0)
x = [p[0] for p in pts]; b = [p[1] for p in pts]; e = [1.96 * p[2] for p in pts]
ax.errorbar(x, b, yerr=e, fmt='o', color='#2a78d6', ecolor='#86b6ef', elinewidth=2, capsize=0, ms=6, mec='#fcfcfb', mew=1)
ax.set_xticks(x); ax.tick_params(axis='x', labelsize=7.5)
ax.set_ylabel('Coefficient on remote work × regulation\n(pp. of renters burdened)', fontsize=8)
ax.grid(axis='y', color=GRID, lw=0.6)
fig.text(0.01, 0.01, 'Note: Points are estimates relative to 2019 with 95% confidence intervals; standard errors clustered by metro.',
         fontsize=7, color=MUTED)
fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig('fig2_event.png', dpi=300); plt.close()
print('ok')
