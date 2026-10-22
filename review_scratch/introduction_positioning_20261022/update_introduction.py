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
SOURCE = JOURNAL / '摘要强化修订_20261022/自适应多尺度加权的多变量网络流量预测_摘要强化稿.docx'
SOURCE_SHA = '0584c193ad08ec053f4d6d9c61072e233b5c14a1a95559b4280f997d6f44fb84'
OUTPUT = JOURNAL / '引言研究定位修订_20261022/自适应多尺度加权的多变量网络流量预测_引言研究定位稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert not OUTPUT.exists()
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old, new = E.fromstring(xml), E.fromstring(xml)
body = new.find('w:body', NS)
changes = [
    (12, 8,
     '则将基于多层感知机（multilayer perceptron，MLP）的LightTS纳入比较。本文关注以低维窗口特征调整不同尺度预测的融合权重。',
     '则将基于多层感知机（multilayer perceptron，MLP）的LightTS纳入比较。多尺度信息的提取还需与融合方式相配合。固定等权或全局权重在窗口间共享融合系数，因而不能根据当前窗口的变化状态调整尺度权重。本文关注如何在控制参数规模的同时，利用窗口信息调整尺度权重。'),
    (13, 0,
     '本文据此将三个独立DLinear专家与四维统计特征驱动的尺度路由相结合。时间聚合形成多尺度输入，各专家在OD变量间共享时间映射，路由网络则随窗口状态调整融合权重，以较少参数完成样本级融合。在Abilene和GÉANT上，以过去96 h预测未来24 h，通过基线比较、融合消融与高需求分析评价模型，并在GÉANT上考察未来168 h的一周预测表现。',
     '据此，本文将三个独立DLinear专家与四维窗口统计特征驱动的尺度路由相结合，构建自适应多尺度加权预测模型。时间聚合形成多分辨率输入，各专家在OD变量间共享时间映射，使参数量不随变量数增加；路由网络仅含131个参数，根据窗口状态分配尺度权重。在Abilene和GÉANT上以96 h输入开展24 h预测、融合消融与高需求点分析，并在GÉANT上开展168 h预测，评价预测误差与参数规模。'),
]
for p, r, before, after in changes:
    nodes = body[p].findall('w:r', NS)[r].findall('w:t', NS)
    assert len(nodes) == 1 and nodes[0].text == before, (p, r)
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
    if i not in [12, 13]:
        assert E.tostring(p) == E.tostring(final.find('w:body', NS)[i]), i
all_text = ''.join(final.xpath('.//w:t/text()', namespaces=NS))
assert '4×16+16+16×3+3=131' in all_text
for p in [12,13]:
    s = ''.join(final.find('w:body', NS)[p].xpath('.//w:t/text()', namespaces=NS))
    assert not any(t in s for t in ['显著领先', '过拟合', '不可替代', '普遍依赖', '仅用131个额外参数', '90分位高需求峰值'])

OUTPUT.parent.mkdir(parents=True)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, xml if info.filename == 'word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    changed = [k for k,v in members.items() if z.read(k) != v]
assert changed == ['word/document.xml']
audit = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
         'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'source_unchanged': True,
         'changed_package_parts': changed, 'only_introduction_paragraphs_3_4_changed': True,
         'all_format_properties_unchanged': True, 'all_citations_and_references_unchanged': True,
         'all_original_math_tables_figures_and_abstracts_unchanged': True, 'new_experiments': False,
         'edits': [{'paragraph': p, 'run': r, 'before': b, 'after': a} for p,r,b,a in changes],
         'paragraph_lengths': [{'paragraph': p, 'before': len(''.join(old.find('w:body', NS)[p].xpath('.//w:t/text()',namespaces=NS))),
                               'after': len(''.join(final.find('w:body', NS)[p].xpath('.//w:t/text()',namespaces=NS)))} for p in [12,13]],
         'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Introduction positioning revision\n\nAuthority: retain the accepted abstract-strengthened manuscript, SHA256 '+SOURCE_SHA+'. '
    'Change only the last text run of introduction paragraph 3 and the text run of paragraph 4. '
    'Retain the existing literature summaries and all superscript citation runs. '
    'Explain the architectural limit of window-invariant coefficients without claiming noise sensitivity or empirical failure of all static methods. '
    'Position the proposed model using its channel-shared expert mappings and 131-parameter window router. '
    'Do not describe standardized window statistics as raw total network load, or infer speed, overfitting, universal superiority or statistical significance. '
    'Retain the established terminology: fixed equal weights, global weights, window statistics, scale routing, high-demand points. '
    'Preserve both abstracts, all evidence, figures, tables, native equations, references, runs, formatting and page geometry. '
    'Render with Word and the packaged rasterizer; review all final page PNGs.\n', encoding='utf-8')
for name in ['export_word.ps1', 'render_verify.py']:
    code = (ROOT / 'review_scratch/abstract_strengthening_20261022' / name).read_text(encoding='utf-8')
    code = code.replace('abstract_strengthening_20261022', 'introduction_positioning_20261022')
    (QA / name).write_text(code, encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='edits'}, ensure_ascii=False))
