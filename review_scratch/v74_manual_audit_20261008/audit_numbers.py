from pathlib import Path
import json, csv, math, statistics as st, sys
import numpy as np
from zipfile import ZipFile
from lxml import etree as E
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1'); out=root/'review_scratch/v74_manual_audit_20261008'; base=root/'abilene_forecasting'
new=json.loads((out/'v74.json').read_text(encoding='utf-8')); old=json.loads((out/'v73.json').read_text(encoding='utf-8'))
rows=[]; checks=[]; datasets=[]
for ds in ['abilene','geant']:
 with np.load(base/f'data/processed/{ds}_1hour.npz') as z:
  splits={k:list(z[k].shape) for k in ['train','val','test']}; record={'dataset':ds,'splits':splits,'windows':{k:splits[k][0]-119 for k in splits},'keys':list(z.files),'active_count':len(z['active_indices']) if 'active_indices' in z else None,'metadata':{k:str(z[k]) for k in ['feature','aggregation','original_shape'] if k in z}}; datasets.append(record)
 for model in ['dlinear','lightts','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']:
  folder='results/global_weight_ablation' if model=='dlinear_scale_global' else 'results/constant_router_ablation' if model=='dlinear_scale_constant_router' else 'results'
  for seed in range(42,45 if model=='lightts' else 50):
   p=base/f'{folder}/{ds}/{model}_seed{seed}/metrics.json'; j=json.loads(p.read_text(encoding='utf-8')); predfile=p.parent/'predictions.npz'
   with np.load(predfile) as z:
    pred=z['prediction']; truth=z['truth']; error=pred-truth; computed={'mse':float(np.mean(error**2)),'mae':float(np.mean(abs(error))),'rmse':float(np.sqrt(np.mean(error**2)))}; maxdiff=max(abs(computed[k]-j['test_normalized'][k]) for k in computed)
    if maxdiff>1e-6: checks.append({'path':str(p),'metric_difference':maxdiff})
    shape=list(pred.shape)
   rows.append({'dataset':ds,'model':model,'seed':seed,'parameters':j['parameters'],**computed,'path':str(p),'shape':shape,'settings':{k:j.get(k) for k in ['batch_size','epochs_max','patience','learning_rate','input_len','pred_len','n_channels']},'raw':j.get('test_original_units')})
summary=[]; paired=[]
for ds in ['abilene','geant']:
 for n in [3,8]:
  models=['dlinear','lightts','dlinear_scale'] if n==3 else ['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
  for model in models:
   sel=[r for r in rows if r['dataset']==ds and r['model']==model and r['seed']<42+n]
   summary.append({'dataset':ds,'model':model,'seeds':n,'parameters':sel[0]['parameters'],**{f'{metric}_{agg}':func([r[metric] for r in sel]) for metric in ['mse','mae','rmse'] for agg,func in [('mean',st.mean),('sd',st.stdev)]}})
   if model!='dlinear_scale':
    for metric in ['mse','mae','rmse']:
     vals=[]
     for r in sel:
      own=next(a for a in rows if a['dataset']==ds and a['model']=='dlinear_scale' and a['seed']==r['seed']); vals.append(100*(r[metric]-own[metric])/r[metric])
     mean=st.mean(vals); half=2.3646242510102993*st.stdev(vals)/math.sqrt(n) if n==8 else None
     paired.append({'dataset':ds,'baseline':model,'metric':metric,'seeds':n,'mean':mean,'ci_low':mean-half if half is not None else None,'ci_high':mean+half if half is not None else None,'wins':sum(v>0 for v in vals),'values':vals})
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(root/'word_output/2026.10.07v74.docx') as z:
 doc=E.fromstring(z.read('word/document.xml')); styles=E.fromstring(z.read('word/styles.xml'))
 refs=[]
 for i,p in enumerate(doc.find('w:body',ns).findall('w:p',ns)):
  if i>=111:continue
  for r in p.findall('w:r',ns):
   s=''.join(r.xpath('.//w:t/text()',namespaces=ns))
   if '[' in s and any(x in s for x in map(str,range(1,12))):refs.append({'p':i,'text':s,'vertical':r.xpath('./w:rPr/w:vertAlign/@w:val',namespaces=ns),'style':r.xpath('./w:rPr/w:rStyle/@w:val',namespaces=ns)})
 abstract=new['paragraphs'][3]['text'].removeprefix('摘要：'); conclusion=new['paragraphs'][110]['text']; lengths={'abstract_characters_no_spaces':len(''.join(abstract.split())),'abstract_han_characters':sum('\u4e00'<=c<='\u9fff' for c in abstract),'conclusion_characters_no_spaces':len(''.join(conclusion.split()))}
 identicalmath=all(E.tostring(a)==E.tostring(b) for a,b in zip(E.fromstring(ZipFile(root/'word_output/2026.10.07v73.docx').read('word/document.xml')).xpath('.//m:oMath',namespaces=ns),doc.xpath('.//m:oMath',namespaces=ns)))
 result={'datasets':datasets,'raw_metric_validation_errors':checks,'run_count':len(rows),'runs':rows,'summary':summary,'paired':paired,'citations':refs,'lengths':lengths,'math_serialization_vs_v73_identical':identicalmath,'tables_vs_v73_equal':new['tables']==old['tables'],'images_vs_v73_equal':new['media']==old['media']}
(out/'numerical_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['datasets','raw_metric_validation_errors','run_count','lengths','math_serialization_vs_v73_identical','tables_vs_v73_equal','images_vs_v73_equal']},ensure_ascii=False))
print('TABLE SUMMARIES');print(json.dumps(summary,ensure_ascii=False))
print('CORE PAIRED'); print(json.dumps([p for p in paired if p['metric']=='mse'],ensure_ascii=False))
