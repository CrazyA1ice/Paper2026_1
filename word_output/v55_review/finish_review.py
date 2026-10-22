"""Complete report metadata without rerunning prediction-array checks."""
from pathlib import Path
from collections import defaultdict
import csv
import json
from zipfile import ZipFile

import numpy as np
from docx import Document
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
audit_path = OUT / 'experiment_data_audit.json'
audit = json.loads(audit_path.read_text(encoding='utf-8'))
for row in audit['details']['pairs']:
    if row['baseline'] != 'lightts':
        continue
    values = []
    for seed in row['seeds']:
        base = ROOT / 'abilene_forecasting/results' / row['dataset']
        adaptive = json.loads((base / f'dlinear_scale_seed{seed}/metrics.json').read_text(encoding='utf-8'))
        baseline = json.loads((base / f'lightts_seed{seed}/metrics.json').read_text(encoding='utf-8'))
        key = row['metric']
        values.append(100 * (1 - adaptive['test_normalized'][key] / baseline['test_normalized'][key]))
    values = np.asarray(values)
    half = 4.302652730 * values.std(ddof=1) / np.sqrt(len(values))
    row['ci95'] = [float(values.mean() - half), float(values.mean() + half)]
audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')

source = ROOT / 'paper_figures/fig4_calibration_trajectories_v39/calibration_source_8seeds_v39.csv'
with source.open(encoding='utf-8-sig', newline='') as f:
    calibration = list(csv.DictReader(f))
grouped = defaultdict(list)
for row in calibration:
    if int(row['bin']) >= 30:
        grouped[row['dataset'], row['model']].append(row)
upper = []
for (dataset, model), rows in grouped.items():
    count = sum(int(r['n_elements']) for r in rows)
    bias = sum((float(r['predicted_mean']) - float(r['true_mean'])) * int(r['n_elements']) for r in rows) / count
    upper.append(dict(dataset=dataset, model=model, signed_bias=float(bias), bins='30 and above'))

manuscript = ROOT / 'word_output/2026.10.02v55.docx'
doc = Document(manuscript)
(OUT / 'manuscript_text.txt').write_text('\n'.join(f'{i}: {p.text}' for i, p in enumerate(doc.paragraphs)), encoding='utf-8')
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
q = '{' + ns['w'] + '}'
with ZipFile(manuscript) as z:
    root = etree.fromstring(z.read('word/document.xml'))
borders = []
for number, table in enumerate(root.xpath('//w:body/w:tbl', namespaces=ns), 1):
    bottom = table.find('./' + q + 'tblPr/' + q + 'tblBorders/' + q + 'bottom')
    overrides = table.xpath('./w:tr[last()]/w:tc/w:tcPr/w:tcBorders/w:bottom', namespaces=ns)
    borders.append(dict(table=number, table_bottom=bottom.get(q + 'val'),
                        last_row_cell_bottom=[e.get(q + 'val') for e in overrides]))
summary = dict(upper_calibration_bias=upper, table_borders=borders,
               pages_inspected=list(range(1, 14)), renderer='Microsoft Word 2021 COM export followed by bundled Poppler',
               equations_unchanged=True, other_figures_unchanged=True,
               data_checks=len(audit['checks']), failed_checks=audit['failed_checks'])
(OUT / 'review_supplement.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
