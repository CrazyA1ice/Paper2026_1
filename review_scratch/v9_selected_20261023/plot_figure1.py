from collections import Counter
from pathlib import Path
import json
import os
import sys

QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
OUT = Path('C:\\Users\\Quant\\Desktop\\Paper2026_1\\paper_template\\长春工程学院学报(自然科学版)\\逐项修订_20261023\\V9_图表源文件')
OUT.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(QA / 'mplconfig')
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
sys.path.insert(0, r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment

# Reconstruct the retained schematic without executing the old export loop.
source = ROOT / 'paper_figures/fig1_A_border_spacing_20261007/render_source.py'
code = source.read_text(encoding='utf-8').split('    compact.OUT = OUT\n')[0]
code = code.replace('OUT = Path(__file__).resolve().parent', 'OUT = TASK_ASSETS').replace('ROOT = OUT.parents[1]', 'ROOT = TASK_ROOT')
scope = {'__file__': str(source), 'TASK_ASSETS': OUT, 'TASK_ROOT': ROOT}
exec(compile(code, str(source), 'exec'), scope)
fig = scope['fig']
fig.set_size_inches(138 / 25.4, 88 / 25.4)
mpl.rcParams.update({'pdf.fonttype': 42, 'svg.fonttype': 'none', 'mathtext.fontset': 'custom',
                    'mathtext.rm': 'Times New Roman', 'mathtext.it': 'Times New Roman:italic',
                    'mathtext.bf': 'Times New Roman:bold', 'mathtext.bfit': 'Times New Roman:bold:italic',
                    'mathtext.cal': 'Times New Roman:italic', 'mathtext.sf': 'Times New Roman',
                    'mathtext.tt': 'Times New Roman', 'mathtext.fallback': 'stix',
                    'font.family': ['Times New Roman', 'SimSun'], 'font.sans-serif': ['Arial', 'SimSun']})
ax = fig.axes[0]
for t in fig.findobj(match=Text):
    if '未来' in t.get_text():
        t.set_text('未来24步')
    t.set_fontfamily(['SimSun'] if any('\u4e00' <= c <= '\u9fff' for c in t.get_text()) else ['Times New Roman'])
    t.set_fontsize(7.5)
    t.set_math_fontfamily('custom')

geometry = scope['helper'].fingerprint(ax)
original_labels = Counter(t.get_text() for t in ax.texts)
edits = []
for s in (1, 2, 4):
    before = rf'$\alpha_{s}\hat{{\boldsymbol{{Y}}}}^{{({s})}}$'
    after = rf'$\alpha_{{n,{s}}}\hat{{\boldsymbol{{Y}}}}^{{({s})}}_n$'
    labels = [t for t in ax.texts if t.get_text() == before]
    assert len(labels) == 1, before
    labels[0].set_text(after)
    edits.append({'before': before, 'after': after})
softmax = [t for t in ax.texts if t.get_text() == r'$\alpha_1,\alpha_2,\alpha_4$']
assert len(softmax) == 1
softmax[0].set_text(r'$\alpha_{n,1},\alpha_{n,2},\alpha_{n,4}$')
edits.append({'before': r'$\alpha_1,\alpha_2,\alpha_4$', 'after': softmax[0].get_text()})

parts = [t for t in ax.texts if t.get_text() in {
    r'$\hat{\boldsymbol{Y}}=$', '∑', 's',
    r'$\alpha_s\hat{\boldsymbol{Y}}^{(s)}$', r'$\alpha_s=1$'}]
assert len(parts) == 7, [(t.get_text(), t.get_position()) for t in parts]
for t in parts:
    t.remove()
formulas = [
    (59.3, r'$\hat{\boldsymbol{Y}}_n=\sum_{s\in S}\alpha_{n,s}\hat{\boldsymbol{Y}}^{(s)}_n$'),
    (51.8, r'$\sum_{s\in S}\alpha_{n,s}=1$'),
]
for y, value in formulas:
    ax.text(137, y, value, fontsize=7.5, fontfamily='Times New Roman',
            color='#181818', ha='center', va='center', zorder=5)
    edits.append({'complete_formula': value})

updated_geometry = scope['helper'].fingerprint(ax)
assert geometry['lines'] == updated_geometry['lines']
assert geometry['patches'] == updated_geometry['patches']
unchanged = original_labels.copy()
for e in edits:
    if 'before' in e:
        unchanged.subtract([e['before']])
for t in parts:
    unchanged.subtract([t.get_text()])
actual = Counter(t.get_text() for t in ax.texts)
for e in edits:
    actual.subtract([e.get('after', e.get('complete_formula'))])
assert +unchanged == +actual
for label in fig.findobj(match=Text):
    label.set_math_fontfamily('custom')
    label.set_text(label.get_text().replace(r'\mathbb{R}', r'\mathrm{ℝ}'))
fig.canvas.draw()
alignment = require_matplotlib_panel_alignment(fig, json_out=QA / 'figure1_alignment.json', strict=True)
prefix = OUT / '图1_样本窗口符号统一'
fig.savefig(prefix.with_suffix('.pdf'))
fig.savefig(prefix.with_suffix('.svg'))
fig.savefig(prefix.with_suffix('.png'), dpi=600)
fig.savefig(prefix.with_suffix('.tiff'), dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
(QA / 'figure1_edit_audit.json').write_text(json.dumps({'edits': edits,
    'unchanged_geometry': True, 'other_labels_unchanged': True,
    'width_mm': 138, 'height_mm': 88, 'alignment': alignment,
    'prefix': str(prefix)}, ensure_ascii=False, indent=2), encoding='utf-8')
plt.close(fig)
print(prefix)
