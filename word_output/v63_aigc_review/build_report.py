from pathlib import Path
from collections import Counter
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
audit = json.loads((QA / 'structural_audit.json').read_text(encoding='utf-8'))
changes = json.loads((QA / 'applied_changes.json').read_text(encoding='utf-8'))
records = json.loads((QA / 'source_segments.json').read_text(encoding='utf-8'))
render = json.loads((QA / 'render_record.json').read_text(encoding='utf-8'))
spec = importlib.util.spec_from_file_location('aigc_scan', 'C:/Users/Quant/.codex/skills/aigc-reduce/scripts/aigc_scan.py')
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
before = scanner.scan((QA / 'scan_before.txt').read_text(encoding='utf-8'))
after = scanner.scan((QA / 'scan_after.txt').read_text(encoding='utf-8'))
for name, data in [('before', before), ('after', after)]:
    (QA / f'style_scan_{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

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
    '# v62至v63句式修订对比报告', '',
    '## 一 修订结果', '',
    '修订依据为《检测报告_2026.10.03v62_.pdf》，原稿为2026.10.03v62.docx。新版另存为2026.10.03v63.docx，v62原文件未覆盖。', '',
    f'本轮调整{audit["changed_paragraphs"]}个段落中的{audit["changed_segments"]}处文字片段，主要重组中文摘要、引言、方法说明、实验设置、结果分析和应用讨论的句式。调整包括改变句子主语、拆开过长的并列句、重新安排条件与结果的顺序，以及改写模板化衔接。没有新增实验、删去实验结果或扩大结论。', '',
    '原检测报告的AIGC率为62.2%，前部、中部、后部分别为34.0%、65.9%、80.6%。这些是v62的送检结果。v63尚未在PaperPure重新检测，不能据本地语言检查报告新的AIGC率。', '',
    '## 二 修订位置', '',
    '| 位置 | 修改段落数 |', '|---|---:|',
]
lines.extend(f'| {name} | {count} |' for name, count in section_counts.items())
lines += [
    '', '中文与英文作者信息、英文摘要、关键词、全部标题、参考文献、图题、表题和图注均未修改。报告将英文单位信息中的占位文字标红，但该处应按真实作者信息填写，因此本轮保留原样。', '',
    '正文中的公式外围句式有调整，数学对象及定义不作替换。固定等权、全局可学习权重、恒定输入路由等对照名称保持原文；未用近义词替换专业术语。', '',
    '## 三 保护内容核对', '',
    '| 核对项目 | 结果 |', '|---|---|',
    f'| 正文段落及结构 | {audit["body_paragraphs"]}个顶层段落；未增删或移动段落，标题及章节层级不变 |',
    f'| 表格 | {audit["tables"]}张表的完整XML相同，包括文字、数值及格式 |',
    f'| 图片 | {audit["figures"]}幅图的图像文件及绘图节点相同，尺寸和插入方式不变 |',
    f'| 公式 | {audit["math_objects"]}个OMML数学对象逐一相同；式（1）至式（16）及编号不变 |',
    '| 格式 | 将正文文字内容排除后，文档XML结构和全部属性完全相同；字体、字号、粗斜体、段落设置、分页设置及页边距均未调整 |',
    '| 其他文档部件 | DOCX中只有word/document.xml改变；样式、页眉页脚、脚注、图片、关系文件及其他部件逐文件相同 |',
    '| 数据与标识 | 修改段落的数值字符串、引用编号及英文标识逐段核对一致；表内数据未改变 |',
    '| 专业术语 | 模型、数据集、指标和方法术语未替换；受保护术语的逐段出现次数一致 |',
    '| 参考文献 | 11条文献及其编号、次序、DOI和链接未修改 |',
    f'| 页数 | Word渲染前后均为{render["page_count_after"]}页 |',
    '| 图表位置 | 图1至图5仍在第2、6、7、8、9页；表1至表3仍在第5、6、7页 |',
    '| 视觉检查 | 最新版10页已逐页查看，未见新增文字重叠、公式缺字、图题分离或表格截断 |', '',
    '句式改写会引起局部自动换行，文字的行内位置并非逐像素不变；所有格式设置、总页数和图表所在页保持原样。', '',
    f'修改片段的文字字符数由{audit["modified_text_chars_before"]}增至{audit["modified_text_chars_after"]}，净增{audit["modified_text_chars_after"]-audit["modified_text_chars_before"]}个字符。此处按DOCX文字节点统计，不含数学对象和表格，也不等于检测平台的字数口径。部分句子有所缩短，但相应的信息在段内重新组织，未以删去内容换取文本减少。', '',
    '关键结果与证据边界复核：', '',
    '- 摘要中的4.07%、4.54%、29.80%、46.89%，以及两类常权重对照的1.80%、4.31%、4.97%保留原值和对应对象。',
    '- 验证集与测试集沿用训练统计量的规则、时间划分、随机种子、训练超参数、配对统计及置信区间计算规则不变。',
    '- GÉANT种子43相对恒定输入路由退步12.78%、典型窗口的例外、种子间权重差异，以及置信区间跨零的描述均保留。',
    '- 流量逆标准化、逆对数变换的先后次序及容量规划的应用范围不变；未将应用讨论写成已完成的部署实验。', '',
    '## 四 本地语言检查', '',
    f'以下采用aigc-reduce脚本，对修改前后相同的{before["summary"]["total_paragraphs"]}个正文段落扫描。扫描不含摘要、图注、表格及参考文献，主要检查语言模式，不能替代PaperPure检测。', '',
    '| 项目 | v62 | v63 |', '|---|---:|---:|',
    f'| 脚本词表内的模板化短语 | {before["template_phrases"]["count"]}处 | {after["template_phrases"]["count"]}处 |',
    f'| 脚本识别的被动句标记 | {before["passive_voice"]["count"]}处 | {after["passive_voice"]["count"]}处 |',
    f'| 平均句长 | {before["burstiness"]["avg_len"]}字 | {after["burstiness"]["avg_len"]}字 |',
    f'| 句长变异系数 | {before["burstiness"]["cv"]} | {after["burstiness"]["cv"]} |',
    f'| 长度相近的段落组 | {len(before["para_symmetry"]["symmetrical_runs"])}组 | {len(after["para_symmetry"]["symmetrical_runs"])}组 |',
    f'| 口语或网络用语命中 | {before["colloquial"]["count"]}处 | {after["colloquial"]["count"]}处 |', '',
    '模板化短语减少，未引入口语或网络用语；段落长度和句长仍会受方法说明、公式说明及连续结果列举的影响。本轮优先保持术语、事实和可读性，没有为追求脚本分数强行变换所有句子。', '',
    '## 五 逐段原文与改文', '',
    '以下覆盖全部36个修改段落。含公式的段落用“［原数学对象］”占位，便于比较外围文字，实际DOCX保留原公式。报告页码指用户提供的检测报告，不是论文页码。', '',
]
for order, i in enumerate(indices, 1):
    edits = [c for c in changes if c['paragraph'] == i]
    reasons = list(dict.fromkeys(c['reason'] for c in edits))
    record = records[i]
    lines += [f'### {order} {section(i)}', '',
              f'定位：原文以“{paragraph(i)[:24]}”起句；检测报告第{record["report_page"]}页，{record["risk"]}。', '',
              '**原文**', '', paragraph(i), '', '**修改后**', '', paragraph(i, True), '',
              '**修改说明**', '', ' '.join(reasons), '']
lines += ['## 六 复测建议', '',
          '将2026.10.03v63.docx作为新版，在与v62相同的平台、相同设置下复测。对比整体比例及新增标记的位置；后续仍应以术语、事实、数据和学术可读性为约束，不依据标红结果替换必要定义、图注或专业名词。', '']
output = ROOT / 'word_output/2026.10.03v63_句式修订对比报告.md'
output.write_text('\n'.join(lines), encoding='utf-8')
assert before['summary']['total_paragraphs'] == after['summary']['total_paragraphs']
assert len(indices) == 36 and len(changes) == 43
assert render['page_count_after'] == render['page_count_before'] == 10
assert render['figure_pages'] == {'1': 2, '2': 6, '3': 7, '4': 8, '5': 9}
assert render['table_pages'] == {'1': 5, '2': 6, '3': 7}
assert not audit['numeric_identifier_issues'] and not audit['term_count_differences']
print(json.dumps({'report': str(output), 'sections': dict(section_counts),
                  'scan_before': before, 'scan_after': after}, ensure_ascii=False, indent=2))
