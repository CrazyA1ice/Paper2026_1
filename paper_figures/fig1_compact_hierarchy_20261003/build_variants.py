"""Compact Figure 1 previews; preserve every label, formula and connection."""
from pathlib import Path
from collections import Counter
import importlib.util
import json
import re
import warnings
import os

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.transforms import Transform
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, PathPatch, Circle, Rectangle
import numpy as np

spec = importlib.util.spec_from_file_location(
    'original_figure', ROOT / 'paper_figures/fig1_fusion_options_20261002/build_fig1.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

WIDTH_MM = 161.925
FONT = FontProperties(family=['Times New Roman', 'SimSun'], size=7.5)
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'SimSun'],
                     'font.size': 7.5, 'svg.fonttype': 'none',
                     'pdf.fonttype': 42, 'mathtext.fontset': 'stix'})

# Compress the spacing and geometry, never the glyphs. Original region order
# remains: scale experts -> curved internal expansion -> independent router.
SOURCE_Y = np.array([0, 3, 20, 23, 26, 43, 51, 53.5, 54, 66, 69, 81, 84, 96, 99, 104, 110])
COMPACT_Y = np.array([0, 2.5, 18.5, 20.5, 23, 38, 44, 46, 46.5, 56.5, 59, 69.5, 72, 82.5, 85, 89, 94])
STYLES = {
    'A_gray_hierarchy': dict(height=97, module='#343434', inner='#777777', outer='#9B9B9B',
        expert_fill='white', fusion_fill='#F5F5F4', router_fill='#FAFAFA',
        fusion_edge='#343434', router_edge='#555555', branch_fill=['#F1F1F0']*3),
    'B_bluegray_hierarchy': dict(height=94, module='#4B626E', inner='#818A8E', outer='#999E9F',
        expert_fill='#FAFBFC', fusion_fill='#F0F4F5', router_fill='#F8FAFA',
        fusion_edge='#415A67', router_edge='#5C717A', branch_fill=['#E9EFF2', '#EDF1EF', '#F1EEE9']),
    'C_teal_emphasis': dict(height=91, module='#555B5D', inner='#8C9393', outer='#A0A4A4',
        expert_fill='white', fusion_fill='#F0F5F2', router_fill='#F7FAF8',
        fusion_edge='#48685D', router_edge='#48685D', branch_fill=['#E9EFF2', '#EDF1EC', '#F1EEE9']),
}


class VerticalLayout(Transform):
    input_dims = output_dims = 2
    is_separable = True
    has_inverse = True

    def __init__(self, source, target):
        super().__init__()
        assert np.all(np.diff(source) > 0) and np.all(np.diff(target) > 0)
        self.source, self.target = source, target

    def transform_non_affine(self, values):
        mapped = np.array(values, dtype=float, copy=True)
        mapped[..., 1] = np.interp(mapped[..., 1], self.source, self.target)
        return mapped

    def inverted(self):
        return VerticalLayout(self.target, self.source)


original_text = base.text


def journal_text(ax, x, y, value, size=8, bold=False, color=base.INK, ha='center'):
    value = value.replace('z_n', r'\boldsymbol{z}_n').replace(r'\hat Y', r'\hat{\boldsymbol{Y}}')
    if value.startswith('$X'):
        value = value.replace('$X', r'$\boldsymbol{X}', 1)
    artist = original_text(ax, x, y, value, size, bold, color, ha)
    artist.set_fontproperties(FONT)
    if '$' in value and re.search(r'[\u4e00-\u9fff]', value):
        artist.set_fontfamily('SimSun')
    artist.set_fontsize(9 if value == '∑' else 7.5)
    artist.set_fontweight('bold' if bold else 'normal')
    return artist


base.text = journal_text


def draw(name, style):
    height = style['height']
    target_y = COMPACT_Y * height / 94
    mapper = VerticalLayout(SOURCE_Y, target_y)
    make_figure = plt.figure

    def physical_figure(*args, **kwargs):
        kwargs['figsize'] = (WIDTH_MM / 25.4, WIDTH_MM * height / 180 / 25.4)
        return make_figure(*args, **kwargs)

    # Render at the final physical width so the summation glyph spacing uses
    # the same metrics as the final export.
    plt.figure = physical_figure
    try:
        fig = base.draw(base.STYLES['B_weighted_branches'])
    finally:
        plt.figure = make_figure
    ax = fig.axes[0]
    content = Counter(t.get_text() for t in ax.texts)
    topology = {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    ax.set_ylim(0, height)
    layout_transform = mapper + ax.transData
    for line in ax.lines:
        line.set_transform(layout_transform)
        line.set_linewidth(.65 if line.get_linestyle() == '--' else .72)
    for patch in ax.patches:
        patch.set_transform(layout_transform)
        if isinstance(patch, FancyBboxPatch):
            x, y = patch.get_x(), patch.get_y()
            patch.set_edgecolor(style['inner'])
            patch.set_linewidth(.55)
            if x < 2:
                patch.set_edgecolor(style['outer'])
                patch.set_linewidth(.4)
            elif (x, y) == (121, 53.5):
                patch.set_edgecolor(style['fusion_edge'])
                patch.set_linewidth(1.0)
                patch.set_facecolor(style['fusion_fill'])
            elif (x, y) == (21, 3):
                patch.set_edgecolor(style['router_edge'])
                patch.set_linewidth(.85)
                patch.set_facecolor(style['router_fill'])
            elif x in (3, 35, 82, 160):
                patch.set_edgecolor(style['module'])
                patch.set_linewidth(.8 if x == 82 else .7)
            elif x == 124:
                center_y = mapper.transform((x, y + patch.get_height()/2))[1]
                patch.set_y(center_y - 2.7)
                patch.set_height(5.4)
                patch.set_transform(ax.transData)
                patch.set_facecolor(style['branch_fill'][[88.3, 80.8, 73.3].index(round(y, 1))])
                patch.set_edgecolor(style['module'])
                patch.set_linewidth(.6)
        elif isinstance(patch, PathPatch):
            patch.set_facecolor(style['expert_fill'])
            patch.set_edgecolor(style['module'])
            patch.set_linewidth(.85)
        elif isinstance(patch, Circle):
            patch.set_center(mapper.transform(patch.get_center()))
            patch.set_transform(ax.transData)
            patch.set_edgecolor(style['module'])
            patch.set_linewidth(.65)
        elif not isinstance(patch, Rectangle):
            patch.set_color('#62686A' if name != 'A_gray_hierarchy' else '#606060')
            patch.set_linewidth(.65)
    for artist in ax.texts:
        x, old_y = artist.get_position()
        new_x, new_y = mapper.transform((x, old_y))
        # Keep the summation indices below their operators with adequate room
        # between the two equations after the surrounding box is shortened.
        if abs(old_y - 65.5) < .001:
            new_y = 59.3 * height / 94
        elif abs(old_y - 58.3) < .001:
            new_y = 52 * height / 94
        elif artist.get_text() == 's':
            new_y = (59.3 if old_y > 58.3 else 52) * height / 94 - 3.9
        artist.set_position((new_x, new_y))
        artist.set_transform(ax.transData)
    assert content == Counter(t.get_text() for t in ax.texts)
    assert topology == {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    return fig, content, topology


def export(fig, name, content, topology):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for artist in fig.axes[0].texts:
        bounds = artist.get_window_extent(renderer)
        assert bounds.x0 >= 0 and bounds.y0 >= 0 and bounds.x1 <= fig.bbox.width and bounds.y1 <= fig.bbox.height, artist.get_text()
        for previous, other in boxes:
            assert not bounds.overlaps(other), (previous, artist.get_text())
        boxes.append((artist.get_text(), bounds))
    stem = OUT / name
    alignment = base.require_matplotlib_panel_alignment(fig, json_out=f'{stem}.alignment.json', strict=True)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        fig.savefig(f'{stem}.png', dpi=300, facecolor='white')
        fig.savefig(f'{stem}.pdf', facecolor='white')
        fig.savefig(f'{stem}.svg', facecolor='white')
    assert not [str(w.message) for w in captured if 'Glyph' in str(w.message)]
    glyphs = base.audit_text(Path(f'{stem}.pdf').read_bytes(), minimum_pt=5)
    collisions = base.audit_collisions(Path(f'{stem}.pdf'))
    for suffix, report in [('text-audit', glyphs), ('collision-audit', collisions)]:
        Path(f'{stem}.{suffix}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    assert glyphs['below_minimum_count'] == 0, glyphs
    assert collisions['summary']['fail'] == 0, collisions['findings']
    height = STYLES[name]['height']
    result = dict(figure=name, width_mm=WIDTH_MM, height_mm=WIDTH_MM*height/180,
        height_reduction_pct=round((1-height/110)*100, 1), unchanged_text=dict(content),
        preserved_topology=topology, minimum_glyph_pt=glyphs['minimum_found_pt'],
        alignment=alignment.get('verdict'), collision_summary=collisions['summary'])
    plt.close(fig)
    return result


if __name__ == '__main__':
    results = []
    for name, style in STYLES.items():
        fig, content, topology = draw(name, style)
        results.append(export(fig, name, content, topology))
    (OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in row.items() if k != 'unchanged_text'} for row in results], ensure_ascii=False))
