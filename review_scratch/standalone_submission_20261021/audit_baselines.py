from pathlib import Path
import json,hashlib,sys
import numpy as np
import pandas as pd
from docx import Document

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2];QA=Path(__file__).resolve().parent
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/主稿独立投稿修订_20261021'
ASSETS=OUT/'存档数据与图表';ASSETS.mkdir(parents=True,exist_ok=True)
models=['dlinear','lightts','dlinear_scale']
records=[]
for ds in ['abilene','geant']:
    for model in models:
        for seed in [42,43,44]:
            p=ROOT/f'abilene_forecasting/results/{ds}/{model}_seed{seed}/metrics.json'
            m=json.loads(p.read_text(encoding='utf8'))
            for k,v in {'dataset':ds,'model':model,'seed':seed,'input_len':96,'pred_len':24}.items():assert m[k]==v
            assert m['split_windows']['test']=={'abilene':813,'geant':451}[ds]
            records.append({'dataset':ds,'model':model,'seed':seed,'mse':m['test_normalized']['mse'],'mae':m['test_normalized']['mae'],'parameters':m['parameters'],'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
frame=pd.DataFrame(records)
prior=pd.read_csv(ROOT/'abilene_forecasting/paper_figures/source_data_v25/fig3_lightts_improvement_summary.csv')
paired=[];summary=[]
for ds in ['abilene','geant']:
    ours=frame[(frame.dataset==ds)&(frame.model=='dlinear_scale')].set_index('seed').sort_index()
    base=frame[(frame.dataset==ds)&(frame.model=='lightts')].set_index('seed').sort_index()
    assert ours.index.tolist()==base.index.tolist()==[42,43,44]
    assert ours.parameters.nunique()==base.parameters.nunique()==1
    for metric in ['mse','mae']:
        values=100*(base[metric]-ours[metric])/base[metric]
        assert (values>0).all()
        archived=prior[(prior.dataset==ds)&(prior.metric==metric.upper())].iloc[0]
        for seed,value in values.items():
            assert np.isclose(value,archived[f'seed{seed}_pct'],rtol=1e-12)
            paired.append({'dataset':ds,'seed':seed,'metric':metric,'relative_reduction_pct':value})
        summary.append({'dataset':ds,'metric':metric,'mean':values.mean(),'sample_sd':values.std(ddof=1),'n_seeds':3,'proposed_parameters':int(ours.parameters.iloc[0]),'lightts_parameters':int(base.parameters.iloc[0]),'parameter_ratio_pct':100*ours.parameters.iloc[0]/base.parameters.iloc[0]})
frame.to_csv(ASSETS/'图2_全部基线记录.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(paired).to_csv(ASSETS/'图2_逐种子相对降幅.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(summary).to_csv(ASSETS/'图2_均值与标准差.csv',index=False,encoding='utf-8-sig')
source=Document(ROOT/'paper_template/长春工程学院学报(自然科学版)/数据处理精简修订_20261021/自适应多尺度加权的多变量网络流量预测_数据分析精简版.docx')
table=source.tables[1]
for row,(ds,model) in zip(table.rows[1:],[(d,m) for d in ['abilene','geant'] for m in models]):
    g=frame[(frame.dataset==ds)&(frame.model==model)]
    assert row.cells[2].text==f'{g.mse.mean():.3f}±{g.mse.std(ddof=1):.3f}'
    assert row.cells[3].text==f'{g.mae.mean():.3f}±{g.mae.std(ddof=1):.3f}'
result={'metric_files_verified':18,'all_seeds':3,'all_comparisons':12,'no_rows_excluded':True,'summary':summary}
(QA/'data_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
