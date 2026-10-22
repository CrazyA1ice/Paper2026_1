"""Separate the E4 card from its enclosing frame without moving the card."""
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
source = ROOT / 'paper_figures/fig1_dark_border_20261007/render_source.py'
code = source.read_text(encoding='utf-8')
code = code.replace("[('A_branch_labels_dark', False), ('B_shared_fork_dark', True)]",
                    "[('A_border_spacing', False)]")
anchor = '    compact.OUT = OUT\n'
assert code.count(anchor) == 1
code = code.replace(anchor, '''    # Lower only the enclosing frame's base and the two expansion anchors.
    # The E4 card, labels, arrows and lower detail box retain their positions.
    boundaries = [p for p in ax.patches if isinstance(p, PathPatch)
                  and any(y == 54 for x, y in p.get_path().vertices)]
    assert len(boundaries) == 3
    unchanged = helper.fingerprint(ax, boundaries)
    for boundary in boundaries:
        vertices = boundary.get_path().vertices
        vertices[vertices[:, 1] == 54, 1] = 52.5
        boundary.stale = True
    assert unchanged == helper.fingerprint(ax, boundaries)
    e4 = [p for p in ax.patches if isinstance(p, compact.FancyBboxPatch)
          and (p.get_x(), p.get_y()) == (82, 54)]
    assert len(e4) == 1
    separation_pt = (mapper.transform((82, 54))[1]
                     - mapper.transform((82, 52.5))[1]) * compact.WIDTH_MM / 180 / 25.4 * 72
    assert separation_pt > 3
''' + anchor)
render_source = OUT / 'render_source.py'
render_source.write_text(code, encoding='utf-8')
exec(compile(code, str(render_source), 'exec'), globals())
