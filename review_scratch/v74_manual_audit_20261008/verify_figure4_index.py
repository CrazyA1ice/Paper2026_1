from pathlib import Path
import csv,json
import numpy as np
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v74_manual_audit_20261008';lines=[]
for ds,ch,wins in [('abilene',46,[278,618]),('geant',296,[397,169])]:
 res={'dataset':ds,'image_label_channel':ch+1,'zero_based_channel':ch,'windows':[]}
 with np.load(root/f'abilene_forecasting/data/processed/{ds}_1hour.npz') as z:res['original_channel_index']=int(z['active_indices'][ch])
 for win in wins:
  vals={}
  for model in ['dlinear','dlinear_scale_static','dlinear_scale_constant_router','dlinear_scale']:
   folder='results/constant_router_ablation' if model=='dlinear_scale_constant_router' else 'results'
   with np.load(root/f'abilene_forecasting/{folder}/{ds}/{model}_seed42/predictions.npz') as z:
    vals[model]=float(np.mean((z['prediction'][win,:,ch]-z['truth'][win,:,ch])**2))
    if model=='dlinear_scale':vals['truth_first_3']=[float(x) for x in z['truth'][win,:3,ch]]
  res['windows'].append({'image_label_window':win+1,'mse':vals})
 lines.append(json.dumps(res))
p=root/'abilene_forecasting/paper_figures/source_data_v2/candidate2_router_weight_distribution_8seeds.csv'
with p.open(encoding='utf8') as f:rows=list(csv.DictReader(f))
for ds in sorted({r['dataset'] for r in rows}):
 means={sc:float(np.mean([float(r['router_weight']) for r in rows if r['dataset']==ds and r['scale']==sc])) for sc in ['1','2','4']};lines.append(ds+' '+str(means))
(out/'figure4_numbering_corrected.txt').write_text('\n'.join(lines),encoding='utf8');print('Complete')
