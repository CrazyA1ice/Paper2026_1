from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
FOLDER = ROOT / 'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023'
SOURCE = FOLDER / '自适应多尺度加权的多变量网络流量预测_ccgcxyxbV6_摘要局部修订稿.docx'
OUTPUT = FOLDER / '自适应多尺度加权的多变量网络流量预测_ccgcxyxbV7_摘要精简稿.docx'
SOURCE_SHA = '518ec952a88674a8286c005561154d32c9b9f56cf6487adb83f12348116c731a'
CHINESE = '针对骨干网小时级源—目的（OD）流量序列兼具高频突发波动与长周期演化趋势、传统多尺度模型参数冗余且静态融合易受噪声干扰的问题，提出一种自适应多尺度加权的多变量网络流量预测方法。该方法利用三个分解线性专家（DLinear），提取四维统计特征，自适应生成融合权重。Abilene和GÉANT实验表明：24 h均方误差较LightTS平均降低25.77%和43.74%，参数量为其6.41%和2.17%。'
ENGLISH = 'An adaptive multiscale weighting method is proposed for multivariate network traffic forecasting to address the coexistence of high-frequency burst fluctuations and long-term evolution in hourly origin-destination (OD) traffic series of backbone networks, as well as parameter redundancy and noise-sensitive static fusion in conventional multiscale models. The method uses three decomposition linear (DLinear) experts, extracts four-dimensional statistical features, and adaptively generates fusion weights. Experiments on Abilene and GÉANT show mean relative reductions in 24-hour mean squared error of 25.77% and 43.74%, respectively, compared with LightTS, with parameter counts equivalent to 6.41% and 2.17% of the respective LightTS configurations.'
assert len(CHINESE) == 199
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert not OUTPUT.exists(), OUTPUT
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
old = E.fromstring(members['word/document.xml'])
new = E.fromstring(members['word/document.xml'])
body = new.find('w:body', NS)
changes = []
for prefix, text in [('摘要：', CHINESE), ('Abstract:', ENGLISH)]:
    matches = [(i, p) for i, p in enumerate(body)
               if ''.join(p.xpath('.//w:t/text()', namespaces=NS)).startswith(prefix)]
    assert len(matches) == 1
    index, paragraph = matches[0]
    nodes = paragraph.xpath('.//w:t', namespaces=NS)
    assert len(nodes) == 2 and nodes[0].text.strip() == prefix
    before = ''.join(n.text or '' for n in nodes)
    if prefix == '摘要：':
        assert nodes[1].text.split('。')[0] == CHINESE.split('。')[0]
    nodes[1].text = (' ' if prefix == 'Abstract:' else '') + text
    changes.append({'index': index, 'before': before,
                    'after': ''.join(n.text or '' for n in nodes)})

def canon(node):
    node = deepcopy(node)
    E.cleanup_namespaces(node)
    return E.tostring(node, method='c14n')

old_body = old.find('w:body', NS)
assert len(old_body) == len(body)
for index, (a, b) in enumerate(zip(old_body, body)):
    if index in {item['index'] for item in changes}:
        a, b = deepcopy(a), deepcopy(b)
        for node in a.xpath('.//w:t', namespaces=NS) + b.xpath('.//w:t', namespaces=NS):
            node.text = ''
    assert canon(a) == canon(b), index
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, E.tostring(new, xml_declaration=True, encoding='UTF-8', standalone=True)
                   if info.filename == 'word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    assert [name for name, data in members.items() if z.read(name) != data] == ['word/document.xml']
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
audit = {
    'source': str(SOURCE), 'source_sha256': SOURCE_SHA,
    'output': str(OUTPUT), 'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(),
    'source_unchanged': True, 'only_two_abstracts_changed': True,
    'chinese_first_sentence_unchanged': True, 'chinese_abstract_characters': len(CHINESE),
    'all_other_body_nodes_unchanged': True,
    'all_styles_figures_tables_equations_unchanged': True,
    'native_math_objects': len(new.xpath('//m:oMath', namespaces=NS)),
    'edits': changes, 'visual_review_pending': True,
}
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Approved abstract compression\n\n'
    'Use the exact 199-character Chinese abstract approved by the user. Preserve its first sentence. '
    'Synchronize the English abstract. Change no other prose, data, figures, equations, tables, '
    'styles or paragraph properties. Preserve V6. Render and inspect before delivery.\n\n'
    'Terminology: OD = origin-destination; DLinear = decomposition linear; '
    'Abilene; GÉANT; LightTS; mean squared error; 24-hour forecasting.\n', encoding='utf-8')
print(json.dumps({k: v for k, v in audit.items() if k != 'edits'}, ensure_ascii=False))
