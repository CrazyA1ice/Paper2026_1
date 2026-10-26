from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
FOLDER = ROOT / 'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023'
SOURCE = FOLDER / '自适应多尺度加权的多变量网络流量预测_ccgcxyxbV7_摘要精简稿.docx'
OUTPUT = FOLDER / '自适应多尺度加权的多变量网络流量预测_ccgcxyxbV8_指定项目修订稿.docx'
SOURCE_SHA = '54aa62d16a2aa678dae7315e0b643e3e5e6c526e219c16428f12c82e31132f3a'
ACCEPTED = ['03', '04', '05', '06', '08', '09', '11', '12', '13', '14', '18', '19']
REJECTED = ['02', '07', '10', '15', '16', '17']
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
if OUTPUT.exists():
    assert sha256(OUTPUT.read_bytes()).hexdigest() == '3068eb18c2c02ddd0a7c8a419d88b0883128ed3f1fb54e3d2a62e8e79b6347c5'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
old = E.fromstring(members['word/document.xml'])
new = E.fromstring(members['word/document.xml'])
old_body = old.find('w:body', NS)
body = new.find('w:body', NS)
original_nodes = list(body)
changes = []
changed = set()
removed = set()

def text(p):
    return ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS))

def canon(p):
    p = deepcopy(p)
    E.cleanup_namespaces(p)
    return E.tostring(p, method='c14n')

def replace(index, before, after, issues):
    p = original_nodes[index]
    nodes = p.xpath('.//w:t', namespaces=NS)
    joined = ''.join(n.text or '' for n in nodes)
    assert joined.count(before) == 1, (index, before)
    start = joined.index(before)
    end = start + len(before)
    offset = 0
    inserted = False
    for node in nodes:
        value = node.text or ''
        a, b = offset, offset + len(value)
        offset = b
        if a < end and b > start:
            left, right = max(start-a, 0), min(end-a, len(value))
            node.text = value[:left] + (after if not inserted else '') + value[right:]
            inserted = True
    assert ''.join(n.text or '' for n in nodes) == joined[:start] + after + joined[end:]
    changed.add(index)
    changes.append({'source_index': index, 'issues': issues, 'operation': 'replace',
                    'before': before, 'after': after})

def insert_after(index, needle, addition, issues):
    p = original_nodes[index]
    nodes = p.xpath('.//w:t', namespaces=NS)
    joined = ''.join(n.text or '' for n in nodes)
    assert joined.count(needle) == 1
    end = joined.index(needle) + len(needle)
    offset = 0
    for node in nodes:
        value = node.text or ''
        if offset < end <= offset + len(value):
            where = end - offset
            node.text = value[:where] + addition + value[where:]
            break
        offset += len(value)
    else:
        raise AssertionError(index)
    changed.add(index)
    changes.append({'source_index': index, 'issues': issues, 'operation': 'insert_after',
                    'needle': needle, 'addition': addition})

def remove(index, issues):
    changes.append({'source_index': index, 'issues': issues, 'operation': 'remove_redundant_paragraph',
                    'before': text(original_nodes[index]), 'after': ''})
    body.remove(original_nodes[index])
    removed.add(index)

# 03: method citation and code provenance are distinct. Existing references 9--11 retain their numbers.
replace(13, 'TimesNet公开基准', 'LightTS', ['03'])
replace(13, '则引入基于多层感知机（MLP）的LightTS处理多维时序',
        '采用基于采样与多层感知机（MLP）的结构进行多变量时间序列预测', ['03'])
replace(63, 'LightTS采用TimesNet公开基准代码库的实现',
        'LightTS采用Time-Series-Library公开代码中的实现', ['03'])
replace(63, '[8]', '[12]', ['03'])
reference8 = ('[8] ZHANG Tianping, ZHANG Yizhuo, CAO Wei, et al. Less is more: fast multivariate time series '
              'forecasting with light sampling-oriented MLP structures[EB/OL]. (2022-07-04)[2026-10-23]. '
              'https://doi.org/10.48550/arXiv.2207.01186.')
replace(111, text(original_nodes[111]), reference8, ['03'])
reference12 = ('[12] THUML. Time-Series-Library[CP/OL]. [2026-10-23]. '
               'https://github.com/thuml/Time-Series-Library/tree/4e938a1767106324dd753b2a44832bf870a0252e.')
new_reference = deepcopy(old_body[111])
new_reference.xpath('.//w:t', namespaces=NS)[0].text = reference12
body.insert(body.index(original_nodes[115]), new_reference)
changes.append({'issues': ['03'], 'operation': 'add_reference', 'after': reference12})

# 04, 05, 19: retain the existing scale definition and q=25/replicate-padding implementation.
remove(32, ['04', '05', '19'])

# 06, 08, 19: revise feature meanings in place, preserve all native inline symbols and rejected-07 routing claims.
replace(44, '上述四维统计特征从不同侧面完整刻画了当前流量窗口的运行工况：全局均值',
        '上述四维统计特征用于汇总标准化空间中的窗口状态：均值', ['06', '19'])
replace(44, '表征当前窗口的整体业务负载水位，标准差',
        '反映标准化窗口相对训练期均值的整体偏移，标准差', ['06'])
replace(44, '衡量窗口内的整体能量离散度与宏观波动幅度；末时刻均值',
        '概括时间与变量两个维度的离散程度；末时刻均值', ['06'])
replace(44, '捕捉历史窗口向未来预测区间过渡时的最新静态边界水平，提供关键的近期锚点信息；平均绝对一阶差分',
        '表征窗口末端状态，平均绝对一阶差分', ['06'])
replace(44, '则直接量化相邻小时之间的高频抖动剧烈程度。',
        '反映相邻小时的变化幅度。', ['06'])
replace(44, '从根本上杜绝了过拟合风险', '以控制路由分支的参数规模', ['08'])
prefix45 = ''.join(original_nodes[45].xpath('.//w:t/text()', namespaces=NS)).split('由此，')[0]
replace(45, prefix45, '', ['19'])
replace(40, '为各窗口预设不同的融合系数', '为各窗口生成相应的融合系数', ['09'])

# 18: verified collection, aggregation and source fields, with no inferred calendar dates.
insert_after(59, '两套数据分别含4656和2849个时间点。',
             '两套数据均取自matrix子集的1_hour聚合文件，Abilene采用小时级平均OD流量字段'
             'matrix_avg_realOD，GÉANT采用小时级平均带宽字段matrix_avg_bandwidth_kbps。', ['18'])

# 11, 12: report repeated-experiment means and consistently name the threshold-defined targets.
replace(14, '90分位高需求峰值估计', '高需求目标点预测', ['12'])
replace(14, '均取得显著领先优势', '均取得平均误差优势', ['11'])
replace(82, '显著降至', '降至', ['11'])
replace(86, '高负载峰值时段', '高需求时段', ['12'])
replace(86, 'AUE专门量化预测值低于真实峰值时的短缺幅度',
        'AUE用于衡量标准化空间中高需求目标点上的平均低估幅度', ['06', '12'])
replace(90, '由图3可见，本文方法在两套数据集上的高需求MAE与平均低估误差均显著低于所有对照模型',
        '由图3可见，在8次重复实验的均值比较中，本文方法在两套数据集上的高需求MAE与平均低估误差均低于所设对照模型', ['11'])
replace(90, '从而显著缓解了', '从而缓解了', ['11'])

# 13, 14: remove the cross-horizon multiplier and unverified accumulation explanation, retain rejected-16 ending verbatim.
replace(92, '历史输入仍保持96 h。', '历史输入仍保持96 h，并直接输出未来168 h的预测结果。', ['14'])
p98 = original_nodes[98]
marker = '此外，图4中全部8个随机种子'
assert text(p98).count(marker) == 1
before98 = text(p98)
target = next(t for t in p98.xpath('.//w:t', namespaces=NS) if marker in (t.text or ''))
target.text = target.text[target.text.index(marker):]
target_child = target
while target_child.getparent() is not p98:
    target_child = target_child.getparent()
for child in list(p98):
    if child is target_child:
        break
    if child.tag != '{'+NS['w']+'}pPr':
        p98.remove(child)
assert text(p98) == before98[before98.index(marker):]
changed.add(98)
changes.append({'source_index': 98, 'issues': ['13', '14'], 'operation': 'trim_prefix',
                'before': before98, 'after': text(p98)})

# 19: remove repeated high-demand setup while preserving the unapproved-17 engineering rationale in the next paragraph.
remove(85, ['19'])
replace(74, '在模型轻量化与预测精度之间取得了极具竞争力的帕累托优势',
        '相对LightTS取得了较少参数与较低平均误差的组合优势', ['19'])
replace(82, 'MSE与MAE均取得全场最优', 'MSE与MAE平均值均为所设对照中的最低值', ['19'])
replace(97, '在168 h超长周期预测任务上展现出压倒性的性能优势',
        '在168 h超长周期预测任务中的平均预测误差低于四种对照', ['19'])

# Check every unchanged body element and every paragraph property. Tables, drawings and numbered formulas remain identical.
for i, (a, b) in enumerate(zip(old_body, original_nodes)):
    if i not in changed | removed:
        assert canon(a) == canon(b), ('unapproved_body_change', i)
    elif i not in removed:
        assert canon(a.find('w:pPr', NS)) == canon(b.find('w:pPr', NS)), ('paragraph_format', i)
        old_math = [canon(x) for x in a.xpath('.//m:oMath', namespaces=NS)]
        new_math = [canon(x) for x in b.xpath('.//m:oMath', namespaces=NS)]
        if i != 98:
            assert old_math == new_math, ('math_changed', i)

# Explicitly protect every rejected proposal, including their overlapping passages.
assert text(original_nodes[13]).split('然而，')[1] == text(old_body[13]).split('然而，')[1]
old_route = text(old_body[44]).split('当网络处于')[1].split('通过在全变量间')[0]
new_route = text(original_nodes[44]).split('当网络处于')[1].split('通过在全变量间')[0]
assert old_route == new_route
assert canon(old_body[73]) == canon(original_nodes[73])
assert canon(old_body[83]) == canon(original_nodes[83])
static90 = text(old_body[90]).split('同样值得注意的是，')[1].split('而本文方法')[0]
assert static90 in text(original_nodes[90])
assert text(original_nodes[98]) == text(old_body[98])[text(old_body[98]).index(marker):]
assert text(original_nodes[90]).endswith('具备更强的工程实用价值。')
assert canon(old_body[33]) == canon(original_nodes[33])
for i in [1, 2, 5, 120]:
    assert canon(old_body[i]) == canon(original_nodes[i]), ('protected_metadata_or_abstract', i)
for i in [74, 82, 90, 97]:
    old_numbers = re.findall(r'\d+(?:\.\d+)?', text(old_body[i]))
    new_numbers = re.findall(r'\d+(?:\.\d+)?', text(original_nodes[i]))
    if i == 90:
        new_numbers.remove('8')
    assert old_numbers == new_numbers, ('result_numbers_changed', i)
math_before = old.xpath('//m:oMath', namespaces=NS)
math_after = new.xpath('//m:oMath', namespaces=NS)
assert len(math_before) - len(math_after) == 6  # only symbols in authorized deleted prose
assert len(body) == len(old_body) - len(removed) + 1

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
    'accepted_issues': ACCEPTED, 'rejected_issues_preserved': REJECTED,
    'source_unchanged': True, 'both_abstracts_unchanged': True,
    'chinese_abstract_characters': 199, 'all_tables_figures_and_numbered_formulas_unchanged': True,
    'styles_and_paragraph_properties_unchanged': True, 'unapproved_changes': 0,
    'native_math_objects_before': len(math_before), 'native_math_objects_after': len(math_after),
    'removed_inline_math_only_in_authorized_deleted_prose': 6,
    'changed_source_indices': sorted(changed), 'removed_source_indices': sorted(removed),
    'unverified_calendar_dates_not_inserted': True,
    'edits': changes, 'visual_review_pending': True,
}
(QA/'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA/'artifact.md').write_text(
    '# User-selected manuscript revision\n\n'
    'Accepted: '+', '.join(ACCEPTED)+'. Rejected: '+', '.join(REJECTED)+'.\n\n'
    'Preserve rejected claims verbatim, including those within changed paragraphs. '
    'Preserve both abstracts, all table cells, figure binaries, numbered formulas and styles. '
    'Use local replacements and authorized deletion of repeated prose. Do not rerun experiments. '
    'Reference 8 becomes the original LightTS paper; reference 12 identifies the actual pinned code. '
    'No inferred data dates. Render and inspect every output page.\n\n'
    'Terms: LightTS; Time-Series-Library; Abilene; GÉANT; 高需求目标点; 标准化空间; '
    'mean and sample standard deviation across seeds 42--49.\n', encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k != 'edits'}, ensure_ascii=False))
