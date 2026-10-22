from pathlib import Path
from collections import Counter
import ast
import difflib
import hashlib
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
audit = json.loads((QA / 'structural_audit.json').read_text(encoding='utf-8'))
changes = json.loads((QA / 'applied_changes.json').read_text(encoding='utf-8'))
records = json.loads((QA / 'source_segments.json').read_text(encoding='utf-8'))
render = json.loads((QA / 'render_record.json').read_text(encoding='utf-8'))
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
import pymupdf

def formula_pages(path):
    with pymupdf.open(path) as pdf:
        return {str(n): [i+1 for i, page in enumerate(pdf) if re.search(r'(?m)^\s*\('+str(n)+r'\)\s*$', page.get_text())]
                for n in range(1, 17)}

render['formula_pages_before'] = formula_pages(ROOT / 'word_output/v65_aigc_review/2026.10.03v65.pdf')
render['formula_pages_after'] = formula_pages(QA / '2026.10.04v66.pdf')
assert render['formula_pages_before'] == render['formula_pages_after']
assert all(len(pages) == 1 for pages in render['formula_pages_after'].values())
render['visually_reviewed_pages'] = list(range(1, 11))
render['visual_review_result'] = '逐页查看10页，无新增重叠、缺字、图题分离或表格截断'
(QA / 'render_record.json').write_text(json.dumps(render, ensure_ascii=False, indent=2), encoding='utf-8')

spec = importlib.util.spec_from_file_location('aigc_scan', 'C:/Users/Quant/.codex/skills/aigc-reduce/scripts/aigc_scan.py')
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
before = scanner.scan((QA / 'scan_before.txt').read_text(encoding='utf-8'))
after = scanner.scan((QA / 'scan_after.txt').read_text(encoding='utf-8'))
for name, data in [('before', before), ('after', after)]:
    (QA / f'style_scan_{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# Character-level measure excludes protected tokens. It is not an AIGC score.
tree = ast.parse((QA / 'apply_revision.py').read_text(encoding='utf-8'))
terms = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'TERMS' for t in node.targets))
pattern = re.compile('|'.join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) +
                     r'|\[\d+\]|(?:图|表|式)\s*[（(]?\d+[）)]?|\d+(?:\.\d+)?|[A-Za-zÀ-ÖØ-öø-ÿ]+(?:-[A-Za-z]+)*')
editable_total = changed_total = 0
for c in changes:
    original, revised = c['before'], c['after']
    protected = {i for m in pattern.finditer(original) for i in range(m.start(), m.end())}
    editable = set(range(len(original))) - protected
    matched = {i for block in difflib.SequenceMatcher(None, original, revised, autojunk=False).get_matching_blocks()
               for i in range(block.a, block.a+block.size)}
    editable_total += len(editable)
    changed_total += len(editable - matched)
measure = {'scope': '本轮修改片段的原文可编辑字符，排除受保护术语、数字、英文标识、引用与图表公式标签',
           'editable_chars': editable_total, 'changed_editable_chars': changed_total,
           'changed_editable_percent': round(changed_total / editable_total * 100, 2),
           'not_aigc_score': True}
(QA / 'sentence_change_measure.json').write_text(json.dumps(measure, ensure_ascii=False, indent=2), encoding='utf-8')

def section(i):
    if i == 3: return '中文摘要'
    if i < 18: return '引言'
    if i < 24: return '第1节 方法总览'
    if i < 35: return '第1.1节 预测任务与数据预处理'
    if i < 46: return '第1.2节 多尺度构造与DLinear专家'
    if i < 58: return '第1.3节 样本级自适应尺度加权'
    if i < 63: return '第1.4节 模型训练与预测输出'
    if i < 77: return '第2.1节 数据集与实验设置'
    if i < 85: return '第2.2节 总体预测性能与基线比较'
    if i < 95: return '第2.3节 八随机种子核心消融与稳定性'
    if i < 107: return '第2.4节 预测行为与尺度权重分析'
    if i < 115: return '第2.5节 运行开销与网络管理应用讨论'
    return '第3节 结语'

indices = audit['paragraph_indices']
section_counts = Counter(section(i) for i in indices)
lookup = {(c['paragraph'], c['segment']): c for c in changes}

def paragraph(i, revised=False):
    result = []
    for si, part in enumerate(records[i]['parts']):
        if 'math' in part:
            result.append(f'［原数学对象{part["math"]+1}］')
        else:
            result.append(lookup[(i, si)]['after'] if revised and (i, si) in lookup else part['text'])
    return ''.join(result)

lines = [
    '# v65至v66句式修订对比报告', '',
    '## 一 修订结果', '',
    '修订依据为用户提供的《检测报告_2026.10.03v65_.pdf》，原稿为2026.10.03v65.docx。新版按本次修改日期另存为2026.10.04v66.docx，v65原文件未覆盖。', '',
    f'本轮修改{audit["changed_paragraphs"]}个高风险段落中的{audit["changed_segments"]}处文字片段，涉及中文摘要、引言、方法说明、实验设置、结果分析、应用讨论和结语。改动以句式为主：重排条件与结果、调整主语、分开过长的并列说明，并改善公式外围文字的衔接。未增删或移动段落，没有新增实验或删去实验结果。', '',
    'PaperPure本次报告显示v65的AIGC率为50.9%，AI特征字符数4881，总字符数9589；前部20%、中部60%、后部20%的分区AIGC率分别为24.5%、56.7%、60.8%。报告编号为PAPERPURE20261004111455，检测时间为2026-10-04 11:14:55。上一份v64报告为51.8%，本次下降0.9个百分点。v66尚未在同一平台复测，不将语言检查指标换算为新版AIGC比例。', '',
    '## 二 修改范围', '',
    '| 位置 | 修改段落数 |', '|---|---:|',
]
lines.extend(f'| {name} | {count} |' for name, count in section_counts.items())
lines += [
    '', '本轮仅处理报告标记的正文句式。未标记段落、提示风险段落，以及全部标题、作者信息、英文摘要、关键词、参考文献、图题、表题和图注均保持原样。报告将英文单位信息中的占位文字标红，该处应按真实作者信息填写，未为降低检测指标改写占位内容。', '',
    '重点改动如下：', '',
    '- 方法部分：按预处理、多尺度构造、专家预测、路由融合的操作顺序组织说明；保留术语、公式和定义。',
    '- 实验设置：将共同条件、模型特定参数和统计计算步骤分别说明，保留所有超参数、种子及数据划分。',
    '- 结果部分：按对照模型组织改进率，再说明逐种子差异与预测轨迹，保留原有例外及证据范围。',
    '- 应用讨论：按观测更新、窗口构造、预测、量纲恢复及链路需求分析组织句子，未写成已经部署的应用实验。', '',
    '## 三 保护内容与格式核对', '',
    '| 核对项目 | 结果 |', '|---|---|',
    f'| 段落结构 | 保留{audit["body_paragraphs"]}个顶层段落，未增删或移动段落，章节层级不变 |',
    f'| 表格 | {audit["tables"]}张表的完整XML逐一相同，文字、实验数据和格式不变 |',
    f'| 图片 | {audit["figures"]}幅图的图像文件及绘图节点逐一相同，内容、尺寸和插入方式不变 |',
    f'| 公式 | {audit["math_objects"]}个OMML数学对象逐一相同，式（1）至式（16）及编号不变 |',
    '| 格式设置 | 排除正文文字内容后，XML结构和属性完全相同；字体、字号、粗斜体、段落设置、分页设置和页边距未调整 |',
    '| 文档其他部件 | 只有word/document.xml的正文文字改变；样式、页眉页脚、脚注、图片、关系文件及其他部件逐文件相同 |',
    '| 数值、标识与引用 | 修改段落的全部数字字符串、英文标识和引用编号逐段核对一致，数值与其对象保持对应 |',
    '| 专业术语 | 模型、数据集、指标和方法术语未作近义词替换，约定受保护术语的逐段出现次数一致 |',
    '| 参考文献 | 11条文献及其编号、顺序、DOI和链接未修改 |',
    '| 页数 | 用Microsoft Word只读打开副本导出检查，前后均为10页 |',
    '| 图表位置 | 图1至图5仍在第2、6、7、8、9页；表1至表3仍在第5、6、7页 |',
    '| 编号公式位置 | 式（1）至式（5）仍在第3页，式（6）至式（13）仍在第4页，式（14）至式（16）仍在第5页 |',
    '| 视觉检查 | 10页已逐页查看，未见新增文字重叠、公式缺字、图题分离或表格截断 |', '',
    '句式调整引起局部自动换行，文字位置并非逐像素相同。全部格式设置、总页数及图表和编号公式的所在页保持不变。', '',
    f'修改片段的文字字符数由{audit["modified_text_chars_before"]}变为{audit["modified_text_chars_after"]}，净减少{audit["modified_text_chars_before"]-audit["modified_text_chars_after"]}个字符。此处按DOCX文字节点统计，不含公式和表格，口径不同于检测平台。字符数变化来自句式重组和连接文字调整；未删去方法步骤、实验数值、结果例外或应用条件，原有信息保留。', '',
    '关键事实核对：', '',
    '- 摘要中的4.07%、4.54%、29.80%、46.89%，以及两类常权重对照的1.80%、4.31%、4.97%，数值与对应模型、数据集均保留。',
    '- 时间划分、窗口不跨边界、训练统计量复用、学习率、早停规则、随机种子及配对置信区间计算不变。',
    '- GÉANT种子43相对恒定输入路由退步12.78%、Abilene典型窗口例外、种子间权重差异和置信区间跨零等内容保留，未扩大核心机制的论证范围。',
    '- 波动分组的窗口数及改进率、高需求阈值与统计结果、参数数量和前向计时结果全部保留。',
    '- 先逆标准化、后逆对数变换的顺序不变；链路容量分析仍作为可参考的应用流程。', '',
    '## 四 本地语言检查', '',
    f'使用aigc-reduce扫描脚本，对前后相同的{before["summary"]["total_paragraphs"]}个正文段落作比较。扫描不含摘要、图注、表格和参考文献，检查的是词表及句子形态，不能替代PaperPure检测。', '',
    '| 指标 | v65 | v66 |', '|---|---:|---:|',
    f'| 词表内模板化短语 | {before["template_phrases"]["count"]}处 | {after["template_phrases"]["count"]}处 |',
    f'| 被动句标记 | {before["passive_voice"]["count"]}处 | {after["passive_voice"]["count"]}处 |',
    f'| 平均句长 | {before["burstiness"]["avg_len"]}字 | {after["burstiness"]["avg_len"]}字 |',
    f'| 句长变异系数 | {before["burstiness"]["cv"]} | {after["burstiness"]["cv"]} |',
    f'| 长度相近的段落组 | {len(before["para_symmetry"]["symmetrical_runs"])}组 | {len(after["para_symmetry"]["symmetrical_runs"])}组 |',
    f'| 口语或网络用语命中 | {before["colloquial"]["count"]}处 | {after["colloquial"]["count"]}处 |', '',
    '本地综合风险等级前后均为“中”。平均句长降低、句长变化增加，未引入口语或网络用语；长度相近的段落组数量未变。没有为了优化本地分数删去定义、术语或必要信息。', '',
    f'在本轮修改片段内，排除受保护术语、数字、英文标识、引用及图表公式标签后，按字符匹配计算的可编辑文字改动比例为{measure["changed_editable_percent"]}%。该比例仅用于描述改动量，既不是全文修改比例，也不是AIGC率。', '',
    '## 五 逐段修改对比', '',
    f'以下列出全部{len(indices)}个修改段落的原文、改文及修改理由。公式以“［原数学对象］”占位，便于比较外围文字；实际论文中的公式完整保留。所列报告页码来自用户提供的检测报告，不是论文页码。', '',
]
for order, i in enumerate(indices, 1):
    edits = [c for c in changes if c['paragraph'] == i]
    reasons = list(dict.fromkeys(c['reason'] for c in edits))
    record = records[i]
    lines += [f'### {order} {section(i)}', '',
              f'定位：原文以“{paragraph(i)[:24]}”起句；检测报告第{record["report_page"]}页，{record["risk"]}。', '',
              '**原文**', '', paragraph(i), '', '**修改后**', '', paragraph(i, True), '',
              '**修改说明**', '', ' '.join(reasons), '']
lines += ['## 六 复测与版本记录', '',
          '复测文件为2026.10.04v66.docx，建议沿用v65的PaperPure平台及相同设置。新版实际比例以复测报告为准，本次不承诺降低到某一数值。', '',
          f'- v65原稿SHA-256：{audit["source_sha256"]}',
          f'- v66新版SHA-256：{audit["output_sha256"]}', '']
output = ROOT / 'word_output/2026.10.04v66_句式修订对比报告.md'
output.write_text('\n'.join(lines), encoding='utf-8')
assert before['summary']['total_paragraphs'] == after['summary']['total_paragraphs']
assert len(indices) == 28 and len(changes) == 34
assert all(records[i]['risk'] == '高风险' for i in indices)
assert render['page_count_after'] == render['page_count_before'] == 10
assert render['figure_pages'] == {'1': 2, '2': 6, '3': 7, '4': 8, '5': 9}
assert render['table_pages'] == {'1': 5, '2': 6, '3': 7}
assert not audit['numeric_identifier_issues'] and not audit['term_count_differences']
assert hashlib.sha256((ROOT / 'word_output/2026.10.03v65.docx').read_bytes()).hexdigest() == audit['source_sha256']
assert hashlib.sha256((ROOT / 'word_output/2026.10.04v66.docx').read_bytes()).hexdigest() == audit['output_sha256']
print(json.dumps({'report': str(output), 'changed_paragraphs': len(indices), 'changed_segments': len(changes),
                  'change_measure': measure, 'protected_content_checks': 'passed',
                  'formula_pages_unchanged': True}, ensure_ascii=False, indent=2))
