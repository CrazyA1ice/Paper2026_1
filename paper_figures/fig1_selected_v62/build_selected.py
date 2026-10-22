"""Selected compact blue-gray Figure 1 with geometrically centered plus signs."""
from pathlib import Path
import importlib.util
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
spec = importlib.util.spec_from_file_location(
    'variants', ROOT / 'paper_figures/fig1_compact_hierarchy_20261003/build_variants.py')
variants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(variants)
variants.OUT = OUT
name = 'B_bluegray_hierarchy'
fig, content, topology = variants.draw(name, variants.STYLES[name])
ax = fig.axes[0]
circles = [patch for patch in ax.patches if isinstance(patch, variants.Circle)]
pluses = [artist for artist in ax.texts if artist.get_text() == '+']
assert len(circles) == len(pluses) == 2
centers = []
for circle in circles:
    cx, cy = circle.get_center()
    artist = min(pluses, key=lambda t: abs(t.get_position()[0]-cx) + abs(t.get_position()[1]-cy))
    pluses.remove(artist)
    artist.remove()
    # Equal arm lengths; the actual strokes, rather than a font's em box,
    # share the exact center of the surrounding circle.
    radius = .8
    ax.plot([cx-radius, cx+radius], [cy, cy], color=variants.base.INK,
            linewidth=.55, solid_capstyle='butt', zorder=5)
    ax.plot([cx, cx], [cy-radius, cy+radius], color=variants.base.INK,
            linewidth=.55, solid_capstyle='butt', zorder=5)
    centers.append([float(cx), float(cy)])
record = variants.export(fig, name, content, topology)
# High-resolution raster for the manuscript; keep the SVG and PDF editable.
fig.savefig(OUT / 'fig1.png', dpi=600, facecolor='white')
record['centered_plus_coordinates'] = centers
record['plus_geometry'] = 'two equal perpendicular strokes intersect at each circle center'
(OUT / 'qa_summary.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in record.items() if key != 'unchanged_text'}, ensure_ascii=False))
