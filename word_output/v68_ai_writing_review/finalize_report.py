from pathlib import Path
from collections import Counter
from zipfile import ZipFile
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
import pymupdf

def read(name):
    return json.loads((QA / name).read_text(encoding='utf-8'))

audit = read('structural_audit.json')
changes = read('span_changes.json')
records = read('source_segments.json')
render = read('render_record.json')
preservation = read('preservation_result.json')
assert preservation['ok'] and not preservation['errors']
assert hashlib.sha256((QA.parent / '2026.10.04v67.docx').read_bytes()).hexdigest() == audit['source_sha256']
assert hashlib.sha256((QA.parent / '2026.10.04v68.docx').read_bytes()).hexdigest() == audit['output_sha256']

formula_pages = {}
for version, path in [('v67', ROOT / 'word_output/v67_aigc_review/2026.10.04v67.pdf'),
                      ('v68', QA / '2026.10.04v68.pdf')]:
    document = pymupdf.open(path)
    found = {}
    for i, page in enumerate(document):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                value = ''.join(span['text'] for span in line['spans']).strip()
                match = re.fullmatch(r'\((\d+)\)', value)
                if match and line['bbox'][0] > page.rect.width * 0.8:
                    found[int(match.group(1))] = i + 1
    assert sorted(found) == list(range(1, 17)), (version, found)
    formula_pages[version] = found
render['formula_pages'] = formula_pages
render['visually_reviewed_pages'] = list(range(1, 11))
render['visual_result'] = 'All ten pages inspected; no new overlap, clipping, missing symbols, or detached captions observed.'
(QA / 'render_record.json').write_text(json.dumps(render, ensure_ascii=False, indent=2), encoding='utf-8')

section_starts = [(3, '中文摘要'), (11, '引言'), (18, '1 方法总体说明'),
                  (24, '1.1 预测任务与数据预处理'), (35, '1.2 多尺度构造与DLinear专家'),
                  (46, '1.3 样本级自适应尺度加权'), (58, '1.4 模型训练与预测输出'),
                  (65, '2.1 数据集与实验设置'), (77, '2.2 总体预测性能与基线比较'),
                  (85, '2.3 八随机种子核心消融与稳定性'), (95, '2.4 预测行为与尺度权重分析'),
                  (107, '2.5 运行开销与网络管理应用讨论'), (115, '3 结语')]

def section(i):
    return [name for start, name in section_starts if start <= i][-1]

para_ids = sorted({c['paragraph'] for c in changes})
section_counts = Counter(section(i) for i in para_ids)
risk_counts = Counter(records[i]['risk'] for i in para_ids)
out = [
    '# v67 → v68 句式修订对比报告',
    '',
    '## 一、依据与本轮范围',
    '',
    '- 原稿：`2026.10.04v67.docx`；新版：`2026.10.04v68.docx`。v67 原稿保留。',
    '- 检测依据：`检测报告_2026.10.04v67_.pdf`，PaperPure，报告编号 PAPERPURE20261004150744，检测时间 2026-10-04 15:07:44。',
    '- 报告原始结果：AIGC 检测率 46.7%，AI 特征字符数 4492，总字符数 9628；前 20%、中 60%、后 20% 的检测率分别为 25.4%、49.4%、61.0%。',
    '- 与 v66 的 47.8% 相比，v67 下降 1.1 个百分点。这是已提供报告的历史结果，不是 v68 的结果。',
    '- 本轮使用 Avoid AI Writing 的局部文件编辑与保护性核验流程，围绕报告标记段落作句式调整，不设机械的改写比例。',
    f'- 共修改 {len(para_ids)} 个段落内的 {len(changes)} 处文字片段：高风险标记段落 {risk_counts.get("高风险", 0)} 个，中风险标记段落 {risk_counts.get("中风险", 0)} 个。每段中未列出的句子保留。',
    '- 修改重点是主语与动作关系、比较对象、操作先后次序及句间衔接。未新增实验、应用验证或结论，保留已有的学术限定。',
    '',
    '## 二、发现的问题及处理方式',
    '',
    '| 原有表达问题 | 本轮处理 |',
    '|---|---|',
    '| “比较显示”“对应的比较降幅”等表达使参照模型与指标关系不够直接 | 按“相对某模型—某指标—改进率”组织语句 |',
    '| 计算步骤由被动句或抽象名词串联 | 以路由器、尺度专家、训练操作为主语，直接说明输入和输出 |',
    '| 概括句与后面的具体操作重复 | 合并重复说明，保留操作、对象及约束 |',
    '| 分组、样本量与结果放在长句中，读取对应关系较费力 | 先交代范围，再按组别写样本量与结果 |',
    '| 推理流程、网络需求用途的衔接不够顺畅 | 将处理、输出及参考用途连贯表达，保持“可供参考”的应用范围 |',
    '',
    '必要的专业表述不按普通词汇重复处理。例如“源—目的节点对”的连接符、模型名称和统计术语保持原样。带引用的文献转述、未标记段落及图表说明未作整段改写。',
    '',
    '## 三、各部分修改数量',
    '',
    '| 位置 | 修改段落数 |',
    '|---|---:|',
]
out += [f'| {name} | {count} |' for name, count in section_counts.items()]
out += [
    '',
    '## 四、逐处修改对比',
    '',
    '以下列出全部修改片段；章节、检测报告页码及修改理由便于逐项核对。显示的是纯文字片段，夹在片段之外的公式仍保持原对象。',
]
for order, c in enumerate(changes, 1):
    i = c['paragraph']
    out += [
        '', f'### {order:02d}．{section(i)}（检测报告第 {records[i]["report_page"]} 页）', '',
        '**修改前**', '', c['before'], '', '**修改后**', '', c['after'], '',
        '**理由：**' + c['reason'],
    ]

out += [
    '', '## 五、内容与格式核验', '',
    '| 核验项 | 结果 |',
    '|---|---|',
    '| 原稿保留 | v67 文件哈希与修改前一致 |',
    '| 修改边界 | 仅改变 `word/document.xml` 中指定的文字；DOCX 其余打包文件内容相同 |',
    '| 字体、字号、段落、行距、缩进、页边距等格式 | 清空文字后的 XML 结构完全一致，所有原有格式节点保留 |',
    '| 未修改段落 | XML 内容逐段一致；正文共有 129 个顶层段落 |',
    '| 表格 | 3 张表的完整 XML 一致，单元格文字与数值未改 |',
    '| 图片 | 5 个绘图对象及所有嵌入媒体文件保持一致，图注与注释未改 |',
    '| 公式 | 41 个 OMML 数学对象逐项一致，包含行内公式和 16 个编号公式 |',
    '| 实验数据与设置 | 修改段落中数值及拉丁标识符逐段计数一致，表格和图像数据未改 |',
    '| 专业术语 | 保护术语清单逐段出现次数一致；人工复核未用近义词改写专业术语 |',
    '| 引用与参考文献 | 引用编号逐段一致；11 条参考文献原文与顺序保留 |',
    '| 技能保护性验证 | 实际 DOCX 提取文本的验证为 PASS，无错误和警告，14 个章节标题结构保留 |',
    '| 语义复核 | 保留比较基线、分组条件、计时均值计算方法、应用参考范围及置信区间跨零描述 |',
    '| 排版检查 | Word 只读副本导出后逐页检查 10 页，未发现新增遮挡、裁切、缺字或图注脱离 |',
    '',
    f'修改段落的文字由 {audit["modified_text_chars_before"]} 个字符变为 {audit["modified_text_chars_after"]} 个字符，净减少 {audit["modified_text_chars_before"] - audit["modified_text_chars_after"]} 个字符。这来自句式压缩及重复连接语调整，未删除实验结果、数据设置、公式、图表或原有应用内容。该字符数采用文档文字节点计数，口径与检测平台的字符数不同。',
    '',
    '语义复核时另校正两处草稿：第 1.1 节保留“压缩流量取值范围”的预处理含义；第 2.5 节将两套数据的差别与应用参考用途分开表达。这些调整已纳入上面的最终对比。',
    '',
    '### 图表位置与自动分页',
    '',
    '- v67 与 v68 均为 10 页。',
    '- 图 1～5 仍在第 2、6、7、8、9 页；表 1～3 仍在第 5、6、7 页。',
    '- 新版编号公式（1）～（6）位于第 3 页，（7）～（13）位于第 4 页，（14）～（16）位于第 5 页。',
    '- 句长改变会使 Word 自动换行或跨页位置变化；格式设置、图表锚点及对象没有调整。公式（6）在新版随正文移至第 3 页末，完整显示，其后的公式（7）正常接续。',
    '',
    '## 六、检测解释与后续验证',
    '',
    '本轮实际执行了技能的本地规则扫描和保护性验证。技术语境下，对相同范围的正文，改写前后均检出 2 项模式：专业表达中的一个长连接符及技术词汇重复。本地规则扫描主要面向英文，正文仅被计作 81 个单词，不能覆盖这篇中文论文的 AIGC 判定，因此没有把它的分数或作者分类用作降率证据，也没有为了消除这些提示改写专业名词。',
    '',
    '包括标题、表格、公式文字及参考文献的全文保护性验证通过；前后残留模式数量未增加。这项核验用于检查保留情况，不代表实际平台 AIGC 检测率。',
    '',
    '**v68 尚未重新提交同平台检测，本轮不能报告新的 AIGC 百分比。** 后续应使用相同平台和设置检测 v68，以新报告确认改动效果。',
    '',
    '## 七、文件核对信息',
    '',
    '- 原稿 SHA-256：`' + audit['source_sha256'] + '`',
    '- 新版 SHA-256：`' + audit['output_sha256'] + '`',
]
report = QA.parent / '2026.10.04v68_句式修订对比报告.md'
report.write_text('\n'.join(out) + '\n', encoding='utf-8')
print(json.dumps({'report': str(report), 'risk_counts': dict(risk_counts),
                  'formula_pages': formula_pages, 'paragraphs': len(para_ids),
                  'spans': len(changes)}, ensure_ascii=False))
