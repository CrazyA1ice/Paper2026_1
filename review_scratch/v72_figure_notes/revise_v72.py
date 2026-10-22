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
SOURCE = ROOT / 'word_output/2026.10.07v71.docx'
TARGET = ROOT / 'word_output/2026.10.07v72.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
Q = lambda tag: f'{{{W}}}{tag}'
SPACE = '{http://www.w3.org/XML/1998/namespace}space'
with ZipFile(SOURCE) as archive:
    infos = archive.infolist()
    parts = {info.filename: archive.read(info.filename) for info in infos}
original = etree.fromstring(parts['word/document.xml'])
root = deepcopy(original)
ps = root.xpath('./w:body/w:p', namespaces=NS)
visible = lambda p: ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS))
assert len(ps) == 128
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
            assert node.tag == Q('t'), 'Native mathematics is protected'
            left = max(0, start-position)
            right = min(len(text), end-position)
            node.text = text[:left] + (new if first else '') + text[right:]
            node.set(SPACE, 'preserve')
            first = False
        position = node_end
    changes.append({'paragraph_v71': index, 'before': old, 'after': new, 'reason': reason})

replace(17, '图1包含专家预测和窗口路由两部分。',
        '图1包含共享同一预处理历史窗口的预测分支与路由分支，梯形虚线展开DLinear专家内部结构。',
        '图1图注的共享输入与结构展开说明合并到图前正文')
replace(17, '给出模型输出。', '给出模型输出。图中曲线和色块仅作示意。',
        '保留机制示意与实验数据的区分')
replace(75, '改进率按共同种子配对计算后求平均，',
        '改进率为对照模型与本文方法的误差之差除以对照误差，按共同种子配对计算后求平均，',
        '将图2误差降低率定义合并到已有统计计算说明，供图2与图3共同使用')
replace(77, '在图2中进一步比较。',
        '在图2中进一步比较，参数比例以各数据集的LightTS参数量为参照。',
        '图2归一化参照移至图前说明，种子范围不重复')
replace(88, before[88],
        before[88] + '散点为单个种子的改进率，黑色菱形及横向误差线分别为均值和95%置信区间。',
        '图3仅保留统计点与置信区间的必要解读，删去种子范围和零线等重复说明')
replace(95, before[95],
        '图4（a、b）将8个种子的全测试预测点按真实值分位点分为最多40组，展示分组平均预测，浅色带表示种子间±1个标准差。图4（c～f）使用种子42，按真实序列选取标准差接近第75百分位的OD通道，以及平均绝对一阶差分接近中位数、第90百分位的窗口。',
        '图4的统计汇总与真实序列选例依据压缩后移至图前正文；删除图例中已有的理想线解释')
replace(100, before[100],
        '图5汇总8个种子的测试窗口权重，彩色点为各随机种子的窗口平均权重，黑色菱形及误差线为这些均值的均值±1个标准差；短横线表示汇总分布中位数，水平虚线表示固定等权1/3。',
        '图5保留汇总层级与误差线的含义，删除颜色对应和重复的分布来源解释')

notes = [20, 81, 91, 98, 103]
captions = [19, 80, 90, 97, 102]
note_changes = []
for number, index in enumerate(notes, 1):
    assert before[index].startswith('注：')
    note_changes.append({'figure': number, 'paragraph_v71': index, 'before': before[index], 'after': '', 'action': '删除独立图注段落，必要信息压缩并移入正文'})
    ps[index].getparent().remove(ps[index])
heading_props = ps[84].find(Q('pPr'))
page_break = heading_props.find(Q('pageBreakBefore'))
if page_break is None:
    page_break = etree.SubElement(heading_props, Q('pageBreakBefore'))
page_break.set(Q('val'), '1')

changed = {17,75,77,84,88,95,100} | set(notes)
old_ps = original.xpath('./w:body/w:p', namespaces=NS)
for index in range(128):
    if index not in changed:
        assert etree.tostring(old_ps[index]) == etree.tostring(ps[index]), index
for index in captions:
    assert etree.tostring(old_ps[index]) == etree.tostring(ps[index])
assert visible(ps[84]) == before[84]
assert [etree.tostring(x) for x in original.xpath('//m:oMath', namespaces=NS)] == [etree.tostring(x) for x in root.xpath('//m:oMath', namespaces=NS)]
assert [etree.tostring(x) for x in original.xpath('//w:tbl', namespaces=NS)] == [etree.tostring(x) for x in root.xpath('//w:tbl', namespaces=NS)]
after = [visible(p) for p in root.xpath('./w:body/w:p', namespaces=NS)]
assert len(after) == 123
assert not any(t.startswith('注：') for t in after)
assert list(dict.fromkeys(int(n) for n in re.findall(r'\[(\d+)\]', '\n'.join(after[:-12])))) == list(range(1,12))
assert all(token in '\n'.join(after) for token in ['95%置信区间', '±1个标准差', '最多40组', '第75百分位', '第90百分位', '仅作示意'])

parts['word/document.xml'] = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
with ZipFile(TARGET, 'w') as archive:
    for info in infos:
        archive.writestr(info, parts[info.filename])
with ZipFile(SOURCE) as old, ZipFile(TARGET) as new:
    assert all(old.read(name) == new.read(name) for name in old.namelist() if name != 'word/document.xml')
count_chars = lambda s: len(re.sub(r'\s', '', s))
audit = {
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'target_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'paragraph_changes': changes, 'deleted_figure_notes': note_changes,
    'note_characters_before': sum(count_chars(before[i]) for i in notes),
    'note_characters_after': 0,
    'body_characters_added': sum(count_chars(visible(ps[i])) - count_chars(before[i]) for i in [17,75,77,88,95,100]),
    'native_math_objects_identical': len(root.xpath('//m:oMath', namespaces=NS)),
    'tables_identical': 3, 'all_media_identical': True,
    'unrelated_paragraphs_xml_identical': True,
    'captions_text_and_font_identical': True,
    'pagination_adjustment': '第2.3节另页开始，避免表3跨页',
}
(QA / 'preservation_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'manuscript_v72.txt').write_text('\n'.join(f'P{i}: {t}' for i,t in enumerate(after)), encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['paragraph_changes','deleted_figure_notes']}, ensure_ascii=False))
