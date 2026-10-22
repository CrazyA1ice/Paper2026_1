from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
contract = json.loads((QA / 'evidence_audit.json').read_text(encoding='utf-8'))
OUT = Path(contract['assets'])
SKILL = Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
sys.path.insert(0, str(SKILL))
from audit_panel_alignment import require_matplotlib_panel_alignment

# The retained journal requires 138 mm width, Songti/Times, and 7.5 pt figure text.
# All 64 matched seed comparisons in the reported weekly task are plotted.
mpl.rcParams.update({'font.family': ['Times New Roman', 'SimSun'], 'font.size': 7.5,
                     'axes.labelsize': 7.5, 'axes.titlesize': 7.5, 'legend.fontsize': 7.5,
                     'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.linewidth': .65, 'axes.unicode_minus': False,
                     'pdf.fonttype': 42, 'svg.fonttype': 'none', 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white', 'xtick.direction': 'in', 'ytick.direction': 'in'})
data = pd.read_csv(OUT / '图4_全部配对降幅.csv')
assert len(data) == 64 and not data.duplicated(['baseline', 'metric', 'seed']).any()
models = ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router']
names = ['DLinear', '固定等权', '全局权重', '恒定路由']
fig, axes = plt.subplots(1, 2, figsize=(5.433070866, 2.4), sharey=True)
fig.subplots_adjust(left=.16, right=.985, bottom=.235, top=.79, wspace=.30)
blue, grey = '#237B98', '#A8B0B7'
for ax, metric, title, maximum, step in zip(axes, ['mse', 'mae'], ['(a) MSE', '(b) MAE'], [50, 25], [10, 5]):
    ax.axvline(0, color='#737B82', lw=.7, ls=(0, (3, 2)), zorder=1)
    for row, model in enumerate(models):
        g = data[(data.baseline == model) & (data.metric == metric)].sort_values('seed')
        assert g.seed.tolist() == list(range(42, 50))
        values = g.reduction_pct.to_numpy()
        assert (values > 0).all()
        center, spread = values.mean(), values.std(ddof=1)
        ax.scatter(values, row + np.linspace(-.065, .065, 8), color=grey, edgecolors='white',
                   linewidths=.3, s=12, zorder=2)
        ax.errorbar(center, row, xerr=spread, fmt='D', color=blue, markersize=4,
                    elinewidth=1.05, capsize=2, capthick=.7, markeredgecolor='white',
                    markeredgewidth=.4, zorder=3)
        ax.text(center, row - .29, f'{center:.2f}%', ha='center', va='bottom', color=blue)
    ax.set_xlim(-maximum * .025, maximum)
    ax.set_xticks(np.arange(0, maximum + .01, step))
    ax.set_ylim(3.45, -.63)
    ax.set_title(title, loc='left', pad=10)
    ax.set_xlabel('相对误差降低率/%', labelpad=6)
    ax.set_yticks(np.arange(4), names)
    ax.tick_params(axis='y', length=0, pad=6)
    ax.tick_params(axis='x', length=3, width=.6)
axes[1].tick_params(axis='y', labelleft=False)
legend = [Line2D([], [], color=grey, marker='o', linestyle='none', markersize=3.3, label='单次重复'),
          Line2D([], [], color=blue, marker='D', linewidth=1, markersize=3.5, label='均值 ± 标准差')]
fig.legend(handles=legend, loc='upper center', bbox_to_anchor=(.56, .995), ncol=2,
           frameon=False, columnspacing=1.7, handlelength=1.9)
for text in fig.findobj(match=Text):
    text.set_fontfamily(['SimSun'] if any('\u4e00' <= c <= '\u9fff' for c in text.get_text()) else ['Times New Roman'])
    text.set_fontsize(7.5)
fig.canvas.draw()
alignment = require_matplotlib_panel_alignment(fig, json_out=QA / 'figure4_alignment.json',
    overlay_svg=QA / 'figure4_alignment.svg', tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
assert alignment['verdict'] == 'PASS'
prefix = OUT / '图4_配对优势图'
fig.savefig(prefix.with_suffix('.pdf'))
fig.savefig(prefix.with_suffix('.svg'))
fig.savefig(prefix.with_suffix('.png'), dpi=600)
fig.savefig(prefix.with_suffix('.tiff'), dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
plt.close(fig)
(QA / 'figure_contract.md').write_text(
    '# Paired weekly advantage figure\n\n'
    'Question: are the reported GÉANT 168-hour improvements consistent across repeated training?\n'
    'Claim: all eight matched seeds have lower MSE and MAE than each of the four controls.\n'
    'Design: quantitative grid, two aligned panels. Each row is a control, each small point is one matched seed; '
    'diamonds and horizontal bars are mean and sample SD, not confidence intervals. A zero-effect reference '
    'and every seed are shown. Positive values mean lower error for the proposed method. No p-values.\n'
    'Scope: the already reported weekly task, all five models and all 307 test origins. The complete horizon grid '
    'has a different question and is not mixed into this figure. No results or numerical observations changed.\n'
    'Journal: retained 138 mm width and 60.96 mm image height, 7.5 pt Songti/Times, 600 dpi; '
    'editable SVG/PDF and TIFF exports. Manuscript layout and image container geometry remain unchanged.\n', encoding='utf-8')
print(json.dumps({'figure': str(prefix.with_suffix('.png')), 'paired_points': len(data), 'alignment': 'PASS'}, ensure_ascii=False))
