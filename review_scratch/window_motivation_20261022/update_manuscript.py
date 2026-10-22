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
SOURCE = JOURNAL / '优势补充与图表优化_20261022/自适应多尺度加权的多变量网络流量预测_优势补充稿.docx'
OUTPUT = JOURNAL / '窗口动机衔接修订_20261022/自适应多尺度加权的多变量网络流量预测_窗口动机修订稿.docx'
SOURCE_SHA = '30e83a8325d6c6800e76e65151b7af4c2c9e2a7cb754e65dcc736cec5ef21ca3'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert not OUTPUT.exists(), 'Retain all existing versions'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old = E.fromstring(xml)
new = E.fromstring(xml)
body = new.find('w:body', NS)
edits = []


def replace(p, r, before, after):
    nodes = body[p].findall('w:r', NS)[r].xpath('.//w:t', namespaces=NS)
    assert len(nodes) == 1 and nodes[0].text == before, (p, r)
    nodes[0].text = after
    edits.append({'paragraph': p, 'run': r, 'before': before, 'after': after})


replace(10, 0,
    '骨干网的容量配置与资源管理需要估计未来的通信需求，而源—目的节点对（origin-destination，OD）的流量预测能够为需求分析提供数据依据。小时级OD流量既包含局部波动，也呈现较慢的趋势变化；同时，不同变量的量级和变化节奏存在差异。因此，预测模型需要从历史序列中提取不同时间尺度的信息，并将其转化为未来多个时刻的预测结果。',
    '骨干网的容量配置与资源管理需要估计未来的通信需求，而源—目的节点对（origin-destination，OD）的流量预测能够为需求分析提供数据依据。小时级OD流量既包含局部波动，也呈现较慢的趋势变化，而且不同历史窗口的波动幅度与近期变化状态有所不同。因此，预测模型需要提取不同时间尺度的信息，并结合当前窗口的统计特征融合各尺度预测，从而估计未来多个时刻的流量需求。')
replace(36, 8, '，组成四维特征向量', '，组成四维窗口整体统计特征向量')
replace(39, 0,
    '均值与标准差概括窗口的整体水平和离散程度，末时刻均值反映近期状态，而平均绝对一阶差分描述相邻时刻的变化幅度。因此，路由网络能够以较低维度接收与当前窗口有关的信息，并据此计算尺度分数：',
    '均值与标准差概括标准化窗口的整体水平和离散程度，末时刻均值反映窗口末端的整体状态，而平均绝对一阶差分描述相邻时刻的平均变化幅度。因此，路由网络能够以较低维度接收当前窗口的整体变化信息，并据此计算尺度分数：')

before_nodes = old.xpath('.//w:t', namespaces=NS)
after_nodes = new.xpath('.//w:t', namespaces=NS)
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
assert len(before_nodes) == len(after_nodes) == len(matches)
for i in range(len(matches) - 1, -1, -1):
    if before_nodes[i].text != after_nodes[i].text:
        match = matches[i]
        xml = xml[:match.start(2)] + escape(after_nodes[i].text or '', quote=False).encode('utf-8') + xml[match.end(2):]
final = E.fromstring(xml)


def without_text(tree):
    tree = deepcopy(tree)
    for node in tree.xpath('.//w:t', namespaces=NS):
        node.text = ''
    return E.tostring(tree)


assert without_text(old) == without_text(final)
for path in ['.//w:tbl', './/m:oMath', './/w:pPr', './/w:rPr', './/w:sectPr']:
    assert [E.tostring(x) for x in old.xpath(path, namespaces=NS)] == [E.tostring(x) for x in final.xpath(path, namespaces=NS)], path
numeric_tokens = lambda tree: re.findall(r'\d+(?:\.\d+)?', ''.join(tree.xpath('.//w:t/text()', namespaces=NS)))
assert numeric_tokens(old) == numeric_tokens(final)
assert len(edits) == 3
OUTPUT.parent.mkdir(parents=True)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, xml if info.filename == 'word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    changed = [key for key, value in members.items() if z.read(key) != value]
assert changed == ['word/document.xml']
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
report = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
          'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'source_unchanged': True,
          'changed_package_parts': changed, 'styles_and_format_properties_unchanged': True,
          'all_original_tables_and_math_unchanged': True, 'all_figures_unchanged': True,
          'all_numeric_text_unchanged': True, 'new_experiments': False,
          'edits': edits, 'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Window motivation revision\n\n'
    'Authority: the retained journal manuscript, SHA256 ' + SOURCE_SHA + '.\n'
    'Apply only the accepted introductory paragraph and clarify the window-level statistics in section 1.3. '
    'Do not equate standardized window summaries with raw total network load or claim individually adaptive variable weights. '
    'Preserve all equations, numerical tokens, tables, figures, reference entries, fonts, runs, paragraph structure and page geometry. '
    'The existing statement that weights are shared across variables and forecast steps remains unchanged. '
    'No algorithm changes, moving-average changes or new experiments. Retain the source manuscript.\n', encoding='utf-8')
previous_qa = ROOT / 'review_scratch/advantages_20261022'
for name in ['export_word.ps1', 'render_verify.py']:
    code = (previous_qa / name).read_text(encoding='utf-8').replace('advantages_20261022', 'window_motivation_20261022')
    (QA / name).write_text(code, encoding='utf-8')
print(json.dumps({key: value for key, value in report.items() if key != 'edits'}, ensure_ascii=False))
