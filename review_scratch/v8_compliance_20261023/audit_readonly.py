from collections import Counter, defaultdict
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from statistics import mean, stdev
from zipfile import ZipFile
import csv
import json
import re
import sys

from lxml import etree as E
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV8_指定项目修订稿.docx'
SOURCE_SHA = '6c832ce97b2f8ec4b5eaec54dcba67ae195618b960c84af292faa23ea8db773d'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
with ZipFile(SOURCE) as z:
    doc = E.fromstring(z.read('word/document.xml'))
    settings = E.fromstring(z.read('word/settings.xml'))
    body = doc.find('w:body', NS)
    text = lambda p: ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS))
    paragraphs = [{'index': i, 'text': text(p)} for i, p in enumerate(body) if p.tag.endswith('}p')]
    tables = [[[text(c) for c in row.findall('w:tc', NS)] for row in t.findall('w:tr', NS)]
              for t in body.findall('w:tbl', NS)]
    images = []
    image_hashes = {}
    for name in z.namelist():
        if name.startswith('word/media/') and name.endswith('.png'):
            data = z.read(name)
            im = Image.open(BytesIO(data))
            images.append({'part': name, 'pixels': im.size, 'dpi': im.info.get('dpi'),
                           'effective_dpi_at_13_8_cm': im.width / (13.8 / 2.54)})
            image_hashes[sha256(data).hexdigest()] = name
    widths = sorted(set(round(int(x) / 360000, 4) for x in doc.xpath('//wp:extent/@cx', namespaces=NS)))

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

template_evidence = json.loads((ROOT/'review_scratch/template_format_20261021/template_evidence.json').read_text(encoding='utf-8'))
for r in template_evidence:
    assert sha256((JOURNAL/(r['name']+'.doc')).read_bytes()).hexdigest() == r['original_sha256']
    assert sha256((ROOT/'review_scratch/template_format_20261021'/(r['name']+'.docx')).read_bytes()).hexdigest() == r['sha256']

ev = json.loads((ROOT/'review_scratch/results_explanation_20261022/evidence_audit.json').read_text(encoding='utf-8'))
raw = {}
for item in ev['input_metrics']:
    path = Path(item['path'])
    assert sha256(path.read_bytes()).hexdigest() == item['sha256']
    record = json.loads(path.read_text(encoding='utf-8'))
    raw[(record['dataset'], record['model'], str(record['seed']))] = record
assert len(raw) == 96
source_data = JOURNAL / '图表组织优化修订_20261022/图表与核验数据'
core = read_csv(source_data/'全部24h逐种子指标.csv')
for r in core:
    original = raw[(r['dataset'], r['model'], r['seed'])]
    for metric in ['mse', 'mae']:
        assert abs(float(r[metric]) - float(original['test_normalized'][metric])) < 1e-12
    assert int(r['parameters']) == original['parameters']
grouped = defaultdict(list)
for r in core:
    grouped[(r['dataset'], r['model'])].append(r)

def metric_cell(rows, metric):
    values = [float(r[metric]) for r in rows]
    assert len(values) == 8
    return f'{mean(values):.3f}±{stdev(values):.3f}'

names = {'dlinear': 'DLinear', 'lightts': 'LightTS', 'dlinear_scale': '本文方法',
         'dlinear_scale_static': '固定等权多尺度', 'dlinear_scale_global': '全局可学习权重',
         'dlinear_scale_constant_router': '恒定输入路由'}
datasets = {'abilene': 'Abilene', 'geant': 'GÉANT'}
expected2 = []
expected3 = []
for ds in datasets:
    for model in ['dlinear', 'lightts', 'dlinear_scale']:
        rows = grouped[(ds, model)]
        expected2.append([datasets[ds], names[model], metric_cell(rows, 'mse'), metric_cell(rows, 'mae'), rows[0]['parameters']])
    for model in ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router', 'dlinear_scale']:
        rows = grouped[(ds, model)]
        expected3.append([datasets[ds], names[model], metric_cell(rows, 'mse'), metric_cell(rows, 'mae')])
assert tables[1][1:] == expected2
assert tables[2][1:] == expected3

weekly_path = ROOT/'abilene_forecasting/results/long_horizon_20261021/per_seed_scores.csv'
high_path = ROOT/'abilene_forecasting/results/high_demand_analysis/per_seed.csv'
assert sha256(weekly_path.read_bytes()).hexdigest() == ev['weekly_csv_sha256']
assert sha256(high_path.read_bytes()).hexdigest() == ev['high_demand_csv_sha256']
week = read_csv(source_data/'图4_168h绝对误差全部种子.csv')
expected4 = []
for model in ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router', 'dlinear_scale']:
    rows = [r for r in week if r['model'] == model]
    expected4.append([names[model], metric_cell(rows, 'all_mse'), metric_cell(rows, 'all_mae')])
assert tables[3][1:] == expected4
expected1 = []
for ds, horizon in [('abilene', 24), ('geant', 24), ('geant', 168)]:
    with np.load(ROOT/f'abilene_forecasting/data/processed/{ds}_1hour.npz') as data:
        rows = [len(data[key]) for key in ['train', 'val', 'test']]
        windows = [n - 96 - horizon + 1 for n in rows]
        expected1.append([datasets[ds], str(data['train'].shape[1]), str(horizon), '/'.join(map(str, rows)), '/'.join(map(str, windows))])
assert tables[0][1:] == expected1

matched_figures = []
for path in [JOURNAL/'图1与一周预测表修订_20261022/图表源文件/图1_样本窗口符号统一.png'] + list(source_data.glob('*.png')):
    match = image_hashes.get(sha256(path.read_bytes()).hexdigest())
    assert match, path
    svg = path.with_suffix('.svg').read_text(encoding='utf-8')
    matched_figures.append({'part': match, 'source': str(path),
                            'font_families': dict(Counter(re.findall(r"font-family: '([^']+)'", svg))),
                            'font_sizes': dict(Counter(re.findall(r'font-size: ([0-9.]+)px', svg))),
                            'vertical_tick_path_examples': re.findall(r'd="(M 0 0\s+L 0 [^\"]+)"', svg)[:3]})
assert len(matched_figures) == 4
cn = next(p['text'][3:] for p in paragraphs if p['text'].startswith('摘要：'))
title = paragraphs[0]['text']
citations = []
for run in body.xpath('./w:p/w:r', namespaces=NS):
    value = text(run)
    if re.fullmatch(r'\[\d+\]', value):
        assert run.xpath('./w:rPr/w:vertAlign/@w:val', namespaces=NS) == ['superscript']
        citations.append(int(value[1:-1]))
first_citations = list(dict.fromkeys(citations))
assert first_citations == list(range(1, 13))
assert len(cn) == 199 and len(title) == 18
assert len(tables) == 4 and len(images) == 4 and max(widths) < 14
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
report = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'source_unchanged': True,
          'two_original_doc_requirements_hashes_confirmed': True,
          'title_characters': len(title), 'chinese_abstract_characters': len(cn),
          'table_count': len(tables), 'figure_count': len(images), 'widths_cm': widths,
          'all_four_tables_recomputed_and_matched': True, 'raw_24h_metrics_sha_verified': 96,
          'high_and_weekly_source_hashes_match_prior_verified_records': True,
          'images': images, 'figure_sources': matched_figures,
          'math_font': settings.xpath('//m:mathFont/@m:val', namespaces=NS),
          'citations_all_superscript': True, 'first_citation_order': first_citations,
          'word_statistics': json.loads((ROOT/'review_scratch/selected_revisions_20261023/word_statistics.json').read_text(encoding='utf-8-sig')),
          'parameters24': 2*24*sum(96//s+1 for s in [1,2,4])+131,
          'parameters168': 2*168*sum(96//s+1 for s in [1,2,4])+131,
          'paragraphs': paragraphs}
(QA/'facts.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['paragraphs', 'images', 'figure_sources']}, ensure_ascii=False))
