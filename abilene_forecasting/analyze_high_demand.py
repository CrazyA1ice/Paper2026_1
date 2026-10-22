"""Evaluate saved H=24 forecasts at training-defined high-demand targets."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results' / 'high_demand_analysis'
MODELS = ('dlinear', 'dlinear_scale_static', 'dlinear_scale_global',
          'dlinear_scale_constant_router', 'dlinear_scale')
SEEDS = range(42, 50)
T_CRITICAL_DF7 = 2.364624251  # Student t 97.5th percentile, 8 paired seeds.


def run_path(dataset, model, seed):
    if model == 'dlinear_scale_global':
        return ROOT / 'results' / 'global_weight_ablation' / dataset / f'{model}_seed{seed}'
    if model == 'dlinear_scale_constant_router':
        return ROOT / 'results' / 'constant_router_ablation' / dataset / f'{model}_seed{seed}'
    return ROOT / 'results' / dataset / f'{model}_seed{seed}'


def mean_sd(values):
    values = np.asarray(values, dtype=np.float64)
    return float(values.mean()), float(values.std(ddof=1))


def write_csv(name, records):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    OUT.mkdir(exist_ok=True)
    rows, datasets, evidence = [], [], []
    for dataset in ('abilene', 'geant'):
        processed = ROOT / 'data' / 'processed' / f'{dataset}_1hour.npz'
        with np.load(processed) as data:
            train, test = data['train'], data['test']
            thresholds = np.quantile(train.astype(np.float64), .9, axis=0)
        # Reconstruct every target from the split to verify ordering and horizon.
        reference = np.stack([test[i + 96:i + 120] for i in range(len(test) - 119)])
        mask = reference > thresholds[None, None, :]
        assert mask.any()
        unique_mask = test[96:] > thresholds[None, :]
        datasets.append({
            'dataset': dataset, 'windows': len(reference), 'channels': test.shape[1],
            'horizon': 24, 'high_forecast_targets': int(mask.sum()),
            'forecast_targets': int(mask.size), 'high_fraction': float(mask.mean()),
            'unique_high_time_od_targets': int(unique_mask.sum()),
            'unique_time_od_targets': int(unique_mask.size),
            'channels_with_high_targets': int(mask.any(axis=(0, 1)).sum()),
            'threshold_min': float(thresholds.min()), 'threshold_max': float(thresholds.max()),
        })
        threshold_rows = [{'channel': i + 1, 'training_q90_normalized': float(t),
                           'high_forecast_targets': int(mask[:, :, i].sum())}
                          for i, t in enumerate(thresholds)]
        write_csv(f'{dataset}_thresholds.csv', threshold_rows)
        paths = [processed]
        y = reference[mask].astype(np.float64)
        for model in MODELS:
            for seed in SEEDS:
                folder = run_path(dataset, model, seed)
                metrics_path = folder / 'metrics.json'
                metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
                assert (metrics['input_len'], metrics['pred_len'], metrics['seed']) == (96, 24, seed)
                prediction_path = folder / 'predictions.npz'
                with np.load(prediction_path) as data:
                    assert np.array_equal(data['truth'], reference), prediction_path
                    prediction = data['prediction']
                assert prediction.shape == reference.shape and np.isfinite(prediction).all()
                mse = np.mean((prediction - reference) ** 2)
                assert np.isclose(mse, metrics['test_normalized']['mse'], rtol=1e-5), metrics_path
                error = prediction[mask].astype(np.float64) - y
                rows.append({
                    'dataset': dataset, 'model': model, 'seed': seed,
                    'n_high_targets': int(mask.sum()),
                    'mae': float(np.abs(error).mean()),
                    'mean_shortfall': float(np.maximum(-error, 0).mean()),
                    'underprediction_fraction': float((error < 0).mean()),
                    'signed_bias': float(error.mean()),
                })
                paths.extend((prediction_path, metrics_path))
        for path in paths:
            evidence.append({'path': str(path.relative_to(ROOT)),
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    summaries, paired = [], []
    for dataset in ('abilene', 'geant'):
        for model in MODELS:
            part = [r for r in rows if r['dataset'] == dataset and r['model'] == model]
            result = {'dataset': dataset, 'model': model, 'n_seeds': 8}
            for metric in ('mae', 'mean_shortfall', 'underprediction_fraction', 'signed_bias'):
                result[f'{metric}_mean'], result[f'{metric}_sd'] = mean_sd([r[metric] for r in part])
            summaries.append(result)
        ours = {r['seed']: r for r in rows if r['dataset'] == dataset and r['model'] == MODELS[-1]}
        for model in MODELS[:-1]:
            baseline = {r['seed']: r for r in rows if r['dataset'] == dataset and r['model'] == model}
            for metric in ('mae', 'mean_shortfall'):
                values = [100 * (baseline[s][metric] - ours[s][metric]) / baseline[s][metric] for s in SEEDS]
                mean, sd = mean_sd(values)
                half = float(T_CRITICAL_DF7 * sd / np.sqrt(8))
                paired.append({'dataset': dataset, 'baseline': model, 'metric': metric,
                               'mean_reduction_pct': mean, 'sd_pct': sd,
                               'ci95_low_pct': mean - half, 'ci95_high_pct': mean + half,
                               'seed_wins': sum(v > 0 for v in values), 'n_seeds': 8})
    write_csv('per_seed.csv', rows)
    write_csv('summary.csv', summaries)
    write_csv('paired_reductions.csv', paired)
    audit = {
        'threshold': 'Per OD training-only 90th percentile; strict truth > threshold.',
        'primary_metrics': ['normalized MAE', 'mean max(truth-prediction,0) across all high targets'],
        'secondary_metrics': ['underprediction fraction', 'signed bias'],
        'aggregation': 'Every saved forecast target counted; compute within seed, then summarize 8 paired seeds.',
        'dependence': 'Overlapping forecast windows repeat target hours; target count is not an independent sample size.',
        'inference_boundary': 'Forecast evaluation only; no capacity, congestion or online deployment benefit measured.',
        'datasets': datasets, 'source_files': evidence,
    }
    (OUT / 'analysis_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in datasets:
        print(json.dumps(item, ensure_ascii=False))
    for item in summaries + paired:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == '__main__':
    main()
