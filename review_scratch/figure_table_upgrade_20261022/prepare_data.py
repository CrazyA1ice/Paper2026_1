from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/图表组织优化修订_20261022'
ASSETS=OUT/'图表与核验数据'
ASSETS.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'paper_template/长春工程学院学报(自然科学版)/实验结果分析修订_20261022/自适应多尺度加权的多变量网络流量预测_实验结果分析稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest()=='a66d4e25a4fc592437afc1b13a1c59f68b9243f9d3d0f0b8d8d9b59e1905a917'
previous=json.loads((ROOT/'review_scratch/results_explanation_20261022/evidence_audit.json').read_text(encoding='utf-8'))
rows=[]
for item in previous['input_metrics']:
    path=Path(item['path'])
    assert sha256(path.read_bytes()).hexdigest()==item['sha256']
    r=json.loads(path.read_text(encoding='utf-8'))
    rows.append(dict(dataset=r['dataset'],model=path.parent.name.rsplit('_seed',1)[0],seed=r['seed'],mse=r['test_normalized']['mse'],mae=r['test_normalized']['mae'],parameters=r['parameters']))
core=pd.DataFrame(rows)
assert len(core)==96 and not core.duplicated(['dataset','model','seed']).any()
assert set(core.seed)==set(range(42,50))
assert core[['mse','mae']].gt(0).all().all()
summary=core.groupby(['dataset','model']).agg(mse_mean=('mse','mean'),mse_sd=('mse','std'),mae_mean=('mae','mean'),mae_sd=('mae','std'),parameters=('parameters','first'),n=('seed','size')).reset_index()
assert summary.n.eq(8).all()
index=core.set_index(['dataset','model','seed'])
effects=[]
for ds in ['abilene','geant']:
    for control in ['dlinear','lightts']:
        for metric in ['mse','mae']:
            for seed in range(42,50):
                b=index.loc[(ds,control,seed),metric];p=index.loc[(ds,'dlinear_scale',seed),metric]
                effects.append(dict(dataset=ds,baseline=control,metric=metric,seed=seed,reduction_pct=100*(b-p)/b))
gains=pd.DataFrame(effects)
assert len(gains)==64
for path,key,expected in [('abilene_forecasting/results/high_demand_analysis/per_seed.csv','high_demand_csv_sha256',80),('abilene_forecasting/results/long_horizon_20261021/per_seed_scores.csv','weekly_csv_sha256',None)]:
    assert sha256((ROOT/path).read_bytes()).hexdigest()==previous[key]
high=pd.read_csv(ROOT/'abilene_forecasting/results/high_demand_analysis/per_seed.csv')
week=pd.read_csv(ROOT/'abilene_forecasting/results/long_horizon_20261021/per_seed_scores.csv')
week=week[(week.dataset=='geant')&(week.horizon==168)].copy()
assert len(high)==80 and len(week)==40
assert not high.duplicated(['dataset','model','seed']).any()
assert not week.duplicated(['model','seed']).any()
wi=week.set_index(['model','seed'])
weekly=[]
for control in ['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router']:
    for metric in ['mse','mae']:
        for seed in range(42,50):
            b=wi.loc[(control,seed),'all_'+metric];p=wi.loc[('dlinear_scale',seed),'all_'+metric]
            weekly.append(dict(baseline=control,metric=metric,seed=seed,reduction_pct=100*(b-p)/b))
weekly=pd.DataFrame(weekly)
assert len(weekly)==64 and weekly.reduction_pct.gt(0).all()
highsummary=high.groupby(['dataset','model'])[['mae','mean_shortfall']].agg(['mean','std'])
strongest=[]
for ds in ['abilene','geant']:
    for metric in ['mse','mae']:
        candidates=summary[(summary.dataset==ds)&(~summary.model.isin(['dlinear_scale','lightts']))]
        best=candidates.loc[candidates[metric+'_mean'].idxmin()]
        proposed=summary[(summary.dataset==ds)&(summary.model=='dlinear_scale')].iloc[0]
        assert proposed[metric+'_mean']<best[metric+'_mean']
        strongest.append(dict(dataset=ds,metric=metric,baseline=best['model'],baseline_mean=best[metric+'_mean'],proposed_mean=proposed[metric+'_mean']))
for frame,name in [(core,'全部24h逐种子指标'),(summary,'24h均值与标准差'),(gains,'图2_配对相对降幅'),(high,'图3_高需求全部种子'),(week,'图4_168h绝对误差全部种子'),(weekly,'图4_168h配对降幅')]:
    frame.to_csv(ASSETS/(name+'.csv'),index=False,encoding='utf-8-sig')
report=dict(source=str(SOURCE),source_sha256=sha256(SOURCE.read_bytes()).hexdigest(),out=str(OUT),assets=str(ASSETS),metric_records=96,figure2_records=64,figure3_records=80,figure4_absolute_records=40,figure4_paired_records=64,no_seed_exclusions=True,all_original_data_hashes_match=True,strongest_controls=strongest,original_metrics=previous['input_metrics'])
(QA/'data_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'figure_contract.md').write_text('''# Figure and table revision contract

Authority: retain latest Results manuscript and all journal typography, 138 mm figure width, editable equations, references and other content. Python/matplotlib is the established and exclusive plotting backend. Use 7.5 pt Songti/Times at actual print size, editable SVG/PDF and 600 dpi PNG/TIFF. No new experiments or significance tests. Use all eight matched seeds 42–49 in each displayed group. Error bars are sample SD, never confidence intervals.

Figure 2 question: how large are the error reductions against both baseline architectures, with what LightTS parameter ratio? Two panels stratify the dataset; within each panel four rows show paired MSE/MAE gains against DLinear and LightTS, all seed points and means ± SD. Parameter ratios are deterministic footer labels; exact counts go to table 2. No joint cross-dataset raw-error comparison and no claim of Pareto domination over DLinear (4656 parameters versus 8339).

Figure 3 question: how does high-demand target error differ between methods? Two dataset panels show all five models, both MAE and AUE, individual seeds and means ± SD. A point plot permits a labelled local numeric axis without encoding a misleading nonzero bar length. DLinear means are references. Proposed markers have restrained colour and shape emphasis. Percentage annotations use paired mean reductions and do not imply significance.

Figure 4 question: how large and consistent is the weekly improvement? A 2×2 grid uses columns for absolute errors and matched relative reductions; rows for MSE and MAE. All 40 absolute records and 64 paired reductions are shown. No density estimates for n=8, no smoothed clouds, no 100% significant annotation. Absolute errors have smaller-is-better direction, relative reductions larger-is-better. Final height may increase locally to retain 7.5 pt readability; page fonts/margins remain unchanged.

Table 2: keep all MSE/MAE values unchanged, retain bold best values, add architecture parameter counts. Table 3: retain bold best values and original columns; do not add a sparse new column with metric-dependent strongest-comparator denominators. Existing prose reports the intended paired comparisons.

QA: run data profiling, multi-panel physical alignment gate, source preflight, exported PDF glyph audit, collision audit and visual review of each panel and grayscale. Inspect every final Word page. Preserve source file byte-for-byte.
''',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='original_metrics'},ensure_ascii=False))
