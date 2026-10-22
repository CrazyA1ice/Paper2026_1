from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
SOURCE = ROOT / 'word_output/2026.10.07v70.docx'
TARGET = ROOT / 'word_output/2026.10.07v71.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W, 'm': M}
Q = lambda tag: f'{{{W}}}{tag}'
SPACE = '{http://www.w3.org/XML/1998/namespace}space'
with ZipFile(SOURCE) as archive:
    infos = archive.infolist()
    parts = {info.filename: archive.read(info.filename) for info in infos}
original = etree.fromstring(parts['word/document.xml'])
root = deepcopy(original)
ps = root.xpath('./w:body/w:p', namespaces=NS)
visible = lambda p: ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS))
before = [visible(p) for p in ps]
changes = []

def replace(index, old, new, reason):
    nodes = ps[index].xpath('.//w:t | .//m:t', namespaces=NS)
    joined = ''.join(node.text or '' for node in nodes)
    assert joined.count(old) == 1, (index, old)
    start = joined.index(old)
    end = start + len(old)
    position = 0
    first = True
    for node in nodes:
        text = node.text or ''
        node_end = position + len(text)
        if position < end and node_end > start:
            assert node.tag == Q('t'), 'Mathematics is protected'
            left = max(0, start - position)
            right = min(len(text), end - position)
            node.text = text[:left] + (new if first else '') + text[right:]
            node.set(SPACE, 'preserve')
            first = False
        position = node_end
    changes.append({'paragraph': index, 'before': old, 'after': new, 'reason': reason})

replace(3,
        '骨干网络流量在小时尺度上的预测要兼顾短期波动和长期趋势，为此设计一种轻量自适应多尺度预测模型。',
        '为兼顾小时级骨干网络流量预测中的短期波动与长期趋势，设计一种轻量自适应多尺度预测模型。',
        '要求5：删除背景式开头，直接陈述研究目的；保留原有研究对象及方法')
replace(9,
        'Hourly forecasting of backbone network traffic requires consideration of both short-term fluctuations and long-term trends. A lightweight adaptive multiscale forecasting model was therefore developed.',
        'A lightweight adaptive multiscale forecasting model was developed to account for short-term fluctuations and long-term trends in hourly backbone network traffic forecasting.',
        '要求9：与中文摘要对应，以过去时直接陈述研究目的')
replace(32, before[32],
        '各尺度序列由同一预处理历史窗口构造，分别保留细粒度变化或较平滑的趋势。',
        '要求10：合并已在框架说明中给出的预处理顺序与共同输入说明，保留尺度构造含义')
replace(70, 'LightTS采用THUML公开实现',
        'LightTS采用清华大学软件学院机器学习组的公开实现',
        '要求10：用机构完整名称替代没有解释的THUML缩写')
replace(122, 'Artificial Intelligence. 2023', 'Artificial Intelligence, 2023',
        '要求17：刊名与出版年之间使用逗号，与期刊文献著录格式一致')

# Split only ordinary text runs containing actual quantity symbols. Native
# equations and their existing italic / bold-italic properties remain intact.
symbol_pattern = re.compile(r'(?<![A-Za-z])[tCnLHsqNS](?![A-Za-z])')
formatting = []
for index in [24, 27, 35, 37, 39, 42, 44, 58, 65, 91, 103]:
    for run in list(ps[index].xpath('./w:r', namespaces=NS)):
        nodes = run.findall(Q('t'))
        if len(nodes) != 1:
            continue
        value = nodes[0].text or ''
        matches = list(symbol_pattern.finditer(value))
        if not matches:
            continue
        assert all(child.tag in [Q('rPr'), Q('t')] for child in run)
        pieces = []
        cursor = 0
        for match in matches:
            if match.start() > cursor:
                pieces.append((value[cursor:match.start()], False))
            pieces.append((match.group(), True))
            cursor = match.end()
        if cursor < len(value):
            pieces.append((value[cursor:], False))
        position = ps[index].index(run)
        for offset, (content, italic) in enumerate(pieces):
            replacement = deepcopy(run)
            props = replacement.find(Q('rPr'))
            if props is None:
                props = etree.Element(Q('rPr'))
                replacement.insert(0, props)
            flag = props.find(Q('i'))
            if flag is None:
                flag = etree.SubElement(props, Q('i'))
            flag.set(Q('val'), '1' if italic else '0')
            replacement.find(Q('t')).text = content
            replacement.find(Q('t')).set(SPACE, 'preserve')
            ps[index].insert(position + offset, replacement)
        ps[index].remove(run)
        formatting.append({'paragraph': index, 'text': value, 'symbols': [m.group() for m in matches]})

outline_changes = []
for index in [16, 62, 114]:
    props = ps[index].find(Q('pPr'))
    outline = props.find(Q('outlineLvl'))
    old_level = None if outline is None else outline.get(Q('val'))
    if outline is None:
        outline = etree.SubElement(props, Q('outlineLvl'))
    outline.set(Q('val'), '0')
    outline_changes.append({'paragraph': index, 'before': old_level, 'after': 0})
header_runs = root.xpath('//w:tbl[1]/w:tr[1]//w:r[w:t="C" or w:t="L/H"]', namespaces=NS)
assert len(header_runs) == 2
for run in header_runs:
    props = run.find(Q('rPr'))
    assert props is not None
    italic = props.find(Q('i'))
    if italic is None:
        italic = etree.SubElement(props, Q('i'))
    italic.set(Q('val'), '1')
after = [visible(p) for p in ps]

# The experimental results, all tables, all images and all math objects are
# protected byte for byte; only prose and ordinary text formatting are edited.
assert [etree.tostring(x) for x in original.xpath('//m:oMath', namespaces=NS)] == [etree.tostring(x) for x in root.xpath('//m:oMath', namespaces=NS)]
old_tables = original.xpath('//w:tbl', namespaces=NS)
new_tables = root.xpath('//w:tbl', namespaces=NS)
assert [etree.tostring(x) for x in old_tables[1:]] == [etree.tostring(x) for x in new_tables[1:]]
def without_italics(table):
    copy = deepcopy(table)
    for flag in copy.xpath('.//w:i', namespaces=NS):
        flag.getparent().remove(flag)
    return etree.tostring(copy)
assert without_italics(old_tables[0]) == without_italics(new_tables[0])
for i in range(128):
    assert re.findall(r'\d+(?:\.\d+)?', before[i]) == re.findall(r'\d+(?:\.\d+)?', after[i]), i
assert before[65:70] == after[65:70]
assert before[71:122] == after[71:122]
abstract = after[3][3:]
han = len(re.findall(r'[\u4e00-\u9fff]', abstract))
chars = len(re.sub(r'\s', '', abstract))
assert 300 <= han <= 400 and 300 <= chars <= 400
assert not any(term in abstract for term in ['我们', '作者', '本文', '笔者'])
assert len(re.sub(r'\s', '', after[115])) <= 150
reference_order = list(dict.fromkeys(int(n) for n in re.findall(r'\[(\d+)\]', '\n'.join(after[:116]))))
assert reference_order == list(range(1, 12))

parts['word/document.xml'] = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with ZipFile(TARGET, 'w') as archive:
    for info in infos:
        archive.writestr(info, parts[info.filename])
with ZipFile(SOURCE) as old, ZipFile(TARGET) as new:
    unchanged_parts = [name for name in old.namelist() if name != 'word/document.xml']
    assert all(old.read(name) == new.read(name) for name in unchanged_parts)

audit = {
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'target_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'prose_changes': changes,
    'ordinary_text_symbol_formatting': formatting,
    'heading_outline': outline_changes,
    'native_math_objects_identical': len(root.xpath('//m:oMath', namespaces=NS)),
    'table_data_and_geometry_identical': 3,
    'tables_2_3_xml_identical': True,
    'table1_header_italic_only': ['C', 'L/H'],
    'all_media_identical': True,
    'all_paragraph_numeric_sequences_identical': True,
    'unchanged_package_parts': len(unchanged_parts),
    'abstract_han_characters': han,
    'abstract_nonspace_characters': chars,
    'conclusion_nonspace_characters': len(re.sub(r'\s', '', after[115])),
    'reference_first_appearance_order': reference_order,
}
(QA / 'preservation_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'manuscript_v71.txt').write_text('\n'.join(f'P{i}: {t}' for i,t in enumerate(after)), encoding='utf-8')
print(json.dumps({key: value for key, value in audit.items() if key not in ['prose_changes', 'ordinary_text_symbol_formatting']}, ensure_ascii=False))
