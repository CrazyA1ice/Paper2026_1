"""Check algebra, paired statistics, and evaluation coverage without rerunning models."""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'abilene_forecasting' / 'results' / 'high_demand_analysis'


def read(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


rows = read('per_seed.csv')
assert len(rows) == 80
assert len({(r['dataset'], r['model'], r['seed']) for r in rows}) == 80
assert set(Counter((r['dataset'], r['model']) for r in rows).values()) == {8}
for row in rows:
    # Absolute error = under + over; signed bias = over - under.
    derived_shortfall = (float(row['mae']) - float(row['signed_bias'])) / 2
    assert abs(derived_shortfall - float(row['mean_shortfall'])) < 1e-12
    assert 0 <= float(row['underprediction_fraction']) <= 1
audit = json.loads((OUT / 'analysis_audit.json').read_text(encoding='utf-8'))
for dataset in audit['datasets']:
    count = sum(int(r['high_forecast_targets']) for r in read(dataset['dataset'] + '_thresholds.csv'))
    assert count == dataset['high_forecast_targets']
for row in read('paired_reductions.csv'):
    for seed in range(42, 50):
        base = next(r for r in rows if r['dataset'] == row['dataset'] and r['model'] == row['baseline'] and int(r['seed']) == seed)
        ours = next(r for r in rows if r['dataset'] == row['dataset'] and r['model'] == 'dlinear_scale' and int(r['seed']) == seed)
        metric = row['metric']
        value = 100 * (float(base[metric]) - float(ours[metric])) / float(base[metric])
        if seed == 42:
            improvements = []
        improvements.append(value)
    assert abs(sum(improvements) / 8 - float(row['mean_reduction_pct'])) < 1e-12
    assert sum(v > 0 for v in improvements) == int(row['seed_wins'])
print('80 unique forecasts, coverage counts, shortfall algebra, and 16 paired comparisons verified.')
