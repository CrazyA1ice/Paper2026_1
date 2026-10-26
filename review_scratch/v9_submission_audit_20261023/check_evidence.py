from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
from datetime import datetime, timezone
import csv
import json
import sys

import numpy as np
import tables
from xml.etree import ElementTree as E

sys.stdout.reconfigure(encoding='utf-8')
qa = Path(__file__).resolve().parent
root = qa.parents[1]
paper = root/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV9_投稿规范修订稿.docx'
assert sha256(paper.read_bytes()).hexdigest() == '63e070311f9b14d291a98a8a0d3d5569049fd566cb371f787275653661863321'
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(paper) as z:
    doc = E.fromstring(z.read('word/document.xml'))
    text_tags = {'{'+ns['w']+'}t','{'+ns['m']+'}t'}
    paragraphs = [{'index':i,'text':''.join(t.text or '' for t in n.iter() if t.tag in text_tags)}
                  for i,n in enumerate(doc.find('w:body',ns))]
(qa/'v9_paragraphs.json').write_text(json.dumps(paragraphs,ensure_ascii=False,indent=2),encoding='utf-8')

source_dir = root/'abilene_forecasting/data/raw/tszoo/databases'
datasets = []
for name,feature in [('Abilene','matrix_avg_realOD'),('GEANT','matrix_avg_bandwidth_kbps')]:
    path = source_dir/name/f'{name}-matrix-backbone_network-1_hour.h5'
    with tables.open_file(path,'r') as f:
        time = f.root.times.times_1_hour.read()
        agg = f.root.backbone_network.agg_1_hour.read()
        observed = np.zeros(len(time),dtype=bool)
        observed[agg['id_time']] = True
        raw_matrix = f.get_node('/backbone_network/'+feature)
        n = len(time)
        endpoints = [0,int(n*.6),int(n*.8),n]
        splits = []
        processed = np.load(root/f'abilene_forecasting/data/processed/{name.lower()}_1hour.npz')
        for i,split_name in enumerate(['train','val','test']):
            a,b = endpoints[i:i+2]
            flags = observed[a:b]
            data = processed[split_name]
            inverse_missing = np.expm1(data[~flags].astype(np.float64)*processed['std']+processed['mean'])
            assert np.allclose(inverse_missing,0,atol=1e-5)
            horizons = []
            for h in ([24,168] if name=='GEANT' else [24]):
                L = 96
                count = len(flags)-L-h+1
                targets = np.stack([flags[j+L:j+L+h] for j in range(count)])
                horizons.append({'horizon':h,'windows':count,
                    'target_time_occurrences':int(targets.size),
                    'missing_target_time_occurrences':int((~targets).sum()),
                    'windows_with_missing_targets':int((~targets).any(axis=1).sum())})
            missing_indices = np.flatnonzero(~flags)+a
            splits.append({'name':split_name,'total':len(flags),'missing':int((~flags).sum()),
                'missing_first_utc':datetime.fromtimestamp(int(time['time'][missing_indices[0]]),timezone.utc).isoformat() if len(missing_indices) else None,
                'missing_last_utc':datetime.fromtimestamp(int(time['time'][missing_indices[-1]]),timezone.utc).isoformat() if len(missing_indices) else None,
                'missing_rows_are_zero_filled_in_saved_experiment_input':True,
                'horizons':horizons})
        datasets.append({'dataset':name,'raw_time_grid':n,'observed_aggregate_rows':len(agg),
            'missing_aggregate_rows':int((~observed).sum()),'splits':splits})

core = root/'paper_template/长春工程学院学报(自然科学版)/图表组织优化修订_20261022/图表与核验数据/全部24h逐种子指标.csv'
with core.open(encoding='utf-8-sig',newline='') as f:
    rows = list(csv.DictReader(f))
spread = []
for dataset in ['abilene','geant']:
    values = {}
    for model in ['dlinear','lightts','dlinear_scale']:
        group = [r for r in rows if r['dataset']==dataset and r['model']==model]
        assert len(group)==8
        values[model] = {metric:{'mean':float(np.mean([float(r[metric]) for r in group])),
                                'sample_sd':float(np.std([float(r[metric]) for r in group],ddof=1))}
                        for metric in ['mse','mae']}
    spread.append({'dataset':dataset,'models':values})

result = {'paper':str(paper),'paper_sha256':sha256(paper.read_bytes()).hexdigest(),
          'missing_data_audit':datasets,'seed_variability':spread}
(qa/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
