from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import csv
import json
import sys

import numpy as np
import tables

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
PROJECT=ROOT/'abilene_forecasting'
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/缺失真值评分复核_20261023'
MODELS=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
SEEDS=list(range(42,50))
H,L=168,96
PAPER=ROOT/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV9_投稿规范修订稿.docx'
PAPER_SHA='63e070311f9b14d291a98a8a0d3d5569049fd566cb371f787275653661863321'
assert sha256(PAPER.read_bytes()).hexdigest()==PAPER_SHA

def digest(path):
    h=sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

sources=[]
def remember(path,expected=None):
    h=digest(path)
    if expected is not None:assert h==expected,path
    sources.append({'path':str(path),'sha256':h})

with np.load(PROJECT/'data/processed/geant_1hour.npz') as data:
    test=data['test'].copy();active=data['active_indices'].copy();n=int(data['original_shape'][0])
h5=PROJECT/'data/raw/tszoo/databases/GEANT/GEANT-matrix-backbone_network-1_hour.h5'
with tables.open_file(h5,'r') as f:
    agg=f.root.backbone_network.agg_1_hour.read()
    raw=f.root.backbone_network.matrix_avg_bandwidth_kbps.read()
valid=np.zeros((n,len(active)),dtype=bool)
cells=raw[agg['id_matrix_avg_bandwidth_kbps']].reshape(len(agg),-1)[:,active]
valid[agg['id_time']]=np.isfinite(cells)&(cells>=0)
test_valid=valid[int(n*.8):]
remember(h5);remember(PROJECT/'data/processed/geant_1hour.npz')
count=len(test)-L-H+1
complete_channel=np.stack([test_valid[i:i+L+H].all(axis=0) for i in range(count)])
complete_windows=complete_channel.all(axis=1)
print('WEEKLY_MASK',json.dumps({'windows':count,'complete_global_windows':int(complete_windows.sum()),
    'complete_channel_windows':int(complete_channel.sum())},ensure_ascii=False),flush=True)
old_csv=PROJECT/'results/long_horizon_20261021/per_seed_scores.csv'
remember(old_csv)
with old_csv.open(encoding='utf-8-sig',newline='') as f:
    previous={(r['model'],int(r['seed'])):r for r in csv.DictReader(f) if r['dataset']=='geant' and int(r['horizon'])==168}
assert len(previous)==40
records=[]
for model in MODELS:
    for seed in SEEDS:
        folder=PROJECT/f'results/long_horizon_20261021/h168/geant/{model}_seed{seed}'
        completion=json.loads((folder/'completion.json').read_text(encoding='utf-8'))
        path=folder/'predictions.npz'
        remember(path,completion['predictions_sha256'])
        remember(folder/'metrics.json',completion['metrics_sha256'])
        assert sources[-2]['sha256']==previous[(model,seed)]['prediction_sha256']
        with np.load(path) as stored:
            prediction=stored['prediction'];truth=stored['truth']
        assert prediction.shape==truth.shape==(count,H,test.shape[1])
        accum={case:[0.,0.,0] for case in ['original_all','observed_targets','complete_channel_windows','unobserved_imputed_targets_diagnostic']}
        for start in range(0,count,16):
            stop=min(start+16,count)
            reference=np.stack([test[i+L:i+L+H] for i in range(start,stop)])
            assert np.array_equal(reference,truth[start:stop])
            error=prediction[start:stop].astype(np.float64)-reference.astype(np.float64)
            assert np.isfinite(error).all()
            mask=np.stack([test_valid[i+L:i+L+H] for i in range(start,stop)])
            channel_mask=np.broadcast_to(complete_channel[start:stop,None,:],error.shape)
            for case,values in [('original_all',error),('observed_targets',error[mask]),
                ('complete_channel_windows',error[channel_mask]),('unobserved_imputed_targets_diagnostic',error[~mask])]:
                accum[case][0]+=float(np.square(values).sum())
                accum[case][1]+=float(np.abs(values).sum())
                accum[case][2]+=values.size
        for case,(squared,absolute,total) in accum.items():
            assert total>0
            record={'dataset':'geant','horizon':168,'case':case,'model':model,'seed':seed,
                    'n_target_values':int(total),'mse':squared/total,'mae':absolute/total}
            if case=='original_all':
                for metric in ['mse','mae']:
                    assert np.isclose(record[metric],float(previous[(model,seed)]['all_'+metric]),rtol=1e-12)
            records.append(record)
        del prediction,truth,error,reference
        print('WEEKLY_SCORED',model,seed,flush=True)

def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

summary=[];effects=[];grouped=defaultdict(list)
for r in records:grouped[(r['case'],r['model'])].append(r)
for (case,model),group in grouped.items():
    assert sorted(r['seed'] for r in group)==SEEDS
    row={'dataset':'geant','horizon':168,'case':case,'model':model,'n_seeds':8,'n_target_values':group[0]['n_target_values']}
    for metric in ['mse','mae']:
        a=np.array([r[metric] for r in group])
        row[metric+'_mean']=float(a.mean());row[metric+'_sd']=float(a.std(ddof=1))
    summary.append(row)
for case in dict.fromkeys(r['case'] for r in records):
    ours={r['seed']:r for r in grouped[(case,'dlinear_scale')]}
    for baseline in MODELS[:-1]:
        control={r['seed']:r for r in grouped[(case,baseline)]}
        for metric in ['mse','mae']:
            values=np.array([100*(control[s][metric]-ours[s][metric])/control[s][metric] for s in SEEDS])
            effects.append({'dataset':'geant','horizon':168,'case':case,'baseline':baseline,'metric':metric,
                'mean_reduction_pct':float(values.mean()),'sample_sd_pct':float(values.std(ddof=1)),
                'seed_wins':int((values>0).sum()),'n_seeds':8,
                'minimum_reduction_pct':float(values.min()),'maximum_reduction_pct':float(values.max())})
write_csv(OUT/'一周逐种子重算指标.csv',records)
write_csv(OUT/'一周各口径均值与标准差.csv',summary)
write_csv(OUT/'一周逐种子配对降幅汇总.csv',effects)
result={'summary':summary,'effects':effects,'complete_global_windows':int(complete_windows.sum()),
    'whole_missing_test_hours':0,'all_models_and_all_8_seeds_included':True,'no_retraining':True,
    'note':'The corrected mask also excludes nonfinite OD entries in present hourly matrices. A fully observed global test window is unavailable; per-OD complete windows are a separately labeled sensitivity subset.'}
(QA/'weekly_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for item in sources:assert digest(Path(item['path']))==item['sha256'],item['path']
assert sha256(PAPER.read_bytes()).hexdigest()==PAPER_SHA
(QA/'weekly_audit.json').write_text(json.dumps({'sources':sources,'originals_unchanged':True,'manuscript_unchanged':True,
    'original_weekly_scores_reproduced':True,'no_retraining':True,'all_40_model_seed_runs_scored':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('WEEKLY_COMPLETE',flush=True)
