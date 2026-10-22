"""Clarify the parallel forecast and routing branches of the selected schematic."""
from pathlib import Path
from collections import Counter
import json
import os
import types

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))
source = ROOT / 'paper_figures/fig1_trapezoid_options_20261007/build_options.py'
helper = types.ModuleType('outline_helpers')
helper.__file__ = str(source)
# Load the existing drawing helpers without running the preview export loop.
exec(compile(source.read_text(encoding='utf-8').split('\nresults = []\n')[0], str(source), 'exec'), helper.__dict__)
compact = helper.compact
from matplotlib.patches import FancyArrowPatch, Circle, PathPatch

mapper = compact.VerticalLayout(compact.SOURCE_Y, compact.COMPACT_Y)

def annotation(ax, x, y, label, size=7.0):
    ax.text(*mapper.transform((x, y)), label, fontproperties=compact.FONT,
            fontsize=size, color=helper.STYLE['module'], va='center', ha='center', zorder=5)

def routed_arrow(ax, points, transform):
    old_lines, old_patches = set(ax.lines), set(ax.patches)
    compact.base.arrow(ax, points, dashed=True, color='#62686A')
    for artist in (set(ax.lines)-old_lines) | (set(ax.patches)-old_patches):
        artist.set_transform(transform)
        artist.set_linewidth(.65)

def remove_arrow(ax, start):
    matches = [p for p in ax.patches if isinstance(p, FancyArrowPatch)
               and tuple(p._posA_posB[0]) == start]
    assert len(matches) == 1, start
    matches[0].remove()

results = []
for name, common_fork in [('A_branch_labels_dark', False), ('B_shared_fork_dark', True)]:
    fig, _, _ = compact.draw(helper.BASE_NAME, helper.STYLE)
    helper.centered_pluses(fig)
    ax = fig.axes[0]
    outer = [p for p in ax.patches if isinstance(p, compact.FancyBboxPatch) and p.get_x() == .9]
    assert len(outer) == 1
    unchanged = helper.fingerprint(ax, outer)
    outer[0].set_edgecolor('#333333')
    assert unchanged == helper.fingerprint(ax, outer)
    old_text = Counter(t.get_text() for t in ax.texts)
    old_curves = [(tuple(line.get_xdata()), tuple(line.get_ydata())) for line in ax.lines
                  if len(line.get_xdata()) > 2]
    outline = [p for p in ax.patches if isinstance(p, PathPatch)]
    assert len(outline) == 1
    helper.draw_outline(ax, outline[0], helper.OPTIONS['A_standard'])
    transform = ax.lines[0].get_transform()

    # Both variants return the weights to the fusion module via a shorter outer track.
    for line in list(ax.lines):
        x, y = list(line.get_xdata()), list(line.get_ydata())
        if (x, y) in [([155,171.5],[11,11]), ([171.5,171.5],[11,57])]:
            line.remove()
    remove_arrow(ax, (171.5,57))
    routed_arrow(ax, [(155,11),(166,11),(166,57),(153,57)], transform)

    if common_fork:
        old_input = [line for line in ax.lines
                     if list(line.get_xdata()) == [15.5,15.5]
                     and list(line.get_ydata()) == [59,11]]
        assert len(old_input) == 1
        old_input[0].remove()
        remove_arrow(ax, (15.5,11))
        # The two branches visibly leave the same junction on the history-input path.
        routed_arrow(ax, [(30.5,75),(30.5,57),(15.5,57),(15.5,11),(21,11)], transform)
        ax.add_patch(Circle(mapper.transform((30.5,75)), .35,
                            facecolor='#62686A', edgecolor='none', zorder=6))

    annotation(ax, 31, 99.5, '预测分支')
    annotation(ax, 8.3, 46.8, '路由分支')
    annotation(ax, 170, 36, '权重', size=6.5)
    content = Counter(t.get_text() for t in ax.texts)
    assert content == old_text + Counter(['预测分支','路由分支','权重'])
    assert old_curves == [(tuple(line.get_xdata()), tuple(line.get_ydata())) for line in ax.lines
                          if len(line.get_xdata()) > 2]
    compact.OUT = OUT
    compact.STYLES[name] = helper.STYLE
    topology = {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    fig.savefig(OUT / f'{name}_highres.png', dpi=600, facecolor='white')
    record = compact.export(fig, name, content, topology)
    record['shared_input_junction'] = common_fork
    record['preserved_original_labels_and_curves'] = True
    results.append(record)

(OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{k:v for k,v in row.items() if k!='unchanged_text'} for row in results], ensure_ascii=False))
