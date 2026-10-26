from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import csv
import json
import sys
import time

import numpy as np
import tables

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
PROJECT = ROOT/'abilene_forecasting'
OUT = ROOT/'paper_template/长春工程学院学报(自然科学版)/缺失真值评分复核_20261023'
OUT.mkdir(parents=True, exist_ok=True)
PAPER = ROOT/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV9_投稿规范修订稿.docx'
PAPER_SHA = '63e070311f9b14d291a98a8a0d3d5569049fd566cb371f787275653661863321'
assert sha256(PAPER.read_bytes()).hexdigest() == PAPER_SHA
MODELS = ['dlinear','lightts','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
SEEDS = list(range(42,50))
NAMES = {'dlinear':'DLinear','lightts':'LightTS','dlinear_scale_static':'固定等权多尺度',
         'dlinear_scale_global':'全局可学习权重','dlinear_scale_constant_router':'恒定输入路由','dlinear_scale':'本文方法'}
previous = json.loads((ROOT/'review_scratch/results_explanation_20261022/evidence_audit.json').read_text(encoding='utf-8'))
metric_sha = {r['path']:r['sha256'] for r in previous['input_metrics']}
data_provenance = json.loads((ROOT/'review_scratch/v9_selected_20261023/data_metadata_raw.json').read_text(encoding='utf-8'))
data_sha = {r['path']:r['sha256'] for r in data_provenance['data']}
source_inputs = []
records = []
metadata = []

def run_path(dataset, model, seed):
    if model=='dlinear_scale_global':
        return PROJECT/'results/global_weight_ablation'/dataset/f'{model}_seed{seed}'
    if model=='dlinear_scale_constant_router':
        return PROJECT/'results/constant_router_ablation'/dataset/f'{model}_seed{seed}'
    return PROJECT/'results'/dataset/f'{model}_seed{seed}'

def remember(path, content=None):
    source_inputs.append({'path':str(path),'sha256':sha256(path.read_bytes() if content is None else content).hexdigest()})

def add_row(dataset,model,seed,case,error,mask,metrics=('mse','mae')):
    selected = error[mask]
    if not selected.size:
        return None
    r = {'dataset':dataset,'model':model,'seed':seed,'case':case,'n_target_values':int(selected.size)}
    if 'mse' in metrics:r['mse']=float(np.mean(selected**2))
    if 'mae' in metrics:r['mae']=float(np.mean(np.abs(selected)))
    if 'aue' in metrics:r['aue']=float(np.mean(np.maximum(-selected,0)))
    records.append(r)
    return r

# Fix all scoring rules before reading any model prediction. No case depends on errors.
protocol = {
    'primary':'Keep the original hourly grid, trained models, normalization and all test origins. Score only finite nonnegative original observations at future target positions. Genuine observed zeros remain valid.',
    'complete_windows':'Sensitivity analysis. Retain only windows whose 96 h input and 24 h target are entirely observed and valid; identical window set for every model.',
    'complete_channel_windows':'Additional sensitivity analysis, applied to both datasets. For each OD variable retain a window only when that variable has a fully observed 96 h input and 24 h target. Other variables may still be incomplete. Empty whole-matrix cases are explicitly unavailable, never scored as zero.',
    'high_same_threshold':'Retain the original training-completed-series per-channel q90; mask unobserved test targets.',
    'high_observed_training_q90':'Sensitivity analysis. Compute per-channel q90 using only valid observed training values in the existing normalization, and score valid observed high targets.',
    'replication':'All seeds 42--49. Report seed means and sample SD. Percentage reductions are calculated within matched seed then averaged. Overlapping forecast targets are not independent repetitions.',
    'training':'No retraining and no checkpoint reselection. This isolates scoring changes; it does not estimate the effect of changing training imputation or validation selection.'}
(OUT/'复核口径.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')

for dataset,label,feature in [('abilene','Abilene','matrix_avg_realOD'),('geant','GEANT','matrix_avg_bandwidth_kbps')]:
    h5 = PROJECT/f'data/raw/tszoo/databases/{label}/{label}-matrix-backbone_network-1_hour.h5'
    assert sha256(h5.read_bytes()).hexdigest()==data_sha[str(h5)]
    remember(h5)
    npz = PROJECT/f'data/processed/{dataset}_1hour.npz'
    remember(npz)
    with np.load(npz) as data:
        train,test = data['train'].copy(),data['test'].copy()
        active = data['active_indices'].copy()
        original_shape = data['original_shape'].copy()
    with tables.open_file(h5,'r') as f:
        times = f.root.times.times_1_hour.read()
        aggregation = f.root.backbone_network.agg_1_hour.read()
        matrix = f.get_node('/backbone_network/'+feature).read()
    assert len(times)==original_shape[0]
    assert np.all(np.diff(times['time'])==3600)
    present = np.zeros(len(times),dtype=bool)
    present[aggregation['id_time']]=True
    raw = matrix[aggregation['id_'+feature]].reshape(len(aggregation),-1)[:,active]
    cell_valid = np.isfinite(raw)&(raw>=0)
    valid = np.zeros((len(times),len(active)),dtype=bool)
    valid[aggregation['id_time']]=cell_valid
    train_end=int(len(times)*.6);test_start=int(len(times)*.8)
    train_valid=valid[:train_end];test_valid=valid[test_start:]
    assert train_valid.shape==train.shape and test_valid.shape==test.shape
    L,H=96,24
    reference = np.stack([test[i+L:i+L+H] for i in range(len(test)-L-H+1)])
    observed = np.stack([test_valid[i+L:i+L+H] for i in range(len(reference))])
    complete = np.array([test_valid[i:i+L+H].all() for i in range(len(reference))])
    complete_channel = np.stack([test_valid[i:i+L+H].all(axis=0) for i in range(len(reference))])
    full = np.ones(reference.shape,dtype=bool)
    clean = np.broadcast_to(complete[:,None,None],reference.shape)
    channel_clean = np.broadcast_to(complete_channel[:,None,:],reference.shape)
    q90 = np.quantile(train.astype(np.float64),.9,axis=0)
    q90_observed = np.nanquantile(np.where(train_valid,train,np.nan).astype(np.float64),.9,axis=0)
    high_original = reference>q90[None,None,:]
    high_observed = high_original&observed
    high_new_q90 = (reference>q90_observed[None,None,:])&observed
    assert np.array_equal(high_original,high_observed),'Unobserved high targets require a separate correction.'
    masks = {'original_all':full,'observed_targets':observed,'complete_windows':clean,
             'complete_channel_windows':channel_clean,
             'high_original_threshold':high_original,'high_observed_same_threshold':high_observed,
             'high_observed_training_q90':high_new_q90,
             'high_complete_windows_same_threshold':high_observed&clean}
    info = {'dataset':dataset,'original_windows':len(reference),'complete_windows':int(complete.sum()),
        'original_target_values':int(reference.size),'observed_target_values':int(observed.sum()),
        'excluded_target_values':int((~observed).sum()),
        'missing_whole_test_hours':int((~present[test_start:]).sum()),
        'nonfinite_cells_in_present_rows':int((~np.isfinite(raw)).sum()),
        'negative_cells_in_present_rows':int((np.isfinite(raw)&(raw<0)).sum()),
        'valid_cells_in_train_val_test':[int(valid[a:b].sum()) for a,b in [(0,train_end),(train_end,test_start),(test_start,len(valid))]],
        'nonfinite_active_cells_in_train_val_test':[int((~cell_valid)[(aggregation['id_time']>=a)&(aggregation['id_time']<b)].sum()) for a,b in [(0,train_end),(train_end,test_start),(test_start,len(valid))]],
        'original_high_targets':int(high_original.sum()),'observed_training_q90_high_targets':int(high_new_q90.sum()),
        'excluded_unobserved_high_targets':int((high_original&~observed).sum()),
        'original_and_observed_train_q90_max_absolute_difference':float(np.max(np.abs(q90-q90_observed))),
        'case_target_counts':{case:int(mask.sum()) for case,mask in masks.items()}}
    metadata.append(info)
    print('DATA',json.dumps(info,ensure_ascii=False),flush=True)
    for model in MODELS:
        for seed in SEEDS:
            folder=run_path(dataset,model,seed)
            metric_path=folder/'metrics.json'
            metric_bytes=metric_path.read_bytes()
            assert sha256(metric_bytes).hexdigest()==metric_sha[str(metric_path)]
            original=json.loads(metric_bytes)
            remember(metric_path,metric_bytes)
            prediction_path=folder/'predictions.npz'
            remember(prediction_path)
            with np.load(prediction_path) as stored:
                prediction=stored['prediction']
                assert np.array_equal(stored['truth'],reference),prediction_path
            assert prediction.shape==reference.shape and np.isfinite(prediction).all()
            error=prediction.astype(np.float64)-reference.astype(np.float64)
            old_row=add_row(dataset,model,seed,'original_all',error,full)
            for metric in ['mse','mae']:
                assert np.isclose(old_row[metric],original['test_normalized'][metric],rtol=2e-6,atol=2e-7),(prediction_path,metric)
            for case in ['observed_targets','complete_windows','complete_channel_windows']:
                add_row(dataset,model,seed,case,error,masks[case])
            if (~observed).any():
                missing_row=add_row(dataset,model,seed,'unobserved_imputed_targets_diagnostic',error,~observed)
                weight=observed.mean()
                good=next(r for r in reversed(records) if r['case']=='observed_targets')
                for metric in ['mse','mae']:
                    assert np.isclose(old_row[metric],weight*good[metric]+(1-weight)*missing_row[metric],rtol=1e-12)
            for case in ['high_original_threshold','high_observed_same_threshold','high_observed_training_q90','high_complete_windows_same_threshold']:
                add_row(dataset,model,seed,case,error,masks[case],metrics=('mae','aue'))
            del prediction,error
        print('SCORED',dataset,model,flush=True)
    (QA/f'{dataset}_checkpoint.json').write_text(json.dumps({'metadata':info,'records':[r for r in records if r['dataset']==dataset]},ensure_ascii=False,indent=2),encoding='utf-8')

def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)

grouped=defaultdict(list)
for row in records:grouped[(row['dataset'],row['case'],row['model'])].append(row)
summary=[]
for (dataset,case,model),group in grouped.items():
    assert sorted(r['seed'] for r in group)==SEEDS
    row={'dataset':dataset,'case':case,'model':model,'n_seeds':8,'n_target_values':group[0]['n_target_values']}
    assert len({r['n_target_values'] for r in group})==1
    for metric in ['mse','mae','aue']:
        if metric in group[0]:
            values=np.array([r[metric] for r in sorted(group,key=lambda r:r['seed'])])
            row[metric+'_mean']=float(values.mean());row[metric+'_sd']=float(values.std(ddof=1))
    summary.append(row)
effects=[]
for dataset in ['abilene','geant']:
    for case in dict.fromkeys(r['case'] for r in records if r['dataset']==dataset):
        ours={r['seed']:r for r in grouped[(dataset,case,'dlinear_scale')]}
        for model in MODELS[:-1]:
            control={r['seed']:r for r in grouped[(dataset,case,model)]}
            for metric in ['mse','mae','aue']:
                if metric not in ours[42]:continue
                changes=np.array([100*(control[s][metric]-ours[s][metric])/control[s][metric] for s in SEEDS])
                effects.append({'dataset':dataset,'case':case,'baseline':model,'metric':metric,
                    'mean_reduction_pct':float(changes.mean()),'sample_sd_pct':float(changes.std(ddof=1)),
                    'seed_wins':int((changes>0).sum()),'n_seeds':8,
                    'minimum_reduction_pct':float(changes.min()),'maximum_reduction_pct':float(changes.max())})

write_csv(OUT/'逐种子重算指标.csv',records)
write_csv(OUT/'各口径均值与标准差.csv',summary)
write_csv(OUT/'逐种子配对降幅汇总.csv',effects)
(QA/'summary.json').write_text(json.dumps({'metadata':metadata,'summary':summary,'effects':effects},ensure_ascii=False,indent=2),encoding='utf-8')

# Old high-demand metrics must reproduce, and the primary observed-target mask must leave them unchanged.
with (PROJECT/'results/high_demand_analysis/per_seed.csv').open(encoding='utf-8-sig',newline='') as f:
    old_high=list(csv.DictReader(f))
for old in old_high:
    key=(old['dataset'],'high_original_threshold',old['model'])
    found=next(r for r in grouped[key] if r['seed']==int(old['seed']))
    assert abs(found['mae']-float(old['mae']))<1e-12
    assert abs(found['aue']-float(old['mean_shortfall']))<1e-12

# Check identical observation masks across all models. Whole-matrix clean cases can be empty.
for dataset in ['abilene','geant']:
    for case in ['original_all','observed_targets','complete_windows','high_observed_training_q90']:
        counts={r['n_target_values'] for r in records if r['dataset']==dataset and r['case']==case}
        assert len(counts)<=1

weekly=PROJECT/'results/long_horizon_20261021/per_seed_scores.csv'
assert sha256(weekly.read_bytes()).hexdigest()==previous['weekly_csv_sha256']
remember(weekly)
# Re-read source hashes at the end; no original data, result or manuscript is mutated.
for item in source_inputs:
    assert sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
assert sha256(PAPER.read_bytes()).hexdigest()==PAPER_SHA
provenance={'manuscript_unchanged':True,'manuscript_sha256':PAPER_SHA,'no_retraining':True,
    'all_models_all_8_seeds_scored':True,'original_metrics_reproduced':True,'original_high_metrics_reproduced':True,
    'all_original_inputs_and_results_unchanged':True,
    'weekly_recalculation_pending':True,
    'protocol':protocol,'metadata':metadata,'sources':source_inputs}
(QA/'audit.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'核验记录.json').write_text(json.dumps({k:v for k,v in provenance.items() if k!='sources'},ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE',OUT,flush=True)
