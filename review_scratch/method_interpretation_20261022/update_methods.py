from copy import deepcopy
from hashlib import sha256
from html import escape
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '引言研究定位修订_20261022/自适应多尺度加权的多变量网络流量预测_引言研究定位稿.docx'
SOURCE_SHA = '0d54c89e68618e0d1b43dd130c28824da1d29258b421acec1e55bd0401c88e2b'
OUTPUT = JOURNAL / '方法含义说明修订_20261022/自适应多尺度加权的多变量网络流量预测_方法含义说明稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
if OUTPUT.exists():
    current_digest = sha256(OUTPUT.read_bytes()).hexdigest()
    assert current_digest in ['e4e8952807320f0ecf1d04aa34ac04e8ef61347508d5e6e51ee1267420e6f99d', '520c0f1f6d5f94306e9d3f4db6c480df97fc7aa2d1e06deea01217d4e338093e']
    (QA / ('iteration1.docx' if current_digest.startswith('e4e895') else 'iteration2.docx')).write_bytes(OUTPUT.read_bytes())
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old, new = E.fromstring(xml), E.fromstring(xml)
body = new.find('w:body', NS)
changes = [
    (28, 6,
     '为聚合窗口内的时间索引。尺度1保留原序列，尺度2与尺度4分别对相邻2个和4个时间点取均值，因而形成96、48和24步的输入。三个尺度使用结构相同、参数独立的DLinear专家',
     '为聚合窗口内的时间索引。各尺度覆盖同一96\u00a0h历史，分别以1\u00a0h输入值、2\u00a0h均值和4\u00a0h均值构成96、48和24步序列。各尺度使用结构相同、参数独立的DLinear专家'),
    (39, 0,
     '均值与标准差概括标准化窗口的整体水平和离散程度，末时刻均值反映窗口末端的整体状态，而平均绝对一阶差分描述相邻时刻的平均变化幅度。因此，路由网络能够以较低维度接收当前窗口的整体变化信息，并据此计算尺度分数：',
     '均值反映标准化窗口相对训练期均值的整体偏移，标准差概括时间与变量两个维度的离散程度；末时刻均值表征窗口末端状态，平均绝对一阶差分反映相邻小时的变化幅度。由此，路由网络以四维输入汇总窗口状态，尺度分数计算为：'),
]
for p, r, before, after in changes:
    nodes = body[p].findall('w:r', NS)[r].findall('w:t', NS)
    assert len(nodes) == 1 and nodes[0].text == before
    nodes[0].text = after
before_nodes, after_nodes = old.xpath('.//w:t', namespaces=NS), new.xpath('.//w:t', namespaces=NS)
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
assert len(matches) == len(before_nodes) == len(after_nodes)
assert sum(a.text != b.text for a,b in zip(before_nodes, after_nodes)) == 2
for i in range(len(matches)-1, -1, -1):
    if before_nodes[i].text != after_nodes[i].text:
        m = matches[i]
        xml = xml[:m.start(2)] + escape(after_nodes[i].text, quote=False).encode('utf-8') + xml[m.end(2):]
final = E.fromstring(xml)


def without_text(tree):
    tree = deepcopy(tree)
    for node in tree.xpath('.//w:t', namespaces=NS):
        node.text = ''
    return E.tostring(tree)


assert without_text(old) == without_text(final)
for path in ['.//m:oMath', './/w:tbl', './/w:pPr', './/w:rPr', './/w:sectPr', './/w:r[w:rPr/w:vertAlign]']:
    assert [E.tostring(x) for x in old.xpath(path, namespaces=NS)] == [E.tostring(x) for x in final.xpath(path, namespaces=NS)], path
for i, p in enumerate(old.find('w:body', NS)):
    if i not in [28,39]:
        assert E.tostring(p) == E.tostring(final.find('w:body', NS)[i]), i
assert all(96 // s == length for s, length in zip([1,2,4], [96,48,24]))
assert 4*16+16+16*3+3 == 131
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, xml if info.filename == 'word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    changed = [k for k,v in members.items() if z.read(k) != v]
assert changed == ['word/document.xml']
audit = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
         'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'source_unchanged': True,
         'changed_package_parts': changed, 'only_method_explanation_paragraphs_28_39_changed': True,
         'all_format_properties_unchanged': True, 'all_citations_references_abstracts_and_introduction_unchanged': True,
         'all_math_tables_figures_and_results_unchanged': True, 'moving_average_description_and_kernels_unchanged': True,
         'algorithm_and_experiments_unchanged': True,
         'edits': [{'paragraph': p, 'run': r, 'before': b, 'after': a} for p,r,b,a in changes],
         'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Method interpretation revision\n\nRetain the latest accepted introduction-positioned manuscript, SHA256 '+SOURCE_SHA+'. '
    'Only revise the explanatory text after equations 5 and 10. '
    'All scale branches cover the same 96-hour history with 1-, 2- and 4-hour aggregation resolution and 96, 48 and 24 steps. '
    'Do not equate aggregation resolution with half-day/daily/weekly periodicity. The data are already log-transformed and standardized. '
    'Interpret the four statistics as standardized mean displacement, joint temporal/channel dispersion, end-of-window aggregate state and mean absolute hourly change. '
    'Do not call these raw total traffic load, energy, peak traffic detection, validated routing regimes or protection against overfitting. '
    'Keep the deferred moving-average issue untouched: q=25, its padding, all equations and code remain unchanged. '
    'No new experiments, no new evidence or claims about mechanisms. Retain all references, abstracts, introduction, results, tables, figures and format properties. '
    'Native Word export and packaged rasterization, then every-page visual review before delivery.\n', encoding='utf-8')
for name in ['export_word.ps1', 'render_verify.py']:
    code = (ROOT / 'review_scratch/introduction_positioning_20261022' / name).read_text(encoding='utf-8')
    code = code.replace('introduction_positioning_20261022', 'method_interpretation_20261022')
    if name == 'export_word.ps1':
        code = code.replace("Join-Path $contentQa 'render_final'", "Join-Path $contentQa 'render_checked'")
    (QA / name).write_text(code, encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='edits'}, ensure_ascii=False))
