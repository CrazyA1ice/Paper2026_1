"""Keep the selected schematic unchanged except for its expansion boundary."""
from pathlib import Path
from collections import Counter
import importlib.util
import json
import os
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))
spec = importlib.util.spec_from_file_location(
    'compact', ROOT / 'paper_figures/fig1_compact_hierarchy_20261003/build_variants.py')
compact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compact)
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch

BASE_NAME = 'B_bluegray_hierarchy'
STYLE = compact.STYLES[BASE_NAME]
OPTIONS = {
    'A_standard': {'closed': False, 'inset': 0, 'linewidth': .70, 'dash': (4.0, 2.5)},
    'B_closed': {'closed': True, 'inset': 0, 'linewidth': .70, 'dash': (4.0, 2.5)},
    'C_inset': {'closed': False, 'inset': 5, 'linewidth': .60, 'dash': (3.0, 2.0)},
}

def centered_pluses(fig):
    ax = fig.axes[0]
    circles = [p for p in ax.patches if isinstance(p, compact.Circle)]
    pluses = [t for t in ax.texts if t.get_text() == '+']
    assert len(circles) == len(pluses) == 2
    for circle in circles:
        cx, cy = circle.get_center()
        artist = min(pluses, key=lambda t: abs(t.get_position()[0]-cx) + abs(t.get_position()[1]-cy))
        pluses.remove(artist)
        artist.remove()
        ax.plot([cx-.8, cx+.8], [cy, cy], color=compact.base.INK,
                linewidth=.55, solid_capstyle='butt', zorder=5)
        ax.plot([cx, cx], [cy-.8, cy+.8], color=compact.base.INK,
                linewidth=.55, solid_capstyle='butt', zorder=5)

def fingerprint(ax, excluded=()):
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = [(t.get_text(), t.get_position(), t.get_fontproperties().get_fontconfig_pattern(),
              t.get_color(), t.get_window_extent(renderer).bounds) for t in ax.texts]
    lines = [(tuple(line.get_xdata()), tuple(line.get_ydata()), line.get_color(),
              line.get_linewidth(), line.get_linestyle(), line.get_transform().get_matrix().tolist())
             for line in ax.lines]
    patches = [(p.get_path().vertices.tolist(), p.get_path().codes.tolist(),
                p.get_facecolor(), p.get_edgecolor(), p.get_linewidth(),
                p.get_transform().transform(p.get_path().vertices).tolist())
               for p in ax.patches if p not in excluded]
    return {'texts': texts, 'lines': lines, 'patches': patches}

def draw_outline(ax, original, option):
    transform = original.get_transform()
    original.remove()
    artists = []

    def path(vertices, closed=False, fill='none', dashed=False):
        codes = [PlotPath.MOVETO] + [PlotPath.LINETO] * (len(vertices)-1)
        if closed:
            vertices = vertices + [vertices[0]]
            codes += [PlotPath.CLOSEPOLY]
        artist = PathPatch(PlotPath(vertices, codes), transform=transform, facecolor=fill,
                           edgecolor=STYLE['module'], linewidth=option['linewidth'] if dashed else .85,
                           linestyle=(0, option['dash']) if dashed else '-',
                           joinstyle='miter', capstyle='butt', zorder=1)
        ax.add_patch(artist)
        artists.append(artist)

    # Same upper and lower extents as the selected curved outline.
    if option['closed']:
        path([(79,54),(79,99),(114,99),(114,54)])
        path([(22,51),(22,23),(158,23),(158,51)])
        path([(79,54),(114,54),(158,51),(22,51)], closed=True, dashed=True)
        # Region fills sit behind the open stroked frames and the dashed trapezoid.
        for points in [[(79,54),(114,54),(114,99),(79,99)],
                       [(22,23),(158,23),(158,51),(22,51)]]:
            vertices = points + [points[0]]
            artist = PathPatch(PlotPath(vertices, [PlotPath.MOVETO]+[PlotPath.LINETO]*3+[PlotPath.CLOSEPOLY]),
                               transform=transform, facecolor=STYLE['expert_fill'],
                               edgecolor='none', zorder=.9)
            ax.add_patch(artist)
            artists.append(artist)
    else:
        path([(79,54),(114,54),(114,99),(79,99)], closed=True, fill=STYLE['expert_fill'])
        path([(22,23),(158,23),(158,51),(22,51)], closed=True, fill=STYLE['expert_fill'])
        inset = option['inset']
        path([(79+inset,54),(22+inset,51)], dashed=True)
        path([(114-inset,54),(158-inset,51)], dashed=True)
    return artists

results = []
for name, option in OPTIONS.items():
    fig, _, _ = compact.draw(BASE_NAME, STYLE)
    centered_pluses(fig)
    ax = fig.axes[0]
    outlines = [p for p in ax.patches if isinstance(p, PathPatch)]
    assert len(outlines) == 1
    original = outlines[0]
    before = fingerprint(ax, [original])
    added = draw_outline(ax, original, option)
    assert before == fingerprint(ax, added), 'Content outside the expansion boundary changed'
    for artist in added:
        assert not any(c in (PlotPath.CURVE3, PlotPath.CURVE4) for c in artist.get_path().codes)
    content = Counter(t.get_text() for t in ax.texts)
    topology = {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    fig.savefig(OUT / f'{name}_highres.png', dpi=600, facecolor='white')
    compact.OUT = OUT
    compact.STYLES[name] = STYLE
    record = compact.export(fig, name, content, topology)
    record['unchanged_outside_expansion_boundary'] = True
    record['expansion_geometry'] = option
    results.append(record)

(OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{k: v for k, v in row.items() if k != 'unchanged_text'} for row in results], ensure_ascii=False))
