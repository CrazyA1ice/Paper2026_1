from pathlib import Path
from hashlib import sha256
import csv
import json
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
BASE = ROOT / 'abilene_forecasting/results'
models = ['dlinear', 'lightts', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router', 'dlinear_scale']
records, inputs = [], []
for ds in ['abilene', 'geant']:
    for model in models:
        parent = BASE / ('global_weight_ablation' if model == 'dlinear_scale_global' else
                         'constant_router_ablation' if model == 'dlinear_scale_constant_router' else '') / ds
        for seed in range(42,50):
            path = parent / f'{model}_seed{seed}/metrics.json'
            r = json.loads(path.read_text(encoding='utf-8'))
            assert r['input_len'] == 96 and r['pred_len'] == 24 and r['seed'] == seed
            records.append({'dataset': ds, 'model': model, 'seed': seed,
                            'mse': r['test_normalized']['mse'], 'mae': r['test_normalized']['mae'], 'parameters': r['parameters']})
            inputs.append({'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest()})
assert len(records) == 96
index = {(r['dataset'],r['model'],r['seed']):r for r in records}
effects = []
for ds in ['abilene','geant']:
    assert all(index[ds,'dlinear_scale',s]['parameters'] == index[ds,'dlinear_scale_constant_router',s]['parameters'] == 8339 for s in range(42,50))
    for baseline in models[:-1]:
        for metric in ['mse','mae']:
            values = [100*(index[ds,baseline,s][metric]-index[ds,'dlinear_scale',s][metric])/index[ds,baseline,s][metric] for s in range(42,50)]
            effects.append({'dataset':ds,'baseline':baseline,'metric':metric,'n':8,
                            'mean':st.mean(values),'sd':st.stdev(values),'wins':sum(v>0 for v in values)})
high_path = BASE / 'high_demand_analysis/per_seed.csv'
with high_path.open(encoding='utf-8-sig',newline='') as f:
    high = list(csv.DictReader(f))
assert len(high) == 80
hi = {(r['dataset'],r['model'],int(r['seed'])):r for r in high}
high_effects = []
high_summary = []
for ds in ['abilene','geant']:
    for model in [m for m in models if m != 'lightts']:
        rows = [hi[ds,model,s] for s in range(42,50)]
        assert len({r['n_high_targets'] for r in rows}) == 1
        high_summary.append({'dataset':ds,'model':model, **{m:st.mean(float(r[m]) for r in rows) for m in ['mae','mean_shortfall']}})
        if model != 'dlinear_scale':
            for metric in ['mae','mean_shortfall']:
                values = [100*(float(hi[ds,model,s][metric])-float(hi[ds,'dlinear_scale',s][metric]))/float(hi[ds,model,s][metric]) for s in range(42,50)]
                high_effects.append({'dataset':ds,'baseline':model,'metric':metric,'n':8,'mean':st.mean(values)})
    # Reproduce the new equation against an existing full prediction archive.
    with np.load(ROOT / f'abilene_forecasting/data/processed/{ds}_1hour.npz') as z:
        threshold = np.quantile(z['train'].astype(np.float64), .9, axis=0)
    prediction_path = BASE / ds / 'dlinear_scale_seed42/predictions.npz'
    with np.load(prediction_path) as z:
        mask = z['truth'] > threshold[None,None,:]
        difference = z['truth'][mask].astype(np.float64)-z['prediction'][mask].astype(np.float64)
    assert int(mask.sum()) == int(hi[ds,'dlinear_scale',42]['n_high_targets'])
    assert np.isclose(np.maximum(0,difference).sum()/mask.sum(), float(hi[ds,'dlinear_scale',42]['mean_shortfall']),rtol=1e-12)
    assert np.isclose(np.abs(difference).mean(),float(hi[ds,'dlinear_scale',42]['mae']),rtol=1e-12)
weekly_path = BASE / 'long_horizon_20261021/per_seed_scores.csv'
with weekly_path.open(encoding='utf-8-sig',newline='') as f:
    week = [r for r in csv.DictReader(f) if r['dataset']=='geant' and int(r['horizon'])==168]
assert len(week)==40
wi = {(r['model'],int(r['seed'])):r for r in week}
weekly = []
for baseline in [m for m in models if m not in ['lightts','dlinear_scale']]:
    for metric in ['mse','mae']:
        values = [100*(float(wi[baseline,s]['all_'+metric])-float(wi['dlinear_scale',s]['all_'+metric]))/float(wi[baseline,s]['all_'+metric]) for s in range(42,50)]
        assert all(v>0 for v in values)
        weekly.append({'baseline':baseline,'metric':metric,'n':8,'mean':st.mean(values),'wins':8})
assert all(int(wi['dlinear_scale',s]['parameters'])==57587 for s in range(42,50))
report={'baseline_metric_records':96,'high_demand_records':80,'weekly_records':40,'no_exclusions':True,
        'baseline_effects':effects,'high_demand_effects':high_effects,'high_demand_summary':high_summary,
        'aue_formula_reproduced_for_full_prediction_archives':['abilene_seed42','geant_seed42'],
        'weekly_effects':weekly,'weekly_positive_paired_comparisons':64,'weekly_router_share_pct':131/57587*100,
        'input_metrics':inputs,'high_demand_csv_sha256':sha256(high_path.read_bytes()).hexdigest(),
        'weekly_csv_sha256':sha256(weekly_path.read_bytes()).hexdigest()}
(QA/'evidence_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['input_metrics','high_demand_summary','baseline_effects','high_demand_effects','weekly_effects']},ensure_ascii=False))
for r in effects:
    if r['dataset']=='abilene' and r['baseline'] in ['dlinear','dlinear_scale_global'] and r['metric']=='mae':
        print('Ablation MAE',r)
