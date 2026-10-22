from hashlib import sha256
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
PROJECT = ROOT / 'abilene_forecasting'
OUT = ROOT / 'paper_template/长春工程学院学报(自然科学版)/八次重复统一修订_20261022'
ASSETS = OUT / '图表与核验数据'
ASSETS.mkdir(parents=True, exist_ok=True)
assert json.loads((QA / 'training_complete.json').read_text(encoding='utf-8-sig'))['all_runs_completed']
manifest = json.loads((QA / 'training_manifest.json').read_text(encoding='utf-8'))
for name, digest in manifest['protected_files_sha256'].items():
    assert sha256(Path(name).read_bytes()).hexdigest() == digest
records = []
for dataset, n_windows, channels in [('abilene', 813, 144), ('geant', 451, 524)]:
    common_truth = None
    for model in ['dlinear', 'lightts', 'dlinear_scale']:
        reference = json.loads((PROJECT / f'results/{dataset}/{model}_seed42/metrics.json').read_text(encoding='utf-8'))
        for seed in range(42, 50):
            directory = PROJECT / f'results/{dataset}/{model}_seed{seed}'
            source = directory / 'metrics.json'
            result = json.loads(source.read_text(encoding='utf-8'))
            for key in ['dataset', 'model', 'model_config', 'n_channels', 'split_rows', 'split_windows',
                        'input_len', 'pred_len', 'batch_size', 'epochs_max', 'patience', 'learning_rate', 'parameters']:
                assert result[key] == reference[key], (dataset, model, seed, key)
            assert result['seed'] == seed and result['input_len'] == 96 and result['pred_len'] == 24
            with np.load(directory / 'predictions.npz') as z:
                prediction, truth = z['prediction'], z['truth']
            assert prediction.shape == truth.shape == (n_windows, 24, channels)
            assert np.isfinite(prediction).all() and np.isfinite(truth).all()
            if common_truth is None:
                common_truth = truth.copy()
            assert np.array_equal(common_truth, truth), (dataset, model, seed, 'test targets differ')
            error = prediction - truth
            mse = float(np.mean(error ** 2))
            mae = float(np.mean(np.abs(error)))
            assert np.isclose(mse, result['test_normalized']['mse'], rtol=1e-7)
            assert np.isclose(mae, result['test_normalized']['mae'], rtol=1e-7)
            records.append({'dataset': dataset, 'model': model, 'seed': seed,
                            'mse': result['test_normalized']['mse'], 'mae': result['test_normalized']['mae'],
                            'parameters': result['parameters'], 'n_test_windows': n_windows,
                            'metrics_sha256': sha256(source.read_bytes()).hexdigest()})
data = pd.DataFrame(records)
assert len(data) == 48 and not data.duplicated(['dataset', 'model', 'seed']).any()
data.to_csv(ASSETS / '表2_全部48次训练记录.csv', index=False, encoding='utf-8-sig')
summary = []
for (dataset, model), group in data.groupby(['dataset', 'model'], sort=False):
    assert sorted(group.seed.tolist()) == list(range(42, 50))
    summary.append({'dataset': dataset, 'model': model, 'n': 8, 'parameters': int(group.parameters.iloc[0]),
                    'mse_mean': group.mse.mean(), 'mse_sd': group.mse.std(ddof=1),
                    'mae_mean': group.mae.mean(), 'mae_sd': group.mae.std(ddof=1)})
pd.DataFrame(summary).to_csv(ASSETS / '表2_八次均值与标准差.csv', index=False, encoding='utf-8-sig')
paired, effects = [], []
for dataset in ['abilene', 'geant']:
    own = data[(data.dataset == dataset) & (data.model == 'dlinear_scale')].set_index('seed').sort_index()
    baseline = data[(data.dataset == dataset) & (data.model == 'lightts')].set_index('seed').sort_index()
    for metric in ['mse', 'mae']:
        assert (baseline[metric] > 0).all()
        values = 100 * (baseline[metric] - own[metric]) / baseline[metric]
        for seed, value in values.items():
            paired.append({'dataset': dataset, 'seed': seed, 'metric': metric, 'relative_reduction_pct': value})
        effects.append({'dataset': dataset, 'metric': metric, 'mean': values.mean(),
                        'sample_sd': values.std(ddof=1), 'n_seeds': 8, 'wins': int((values > 0).sum()),
                        'proposed_parameters': int(own.parameters.iloc[0]),
                        'lightts_parameters': int(baseline.parameters.iloc[0]),
                        'parameter_ratio_pct': 100 * own.parameters.iloc[0] / baseline.parameters.iloc[0]})
pd.DataFrame(paired).to_csv(ASSETS / '图2_逐种子相对降幅.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(effects).to_csv(ASSETS / '图2_均值与标准差.csv', index=False, encoding='utf-8-sig')
assert len(paired) == 32 and len(effects) == 4
audit = {'metric_files_verified': 48, 'prediction_archives_verified': 48, 'new_training_runs': 10,
         'all_seeds': list(range(42, 50)), 'all_test_targets_identical_within_dataset': True,
         'all_predictions_finite': True, 'all_metrics_recomputed_from_predictions': True,
         'no_rows_excluded': True, 'original_data_code_and_metrics_unchanged': True,
         'summary': summary, 'effects': effects, 'assets': str(ASSETS)}
(QA / 'data_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(audit, ensure_ascii=False))
