from copy import deepcopy
from hashlib import sha256
from html import escape
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import re
import statistics as st
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '图1与一周预测表修订_20261022/自适应多尺度加权的多变量网络流量预测_图1与一周预测表修订稿.docx'
SOURCE_SHA = '3dcd7851350ab8492488c2dfffd056eb365887fcfbbcb5cfa2fcd163c4f2fc34'
OUTPUT = JOURNAL / '摘要强化修订_20261022/自适应多尺度加权的多变量网络流量预测_摘要强化稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
if OUTPUT.exists():
    assert sha256(OUTPUT.read_bytes()).hexdigest() == 'd8fab95afdb577e4020c90ca182783223e31aa42147ea601db99acebad47e96d'
    (QA / 'iteration1.docx').write_bytes(OUTPUT.read_bytes())

CN = '提出自适应多尺度加权方法，按窗口统计量融合三个分解线性模型（DLinear）的小时级流量预测。8次重复中，Abilene和GÉANT的24 h均方误差较LightTS平均降低25.77%和43.74%，参数量为其6.41%和2.17%。较DLinear，Abilene高需求点平均低估误差降低16.07%，GÉANT的168 h均方误差和平均绝对误差降低23.16%和11.16%，辅助容量需求估计。'
EN = (' An adaptive multiscale weighting method forecasts hourly traffic by combining three decomposition linear models (DLinear) according to window statistics. '
      'Across eight training runs, mean relative reductions in 24-hour mean squared error versus LightTS are 25.77% on Abilene and 43.74% on GÉANT. '
      'Parameter counts are 6.41% and 2.17% of the respective LightTS configurations. '
      'Relative to DLinear, the mean shortfall at high-demand Abilene points decreases by 16.07%. '
      'For 168-hour GÉANT forecasting against DLinear, mean squared error and mean absolute error decrease by 23.16% and 11.16%, respectively. '
      'These results support capacity demand estimation using hourly traffic forecasts.')
assert len(CN) <= 200, len(CN)
assert all(len(s.split()) <= 30 for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', EN.strip()))

# Reconcile every numerical claim with the existing, verified experiments.
baseline = json.loads((ROOT / 'review_scratch/eight_seed_unification_20261022/data_audit.json').read_text(encoding='utf-8'))
effects = {(r['dataset'], r['metric']): r for r in baseline['effects']}
assert f'{effects["abilene","mse"]["mean"]:.2f}' == '25.77'
assert f'{effects["geant","mse"]["mean"]:.2f}' == '43.74'
assert f'{effects["abilene","mse"]["parameter_ratio_pct"]:.2f}' == '6.41'
assert f'{effects["geant","mse"]["parameter_ratio_pct"]:.2f}' == '2.17'
with (ROOT / 'abilene_forecasting/results/high_demand_analysis/per_seed.csv').open(encoding='utf-8-sig', newline='') as f:
    high = {(r['model'], int(r['seed'])): r for r in csv.DictReader(f) if r['dataset'] == 'abilene'}
shortfall = [100 * (float(high['dlinear',s]['mean_shortfall']) - float(high['dlinear_scale',s]['mean_shortfall'])) / float(high['dlinear',s]['mean_shortfall']) for s in range(42,50)]
assert f'{st.mean(shortfall):.2f}' == '16.07'
with (ROOT / 'abilene_forecasting/results/long_horizon_20261021/per_seed_scores.csv').open(encoding='utf-8-sig', newline='') as f:
    week = {(r['model'], int(r['seed'])): r for r in csv.DictReader(f) if r['dataset'] == 'geant' and int(r['horizon']) == 168}
for metric, expected in [('mse', '23.16'), ('mae', '11.16')]:
    v = [100 * (float(week['dlinear',s]['all_'+metric]) - float(week['dlinear_scale',s]['all_'+metric])) / float(week['dlinear',s]['all_'+metric]) for s in range(42,50)]
    assert f'{st.mean(v):.2f}' == expected

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old, new = E.fromstring(xml), E.fromstring(xml)
body = new.find('w:body', NS)
edits = []
for index, label, value in [(5, '摘要：', CN), (104, 'Abstract:', EN)]:
    nodes = body[index].xpath('./w:r/w:t', namespaces=NS)
    assert len(nodes) == 2 and nodes[0].text == label
    edits.append({'paragraph': index, 'before': nodes[1].text, 'after': value})
    nodes[1].text = value
before, after = old.xpath('.//w:t', namespaces=NS), new.xpath('.//w:t', namespaces=NS)
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
assert len(matches) == len(before) == len(after)
assert sum(a.text != b.text for a,b in zip(before,after)) == 2
for i in range(len(matches)-1, -1, -1):
    if before[i].text != after[i].text:
        m = matches[i]
        xml = xml[:m.start(2)] + escape(after[i].text, quote=False).encode('utf-8') + xml[m.end(2):]
final = E.fromstring(xml)
def no_text(t):
    t = deepcopy(t)
    for node in t.xpath('.//w:t', namespaces=NS):
        node.text = ''
    return E.tostring(t)
assert no_text(old) == no_text(final)
for path in ['.//m:oMath', './/w:tbl', './/w:pPr', './/w:rPr', './/w:sectPr']:
    assert [E.tostring(x) for x in old.xpath(path, namespaces=NS)] == [E.tostring(x) for x in final.xpath(path, namespaces=NS)]
for i, p in enumerate(old.find('w:body', NS)):
    if i not in [5,104]:
        assert E.tostring(p) == E.tostring(final.find('w:body', NS)[i]), i
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, xml if info.filename == 'word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    changed = [k for k,v in members.items() if z.read(k) != v]
assert changed == ['word/document.xml']
audit = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
         'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'changed_package_parts': changed,
         'source_unchanged': True, 'only_abstracts_changed': True, 'format_and_geometry_unchanged': True,
         'all_math_tables_figures_and_main_text_unchanged': True, 'chinese_abstract_characters': len(CN),
         'english_abstract_words': len(EN.split()), 'claims_verified': True, 'new_experiments': False,
         'edits': edits, 'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Abstract strengthening\n\nRetain the accepted journal manuscript, SHA256 '+SOURCE_SHA+'. '
    'Revise only the two abstract text runs. Chinese abstract <=200 characters according to the supplied submission guide. '
    'Preserve third person, one paragraph, first-use DLinear expansion and exact claim alignment with English. '
    'Use current eight-seed paired mean reductions; high-demand result applies to Abilene only and compares mean shortfall with DLinear. '
    'Do not call high-demand points peak events or infer noise resistance, universal stability, speed, runtime or deployment outcomes. '
    'Retain all existing body text, native equations, four tables, four figures, page geometry and formatting. '
    'Term ledger: 自适应多尺度加权/adaptive multiscale weighting; 分解线性模型/decomposition linear model (DLinear); '
    '均方误差/mean squared error; 平均绝对误差/mean absolute error; 平均低估误差/mean shortfall. '
    'Final gate: native Word export, packaged page rasterization, every page visually inspected.\n', encoding='utf-8')
for name in ['export_word.ps1', 'render_verify.py']:
    code = (ROOT / 'review_scratch/figure1_table4_20261022' / name).read_text(encoding='utf-8')
    code = code.replace('figure1_table4_20261022', 'abstract_strengthening_20261022')
    (QA / name).write_text(code, encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='edits'}, ensure_ascii=False))
