from pathlib import Path
import hashlib, json, shutil, sys
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
PROJECT=ROOT/'abilene_forecasting'
DATA=PROJECT/'results/long_horizon_20261021'
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/长预测核验与修订_20261021'
ASSETS=OUT/'数据与图表'
ASSETS.mkdir(parents=True,exist_ok=True)
MODELS=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
LABELS=dict(zip(MODELS,['DLinear','固定等权','全局可学习权重','恒定输入路由','本文方法']))

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def run_dir(ds,model,seed,h):
    if h!=24:return DATA/f'h{h:03d}'/ds/f'{model}_seed{seed}'
    parent=PROJECT/'results'
    if model=='dlinear_scale_global':parent=parent/'global_weight_ablation'
    if model=='dlinear_scale_constant_router':parent=parent/'constant_router_ablation'
    return parent/ds/f'{model}_seed{seed}'

protocol=json.loads((DATA/'protocol.json').read_text(encoding='utf8'))
for name,value in protocol['source_sha256'].items():assert sha(PROJECT/name)==value,name
frame=pd.read_csv(DATA/'per_seed_scores.csv')
summary=pd.read_csv(DATA/'summary.csv')
paired=pd.read_csv(DATA/'paired_reductions.csv')
assert len(frame)==320 and len(summary)==40 and len(paired)==64
assert not frame.duplicated(['dataset','model','horizon','seed']).any()
verified=[]
for (ds,h,model),group in frame.groupby(['dataset','horizon','model']):
    assert sorted(group.seed)==list(range(42,50))
    saved=summary[(summary.dataset==ds)&(summary.horizon==h)&(summary.model==model)].iloc[0]
    for metric in ['common_mse','common_mae','all_mse','all_mae']:
        assert np.isclose(group[metric].mean(),saved[metric+'_mean'],rtol=1e-12)
        assert np.isclose(group[metric].std(ddof=1),saved[metric+'_sd'],rtol=1e-12)
    for _,row in group.iterrows():
        folder=run_dir(ds,model,int(row.seed),int(h))
        metadata=json.loads((folder/'metrics.json').read_text(encoding='utf8'))
        for key,value in {'dataset':ds,'model':model,'seed':int(row.seed),'input_len':96,'pred_len':int(h),'batch_size':16,'epochs_max':30,'patience':6,'learning_rate':.001}.items():
            assert metadata[key]==value,(folder,key)
        expected_params={'dlinear':194*h,'dlinear_scale_static':342*h,'dlinear_scale_global':342*h+3,'dlinear_scale_constant_router':342*h+131,'dlinear_scale':342*h+131}[model]
        assert int(row.parameters)==metadata['parameters']==expected_params
        assert int(row.n_common_origins)=={'abilene':669,'geant':307}[ds]
        assert np.isclose(row.all_mse,metadata['test_normalized']['mse'],rtol=1e-5)
        assert np.isclose(row.all_mae,metadata['test_normalized']['mae'],rtol=1e-5)
        actual_hash=sha(folder/'predictions.npz')
        assert actual_hash==row.prediction_sha256,folder
        if h!=24:
            complete=json.loads((folder/'completion.json').read_text(encoding='utf8'))
            assert complete['metrics_sha256']==sha(folder/'metrics.json')
            assert complete['predictions_sha256']==actual_hash
        verified.append({'dataset':ds,'horizon':int(h),'model':model,'seed':int(row.seed),'prediction_sha256':actual_hash})
    print(f'verified {ds} H{h} {model}',flush=True)

for _,row in paired.iterrows():
    group=frame[(frame.dataset==row.dataset)&(frame.horizon==row.horizon)]
    base=group[group.model==row.baseline].sort_values('seed')['common_'+row.metric].to_numpy()
    ours=group[group.model=='dlinear_scale'].sort_values('seed')['common_'+row.metric].to_numpy()
    effect=100*(base-ours)/base
    assert np.isclose(effect.mean(),row.mean_reduction_pct,rtol=1e-12,atol=1e-12)
    assert np.isclose(effect.std(ddof=1),row.reduction_sd_pct,rtol=1e-12)
    assert int((effect>0).sum())==row.seed_wins

trend=[]
for keys,g in paired.groupby(['dataset','baseline','metric']):
    g=g.sort_values('horizon');v=g.mean_reduction_pct.to_numpy()
    assert g.horizon.tolist()==[24,48,96,168]
    trend.append({'dataset':keys[0],'baseline':keys[1],'metric':keys[2],'monotonic':bool(np.all(np.diff(v)>=0)),'endpoint_improvement':bool(v[-1]>v[0])})
assert sum(x['monotonic'] for x in trend)==0
assert sum(x['endpoint_improvement'] for x in trend)==8

weekly=frame[(frame.dataset=='geant')&(frame.horizon==168)]
assert len(weekly)==40
weekly.to_csv(ASSETS/'图5_全部八种子数据.csv',index=False,encoding='utf-8-sig')
weekly_summary=summary[(summary.dataset=='geant')&(summary.horizon==168)].set_index('model').loc[MODELS].reset_index()
weekly_summary.insert(1,'model_label',weekly_summary.model.map(LABELS))
weekly_summary.to_csv(ASSETS/'图5_均值与样本标准差.csv',index=False,encoding='utf-8-sig')
for name in ['per_seed_scores.csv','summary.csv','paired_reductions.csv','trend_check.json','protocol.json']:
    shutil.copy2(DATA/name,ASSETS/name)
result={'records':len(frame),'groups':len(summary),'paired_groups':len(paired),'prediction_files_hash_verified':len(verified),'source_files_hash_verified':len(protocol['source_sha256']),'all_seeds_preserved':True,'monotonic_groups':0,'endpoint_increasing_groups':8,'weekly_means':weekly_summary.to_dict(orient='records'),'trends':trend,'predictions':verified}
(QA/'data_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['predictions','weekly_means','trends']},ensure_ascii=False))
