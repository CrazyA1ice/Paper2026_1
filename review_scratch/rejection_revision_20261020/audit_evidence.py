from pathlib import Path
import json, csv, statistics, math, sys, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RES = ROOT / 'abilene_forecasting/results'
T7 = 2.3646242515927844

def stats(values):
    x = list(map(float, values))
    avg = statistics.mean(x)
    sd = statistics.stdev(x)
    half = T7 * sd / math.sqrt(len(x))
    return dict(mean=avg, sd=sd, ci95=[avg-half, avg+half])

def read_metric(folder):
    return json.loads((folder/'metrics.json').read_text(encoding='utf8'))

def prediction_metric(folder):
    a = np.load(folder/'predictions.npz')
    predkey = next(k for k in ['prediction', 'predictions', 'pred'] if k in a.files)
    truekey = next(k for k in ['truth', 'true', 'targets'] if k in a.files)
    p, y = a[predkey].astype(np.float64), a[truekey].astype(np.float64)
    return float(np.mean((p-y)**2)), float(np.mean(np.abs(p-y))), y

def main():
    audit = {'source': str(ROOT/'word_output/基于自适应多尺度加权的多变量网络流量预测方法.docx'),
             'datasets': {}, 'h12': {}, 'h24': {}, 'timing': {}}
    audit['source_sha256'] = hashlib.sha256(Path(audit['source']).read_bytes()).hexdigest()
    for ds in ['abilene', 'geant']:
        arr = np.load(ROOT/f'abilene_forecasting/data/processed/{ds}_1hour.npz')
        shapes = {k: list(arr[k].shape) for k in ['train', 'val', 'test']}
        audit['datasets'][ds] = {'shapes': shapes,
            'train_equivalent_days': shapes['train'][0]/24,
            'all_equivalent_days': sum(shapes[k][0] for k in shapes)/24}
        values = {}
        for h in [12, 24]:
            root = RES/'horizon12_global_vs_router'/ds if h == 12 else RES/ds
            models = ['dlinear_scale_global', 'dlinear_scale'] if h == 12 else ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router', 'dlinear_scale', 'lightts']
            for model in models:
                metrics, maes, times = [], [], []
                seeds = range(42,45) if model == 'lightts' else range(42,50)
                for seed in seeds:
                    folder = root/f'{model}_seed{seed}'
                    if h == 24 and model == 'dlinear_scale_global':
                        folder = RES/'global_weight_ablation'/ds/f'{model}_seed{seed}'
                    if h == 24 and model == 'dlinear_scale_constant_router':
                        folder = RES/'constant_router_ablation'/ds/f'{model}_seed{seed}'
                    m = read_metric(folder)
                    assert m['input_len'] == 96 and m['pred_len'] == h
                    assert m['split_rows'] == {k: shapes[k][0] for k in shapes}
                    assert m['split_windows'] == {k: shapes[k][0]-96-h+1 for k in shapes}
                    # Recompute new-horizon evidence from the saved predictions, including identical targets.
                    if h == 12:
                        mse, mae, truth = prediction_metric(folder)
                        assert abs(mse-m['test_normalized']['mse']) < 2e-6
                        assert abs(mae-m['test_normalized']['mae']) < 2e-6
                        if model == 'dlinear_scale_global':
                            values[seed] = truth
                        else:
                            assert np.array_equal(values[seed], truth)
                    metrics.append(m['test_normalized']['mse'])
                    maes.append(m['test_normalized']['mae'])
                    times.append(m['elapsed_seconds'])
                dest = audit[f'h{h}'].setdefault(ds, {})
                dest[model] = {'mse': stats(metrics) if len(metrics)==8 else {'mean':statistics.mean(metrics),'sd':statistics.stdev(metrics)},
                    'mae': {'mean':statistics.mean(maes),'sd':statistics.stdev(maes)},
                    'elapsed_pipeline_seconds': {'mean':statistics.mean(times),'sd':statistics.stdev(times)},
                    'parameters': m['parameters'], 'mse_by_seed':metrics, 'mae_by_seed':maes}
            dest = audit[f'h{h}'][ds]
            router = dest['dlinear_scale']['mse_by_seed']
            global_ = dest['dlinear_scale_global']['mse_by_seed']
            reduction = [(g-r)/g*100 for g,r in zip(global_,router)]
            dest['router_vs_global'] = {**stats(reduction), 'wins':sum(r<g for r,g in zip(router,global_))}
            if h == 24:
                for base in ['dlinear','lightts']:
                    b=dest[base]['mse_by_seed'][:3]
                    r=router[:3]
                    dest[f'router_vs_{base}_three_seed_pct']=statistics.mean((x-y)/x*100 for x,y in zip(b,r))
        for label in ['inference_benchmark_cuda_events','inference_benchmark_cpu1']:
            rows = list(csv.DictReader((RES/label/'inference_benchmark_summary.csv').open(encoding='utf8')))
            meta = json.loads((RES/label/'benchmark_metadata.json').read_text(encoding='utf8'))
            audit['timing'][label] = {'rows':rows,'metadata':meta}
    (OUT/'verified_evidence.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:audit[k] for k in ['source_sha256','datasets']},ensure_ascii=False))
    for h in [12,24]:
        for ds in ['abilene','geant']:
            a = audit[f'h{h}'][ds]
            print(h, ds, 'router vs global', a['router_vs_global'])
            if h==12:
                for m in ['dlinear_scale_global','dlinear_scale']:
                    print(m, a[m]['mse'], a[m]['parameters'])
    print('Evidence verified and saved')

if __name__ == '__main__':
    main()
