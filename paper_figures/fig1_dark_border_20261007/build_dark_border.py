"""Generate the two parallel-branch previews with a dark gray outer border."""
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
source = ROOT / 'paper_figures/fig1_parallel_options_20261007/build_parallel.py'
code = source.read_text(encoding='utf-8')
code = code.replace("'A_branch_labels'", "'A_branch_labels_dark'")
code = code.replace("'B_shared_fork'", "'B_shared_fork_dark'")
anchor = '    ax = fig.axes[0]\n'
assert code.count(anchor) == 1
code = code.replace(anchor, anchor + '''    outer = [p for p in ax.patches if isinstance(p, compact.FancyBboxPatch) and p.get_x() == .9]
    assert len(outer) == 1
    unchanged = helper.fingerprint(ax, outer)
    outer[0].set_edgecolor('#333333')
    assert unchanged == helper.fingerprint(ax, outer)
''')
render_source = OUT / 'render_source.py'
render_source.write_text(code, encoding='utf-8')
exec(compile(code, str(render_source), 'exec'), globals())
