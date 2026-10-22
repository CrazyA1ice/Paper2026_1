"""Correct two descriptive panel titles without changing quantitative artists."""
from pathlib import Path
import importlib.util
import hashlib
import json
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paper_figures/v70_terminology'
OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('submission_figures', ROOT / 'paper_figures/v56_cdgyxy/build_submission_figures.py')
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)
style.OUT = OUT
model = style.module('abilene_forecasting/plot_fig4_calibration_trajectories_v39.py', 'existing_figure4')
model.add_constant_calibration = lambda _: style.pd.read_csv(ROOT / 'paper_figures/fig4_calibration_trajectories_v39/calibration_source_8seeds_v39.csv')
fig = style.capture(model)
style.typography(fig)
before = style.geometry(fig)
fig.savefig(OUT / 'fig4_before.png', dpi=600, facecolor='white')
baseline = np.asarray(Image.open(OUT / 'fig4_before.png').convert('RGBA'))
embedded = np.asarray(Image.open(ROOT / 'review_scratch/v69_review/image4.png').convert('RGBA'))
assert baseline.shape == embedded.shape
baseline_diff = np.any(baseline != embedded, axis=2)
baseline_ys, baseline_xs = np.where(baseline_diff)
# The existing builder's legend measures depend on earlier font settings.
# The plots and both title bands reproduce the embedded V69 exactly.
assert not baseline_diff[:2500].any(), 'Reconstruction differs in a plot or title'
changes = []
for artist in fig.findobj(style.Text):
    title = artist.get_text()
    if '全测试点校准' in title:
        revised = title.replace('全测试点校准', '真实值分组预测')
        artist.set_text(revised)
        changes.append([title, revised])
assert len(changes) == 2
assert before == style.geometry(fig)
fig.canvas.draw()
fig.savefig(OUT / 'fig4.png', dpi=600, facecolor='white')
after = np.asarray(Image.open(OUT / 'fig4.png').convert('RGBA')).copy()
diff = np.any(baseline != after, axis=2)
ys, xs = np.where(diff)
assert ys.max() < 120, 'Unexpected pixel changes below the panel titles'
# Preserve every original pixel below the title band, including the legend.
after[120:] = embedded[120:]
Image.fromarray(after).save(OUT / 'fig4.png', dpi=(600, 600))
assert np.array_equal(after[120:], embedded[120:])
svg = (ROOT / 'paper_figures/v56_cdgyxy/fig4.svg').read_text(encoding='utf-8')
assert svg.count('全测试点校准') == 2
(OUT / 'fig4.svg').write_text(svg.replace('全测试点校准', '真实值分组预测'), encoding='utf-8')
audit = {'titles': changes, 'numeric_artists_unchanged': before == style.geometry(fig),
         'baseline_plot_and_title_pixels_identical_to_v69': True,
         'final_pixels_outside_title_band_identical_to_v69': True,
         'svg_changes_only_two_text_nodes': True,
         'changed_pixel_bounds': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
         'source_csv_sha256': hashlib.sha256((ROOT / 'paper_figures/fig4_calibration_trajectories_v39/calibration_source_8seeds_v39.csv').read_bytes()).hexdigest()}
(OUT / 'label_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(audit, ensure_ascii=False))
