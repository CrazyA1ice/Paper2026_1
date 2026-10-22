from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
PROJECT = ROOT / 'abilene_forecasting'
PYTHON = PROJECT / '.venv/Scripts/python.exe'
LOGS = PROJECT / 'logs/lightts_8seeds_20261022'
LOGS.mkdir(parents=True, exist_ok=True)
DATASETS = ['abilene', 'geant']
SEEDS = list(range(45, 50))
EXPECTED = {'input_len': 96, 'pred_len': 24, 'batch_size': 16,
            'epochs_max': 50, 'patience': 10, 'learning_rate': .0001}
protected = {}
for dataset in DATASETS:
    for model, seeds in [('dlinear', range(42, 50)), ('dlinear_scale', range(42, 50)), ('lightts', range(42, 45))]:
        for seed in seeds:
            path = PROJECT / f'results/{dataset}/{model}_seed{seed}/metrics.json'
            metrics = json.loads(path.read_text(encoding='utf-8'))
            assert metrics['model'] == model and metrics['seed'] == seed
            assert metrics['input_len'] == 96 and metrics['pred_len'] == 24
            if model == 'lightts':
                assert all(metrics[k] == v for k, v in EXPECTED.items())
            protected[str(path)] = sha256(path.read_bytes()).hexdigest()
    data = PROJECT / f'data/processed/{dataset}_1hour.npz'
    protected[str(data)] = sha256(data.read_bytes()).hexdigest()
for relative in ['train.py', 'src/models.py', 'src/data.py', 'src/lightts_adapter.py', 'external/lightts/models/LightTS.py']:
    path = PROJECT / relative
    protected[str(path)] = sha256(path.read_bytes()).hexdigest()
manifest = {'datasets': DATASETS, 'seeds_to_add': SEEDS, 'new_runs': 10,
            'fixed_training_configuration': EXPECTED, 'workers': 2,
            'protected_files_sha256': protected, 'selection_rule': 'all prespecified seeds; no exclusions'}
(QA / 'training_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def run(dataset, seed):
    directory = PROJECT / f'results/{dataset}/lightts_seed{seed}'
    assert not directory.exists(), f'Refusing to overwrite {directory}'
    log = LOGS / f'{dataset}_lightts_seed{seed}.log'
    args = [str(PYTHON), '-u', 'train.py', '--dataset', dataset, '--model', 'lightts',
            '--seed', str(seed), '--input-len', '96', '--pred-len', '24',
            '--epochs', '50', '--patience', '10', '--batch-size', '16', '--learning-rate', '0.0001']
    print(json.dumps({'event': 'started', 'dataset': dataset, 'seed': seed}, ensure_ascii=False), flush=True)
    started = time.monotonic()
    with log.open('w', encoding='utf-8') as handle:
        process = subprocess.run(args, cwd=PROJECT, stdout=handle, stderr=subprocess.STDOUT, check=True)
    path = directory / 'metrics.json'
    metrics = json.loads(path.read_text(encoding='utf-8'))
    assert all(metrics[k] == v for k, v in EXPECTED.items())
    reference = json.loads((PROJECT / f'results/{dataset}/lightts_seed42/metrics.json').read_text(encoding='utf-8'))
    for key in ['model_config', 'n_channels', 'split_rows', 'split_windows', 'parameters', 'data_feature', 'data_aggregation']:
        assert metrics[key] == reference[key], (dataset, seed, key)
    assert (directory / 'best_model.pt').exists() and (directory / 'predictions.npz').exists()
    result = {'event': 'completed', 'dataset': dataset, 'seed': seed,
              'wall_seconds': time.monotonic() - started, 'metrics': metrics['test_normalized'],
              'metrics_sha256': sha256(path.read_bytes()).hexdigest(), 'log': str(log)}
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


completed = []
jobs = [(dataset, seed) for seed in SEEDS for dataset in DATASETS]
with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(run, dataset, seed) for dataset, seed in jobs]
    for future in as_completed(futures):
        completed.append(future.result())
        (QA / 'training_progress.json').write_text(json.dumps({'completed': completed, 'total': 10}, ensure_ascii=False, indent=2), encoding='utf-8')
assert len(completed) == 10
assert all(sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in protected.items())
(QA / 'training_complete.json').write_text(json.dumps({'new_runs': 10, 'all_protected_files_unchanged': True,
    'all_runs_completed': True, 'runs': completed}, ensure_ascii=False, indent=2), encoding='utf-8')
print('ALL TEN NEW RUNS COMPLETE; ORIGINAL DATA, CODE AND METRICS UNCHANGED', flush=True)
