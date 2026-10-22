from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import argparse
import copy
import hashlib
import json
import re
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
SOURCE = ROOT / 'word_output/2026.10.03v65.docx'
OUTPUT = ROOT / 'word_output/2026.10.04v66.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W, 'm': M}
TERMS = ['源—目的节点对', 'OD', 'DLinear', 'LightTS', 'TimeMixer', 'Softmax',
         'CESNET TS-Zoo', 'THUML', 'Python', 'PyTorch', 'MSE', 'MAE', 'RMSE',
         '两层感知器', '非重叠平均池化', '中心移动平均', '移动平均', '趋势项', '余项',
         '分解线性模型', '分解线性专家', '序列分解', '线性映射', '自适应矩估计',
         '修正线性单元', 'ReLU', 'Adam', '全局可学习权重', '恒定输入路由',
         '固定等权', '对数变换', '标准化', '逆标准化', '逆对数变换',
         '平均绝对一阶差分', '平均低估幅度', '置信区间', '标准误', '标准差',
         '均方误差', '均方根误差', '平均绝对误差', '平均绝对偏差', '三分位数']

def segments(p):
    parts, nodes = [], []
    for child in p:
        if child.tag in (f'{{{M}}}oMath', f'{{{M}}}oMathPara'):
            if nodes:
                parts.append(nodes)
                nodes = []
            parts.append(child)
        else:
            nodes.extend(child.findall(f'.//{{{W}}}t'))
    if nodes:
        parts.append(nodes)
    return parts

def text(p):
    return ''.join(n.text or '' for n in p.findall(f'.//{{{W}}}t'))

def canonical(node):
    return etree.tostring(node, method='c14n')

def skeleton(node):
    clone = copy.deepcopy(node)
    for n in clone.findall(f'.//{{{W}}}t'):
        n.text = ''
    return canonical(clone)

def numbers(s):
    return Counter(re.findall(r'\d+(?:\.\d+)?', s))

def words(s):
    return Counter(re.findall(r'[A-Za-zÀ-ÖØ-öø-ÿ]+(?:-[A-Za-z]+)*', s))

parser = argparse.ArgumentParser()
parser.add_argument('--write', action='store_true')
args = parser.parse_args()
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash == 'c39882af359b03e6f44f49cf46aa6852c8885da97057f1e41307eb18fed47e93', source_hash
replacements = json.loads((QA / 'replacements.json').read_text(encoding='utf-8'))
records = json.loads((QA / 'source_segments.json').read_text(encoding='utf-8'))
with ZipFile(SOURCE) as z:
    original_bytes = z.read('word/document.xml')
original = etree.fromstring(original_bytes)
revised = copy.deepcopy(original)
old_ps = original.find(f'{{{W}}}body').findall(f'{{{W}}}p')
new_ps = revised.find(f'{{{W}}}body').findall(f'{{{W}}}p')
assert len(old_ps) == len(new_ps) == 129
changes = []
for key, replacement in replacements.items():
    pi, si = map(int, key.split('.'))
    group = segments(new_ps[pi])[si]
    assert isinstance(group, list), key
    before = ''.join(n.text or '' for n in group)
    assert before == records[pi]['parts'][si]['text'], key
    after = replacement['after']
    assert after != before
    if len(group) == 1:
        group[0].text = after
    else:
        prefix = ''.join(n.text or '' for n in group[:-1])
        assert after.startswith(prefix), (key, prefix)
        group[-1].text = after[len(prefix):]
    changes.append({'paragraph': pi, 'segment': si, 'before': before, 'after': after,
                    'reason': replacement['reason'], 'risk': records[pi]['risk'],
                    'report_page': records[pi]['report_page']})

changed_indices = sorted(set(c['paragraph'] for c in changes))
assert skeleton(original) == skeleton(revised), 'XML structure or formatting changed'
issues = []
term_differences = []
for i, (old, new) in enumerate(zip(old_ps, new_ps)):
    old_text, new_text = text(old), text(new)
    if i not in changed_indices:
        assert canonical(old) == canonical(new), ('Unexpected paragraph change', i)
        continue
    if numbers(old_text) != numbers(new_text):
        issues.append({'paragraph': i, 'kind': 'numbers', 'before': dict(numbers(old_text)), 'after': dict(numbers(new_text))})
    if words(old_text) != words(new_text):
        issues.append({'paragraph': i, 'kind': 'Latin identifiers', 'before': dict(words(old_text)), 'after': dict(words(new_text))})
    for term in TERMS:
        if old_text.count(term) != new_text.count(term):
            term_differences.append({'paragraph': i, 'term': term, 'before': old_text.count(term), 'after': new_text.count(term)})
    assert Counter(re.findall(r'\[\d+\]', old_text)) == Counter(re.findall(r'\[\d+\]', new_text)), ('Citation difference', i)

for xpath in ['.//w:tbl', './/w:drawing', './/m:oMath']:
    assert [canonical(n) for n in original.xpath(xpath, namespaces=NS)] == [canonical(n) for n in revised.xpath(xpath, namespaces=NS)], xpath
stats = {'source_sha256': source_hash, 'changed_paragraphs': len(changed_indices),
         'changed_segments': len(changes), 'paragraph_indices': changed_indices,
         'body_paragraphs': len(new_ps), 'tables': len(revised.xpath('.//w:tbl', namespaces=NS)),
         'figures': len(revised.xpath('.//w:drawing', namespaces=NS)),
         'math_objects': len(revised.xpath('.//m:oMath', namespaces=NS)),
         'modified_text_chars_before': sum(len(c['before']) for c in changes),
         'modified_text_chars_after': sum(len(c['after']) for c in changes),
         'all_prose_chars_before': sum(len(text(p)) for p in old_ps),
         'all_prose_chars_after': sum(len(text(p)) for p in new_ps),
         'format_skeleton_identical': True, 'numeric_identifier_issues': issues,
         'term_count_differences': term_differences}
print(json.dumps(stats, ensure_ascii=False, indent=2))
if not args.write:
    raise SystemExit()
assert not issues, 'Protected numeric or Latin tokens differ'
assert not term_differences, 'Protected terminology counts differ'
new_bytes = etree.tostring(revised, encoding='UTF-8', xml_declaration=True, standalone=True)
with ZipFile(SOURCE) as src, ZipFile(OUTPUT, 'w') as dest:
    for item in src.infolist():
        dest.writestr(item, new_bytes if item.filename == 'word/document.xml' else src.read(item.filename))
with ZipFile(SOURCE) as src, ZipFile(OUTPUT) as dest:
    changed_members = [name for name in src.namelist() if src.read(name) != dest.read(name)]
assert changed_members == ['word/document.xml'], changed_members
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
stats['changed_zip_members'] = changed_members
stats['output_sha256'] = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
(QA / 'structural_audit.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'applied_changes.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
scan_indices = [i for i in range(12, 117) if text(old_ps[i]) and not text(old_ps[i]).startswith(('注：', '图', '表')) and len(text(old_ps[i])) > 35]
(QA / 'scan_before.txt').write_text('\n\n'.join(text(old_ps[i]) for i in scan_indices), encoding='utf-8')
(QA / 'scan_after.txt').write_text('\n\n'.join(text(new_ps[i]) for i in scan_indices), encoding='utf-8')
print('Saved:', OUTPUT)
