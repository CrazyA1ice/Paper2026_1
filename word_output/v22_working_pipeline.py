from __future__ import annotations

from pathlib import Path
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "2026.09.21v21.docx"
TARGET = ROOT / "word_output" / "v22_working.docx"

doc = Document(SOURCE)

def find(prefix):
    xs = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(xs) != 1:
        raise RuntimeError(f"{prefix!r}: {len(xs)} matches")
    return xs[0]

def set_text(p, text):
    first = p.runs[0] if p.runs else p.add_run()
    first.text = text
    for r in p.runs[1:]:
        r.text = ""

def repl(prefix, text):
    p = find(prefix)
    set_text(p, text)
    return p

# -------------------------
# Step 2: expand introduction only
# -------------------------

p1 = repl(
    "云计算、视频业务、数据中心互联及智能网络应用持续扩展后",
    "随着云计算、视频业务、数据中心互联及智能网络应用不断扩展，骨干网络承载的数据规模持续增长，业务流量在时间上的变化也更加复杂。源—目的节点对（origin-destination，OD）流量描述网络中不同节点对之间的通信需求，其变化能够反映业务在网络内部的迁移和聚集情况。对于容量规划、拥塞预警、资源调度和流量工程等任务而言，若能够提前获得后一时段的OD流量估计，网络管理系统就可以在业务变化发生前进行相应调整。与相对平稳的单变量序列不同，OD流量通常同时包含周期变化、局部波动和突发变化，不同OD变量的数值范围也存在明显差异。因此，网络流量预测不仅需要描述较长时间范围内的变化趋势，还要保留对短时状态变化的响应能力。"
)

p2 = repl(
    "网络流量预测早期多采用统计模型",
    "围绕网络流量的时间变化规律，相关研究经历了从统计模型到机器学习、深度学习方法的发展。Lohrasbinasab等[1]对网络流量预测方法进行了系统梳理，说明数据驱动方法已成为复杂流量预测的重要研究方向。随着网络规模扩大，仅从单一序列的时间变化进行建模已难以覆盖OD变量之间的关联关系。Qin等[2]将图神经网络用于通信网络流量预测，把空间关联和时间依赖纳入同一模型；韦烜等[10]围绕大型IP网络流量矩阵开展分析与预测，进一步讨论了不同OD变量之间的关联及其随时间变化的特点。除变量关联外，周期规律也是网络流量中的重要信息，唐文杰等[11]提出CycleLLH模型，将周期性信息引入预测过程。上述工作分别从时间依赖、变量关联和周期结构等角度改进了网络流量预测，为后续从更细的时间结构分析流量变化提供了基础。"
)

p3 = repl(
    "同一段网络流量在不同时间分辨率下呈现出的信息并不相同",
    "除变量关联和周期特征外，同一段网络流量在不同时间分辨率下呈现出的信息也并不完全相同。原始分辨率序列保留了较多细节，更容易反映短时起伏；经过一定时间聚合后，局部扰动被削弱，较慢的变化趋势则更加突出。针对这类多时间尺度特征，Zhou等[3]利用深度回声状态网络开展多尺度网络流量预测，通过不同时间分辨率提取互补信息。与此同时，一些研究开始关注预测模型的结构复杂度。DLinear[4]采用时间序列分解和线性映射完成预测，结构相对简洁；TimeMixer[5]通过多尺度混合机制处理不同分辨率序列；LightTS[6]利用采样导向的MLP结构进行快速多变量时间序列预测。可以看到，多尺度建模和轻量时间序列预测分别从信息利用方式和模型结构两个方向提供了改进思路。对于骨干网络OD流量，如果能够在较小模型开销下同时使用不同时间尺度的信息，就有可能兼顾局部变化与整体趋势。"
)

p4 = repl(
    "实际流量序列中，各输入窗口的状态差异较大",
    "现有多尺度方法通常需要先确定若干时间尺度，但尺度建立之后，不同尺度在融合阶段往往采用预先设定的组合方式。实际流量序列中，各输入窗口的状态差异较大：有的窗口短时波动明显，有的窗口则主要呈现较平缓的趋势。当输入状态发生变化时，尺度1、2和4所包含的信息价值也可能随之变化。如果始终采用单一尺度，容易遗漏其他时间分辨率中的有效信息；如果对多个尺度长期使用固定比例，又难以反映不同窗口之间的状态差异。由此，本文关注的问题不只是如何构造多个时间尺度，还包括如何根据当前输入样本改变不同尺度在最终预测中的参与程度。"
)

# Add one new paragraph before section 1, using the same paragraph style as the prior introduction.
sec1 = find("1 自适应多尺度网络流量预测方法")
new_p = sec1.insert_paragraph_before(
    "基于上述考虑，本文构建一种样本级自适应多尺度网络流量预测方法。首先，在原始输入窗口上采用尺度1、2和4构造多分辨率序列，并使用结构简洁的DLinear作为各尺度预测专家，使不同时间分辨率分别形成候选预测结果；随后，从当前输入窗口提取能够反映总体水平、离散程度、最近状态和变化强度的统计量，经轻量路由网络生成Softmax尺度权重，再对各尺度预测结果进行融合。该设计将“各尺度如何预测”和“当前样本更需要哪个尺度”两个问题分开处理，使路由模块不必重新承担完整的时序预测任务。实验在Abilene和GÉANT两个公开骨干网数据集上进行，并通过DLinear、LightTS外部基线、固定等权多尺度消融、多个随机种子重复实验以及路由权重分析，对模型的预测结果和尺度分配行为进行验证。"
)
new_p.style = p4.style

# Guardrails
full = "\n".join(p.text for p in doc.paragraphs)
for token in [
    "源—目的节点对", "OD", "DLinear", "Softmax", "Abilene", "GÉANT",
    "LightTS", "CycleLLH", "TimeMixer",
    "Lohrasbinasab等[1]", "Qin等[2]", "Zhou等[3]", "韦烜等[10]", "唐文杰等[11]"
]:
    assert token in full, token

assert len(doc.tables) == 3
assert len(doc.inline_shapes) == 4

# Report introduction growth for later audit.
paras = [p.text.strip() for p in doc.paragraphs]
i_intro = next(i for i,t in enumerate(paras) if t.startswith("随着云计算"))
i_sec1 = next(i for i,t in enumerate(paras) if t.startswith("1 自适应多尺度网络流量预测方法"))
intro_chars = sum(len(t) for t in paras[i_intro:i_sec1] if t)
print("intro_chars_after", intro_chars)
print("intro_paragraphs", sum(1 for t in paras[i_intro:i_sec1] if t))

doc.save(TARGET)
print(TARGET)

# Step 2 introduction expansion complete.
