"""Restyle the existing five figures without changing their data or layouts."""
from pathlib import Path
import importlib.util
import json
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.font_manager import FontProperties
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'abilene_forecasting'))
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
sys.path.insert(0, 'C:/Users/Quant/.codex/skills/nature-figure/scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
from audit_pdf_text import audit_pdf as audit_text
from audit_figure_collisions import audit_pdf as audit_collisions

# Figure roles and data: framework schematic; three-seed LightTS comparison;
# paired eight-seed improvements; calibration plus truth-only trajectories;
# all-window router weights. No points, seeds, bins or models are excluded.
WIDTH_MM = 161.925
FONT_PT = 7.5
FONT = FontProperties(family=['Times New Roman', 'SimSun'], size=FONT_PT)
plt.rcParams.update({'font.family': ['Times New Roman', 'SimSun'], 'font.size': 7.5,
                     'pdf.fonttype': 42, 'svg.fonttype': 'none',
                     'mathtext.fontset': 'stix', 'axes.unicode_minus': False})


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(mod):
    figures = []
    save = Figure.savefig
    def remember(fig, *args, **kwargs):
        if fig not in figures:
            figures.append(fig)
    mod.OUT = OUT
    # The fresh alignment gate runs below, after final typography is applied.
    mod.require_matplotlib_panel_alignment = lambda *args, **kwargs: None
    Figure.savefig = remember
    try:
        mod.main()
    finally:
        Figure.savefig = save
    assert len(figures) == 1
    return figures[0]


def typography(fig):
    old_w, old_h = fig.get_size_inches()
    fig.set_size_inches(WIDTH_MM / 25.4, old_h * WIDTH_MM / 25.4 / old_w)
    for ax in fig.axes:
        ax.tick_params(axis='both', which='both', direction='in')
    for text in fig.findobj(Text):
        weight = text.get_fontweight()
        text.set_fontproperties(FONT)
        if '$' in text.get_text() and re.search(r'[\u4e00-\u9fff]', text.get_text()):
            text.set_fontfamily('SimSun')
        text.set_fontweight(weight)
        text.set_fontsize(9.0 if text.get_text() == '∑' else FONT_PT)
        text.set_text(text.get_text().replace('相对改进率（%）', '相对改进率/%')
                      .replace('参数量比例（%）', '参数量比例/%')
                      .replace('相对 LightTS 的误差降低率（%）', '相对LightTS的误差降低率/%'))
    fig.canvas.draw()


def geometry(fig):
    """Record all quantitative artists before and after style changes."""
    result = []
    for ax in fig.axes:
        for line in ax.lines:
            result.append(['line', np.asarray(line.get_xdata()).tolist(), np.asarray(line.get_ydata()).tolist()])
        for collection in ax.collections:
            result.append(['collection', np.asarray(collection.get_offsets()).tolist(),
                           [p.vertices.tolist() for p in collection.get_paths()]])
        for image in ax.images:
            result.append(['image', np.asarray(image.get_array()).tolist()])
        for patch in ax.patches:
            if isinstance(patch, Rectangle):
                result.append(['rectangle', patch.get_x(), patch.get_y(), patch.get_width(), patch.get_height()])
    return result


def export(fig, number, comparable_axes=None):
    before = geometry(fig)
    typography(fig)
    assert before == geometry(fig), 'Style edit changed plotted geometry'
    stem = OUT / f'fig{number}'
    kwargs = {'axes': comparable_axes, 'row_groups': [['a', 'b'], ['c', 'd']],
              'column_groups': []} if comparable_axes is not None else {}
    alignment = require_matplotlib_panel_alignment(fig, json_out=f'{stem}.alignment.json',
                 tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True, **kwargs)
    # No tight crop: physical width and the 7.5 pt labels remain exact in Word.
    fig.savefig(f'{stem}.pdf', facecolor='white')
    fig.savefig(f'{stem}.svg', facecolor='white')
    fig.savefig(f'{stem}.png', dpi=600, facecolor='white')
    with Image.open(f'{stem}.png') as image:
        image.convert('RGB').save(f'{stem}.jpg', quality=97, dpi=(600, 600))
    glyphs = audit_text(Path(f'{stem}.pdf').read_bytes(), minimum_pt=5)
    collisions = audit_collisions(Path(f'{stem}.pdf'))
    Path(f'{stem}.text-audit.json').write_text(json.dumps(glyphs, indent=2), encoding='utf-8')
    Path(f'{stem}.collision-audit.json').write_text(json.dumps(collisions, ensure_ascii=False, indent=2), encoding='utf-8')
    assert glyphs['below_minimum_count'] == 0, glyphs
    assert collisions['summary']['fail'] == 0, collisions['summary']
    plt.close(fig)
    return {'figure': number, 'alignment': alignment.get('verdict'),
            'data_geometry_unchanged': True, 'width_mm': WIDTH_MM,
            'text_pt': FONT_PT, 'collisions': collisions['summary']}


def figure2():
    data = pd.read_csv(ROOT / 'abilene_forecasting/paper_figures/source_data_v25/fig3_lightts_improvement_seed42_44.csv')
    assert len(data) == 18
    matrices, params = {}, {}
    for ds in ('abilene', 'geant'):
        part = data[data.dataset == ds]
        values = part.pivot(index='metric', columns='seed', values='relative_improvement_pct').loc[['MSE', 'MAE', 'RMSE'], [42, 43, 44]].to_numpy()
        matrices[ds] = np.column_stack([values, values.mean(1)])
        params[ds] = (int(part.adaptive_parameters.iloc[0]), int(part.lightts_parameters.iloc[0]))
    # Reuse only the original drawing function; do not execute its old DOCX
    # editing or source-data writing blocks.
    source = (ROOT / 'word_output/build_v25_replace_fig3.py').read_text(encoding='utf-8')
    drawing = source[source.index('def draw(path, grayscale=False):'):source.index('draw(COLOR_FIG, grayscale=False)')]
    namespace = dict(plt=plt, np=np, LinearSegmentedColormap=LinearSegmentedColormap,
                     datasets=['abilene', 'geant'], matrices=matrices, params=params)
    exec(compile(drawing, '<existing-heatstrip-draw>', 'exec'), namespace)
    remembered = []
    save = Figure.savefig
    Figure.savefig = lambda fig, *args, **kwargs: remembered.append(fig)
    try:
        namespace['draw'](OUT / 'fig2.png')
    finally:
        Figure.savefig = save
    fig = remembered[0]
    positions = [(0.075, 0.32, 0.285, 0.58), (0.55, 0.32, 0.285, 0.58),
                 (0.395, 0.32, 0.09, 0.58), (0.87, 0.32, 0.105, 0.58)]
    for ax, position in zip(fig.axes[:4], positions):
        ax.set_position(position)
    fig.axes[4].set_position((0.075, 0.13, 0.9, 0.04))
    # Direct labels keep the journal-size type inside each parameter panel.
    for ax in fig.axes[2:4]:
        ax.set_yticks([])
        ax.grid(False)
        ax.set_xlabel('参数比例/%', labelpad=3)
        for label, y in zip(('本文方法', 'LightTS'), (0, 1)):
            ax.text(0, y + 0.32, label, ha='left', va='center')
        for text, y in zip(ax.texts[:2], (0, 1)):
            text.set_position((0, y - 0.32))
            text.set_ha('left')
            text.set_va('center')
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    schematic = module('paper_figures/fig1_fusion_options_20261002/build_fig1.py', 'existing_framework')
    original_text = schematic.text
    def template_text(ax, x, y, value, size=8, bold=False, color=schematic.INK, ha='center'):
        # Keep the original content, but use bold italic for matrix/vector names.
        value = value.replace('z_n', r'\boldsymbol{z}_n').replace(r'\hat Y', r'\hat{\boldsymbol{Y}}')
        if value.startswith('$X'):
            value = value.replace('$X', r'$\boldsymbol{X}', 1)
        artist = original_text(ax, x, y, value, size, bold, color, ha)
        artist.set_fontproperties(FONT)
        if '$' in value and re.search(r'[\u4e00-\u9fff]', value):
            artist.set_fontfamily('SimSun')
        artist.set_fontsize(FONT_PT if value != '∑' else 9.0)
        artist.set_fontweight('bold' if bold else 'normal')
        return artist
    schematic.text = template_text
    # Preserve the diagram's coordinates; draw at final physical size so the
    # measured summation glyph spacing uses the correct font metrics.
    make_figure = plt.figure
    def final_size_figure(*args, **kwargs):
        kwargs['figsize'] = (WIDTH_MM / 25.4, WIDTH_MM * 110 / 180 / 25.4)
        return make_figure(*args, **kwargs)
    plt.figure = final_size_figure
    try:
        fig = schematic.draw(schematic.STYLES['B_weighted_branches'])
    finally:
        plt.figure = make_figure
    results.append(export(fig, 1))
    fig = figure2()
    # Heatmaps and parameter mini-panels form two separate comparable groups;
    # the deliberately spanning colorbar is excluded from plot alignment.
    results.append(export(fig, 2, fig.axes[:4]))
    paired = module('abilene_forecasting/plot_fig3_classic_companion.py', 'existing_paired')
    results.append(export(capture(paired), 3))
    calibration = module('abilene_forecasting/plot_fig4_calibration_trajectories_v39.py', 'existing_calibration')
    calibration.add_constant_calibration = lambda _: pd.read_csv(ROOT / 'paper_figures/fig4_calibration_trajectories_v39/calibration_source_8seeds_v39.csv')
    results.append(export(capture(calibration), 4))
    weights = module('abilene_forecasting/plot_fig5_classic_restored.py', 'existing_weights')
    results.append(export(capture(weights), 5))
    (OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False))


if __name__ == '__main__':
    main()
