"""Targeted prose editing of v43, with numeric and artifact preservation checks."""

import hashlib
import re
from pathlib import Path
from zipfile import ZipFile

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output/2026.09.27v43.docx"
TARGET = ROOT / "word_output/2026.09.27v44.docx"
REPORT = ROOT / "word_output/2026.09.27v44_语言修改对照.md"

# Every replacement retains the original measurements, comparisons and terms.
EDITS = {
    3: [
        ("骨干网络源—目的节点对流量同时包含短时起伏与较慢趋势，单一时间分辨率难以兼顾。",
         "骨干网络源—目的节点对流量兼有短时起伏和较慢趋势，单一时间分辨率难以同时表征两者。"),
        ("本文采用尺度1、2和4的DLinear专家，并由输入窗口统计量驱动的轻量路由网络计算Softmax融合权重。",
         "本文采用尺度1、2和4的DLinear专家，由轻量路由网络根据输入窗口统计量生成Softmax融合权重。"),
    ],
    9: [
        ("Backbone origin-destination traffic contains both short-term fluctuations and slower trends.",
         "Backbone origin-destination traffic exhibits short-term fluctuations alongside slower trends."),
    ],
    12: [
        ("容量规划、拥塞预警、资源调度和流量工程都需要对后续流量状态作出判断，提前获得后一时段的OD流量估计有助于网络管理系统预先调整资源。",
         "容量规划、拥塞预警、资源调度和流量工程均依赖对后续流量状态的判断。后一时段的OD流量估计可为网络管理系统预先调整资源提供依据。"),
    ],
    13: [
        ("网络流量预测已经从传统统计模型逐步扩展到机器学习和深度学习方法。",
         "网络流量预测方法已由传统统计模型扩展至机器学习和深度学习模型。"),
        ("现有工作已经涉及时间依赖、变量关联和周期结构等多个方面，也为进一步分析不同时间分辨率下的流量变化提供了基础。",
         "这些工作分别从时间依赖、变量关联和周期结构刻画流量变化。"),
    ],
    14: [
        ("另一方面，模型结构开销也需要考虑。", "模型结构开销也不可忽略。"),
        ("本文在这些工作的基础上，把关注点放在多时间尺度信息的利用与模型规模控制之间的平衡。",
         "据此，本文同时考察多时间尺度信息的利用与模型规模控制。"),
    ],
    15: [
        ("问题在于，不同输入窗口的流量状态并不相同：", "不同输入窗口的流量状态存在差异："),
        ("基于这一现象，本文不仅构造多个时间尺度，还让各尺度在最终预测中的参与程度随当前输入样本变化。",
         "因此，模型在构造多个时间尺度的同时，根据当前输入样本调整各尺度在最终预测中的权重。"),
    ],
    17: [
        ("实验在Abilene和GÉANT两个公开骨干网数据集上进行，并设置DLinear、LightTS、固定等权、全局可学习固定权重与恒定输入路由模型、多个随机种子重复实验和路由权重分析，用于检验预测误差、核心结构消融和尺度分配行为。",
         "实验在Abilene和GÉANT两个公开骨干网数据集上进行，比较DLinear、LightTS、固定等权、全局可学习固定权重与恒定输入路由模型，并通过多个随机种子重复实验和路由权重分析检验预测误差、核心结构消融与尺度分配行为。"),
    ],
    19: [
        ("方法把多尺度预测和尺度选择分成两个模块：", "模型包含多尺度预测和尺度选择两个模块："),
        ("原始OD流量先进行对数变换和标准化，再形成3个时间分辨率的输入序列；3个专家得到候选预测后，由样本级权重完成融合。",
         "原始OD流量经对数变换和标准化后形成3个时间分辨率的输入序列；3个专家分别预测，再按样本级权重融合。"),
        ("用于分别比较等权、全局非等权与输入相关融合的结果。",
         "用以比较等权、全局非等权与输入相关融合。"),
    ],
    20: [
        ("只使用一个尺度会舍弃其他分辨率的信息；长期采用固定比例又不能随输入窗口变化。", ""),
    ],
    30: [
        ("经过上述处理后，每个输入样本仍保持原始时间分辨率。为了让后续专家同时观察细粒度变化和较平滑的趋势，需要进一步从同一历史窗口构造不同时间尺度的表示。",
         "预处理后的输入样本仍为原始时间分辨率。为使专家分别观察细粒度变化与较平滑的趋势，下一步从同一历史窗口构造不同尺度的表示。"),
    ],
    37: [
        ("尺度集合采用1、2和4，主要是为了在96步历史窗口内形成三个层次清晰且长度均为整数的时间分辨率，同时控制专家数量。",
         "选择尺度1、2和4，可由96步历史窗口形成三组长度均为整数的序列，同时控制专家数量。"),
    ],
    45: [
        ("采用DLinear作为尺度专家，主要是为了把预测主干与尺度融合的影响区分开。",
         "采用DLinear作为尺度专家，有助于区分预测主干和尺度融合各自的影响。"),
    ],
    51: [
        ("路由器仅计算三个尺度的融合分数，不需要再次完成完整的OD流量预测，",
         "路由器仅计算三个尺度的融合分数，无需再次预测完整的OD流量，"),
    ],
    53: [
        ("式（11）得到的3个尺度分数仍是未归一化值。", "式（11）输出的3个尺度分数尚未归一化。"),
        ("为使这些分数可以直接解释为各专家在最终预测中的相对贡献，使用Softmax进行归一化。经Softmax处理后，每个权重均为非负值，并且3个权重之和为1：",
         "经Softmax归一化后，3个非负权重之和为1，可用于表示各专家在最终预测中的相对贡献："),
    ],
    61: [
        ("参数训练使用Adam优化器，并以验证集MSE选择最终模型。",
         "模型使用Adam优化器训练，并依据验证集MSE选择最终模型。"),
    ],
    62: [
        ("模型的计算过程可以概括为三个环节：", "模型计算依次经过三个环节："),
    ],
    64: [
        ("实验按外部基线、核心消融和路由行为三个层次组织。",
         "实验分为外部基线比较、核心消融和路由行为分析三个层次。"),
    ],
    66: [
        ("两者在序列长度和变量规模上差异较大，能够在相同预测流程下提供不同的数据条件。",
         "两者的序列长度和变量规模差异较大，可用于观察同一预测流程在不同数据条件下的表现。"),
    ],
    68: [
        ("实验不为各模型单独搜索最优超参数，而是在统一预测任务下控制数据与训练条件。",
         "为控制数据与训练条件，实验未分别搜索各模型的最优超参数。"),
    ],
    71: [
        ("实验设置DLinear、LightTS、固定等权多尺度、全局可学习权重和恒定输入路由五类对照。",
         "对照包括DLinear、LightTS、固定等权多尺度、全局可学习权重和恒定输入路由五类模型。"),
    ],
    75: [
        ("同时给出平均水平和重复实验间的波动。",
         "分别反映平均水平和随机种子间的波动。"),
    ],
    79: [
        ("图2聚焦独立外部基线LightTS，并使用两种方法共同具备的随机种子42～44。",
         "图2以LightTS为独立外部基线，使用两种方法共有的随机种子42～44。"),
    ],
    82: [
        ("两个数据集上的相对降幅并不相同。", "两个数据集的相对降幅存在差异。"),
    ],
    87: [
        ("图中的散点对应单次随机种子实验，半小提琴以平滑轮廓展示8次结果的分布，黑色菱形和横向误差线表示8次改进率的均值及95%置信区间，",
         "散点对应各随机种子，半小提琴展示8次结果的分布；黑色菱形和横向误差线表示8次改进率的均值及95%置信区间，"),
    ],
    90: [
        ("这一比较仍不足以证明每个窗口的尺度权重分配本身有效。",
         "因此，这一比较仍无法单独证明逐窗口权重分配有效。"),
    ],
    93: [
        ("四种模型在高真实值区域均有低估，本文方法的平均偏差较小，但分组均值不能代表逐点误差。",
         "四种模型在高真实值区域均出现低估。本文方法的平均偏差较小，但分组均值不代表逐点误差。"),
    ],
    95: [
        ("小提琴合并了种子与窗口两个层次，其宽度不能直接解释为同一种子内的窗口响应强度。",
         "小提琴同时包含种子间差异和窗口间差异，其宽度不能直接表示同一种子内的窗口响应强度。"),
    ],
    99: [
        ("进一步以输入窗口平均绝对一阶差分衡量波动强度，并用训练窗口的三分位数阈值划分测试窗口。",
         "输入窗口的平均绝对一阶差分用于衡量波动强度；测试窗口按训练窗口的三分位数阈值分组。"),
    ],
    100: [
        ("除预测误差和路由行为外，还需考察前向开销。", "模型前向开销另行测量。"),
    ],
    102: [
        ("本文面向骨干网络OD流量中的短时波动和较慢趋势，",
         "本文针对骨干网络OD流量的短时波动与较慢趋势，"),
    ],
}


def numbers(text):
    return re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?%?", text)


def citations(text):
    return re.findall(r"\[\d+\]", text)


original = Document(SOURCE)
document = Document(SOURCE)
assert len(document.paragraphs) == 115
before_paragraphs = [p.text for p in original.paragraphs]
changes = []
for index, replacements in EDITS.items():
    paragraph = document.paragraphs[index]
    assert not paragraph._p.xpath(".//w:drawing")
    assert not paragraph._p.xpath(".//m:oMath")
    before = paragraph.text
    assert paragraph.runs and paragraph.runs[0].text == before, index
    after = before
    for old, new in replacements:
        assert after.count(old) == 1, (index, old)
        after = after.replace(old, new, 1)
    assert numbers(after) == numbers(before), index
    assert citations(after) == citations(before), index
    paragraph.runs[0].text = after
    assert paragraph.text == after
    changes.append((index, before, after))

document.save(TARGET)
check = Document(TARGET)
assert len(check.inline_shapes) == len(original.inline_shapes) == 5
assert len(check.tables) == len(original.tables) == 3
assert len(check.paragraphs) == len(original.paragraphs)
for i, (before, after) in enumerate(zip(before_paragraphs, [p.text for p in check.paragraphs])):
    if i in EDITS:
        assert after == next(item[2] for item in changes if item[0] == i)
    else:
        assert after == before, i
for old_table, new_table in zip(original.tables, check.tables):
    assert [[c.text for c in row.cells] for row in old_table.rows] == [
        [c.text for c in row.cells] for row in new_table.rows
    ]
with ZipFile(SOURCE) as source_zip, ZipFile(TARGET) as target_zip:
    source_media = {
        name: hashlib.sha256(source_zip.read(name)).hexdigest()
        for name in source_zip.namelist() if name.startswith("word/media/")
    }
    target_media = {
        name: hashlib.sha256(target_zip.read(name)).hexdigest()
        for name in target_zip.namelist() if name.startswith("word/media/")
    }
    assert source_media == target_media
    assert source_zip.read("word/document.xml").count(b"<m:oMath") == \
        target_zip.read("word/document.xml").count(b"<m:oMath")

lines = [
    "# v44 语言修改对照", "",
    "仅对下列正文段落作语言修改；表格、图像、公式、数值、引用编号及其余段落未变。",
    "",
]
for index, before, after in changes:
    lines += [f"## 段落 {index}", "", "修改前：", "", before, "", "修改后：", "", after, ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(TARGET)
print(REPORT)
print(f"Modified paragraphs: {len(changes)}")
