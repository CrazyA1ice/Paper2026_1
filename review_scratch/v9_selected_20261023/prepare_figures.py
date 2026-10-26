from pathlib import Path
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
qa = Path(__file__).resolve().parent
root = qa.parents[1]
assets = root/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/V9_图表源文件'
assets.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(qa/'mplconfig')

# Exact reuse: retain every observation, statistic, limit and panel rectangle.
contract = json.loads((root/'review_scratch/figure_table_upgrade_20261022/data_audit.json').read_text(encoding='utf-8'))
(qa/'data_audit.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding='utf-8')
source = (root/'review_scratch/figure_table_upgrade_20261022/plot_figures.py').read_text(encoding='utf-8')
source = source.replace("OUT=Path(contract['assets'])", "DATA=Path(contract['assets'])\nOUT=Path("+repr(str(assets))+")")
source = source.replace('pd.read_csv(OUT/', 'pd.read_csv(DATA/')
source = source.replace("'font.serif':['Times New Roman','SimSun']", "'font.serif':['Times New Roman','SimSun'],'font.sans-serif':['Arial','SimSun']")
assert source.count("ax.tick_params(axis='x',length=") == 4
source = source.replace("ax.tick_params(axis='x',length=", "ax.tick_params(axis='x',direction='in',length=")
# Tick geometry changes only its direction; data and uncertainty stay identical.
guard = """
    for axis in fig.axes:
        for tick in axis.xaxis.get_major_ticks():
            assert tick._tickdir == 'in'
    (QA/f'figure{number}_geometry.json').write_text(json.dumps([
        {'xlim': list(axis.get_xlim()), 'ylim': list(axis.get_ylim()),
         'xticks': list(axis.get_xticks()), 'yticks': list(axis.get_yticks()),
         'lines': [{'x': list(line.get_xdata()), 'y': list(line.get_ydata())} for line in axis.lines],
         'collections': [collection.get_offsets().tolist() for collection in axis.collections]}
        for axis in fig.axes], ensure_ascii=False, indent=2, default=float), encoding='utf-8')
"""
source = source.replace('    prefix=OUT/stem', guard+'\n    prefix=OUT/stem')
(qa/'plot_figures234.py').write_text(source, encoding='utf-8')

source1 = (root/'review_scratch/figure1_table4_20261022/plot_figure1.py').read_text(encoding='utf-8')
source1 = source1.replace("OUT = ROOT / 'paper_template/长春工程学院学报(自然科学版)/图1与一周预测表修订_20261022/图表源文件'", 'OUT = Path('+repr(str(assets))+')')
source1 = source1.replace("'mathtext.fontset': 'stix'", "'mathtext.fontset': 'custom',\n                    'mathtext.rm': 'Times New Roman', 'mathtext.it': 'Times New Roman:italic',\n                    'mathtext.bf': 'Times New Roman:bold', 'mathtext.bfit': 'Times New Roman:bold:italic',\n                    'mathtext.cal': 'Times New Roman:italic', 'mathtext.sf': 'Times New Roman',\n                    'mathtext.tt': 'Times New Roman', 'mathtext.fallback': 'stix'")
source1 = source1.replace('    t.set_fontsize(7.5)', "    t.set_fontsize(7.5)\n    t.set_math_fontfamily('custom')")
source1 = source1.replace("fig.canvas.draw()\nalignment", "for label in fig.findobj(match=Text):\n    label.set_math_fontfamily('custom')\n    label.set_text(label.get_text().replace(r'\\mathbb{R}', r'\\mathrm{ℝ}'))\nfig.canvas.draw()\nalignment")
(qa/'plot_figure1.py').write_text(source1, encoding='utf-8')

(qa/'figure_contract.md').write_text('''# V9 figure revision contract

The user selected issues 04 and 05. Python remains the established backend.
Exact reuse of the existing scientific plots; do not restructure panels or change data.
Figure 1: retain the forecast and routing schematic, all labels and geometry; use Times New Roman mathematics.
Figure 2: preserve 64 seed-matched improvements, both datasets, and parameter ratios; inward x ticks.
Figure 3: preserve 80 high-demand records and both metrics, sample-SD bars and original axis limits; inward x ticks.
Figure 4: preserve 40 absolute-error records and 64 paired improvements, all four panels; inward x ticks.
No observations are excluded. Eight training seeds 42–49; centers are arithmetic means, bars are sample SD.
Export at the existing 138 mm physical width and original heights, 600 dpi PNG/TIFF plus editable PDF/SVG.
Require final rendered panel alignment within 1.5 pt, glyph audit, collision audit, and visual inspection.
The journal template controls SimSun/Times New Roman typography over generic sans-serif defaults.
''', encoding='utf-8')
print(assets)
