"""Fixed 96-hour-input comparison at 24/48/96/168-hour forecast horizons."""
from __future__ import annotations

import argparse
import contextlib
import gc
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/long_horizon_20261021'
DATASETS=('geant','abilene')
MODELS=('dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale')
TRAIN_ORDER=('dlinear','dlinear_scale','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router')
HORIZONS=(24,48,96,168)
SEEDS=tuple(range(42,50))
L=96
LABELS={'dlinear':'DLinear','dlinear_scale_static':'固定等权','dlinear_scale_global':'全局可学习权重','dlinear_scale_constant_router':'恒定输入路由','dlinear_scale':'本文方法'}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')

def archived(ds,model,seed):
    parent=ROOT/'results'
    if model=='dlinear_scale_global':parent=parent/'global_weight_ablation'
    if model=='dlinear_scale_constant_router':parent=parent/'constant_router_ablation'
    return parent/ds/f'{model}_seed{seed}'

def run_dir(ds,model,seed,horizon):
    return archived(ds,model,seed) if horizon==24 else OUT/f'h{horizon:03d}'/ds/f'{model}_seed{seed}'

def verify_config(record,ds,model,seed,horizon):
    expected={'dataset':ds,'model':model,'seed':seed,'input_len':96,'pred_len':horizon,'batch_size':16,'epochs_max':30,'patience':6,'learning_rate':.001,'cut_ratio':.5}
    for key,value in expected.items():assert record[key]==value,(key,record[key],value)

def jobs():
    return [{'dataset':ds,'model':model,'seed':seed,'horizon':horizon}
        for ds in DATASETS for horizon in (168,96,48) for seed in SEEDS for model in TRAIN_ORDER]

def arguments(job):
    return ['--dataset',job['dataset'],'--model',job['model'],'--seed',str(job['seed']),
        '--input-len','96','--pred-len',str(job['horizon']),'--batch-size','16','--epochs','30',
        '--patience','6','--learning-rate','0.001','--cut-ratio','0.5',
        '--output-root',str(OUT/f"h{job['horizon']:03d}")]

def init():
    OUT.mkdir(exist_ok=True)
    sources={str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'train.py',ROOT/'src/models.py',ROOT/'src/data.py',*(ROOT/f'data/processed/{ds}_1hour.npz' for ds in DATASETS)]}
    counts={}
    for ds in DATASETS:
        with np.load(ROOT/f'data/processed/{ds}_1hour.npz') as raw:
            rows={split:len(raw[split]) for split in ('train','val','test')}
            counts[ds]={'rows':rows,'channels':raw['train'].shape[1],
                'windows':{str(h):{s:n-L-h+1 for s,n in rows.items()} for h in HORIZONS},
                'common_test_origins':rows['test']-L-max(HORIZONS)+1}
            assert all(n-L-max(HORIZONS)+1>0 for n in rows.values())
        for model in MODELS:
            for seed in SEEDS:
                folder=archived(ds,model,seed)
                record=json.loads((folder/'metrics.json').read_text(encoding='utf8'))
                verify_config(record,ds,model,seed,24)
                assert (folder/'predictions.npz').stat().st_size>0
    protocol={'version':'long-horizon-20261021-v1','input_len':L,'horizons':HORIZONS,
        'datasets':DATASETS,'models':MODELS,'seeds':SEEDS,'training':{'batch_size':16,'epochs_max':30,'patience':6,'learning_rate':.001},
        'sampling':'unchanged hourly data, same chronological 6:2:2 split and training-only normalizers',
        'training_method':'call the unchanged train.main separately per configuration; independent model and optimizer; reset original seeds each run',
        'primary_scoring':'common forecast origins admitting H=168, score every target hour and OD variable inside each horizon; summarize paired seeds',
        'secondary_scoring':'all valid test origins per horizon retained for traceability',
        'primary_metrics':['normalized MSE','normalized MAE'],
        'improvement':'mean across paired seeds of 100*(baseline-proposed)/baseline; retain negative values',
        'trend':'descriptive change in the same relative improvement over four fixed horizons; no guaranteed monotonicity',
        'random_unit':'training seed; overlapping forecast targets are not independent experimental replicates',
        'h24_reuse':'80 complete archived model-seed runs, rescored on common origins without retraining',
        'new_runs':240,'parallel_workers':2,'source_sha256':sources,'data_readiness':counts}
    path=OUT/'protocol.json'
    if path.exists():assert json.loads(path.read_text(encoding='utf8'))==json.loads(json.dumps(protocol))
    else:write_json(path,protocol)
    write_json(OUT/'jobs.json',[{**job,'arguments':arguments(job)} for job in jobs()])
    print(json.dumps({'new_runs':240,'archived_runs':80,'data':counts,'output':str(OUT)},ensure_ascii=False),flush=True)

def worker(worker_id):
    import torch
    import train
    from src.models import build_model
    assert torch.cuda.is_available(),'Expected the existing CUDA runtime for this experiment.'
    protocol=json.loads((OUT/'protocol.json').read_text(encoding='utf8'))
    for rel,sha in protocol['source_sha256'].items():assert digest(ROOT/rel)==sha,rel
    # Validate changed output lengths with the same unmodified model classes.
    with torch.no_grad():
        x=torch.zeros(2,96,144,device='cuda')
        for horizon in (48,96,168):
            for model in MODELS:
                candidate=build_model(model,96,horizon).to('cuda')
                result=train.split_model_output(candidate(x))[0]
                assert result.shape==(2,horizon,144) and torch.isfinite(result).all()
        del candidate,result,x
    gc.collect();torch.cuda.empty_cache()
    assigned=jobs()[worker_id::2]
    state_path=OUT/f'worker_{worker_id}.json'
    state={'worker':worker_id,'pid':os.getpid(),'device':torch.cuda.get_device_name(0),'started_unix':time.time(),'assigned':len(assigned),'done':0,'status':'running'}
    write_json(state_path,state)
    for job in assigned:
        folder=run_dir(job['dataset'],job['model'],job['seed'],job['horizon'])
        complete=folder/'completion.json'
        if complete.exists():
            record=json.loads((folder/'metrics.json').read_text(encoding='utf8'))
            verify_config(record,job['dataset'],job['model'],job['seed'],job['horizon'])
            assert (folder/'predictions.npz').stat().st_size>0
            state['done']+=1
            continue
        assert not (folder/'metrics.json').exists(),f'Incomplete prior run needs review: {folder}'
        folder.mkdir(parents=True,exist_ok=True)
        state.update(current=job,current_started_unix=time.time(),log=str(folder/'training.log'))
        write_json(state_path,state)
        print(json.dumps({'event':'start','worker':worker_id,**job},ensure_ascii=False),flush=True)
        try:
            sys.argv=[str(ROOT/'train.py'),*arguments(job)]
            with (folder/'training.log').open('w',encoding='utf8',buffering=1) as log:
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):train.main()
            record=json.loads((folder/'metrics.json').read_text(encoding='utf8'))
            verify_config(record,job['dataset'],job['model'],job['seed'],job['horizon'])
            assert (folder/'predictions.npz').stat().st_size>0
            write_json(complete,{'job':job,'completed_unix':time.time(),'metrics_sha256':digest(folder/'metrics.json'),'predictions_sha256':digest(folder/'predictions.npz')})
        except Exception as exc:
            state.update(status='failed',error=repr(exc));write_json(state_path,state)
            raise
        gc.collect();torch.cuda.empty_cache()
        state['done']+=1
        state['last_completed']=job
        state['updated_unix']=time.time()
        write_json(state_path,state)
        print(json.dumps({'event':'complete','worker':worker_id,'done':state['done'],'assigned':len(assigned),**job,'training_seconds':record['elapsed_seconds']},ensure_ascii=False),flush=True)
    state.update(status='complete',finished_unix=time.time());write_json(state_path,state)

def score_one(ds,model,seed,horizon):
    folder=run_dir(ds,model,seed,horizon)
    path=folder/'predictions.npz'
    cache=OUT/'analysis_cache'/f'{ds}_{model}_s{seed}_h{horizon}.json'
    if cache.exists():return json.loads(cache.read_text(encoding='utf8'))
    metadata=json.loads((folder/'metrics.json').read_text(encoding='utf8'))
    verify_config(metadata,ds,model,seed,horizon)
    with np.load(ROOT/f'data/processed/{ds}_1hour.npz') as raw:test=raw['test']
    common=len(test)-L-max(HORIZONS)+1
    with np.load(path) as raw:
        prediction=raw['prediction'];truth=raw['truth']
    expected_shape=(len(test)-L-horizon+1,horizon,test.shape[1])
    assert prediction.shape==truth.shape==expected_shape
    sums={'all':[0.,0.,0],'common':[0.,0.,0]}
    for start in range(0,len(prediction),16):
        stop=min(start+16,len(prediction))
        reference=np.stack([test[i+L:i+L+horizon] for i in range(start,stop)])
        assert np.array_equal(reference,truth[start:stop])
        error=prediction[start:stop].astype(np.float64)-reference.astype(np.float64)
        assert np.isfinite(error).all()
        for key,part in [('all',error),('common',error[:max(0,min(stop,common)-start)])]:
            sums[key][0]+=float(np.square(part).sum())
            sums[key][1]+=float(np.abs(part).sum())
            sums[key][2]+=part.size
    row={'dataset':ds,'model':model,'seed':seed,'horizon':horizon,'input_len':L,'n_common_origins':common,'n_all_origins':len(prediction),'parameters':metadata['parameters'],'training_seconds':metadata['elapsed_seconds'],'prediction_sha256':digest(path)}
    for key,(squared,absolute,count) in sums.items():
        assert count>0
        row[key+'_mse']=squared/count;row[key+'_mae']=absolute/count
    assert np.isclose(row['all_mse'],metadata['test_normalized']['mse'],rtol=1e-5)
    cache.parent.mkdir(exist_ok=True);write_json(cache,row)
    return row

def analyze(allow_partial):
    rows=[];missing=[]
    for ds in DATASETS:
        for h in HORIZONS:
            for model in MODELS:
                for seed in SEEDS:
                    folder=run_dir(ds,model,seed,h)
                    if h!=24 and not (folder/'completion.json').exists():missing.append((ds,h,model,seed));continue
                    rows.append(score_one(ds,model,seed,h))
    if missing and not allow_partial:raise RuntimeError(f'{len(missing)} runs not yet complete')
    frame=pd.DataFrame(rows)
    frame.to_csv(OUT/'per_seed_scores.csv',index=False,encoding='utf-8-sig')
    summary=[];paired=[]
    for (ds,h,model),group in frame.groupby(['dataset','horizon','model'],sort=False):
        if sorted(group.seed.tolist())!=list(SEEDS):continue
        record={'dataset':ds,'horizon':int(h),'model':model,'n_seeds':8,'n_common_origins':int(group.n_common_origins.iloc[0])}
        for metric in ['common_mse','common_mae','all_mse','all_mae']:
            record[metric+'_mean']=group[metric].mean();record[metric+'_sd']=group[metric].std(ddof=1)
        summary.append(record)
    for ds in DATASETS:
        for h in HORIZONS:
            ours=frame[(frame.dataset==ds)&(frame.horizon==h)&(frame.model=='dlinear_scale')].sort_values('seed')
            if ours.seed.tolist()!=list(SEEDS):continue
            for model in MODELS[:-1]:
                baseline=frame[(frame.dataset==ds)&(frame.horizon==h)&(frame.model==model)].sort_values('seed')
                if baseline.seed.tolist()!=list(SEEDS):continue
                for metric in ['mse','mae']:
                    b=baseline['common_'+metric].to_numpy();p=ours['common_'+metric].to_numpy()
                    reduction=100*(b-p)/b
                    paired.append({'dataset':ds,'horizon':h,'baseline':model,'metric':metric,'n_seeds':8,'mean_reduction_pct':float(reduction.mean()),'reduction_sd_pct':float(reduction.std(ddof=1)),'seed_wins':int((reduction>0).sum()),'baseline_mean':float(b.mean()),'proposed_mean':float(p.mean())})
    summary_frame=pd.DataFrame(summary);paired_frame=pd.DataFrame(paired)
    summary_frame.to_csv(OUT/'summary.csv',index=False,encoding='utf-8-sig')
    paired_frame.to_csv(OUT/'paired_reductions.csv',index=False,encoding='utf-8-sig')
    trends=[]
    if not paired_frame.empty:
        for (ds,base,metric),part in paired_frame.groupby(['dataset','baseline','metric']):
            part=part.sort_values('horizon')
            if part.horizon.tolist()!=list(HORIZONS):continue
            values=part.mean_reduction_pct.to_numpy()
            trends.append({'dataset':ds,'baseline':base,'metric':metric,'horizons':list(HORIZONS),'mean_reductions_pct':values.tolist(),'monotonically_increasing':bool(np.all(np.diff(values)>=0)),'change_168_minus_24_percentage_points':float(values[-1]-values[0])})
    write_json(OUT/'trend_check.json',trends)
    write_json(OUT/'analysis_status.json',{'complete':not missing,'scored_runs':len(rows),'missing_runs':len(missing),'complete_model_horizon_groups':len(summary),'trend_groups':len(trends),'updated_unix':time.time()})
    print(json.dumps({'scored_runs':len(rows),'missing_runs':len(missing),'summary_rows':len(summary),'trend_groups':len(trends)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    os.chdir(ROOT)
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['init','worker','analyze'])
    parser.add_argument('--worker-id',type=int,choices=[0,1],default=0)
    parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args()
    if args.mode=='init':init()
    elif args.mode=='worker':worker(args.worker_id)
    else:analyze(args.allow_partial)
