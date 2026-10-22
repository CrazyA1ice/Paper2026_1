from copy import deepcopy
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import re
import statistics as st
import sys

from lxml import etree as E
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '八次重复统一修订_20261022/自适应多尺度加权的多变量网络流量预测_八次重复统一稿.docx'
SOURCE_SHA = 'bc045d2ed19899e315b3ff5fe7f5dc77f889bcb8b0b09c2051a288364bd6b3cd'
OUT = JOURNAL / '图1与一周预测表修订_20261022'
ASSETS = OUT / '图表源文件'
OUTPUT = OUT / '自适应多尺度加权的多变量网络流量预测_图1与一周预测表修订稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
if OUTPUT.exists():
    assert sha256(OUTPUT.read_bytes()).hexdigest() == '344fb3c0b926c562101aac3f2befee1aadfe0643d6e2a86246cf789e7cdbbb93'
    (QA / 'iteration1.docx').write_bytes(OUTPUT.read_bytes())
base = ROOT / 'abilene_forecasting/results/long_horizon_20261021'
with (base / 'per_seed_scores.csv').open(encoding='utf-8-sig', newline='') as f:
    raw = [r for r in csv.DictReader(f) if r['dataset'] == 'geant' and int(r['horizon']) == 168]
models = ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router', 'dlinear_scale']
names = ['DLinear', '固定等权多尺度', '全局可学习权重', '恒定输入路由', '本文方法']
assert len(raw) == 40
index = {(r['model'], int(r['seed'])): r for r in raw}
assert len(index) == 40
summary = []
for model, name in zip(models, names):
    runs = [index[model, seed] for seed in range(42, 50)]
    for r in runs:
        assert r['n_all_origins'] == r['n_common_origins'] == '307'
        metrics = json.loads((base / f'h168/geant/{model}_seed{r["seed"]}/metrics.json').read_text(encoding='utf-8'))
        assert metrics['input_len'] == 96 and metrics['pred_len'] == 168
        assert metrics['n_channels'] == 524 and metrics['split_windows']['test'] == 307
        for metric in ['mse', 'mae']:
            assert abs(float(r['all_' + metric]) - metrics['test_normalized'][metric]) < 1e-6
    s = {'model': model, 'name': name, 'n': 8}
    for metric in ['mse', 'mae']:
        values = [float(r['all_' + metric]) for r in runs]
        s[metric + '_mean'], s[metric + '_sd'] = st.mean(values), st.stdev(values)
        s[metric + '_display'] = f'{st.mean(values):.3f}±{st.stdev(values):.3f}'
    summary.append(s)
assert all(summary[-1][m + '_mean'] < s[m + '_mean'] for s in summary[:-1] for m in ['mse', 'mae'])
assert all(float(index['dlinear_scale', seed]['all_'+m]) < float(index[control, seed]['all_'+m])
           for seed in range(42, 50) for control in models[:-1] for m in ['mse', 'mae'])
with (ASSETS / '表4_八次均值与样本标准差.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
with (ASSETS / '表4_全部40次原始误差.csv').open('w', encoding='utf-8-sig', newline='') as f:
    fields = ['dataset', 'model', 'seed', 'horizon', 'n_all_origins', 'all_mse', 'all_mae']
    w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(raw)

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W = '{' + NS['w'] + '}'


def canonical(node):
    copy = deepcopy(node)
    E.cleanup_namespaces(copy)
    return E.tostring(copy, method='c14n')


with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old, new = E.fromstring(xml), E.fromstring(xml)
body = new.find('w:body', NS)
edits = []
node = body[78].findall('w:r', NS)[2].find('w:t', NS)
assert node.text.endswith('结果见图4。')
body[78].findall('w:r', NS)[0].find('w:t', NS).text = '一周预测取'
node.text = '=168，保持96 h输入及原有数据划分与预处理。表4所列五种模型均沿用2.1节的训练设置，按168 h输出独立训练，并在GÉANT的全部307个测试窗口上评价。'
edits.append({'location': 'section 2.5 setup', 'after': node.text})
node = body[80].find('w:r/w:t', NS)
assert node.text.startswith('本文方法的MSE和MAE分别为0.841±0.088和0.536±0.028，低于图4中的四种对照。')
node.text = '表4中，本文方法的平均MSE和MAE均为最优，较DLinear平均降低23.16%和11.16%。图4中，小圆点为单次配对降幅，菱形及横线为均值与样本标准差；相对每个对照，8次重复的两项误差均降低。'
edits.append({'location': 'section 2.5 results', 'after': node.text})

# Patch existing text bytes without rewriting any untouched Word XML.
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
before_nodes, after_nodes = old.xpath('.//w:t', namespaces=NS), new.xpath('.//w:t', namespaces=NS)
assert len(matches) == len(before_nodes) == len(after_nodes)
for i in range(len(matches) - 1, -1, -1):
    if before_nodes[i].text != after_nodes[i].text:
        mt = matches[i]
        xml = xml[:mt.start(2)] + escape(after_nodes[i].text, quote=False).encode('utf-8') + xml[mt.end(2):]

tables = new.xpath('.//w:tbl', namespaces=NS)
caption = deepcopy(body[63])
caption.find('w:r/w:t', NS).text = '表4 GÉANT一周预测的绝对误差（8次重复）'
table = deepcopy(tables[2])
rows = table.findall('w:tr', NS)
for row in rows:
    table.remove(row)
grid = table.find('w:tblGrid', NS)
for c in list(grid):
    grid.remove(c)
widths = [3628, 2608, 2608]
for width in widths:
    E.SubElement(grid, W+'gridCol', {W+'w': str(width)})
templates = [rows[0], *[rows[i] for i in range(6, 11)]]
values = [['方法', 'MSE', 'MAE']] + [[s['name'], s['mse_display'], s['mae_display']] for s in summary]
for template, vals in zip(templates, values):
    row = deepcopy(template)
    cells = row.findall('w:tc', NS)
    row.remove(cells[0])
    for cell, text, width in zip(cells[1:], vals, widths):
        cell.find('w:tcPr/w:tcW', NS).set(W+'w', str(width))
        texts = cell.xpath('.//w:t', namespaces=NS)
        assert len(texts) == 1
        texts[0].text = text
    table.append(row)

blocks = list(re.finditer(rb'<w:p(?:\s[^>]*)?>.*?</w:p>', xml, re.S))
anchor = next(m.start() for m in blocks if b'JournalFigureBox4' in m.group())
xml = xml[:anchor] + E.tostring(caption) + E.tostring(table) + xml[anchor:]
final = E.fromstring(xml)
final_body = final.find('w:body', NS)
assert len(final_body) == len(old.find('w:body', NS)) + 2
assert canonical(final_body[79]) == canonical(caption), ''.join(final_body[79].xpath('.//w:t/text()', namespaces=NS))
assert canonical(final_body[80]) == canonical(table)
for i, p in enumerate(old.find('w:body', NS)):
    if i in [78, 80]:
        continue
    assert canonical(p) == canonical(final_body[i if i < 79 else i+2]), i
assert [canonical(x) for x in old.xpath('.//m:oMath', namespaces=NS)] == [canonical(x) for x in final.xpath('.//m:oMath', namespaces=NS)]
assert [canonical(x) for x in old.xpath('.//w:tbl', namespaces=NS)] == [canonical(x) for x in final.xpath('.//w:tbl', namespaces=NS)[:3]]
image_key = 'word/media/journal_figure1.png'
image = (ASSETS / '图1_样本窗口符号统一.png').read_bytes()
with Image.open(BytesIO(members[image_key])) as a, Image.open(BytesIO(image)) as b:
    assert a.size == b.size, (a.size, b.size)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, xml if info.filename == 'word/document.xml' else image if info.filename == image_key else members[info.filename])
with ZipFile(OUTPUT) as z:
    changed = [k for k, v in members.items() if z.read(k) != v]
assert changed == ['word/document.xml', image_key]
audit = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
         'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'source_unchanged': True,
         'changed_package_parts': changed, 'original_math_and_tables_unchanged': True,
         'figures_2_3_4_unchanged': True, 'existing_paragraphs_unchanged_except_section_2_5': True,
         'original_styles_and_page_geometry_unchanged': True, 'table4_original_records_verified': 40,
         'no_exclusions': True, 'new_training': False, 'table4_summary': summary,
         'edits': edits, 'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
for name in ['export_word.ps1', 'render_verify.py']:
    code = (ROOT / 'review_scratch/eight_seed_unification_20261022' / name).read_text(encoding='utf-8')
    code = code.replace('eight_seed_unification_20261022', 'figure1_table4_20261022')
    if name == 'export_word.ps1':
        code = code.replace("Join-Path $contentQa 'render'", "Join-Path $contentQa 'render_final'")
    if name == 'render_verify.py':
        code = code.replace("assert len(root.xpath('.//w:tbl', namespaces=ns)) == 3", "assert len(root.xpath('.//w:tbl', namespaces=ns)) == 4")
        code = code.replace("'native_math': 16, 'tables': 3,", "'native_math': 16, 'tables': 4,")
        code = code.replace("for token in ['2.77%'", "for token in ['表4GÉANT一周预测的绝对误差（8次重复）', '1.100±0.091', '1.149±0.107', '1.148±0.108', '1.102±0.028', '0.841±0.088', '0.536±0.028', '2.77%'")
    (QA / name).write_text(code, encoding='utf-8')
(QA / 'artifact.md').write_text((QA / 'figure_contract.md').read_text(encoding='utf-8') + '\n\nSource SHA256: ' + SOURCE_SHA + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in audit.items() if k not in ['table4_summary', 'edits']}, ensure_ascii=False))
