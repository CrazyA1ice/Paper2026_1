from pathlib import Path
import json, numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
records=[]
for ds in ['abilene','geant']:
    models=['dlinear','dlinear_scale_static','dlinear_scale_constant_router','dlinear_scale']
    arrays={}
    for model in models:
        prefix='constant_router_ablation' if model.endswith('constant_router') else ''
        path=ROOT/'abilene_forecasting/results'/prefix/ds/f'{model}_seed42'/'predictions.npz'
        with np.load(path) as z:
            arrays[model]=(z['prediction'].copy(),z['truth'].copy())
    truth=arrays['dlinear_scale'][1]
    assert all(np.array_equal(v[1],truth) for v in arrays.values())
    channel_sd=truth.std(axis=(0,1))
    eligible=np.flatnonzero(channel_sd>0)
    channel=int(eligible[np.argmin(np.abs(channel_sd[eligible]-np.quantile(channel_sd[eligible],.75)))])
    variation=np.abs(np.diff(truth[:,:,channel],axis=1)).mean(axis=1)
    windows=[int(np.argmin(np.abs(variation-np.quantile(variation,q)))) for q in [.5,.9]]
    for window in windows:
        errors={m:float(np.mean((v[0][window,:,channel]-truth[window,:,channel])**2)) for m,v in arrays.items()}
        records.append({'dataset':ds,'OD_one_based':channel+1,'window_one_based':window+1,'mse':errors,
                        'adaptive_better_all':all(errors['dlinear_scale']<errors[m] for m in models[:-1])})
    full_metrics={m:float(np.mean((v[0]-truth)**2)) for m,v in arrays.items()}
    print(ds,'seed42 full MSE',full_metrics)
(OUT/'figure4_audit.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
