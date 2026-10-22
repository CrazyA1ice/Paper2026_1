from pathlib import Path
from hashlib import sha256
import csv
import json
import statistics as st
import sys

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
BASE = ROOT / 'abilene_forecasting/results'
OUT = ROOT / 'paper_template/长春工程学院学报(自然科学版)/优势补充与图表优化_20261022'
ASSETS = OUT / '图表源文件'
ASSETS.mkdir(parents=True, exist_ok=True)


def read(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


raw_week = read('long_horizon_20261021/per_seed_scores.csv')
week = [r for r in raw_week if r['dataset'] == 'geant' and int(r['horizon']) == 168]
assert len(week) == 40
models = ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router']
index = {(r['model'], int(r['seed'])): r for r in week}
assert len(index) == 40
for r in week:
    assert r['n_all_origins'] == r['n_common_origins'] == '307'
    p = BASE / f'long_horizon_20261021/h168/geant/{r["model"]}_seed{r["seed"]}/metrics.json'
    original = json.loads(p.read_text(encoding='utf-8'))
    assert original['input_len'] == 96 and original['pred_len'] == 168
    assert original['n_channels'] == 524 and original['split_windows']['test'] == 307
    for metric in ['mse', 'mae']:
        assert abs(float(r['all_' + metric]) - original['test_normalized'][metric]) < 1e-6

paired, summary = [], []
for model in models:
    for metric in ['mse', 'mae']:
        effects = []
        for seed in range(42, 50):
            control = float(index[model, seed]['all_' + metric])
            own = float(index['dlinear_scale', seed]['all_' + metric])
            effect = 100 * (control - own) / control
            effects.append(effect)
            paired.append({'baseline': model, 'metric': metric, 'seed': seed,
                           'baseline_error': control, 'proposed_error': own, 'reduction_pct': effect})
        summary.append({'baseline': model, 'metric': metric, 'n': 8, 'wins': sum(x > 0 for x in effects),
                        'mean': st.mean(effects), 'sd': st.stdev(effects), 'min': min(effects), 'max': max(effects)})
assert all(r['wins'] == 8 for r in summary)
with (ASSETS / '图4_全部配对降幅.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(paired[0])); writer.writeheader(); writer.writerows(paired)
with (ASSETS / '图4_五种模型原始误差.csv').open('w', encoding='utf-8-sig', newline='') as f:
    fields = ['dataset', 'model', 'seed', 'horizon', 'n_all_origins', 'all_mse', 'all_mae']
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(week)

demand = read('high_demand_analysis/per_seed.csv')
assert len(demand) == 80
demand_summary = []
for ds in ['abilene', 'geant']:
    ix = {(r['model'], int(r['seed'])): r for r in demand if r['dataset'] == ds}
    for metric in ['mae', 'mean_shortfall', 'underprediction_fraction']:
        controls = [float(ix['dlinear', s][metric]) for s in range(42, 50)]
        own = [float(ix['dlinear_scale', s][metric]) for s in range(42, 50)]
        effects = [100 * (c - p) / c for c, p in zip(controls, own)]
        demand_summary.append({'dataset': ds, 'metric': metric, 'n': 8,
                               'baseline_mean': st.mean(controls), 'proposed_mean': st.mean(own),
                               'mean_paired_reduction_pct': st.mean(effects),
                               'wins': sum(x > 0 for x in effects)})
for row in demand_summary:
    if row['metric'] == 'underprediction_fraction':
        row['main_text_status'] = 'Not added: introduces a third endpoint; error magnitude already answers the main question.'
    else:
        row['main_text_status'] = 'Existing endpoint; add the Abilene paired reduction in prose.'

inventory = []
for name, status in [
    ('core_v2_summary.csv', 'Main 24-hour comparison already represented; do not mix original-unit or redundant RMSE endpoints.'),
    ('global_weight_ablation/analysis/paired_summary.csv', 'Main fusion comparison already represented.'),
    ('constant_router_ablation/summary.csv', 'Main constant-input control already represented if the aggregate file exists.'),
    ('supplement_20261020/temporal_paired_effects.csv', 'Conditional subperiod effects; restoring the entire time-stratification protocol would enlarge scope.'),
    ('supplement_20261020/learning_curve_paired_effects.csv', 'Training-fraction effects are mixed; not a general data-efficiency advantage.'),
    ('supplement_20261020/seasonal_paired_effects.csv', 'Different usable target windows; do not combine with the current learned-model comparison.'),
    ('global_weight_ablation/analysis/volatility_summary.csv', 'Descriptive strata overlap the existing average comparison; not an additional generalization study.'),
    ('router_window_assignment_audit/summary.csv', 'Does not establish a universal benefit from per-window weight assignment.'),
    ('long_horizon_20261021/paired_reductions.csv', 'Retain the reported 168-hour task; the full horizon grid has mixed effects.'),
    ('inference_benchmark_cpu1/inference_benchmark_summary.csv', 'Excluded from main text under the standing instruction to omit hardware/timing discussion.')]:
    p = BASE / name
    if p.exists():
        rows = read(name)
        inventory.append({'source': str(p), 'rows': len(rows), 'sha256': sha256(p.read_bytes()).hexdigest(), 'decision': status})

report = {'output_dir': str(OUT), 'assets': str(ASSETS), 'weekly_raw_rows': len(week),
          'weekly_paired_rows': len(paired), 'weekly_summary': summary, 'high_demand': demand_summary,
          'router_share_pct': 100 * 131 / 8339, 'inventory': inventory,
          'data_exclusion_rule': 'All five models, seeds 42-49, and all 307 test origins in the reported GÉANT H168 task; no within-task filtering.',
          'no_new_experiments': True, 'no_significance_tests_added': True}
(QA / 'evidence_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'weekly_summary': summary, 'high_demand': demand_summary[:2],
                  'router_share_pct': report['router_share_pct'], 'audited_families': len(inventory)}, ensure_ascii=False))
