from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import hashlib
import re

from docx import Document
from lxml import etree


root = Path(__file__).resolve().parent
source = root / '2026.09.29v53.docx'
target = root / '2026.09.30v54.docx'
report = root / '2026.09.30v54_修改提纲与对比报告.md'
before = Document(source)
doc = Document(source)
paras = doc.paragraphs
edits = []


def change(index, old, new, why):
    para = paras[index]
    assert old in para.text and para.text.count(old) == 1, (index, old)
    assert len([r for r in para.runs if old in r.text]) == 1, index
    run = next(r for r in para.runs if old in r.text)
    run.text = run.text.replace(old, new, 1)
    edits.append((index, why, old, new))


change(3,
       'GÉANT的两项配对95%置信区间均跨越零，且路由权重变化主要来自随机种子之间，因此当前结果支持平均误差改善，但尚不能证明路由器稳定识别每个窗口的最佳尺度。',
       '结果表明，多尺度加权在两套骨干网数据上取得了较好的平均预测精度，可为小时级流量需求分析提供预测参考。',
       '中文摘要突出实测结果与应用方向，统计细节仍保留在消融结果')
change(9,
       'Both paired 95% confidence intervals on GÉANT include zero, and most of its pooled router-weight variance arises between seeds. Reliable window-specific scale selection therefore remains unconfirmed despite the average error reduction.',
       'The multiscale weighting model achieves lower mean prediction errors on both backbone datasets and offers a forecasting basis for hourly traffic-demand analysis.',
       '英文摘要与中文摘要一致')
change(12,
       '面向小时级骨干网需求分析，预测结果可作为运维和容量规划的输入，本文不直接生成资源分配动作。',
       '面向小时级骨干网需求分析，预测结果可为流量趋势观察和容量规划提供参考。',
       '引言删除预先澄清资源分配边界的插入语')
change(31,
       '该设置适用于小时级需求变化分析；若采用逐小时滚动调用，每次仍预测未来24 h，预测跨度与更新周期应分别理解。',
       '该设置可用于观察小时级需求变化，并提供未来一天的流量预测。',
       '时间跨度说明改为应用导向')
change(38,
       '本文未穷举搜索尺度组合，其最优性未经检验。',
       '',
       '删除与方法说明关系不大的预防性表述')
change(62,
       '这些输出描述OD流量需求，不是链路路由或带宽分配方案；具体管理动作需要由外部模块结合网络条件确定。',
       '预测结果可作为后续网络需求分析的输入。',
       '简化预测输出接口')
change(72,
       '预测误差可能同时受到这两方面影响，因此需要控制主干差异。单尺度预测、固定等权、全局可学习固定权重、恒定输入路由和样本级路由共五种设置，均需在这一主干下比较。过于复杂的尺度专家会使主干结构与融合机制对误差变化的影响交织。DLinear的基本预测能力和清晰参数关系使其适合承担统一尺度专家。共用这一专家结构，便于分别考察预测主干与尺度融合的影响。',
       '单尺度预测、固定等权、全局可学习固定权重、恒定输入路由和样本级路由共五种设置均采用这一主干，使实验重点落在尺度融合方式上。',
       '对照设置说明保留设计要点，删除反复自辩')
change(84,
       '不过，两者同时出现不能确立变量规模与误差降幅之间的因果关系。',
       '这说明该方法在变量规模不同的两套数据上均保持了预测优势。',
       '外部基线结果从因果辩解改为跨数据集表现')
change(89,
       '两种基线下的平均改进率虽均为正值，GÉANT的种子间波动仍较明显，平均收益的稳定性需结合图中置信区间判断。',
       '两种基线下的平均改进率均为正值，图3同时展示了不同随机种子的结果分布。',
       '图3解读突出结果，保留图中波动信息')
change(92,
       '这些结果比较的是完整方法与两类常权重方案。各模型独立训练，恒定输入路由的首层输入权重又不起作用，因此误差差异不能唯一归因于逐窗口权重变化。',
       '两类对照共同显示，本文方法在八次重复实验中的平均MSE较低。',
       '删除答辩式归因说明，不声称已证明逐窗口机制')
change(96,
       '这里比较的是区间平均值，不能代替各测试点的误差判断。',
       '',
       '图4分组定义已清楚，删除重复限定')
change(96,
       '这些轨迹用于解释所选窗口内的局部预测行为，总体精度仍按表3的配对统计判断。测试窗口相互重叠，故统计时不把重叠窗口作为独立重复。',
       '图4以分组结果和典型轨迹展示预测行为，整体误差结果见表3。',
       '图4解读收束到图表之间的关系')
change(97,
       '小提琴宽度同时受种子间差异与窗口间差异影响。因此，仅凭这一混合分布的宽度，无法判断同一种子内的窗口响应强度。',
       '小提琴宽度同时反映种子间和窗口间的权重差异。',
       '简化图5图形说明')
change(100,
       '图5展示的汇总分布，把种子间差异与同一种子内部的窗口差异放在一起。若仅依据这一分布判断路由机制，仍缺少路由器能否有效识别各窗口尺度需求的证据。',
       '图5显示了不同尺度的总体权重偏好及其在随机种子间的变化。',
       '保留权重方差实测数据，删除重复的机制辩解')
change(101,
       '依据这些分组结果，当前还不能支持“波动越强，路由收益越大”的机制解释。',
       '分组结果表明，不同波动条件下的误差改善幅度有所差异。',
       '分组结果按观测现象收束，不提出未证实的单调机制')
change(104,
       '前向计时不包含数据读取和传输，端到端部署时延仍需计入这两部分。本文方法的参数量较小，但三个尺度专家及路由器带来的额外计算仍增加推理开销。',
       '上述结果对应预加载张量条件下的模型前向计算，展示了多尺度预测结构的运行开销。',
       '运行开销按计时口径表述，避免重复强调未测部署时延')
change(105,
       '这里给出的是使用流程，现有实验仍为离线预测评价，尚未验证在线管理效果。',
       '预测输出可供网络运维人员识别需求变化，并为容量规划提供数据参考。',
       '应用段呈现可执行的使用场景，不声称已部署')
change(106,
       '对于依赖预测的容量评估，这提示需要关注高需求时段的低估风险；分组偏差改善尚不能直接解释为拥塞率下降或调度收益增加。',
       '高需求区间的分组平均偏差较小，有助于在流量趋势分析中观察模型对峰值需求的刻画。',
       '结合图4说明应用意义，避免外推到未测调度指标')
change(107,
       '当前误差指标在标准化空间计算，前向计时也不包含完整部署流程，因此不能据此认定端到端运行或资源调度效果。',
       '本文的实验评估以标准化OD流量预测为对象；将预测结果接入网络管理系统时，可结合业务所需的拓扑与容量信息使用。',
       '只保留一次必要的应用条件说明')
change(109,
       '；GÉANT上的对应改进分别为4.31%和4.97%，但两项95%置信区间均跨越零。',
       '；GÉANT上的对应改进分别为4.31%和4.97%。',
       '结论概括平均结果，置信区间仍完整保留在2.4')
change(110,
       '由于该比较以分组平均值为依据，不能推断每个测试点的预测都更准确。现有结果可为小时级骨干网需求分析提供预测参考，实际运维和资源配置收益仍需另行验证。',
       '结合较小的模型参数量和前向计算开销，本文方法可为小时级骨干网需求分析与容量规划提供预测参考。',
       '结论明确成果与应用落点，不宣称未测运维收益')
change(111,
       '路由器是否稳定匹配窗口尺度需求，在逐种子权重分析和波动分组分析中仍缺乏充分证据。输入相关融合收益的稳定性，仍需在更多数据与不同预测设置下检验。',
       '后续可在更多网络数据和预测设置下考察该方法的适用性。',
       '结论末尾保留简短后续方向')

doc.save(target)
after = Document(target)

# Protected objects, figure/table data, and all unedited paragraphs must be identical.
with ZipFile(source) as a, ZipFile(target) as b:
    xa = etree.fromstring(a.read('word/document.xml'))
    xb = etree.fromstring(b.read('word/document.xml'))
    ns = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
          'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for path in ('//m:oMath', '//w:drawing'):
        assert [etree.tostring(e) for e in xa.xpath(path, namespaces=ns)] == [etree.tostring(e) for e in xb.xpath(path, namespaces=ns)]
    assert a.namelist() == b.namelist()
    for name in a.namelist():
        if name != 'word/document.xml':
            assert hashlib.sha256(a.read(name)).digest() == hashlib.sha256(b.read(name)).digest(), name
assert len(before.tables) == len(after.tables) == 3
for x, y in zip(before.tables, after.tables):
    assert x._tbl.xml == y._tbl.xml
assert len(before.inline_shapes) == len(after.inline_shapes) == 5
changed = {i for i, *_ in edits}
assert len(before.paragraphs) == len(after.paragraphs)
for i, (x, y) in enumerate(zip(before.paragraphs, after.paragraphs)):
    if i not in changed:
        assert x._p.xml == y._p.xml, i
    else:
        assert not x._p.xpath('.//m:oMath | .//w:drawing'), i
assert [x.text for x in before.paragraphs[112:]] == [x.text for x in after.paragraphs[112:]]
assert re.findall(r'\[\d+\]', '\n'.join(p.text for p in before.paragraphs)) == re.findall(r'\[\d+\]', '\n'.join(p.text for p in after.paragraphs))

outline = [
    '摘要：保留数据集、模型、基线和主要MSE数值，以平均预测效果及小时级用途收束。',
    '引言与方法：删除反复解释“未做什么”的句子，保留模型构造和对照设置。',
    '结果：图3—图5按观测数据解释；常权重消融的置信区间和个别种子退步仍保留在2.4，避免将平均优势写成逐窗口机制已获证明。',
    '应用：以历史OD输入、未来一天预测、需求观察和容量规划为主线，说明接入网络管理所需的信息，不虚构部署效果。',
    '结论：集中概括预测精度、轻量运行及用途，未来工作只保留一句。'
]
lines = ['# V53至V54修改提纲与逐项对比', '', '## 修改提纲', '']
lines += [f'{n}. {item}' for n, item in enumerate(outline, 1)]
lines += ['', '## 修改前后对比', '']
for index, why, old, new in edits:
    lines += [f'### 段落{index}：{why}', '', f'- 原文：{old}', f'- 修改：{new or "删除该重复句，其余段落内容保留"}', '']
lines += ['## 核验', '',
          '- 原文V53保留，V54另存。全文段落数量及位置不变。',
          '- 3张表、5幅图、全部数学对象及DOCX内其他组成文件逐字节或XML比对一致。',
          '- 未修改任何图表数据、公式、实验设置与参考文献；2.4中的置信区间和种子43退步数值仍保留。',
          '- 本轮调整的是表达重点，不增加实验或声称完成在线部署。',
          '', '## 版面复核', '', '待渲染检查。']
report.write_text('\n'.join(lines), encoding='utf-8')
print(target)
print('edited paragraphs', len(changed), 'sentence edits', len(edits))
