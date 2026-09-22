from __future__ import annotations

from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "2026.09.21v21.docx"
TARGET = ROOT / "word_output" / "2026.09.22v22.docx"

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


# -------------------------
# Step 3: expand Section 1 methodology
# -------------------------

# 1. Overall design rationale
p_method = repl(
    "图1所示流程从原始OD流量开始",
    "图1给出了自适应多尺度网络流量预测方法的整体流程。本文没有直接使用一个复杂模型同时完成多尺度特征提取和预测，而是将任务拆分为两个相对独立的部分：一部分负责在不同时间分辨率下完成预测，另一部分负责判断当前输入窗口中各尺度结果应占多大比重。原始OD流量经过对数变换和标准化后，在尺度1、2和4上形成3组输入序列，分别交由独立的DLinear专家处理；与此同时，轻量路由网络只读取当前窗口的统计特征，为3个尺度生成样本级权重。最终预测由3个专家输出按权重组合得到。这样的结构使多尺度预测和尺度选择各自承担明确功能，也便于后续通过固定等权模型单独考察自适应权重的作用。"
)
caption1 = find("图1 自适应多尺度网络流量预测方法框架")
p_design = caption1.insert_paragraph_before(
    "这一设计的出发点是，不同时间分辨率对同一流量窗口的描述侧重点不同。原始尺度保留的局部变化较多，较粗尺度则通过时间聚合削弱部分短时扰动，更容易呈现整体变化。若只保留其中一个尺度，其他时间分辨率的信息将不会进入预测过程；若简单固定多个尺度的融合比例，又无法随输入状态变化。基于此，本文保留3个尺度的独立预测结果，再把尺度组合问题交给路由网络处理。DLinear结构较为简洁，可在控制模型规模的同时作为不同尺度上的预测专家，使方法的重点放在多尺度构造和样本级融合机制上。"
)
p_design.style = p_method.style

# 1.1 Problem definition and preprocessing
repl(
    "记预处理后的多变量流量序列为",
    "记预处理后的多变量流量序列为 xt∈RC，其中t表示时间索引，C表示有效OD变量数。对连续序列按时间滑动得到监督学习样本，第n个样本由一段历史窗口和其后的预测区间组成。历史窗口记为Xn，包含连续L个时间点；预测目标记为Yn，包含紧随其后的H个时间点。因而，模型学习的实质是利用多个OD变量在过去L步中的联合变化，估计这些变量未来H步的取值。第n个样本对应的输入与目标定义为"
)
repl(
    "本文取输入长度L=96、预测长度H=24",
    "本文取输入长度L=96、预测长度H=24，变量数C由具体数据集保留的有效OD维度决定，学习映射记为Ŷn=fθ(Xn)。L决定模型每次能够观察到的历史范围，H则对应一次需要连续预测的未来长度。由于原始OD流量为非负值，且不同OD变量之间的流量量级可能存在明显差异，若直接使用原始数值训练，较大的数值范围会使不同变量处于不一致的尺度。为减小这种数值跨度，首先对原始流量vt,c作对数变换"
)
repl(
    "其中μctr和σctr只在训练集上计算",
    "其中μctr和σctr分别表示第c个OD变量在训练集上的均值和标准差，只由训练数据计算，验证集和测试集均沿用训练阶段得到的统计量。log(1+x)变换用于压缩非负流量的数值范围，同时保留流量大小关系；随后进行按变量标准化，使不同OD维度以相近的数值尺度进入模型。两步处理承担的作用并不相同：前者主要缓和原始流量量级差异，后者使各变量在统一尺度下参与损失计算和参数更新。数据仍按时间顺序以6∶2∶2划分为训练集、验证集和测试集，各集合内部独立生成滑动窗口，避免窗口跨越不同数据划分边界。"
)

# Add a short bridge before Section 1.2
h12 = find("1.2 多尺度序列构造")
p_bridge12 = h12.insert_paragraph_before(
    "经过上述处理后，每个输入样本仍保持原始时间分辨率。为了让后续专家同时观察细粒度变化和较平滑的趋势，需要进一步从同一历史窗口构造不同时间尺度的表示。"
)
p_bridge12.style = find("其中μctr和σctr分别表示").style

# 1.2 Multiscale construction
repl(
    "设尺度集合S={1,2,4}。对于任一尺度s",
    "设尺度集合S={1,2,4}。尺度s表示沿时间维进行聚合时使用的窗口大小。对于任一尺度s，采用窗口大小为s、步长也为s的非重叠平均池化："
)
repl(
    "本文使用尺度集合S={1,2,4}",
    "本文使用尺度集合S={1,2,4}。在输入长度L=96时，尺度1保留原始96步序列；尺度2将相邻2个时间点取平均，得到48步序列；尺度4按4个时间点进行平均，得到24步序列。三者分别对应原始、中等和平滑程度更高的时间表示。尺度1不压缩时间轴，因此保留较完整的短时起伏；尺度2对局部变化进行适度平滑；尺度4进一步削弱短时间内的高频变化，使较慢的变化趋势更突出。这里采用平均池化而不是新增可训练的尺度变换模块，是为了在构造多分辨率输入时不额外增加模型参数。"
)
h13 = find("1.3 DLinear尺度专家")
p_scale_reason = h13.insert_paragraph_before(
    "尺度集合采用1、2和4，主要是为了在96步历史窗口内形成三个层次清晰且长度均为整数的时间分辨率，同时控制专家数量。尺度继续增加虽然可以产生更粗的序列，但也会继续缩短有效时间长度并增加新的专家分支。本文并不将{1,2,4}作为经过穷举得到的最优尺度组合，而是把它作为兼顾细粒度信息、趋势信息和模型规模的一组固定设计。采用非重叠池化还使每个原始时间点只参与一次同尺度聚合，尺度变化的含义较为直接。"
)
p_scale_reason.style = find("本文使用尺度集合S={1,2,4}").style

# 1.3 DLinear experts
repl(
    "尺度1、2和4各配置一个DLinear专家[4]",
    "尺度1、2和4分别配置一个DLinear专家[4]，每个专家只处理本尺度对应的输入序列。DLinear的核心思路是先将序列拆分为变化较慢的趋势项和围绕趋势变化的余项，再分别完成时间映射。对尺度s的输入，本文使用长度q=25的中心移动平均提取趋势项。移动平均相当于在局部时间邻域内进行平滑，为避免序列两端因窗口不足而缩短，边界位置采用端点复制方式补齐，从而保持分解前后的时间长度一致："
)
repl(
    "对3个尺度分别使用独立DLinear专家[4]",
    "由式（6）和式（7）可得到尺度s上的趋势项T(s)和余项R(s)。趋势项表示经过局部平滑后保留下来的较慢变化部分，余项则由原序列减去趋势项得到，保留未被移动平均解释的局部变化。式（8）分别对两部分沿时间维进行线性映射，并把二者的预测结果相加形成该尺度的候选预测。3个尺度使用独立DLinear专家，是因为尺度1、2和4的输入长度分别为96、48和24，对应的时间分辨率和时间映射关系并不相同；若强制共用一组尺度间参数，会把不同长度、不同平滑程度的序列约束到同一映射中。同一尺度内部，各OD变量共享时间映射参数，模型学习的是这一时间尺度下通用的时间映射形式，而不是为每个OD变量分别建立一套线性层。"
)
h14 = find("1.4 样本级自适应尺度加权")
p_expert_reason = h14.insert_paragraph_before(
    "选择DLinear作为尺度专家还有一个考虑：本文需要比较“单尺度预测”“固定等权多尺度”和“样本级自适应多尺度”之间的差异。如果尺度专家本身使用结构过于复杂的网络，最终误差变化会同时受到预测主干和尺度融合机制的影响。DLinear参数结构较清晰，因此可以在保持预测能力的同时，把实验关注点更多放在多尺度输入和权重分配方式上。"
)
p_expert_reason.style = find("由式（6）和式（7）").style

# 1.4 Sample-wise adaptive scale weighting
repl(
    "3个DLinear专家输出后",
    "经过3个DLinear专家后，同一样本会得到3组预测结果。下一步需要确定这些结果在最终预测中的比例。最直接的方式是令3个尺度均取1/3，但这种处理默认所有输入窗口的尺度需求完全相同。实际上，某些窗口的局部波动较明显，细粒度信息可能更值得保留；另一些窗口变化较平稳，较粗尺度中的趋势信息可能更有参考价值。因此，本文不直接固定融合比例，而是从原始输入Xn中提取四维统计向量zn=[μn,σn,ℓn,dn]，用这些统计量描述当前窗口状态，其中"
)
repl(
    "μn、σn、ℓn和dn分别表示输入窗口的总体水平",
    "μn、σn、ℓn和dn分别表示输入窗口的总体水平、离散程度、最近状态和平均变化强度。μn用于概括当前窗口整体处于较高还是较低的流量水平；σn反映窗口内部各观测值的离散程度，可用于描述整体波动大小；ℓn对应窗口末时刻的平均状态，为路由器提供最接近预测起点的信息；dn由相邻时间点的一阶变化构造，用于补充窗口内部变化速度的信息。这4个统计量分别从水平、波动、最近状态和局部变化四个角度概括输入窗口。它们并不直接承担未来流量预测，而是作为尺度选择的依据。"
)
# Add routing explanation immediately before the Softmax paragraph (i.e. after formula 11).
softmax_para = find("3个尺度分数经Softmax处理后得到非负权重")
p_router = softmax_para.insert_paragraph_before(
    "四维向量输入隐藏维数为16的两层感知器，输出3个尺度对应的未归一化分数。这里没有再使用额外的循环网络、注意力网络或其他完整时序编码器，原因是路由器的任务不是重新学习一遍OD流量预测，而只是根据已经提取的窗口状态判断三个尺度的相对重要程度。低维统计量和较小隐藏层可以把路由模块的参数规模限制在较低水平。其尺度分数计算为"
)
p_router.style = find("μn、σn、ℓn和dn分别表示输入窗口的总体水平").style

repl(
    "3个尺度分数经Softmax处理后得到非负权重",
    "式（11）得到的3个尺度分数仍是未归一化值。为使这些分数可以直接解释为各专家在最终预测中的相对贡献，使用Softmax进行归一化。经Softmax处理后，每个权重均为非负值，并且3个权重之和为1："
)
# Explain final fusion after equation 13
repl(
    "Softmax输出对应当前输入样本的一组尺度权重",
    "式（13）利用上述权重对3个DLinear专家的预测结果进行加权求和，得到最终预测Ŷn。这里的权重是样本级而不是全局固定参数，即不同输入窗口可以得到不同的尺度组合；同一个输入窗口内，该组权重由全部OD变量共享。这样处理可以避免为每个OD变量单独设置路由器，从而控制参数量。为了区分“使用多尺度”与“使用自适应权重”两部分作用，固定等权消融模型直接把3个尺度权重设为1/3，其尺度集合、DLinear专家、数据处理和训练过程均保持一致。"
)

# 1.5 Training objective and complexity
repl(
    "模型以所有样本、预测时刻和OD变量上的均方误差为目标",
    "模型训练以均方误差作为优化目标。误差在训练样本、未来H个预测时刻以及全部C个OD变量上共同计算，因此每次参数更新同时考虑不同预测步和不同OD维度的偏差。对应训练目标为"
)
repl(
    "参数训练使用Adam优化器",
    "参数训练使用Adam优化器，并以验证集MSE选择最终模型。单尺度DLinear包含4656个可训练参数；扩展为3个尺度专家后，固定等权多尺度模型包含8208个参数；加入样本级路由网络后，本文方法共有8339个参数。由8208增加到8339的131个参数即来自路由模块，这部分相对于多尺度专家主体所占比例较小。因而，从固定等权多尺度模型到本文方法的变化主要是融合方式由常数权重变为样本相关权重，而不是通过大幅增加预测主干规模获得额外容量。"
)

# Add end-of-method synthesis before Section 2
sec2 = find("2 实验与结果分析")
p_method_summary = sec2.insert_paragraph_before(
    "综上，本文方法先利用平均池化把同一输入窗口转换为3个时间分辨率，再由独立DLinear专家分别形成候选预测；随后，路由网络根据原始窗口的4个统计量计算样本级尺度权重，完成预测融合。多尺度序列解决“从哪些时间分辨率观察历史流量”的问题，DLinear专家负责“各尺度分别如何预测”，路由网络则处理“当前样本应如何组合这些尺度”。三个模块的功能相互区分，后续实验也据此设置单尺度基线、固定等权多尺度模型和本文方法进行比较。"
)
p_method_summary.style = find("参数训练使用Adam优化器").style

# Method-section growth audit
paras_m = [p.text.strip() for p in doc.paragraphs]
i_m = next(i for i,t in enumerate(paras_m) if t.startswith("1 自适应多尺度网络流量预测方法"))
i_e = next(i for i,t in enumerate(paras_m) if t.startswith("2 实验与结果分析"))
method_chars = sum(len(t) for t in paras_m[i_m:i_e] if t and not t.startswith("图"))
print("method_chars_after", method_chars)


# -------------------------
# Step 4: expand Section 2 experiments and result analysis
# -------------------------

# Add an experiment-design overview before Section 2.1.
h21 = find("2.1 数据集与实验设置")
p_exp_overview = h21.insert_paragraph_before(
    "实验部分围绕三个问题展开。首先，通过DLinear和LightTS两个外部基线，观察本文方法在统一数据划分和预测任务下的整体误差水平；其次，将固定等权多尺度模型与本文方法进行比较，在保持尺度集合和DLinear专家一致的条件下，考察样本级尺度权重带来的变化；最后，结合多个随机种子的重复实验和路由权重分布，观察这种变化是否只出现在个别初始化条件下，以及模型在测试阶段实际如何分配三个尺度。"
)
p_exp_overview.style = find("综上，本文方法先利用平均池化").style

# 2.1 Datasets and experimental settings
repl(
    "实验数据来自CESNET TS-Zoo[7]",
    "实验数据来自CESNET TS-Zoo[7]，选取Abilene[8]和GÉANT[9]两个1 h聚合的骨干网流量矩阵。Abilene共有4656个时间点，保留144维有效OD流量；GÉANT共有2849个时间点，去除恒定通道后保留524维有效OD流量。两个数据集在序列长度和变量规模上存在明显差异：Abilene时间点更多，而GÉANT包含更多OD变量。因而，在相同预测流程下同时使用这两个数据集，可以观察模型在不同变量规模和样本数量条件下的表现。两者均按时间顺序以6∶2∶2划分为训练集、验证集和测试集，输入长度L=96，预测长度H=24，预处理方式与第1.1节保持一致。表1列出了具体的数据规模和窗口数量。"
)
repl(
    "所有对比模型使用相同的数据划分",
    "所有对比模型采用相同的数据划分、输入长度、预测长度和评价指标，批量大小统一设为16。这样设置的目的不是比较不同模型各自的最佳超参数，而是在统一预测任务下控制数据条件的一致性。DLinear、固定等权多尺度模型和本文方法最多训练30轮，LightTS最多训练50轮，训练过程中均根据验证集MSE选择用于测试的模型参数，而不是直接使用最后一轮结果。验证集在这里承担模型选择作用，测试集只用于最终性能统计。"
)

h22 = find("2.2 对比模型与评价指标")
p_seed = h22.insert_paragraph_before(
    "随机种子的设置分为两组。外部基线比较使用42—44共3个共同随机种子，使DLinear、LightTS和本文方法能够在相同初始化编号下进行重复比较；核心消融进一步扩展到42—49共8个随机种子，只比较DLinear、固定等权多尺度模型和本文方法。前一组用于给出与外部基线的统一比较，后一组则增加重复次数，以便更充分地观察多尺度结构和样本级加权在不同初始化下的结果变化。"
)
p_seed.style = find("所有对比模型采用相同的数据划分").style

# 2.2 Baselines and metrics
repl(
    "实验中的对比对象包括3类",
    "实验中的对比对象包括3类：单尺度DLinear、LightTS和固定等权多尺度模型。三类模型承担的比较作用并不相同。DLinear与本文各尺度专家采用相同的基础预测结构，可作为单尺度基线，用于观察从单一时间分辨率扩展到多尺度后的变化；LightTS是独立的轻量多变量时间序列预测模型，用于提供外部结构基线；固定等权多尺度模型与本文方法使用完全相同的尺度集合{1,2,4}和DLinear专家，但取消样本级路由，3个尺度始终以1/3权重融合。因此，从DLinear到固定等权模型主要增加多尺度信息，而从固定等权模型到本文方法只改变尺度融合方式。"
)
repl(
    "预测误差采用均方误差（MSE）",
    "预测性能采用均方误差（MSE）、平均绝对误差（MAE）和均方根误差（RMSE）评价。MSE按式（14）计算，MAE和RMSE分别定义为"
)
repl(
    "MSE、MAE和RMSE均基于标准化后的数据计算",
    "MSE、MAE和RMSE均在标准化空间中计算，数值越小表示预测结果与真实值之间的偏差越小。三项指标的侧重点有所不同：MSE对较大的预测误差更敏感，MAE直接统计绝对误差的平均水平，RMSE则在均方误差基础上开方，便于从另一种尺度观察整体偏差。正文以MSE和MAE作为主要比较指标，RMSE用于补充评价。表2统计随机种子42—44的均值±标准差，表3统计随机种子42—49的均值±标准差，从而同时保留平均水平和不同重复实验之间的波动信息。"
)

# 2.3 External baseline comparison
repl(
    "表2中，本文方法在Abilene上的MSE为0.186",
    "表2给出了3个共同随机种子下的外部基线结果。本文方法在Abilene上的MSE为0.186，在GÉANT上为0.434。相对于DLinear，两项MSE分别降低4.06%和4.43%；相对于LightTS，分别降低29.89%和46.83%。MAE的变化方向与MSE一致。由比较幅度可以看到，本文方法相对DLinear的改进较为接近，而相对LightTS的差距更大，这说明在当前两个数据集和既定参数设置下，DLinear本身已经是更接近本文方法的强基线。本文的改进是在这一基础上进一步引入多尺度输入和样本级融合获得的。"
)
repl(
    "图2给出了随机种子42—44的单次结果",
    "图2进一步给出了随机种子42—44的单次实验结果，用于观察表2中的平均值由哪些重复实验构成。Abilene上，本文方法在3次实验中的MSE和MAE均低于DLinear和LightTS。GÉANT上，相对LightTS的3次结果同样保持较低误差；与DLinear相比则存在个别随机种子的波动，但3次结果取平均后仍低于DLinear。由此可见，表2中的平均改善并非完全来自某一个随机种子的异常结果，尤其在Abilene上，3次重复实验的变化方向较一致。"
)
h24 = find("2.4 八随机种子核心消融与稳定性")
p_baseline_summary = h24.insert_paragraph_before(
    "两个数据集上的相对降幅并不完全相同。GÉANT的OD变量数明显多于Abilene，而本文方法相对LightTS在GÉANT上的MSE降幅也更大；不过，这一现象只能说明在当前数据集和实验设置下两种模型之间的差距不同，不能据此把误差变化简单归因于变量规模。更直接的判断仍需要依赖后续固定等权消融，因为该模型与本文方法共享相同的多尺度专家结构。"
)
p_baseline_summary.style = find("图2进一步给出了随机种子42—44的单次实验结果").style

# 2.4 Ablation and stability
repl(
    "表3使用随机种子42—49重新统计核心模型",
    "为进一步区分多尺度结构和自适应权重各自带来的影响，表3把核心模型扩展到随机种子42—49共8次重复实验。这里可以按两步理解结果。第一步比较DLinear与本文方法：Abilene和GÉANT上的平均MSE分别降低2.77%和2.37%，说明完整模型相对单尺度DLinear保持较低的平均误差。第二步比较固定等权多尺度模型与本文方法：两者拥有相同的尺度集合和3个DLinear专家，区别只在融合权重是否随样本变化。在这一更严格的结构对照下，本文方法的平均MSE仍分别降低1.67%和4.68%。因此，表3把性能变化分成了“引入多尺度信息”和“进一步改变尺度融合方式”两个层次。"
)
repl(
    "图3采用同一随机种子进行配对比较",
    "图3按照相同随机种子对固定等权模型和本文方法进行配对比较，以避免把不同随机初始化之间的自然波动混入模型差异。Abilene的8个随机种子中，本文方法有6次取得更低MSE；GÉANT中有7次取得更低MSE。两个数据集的平均ΔMSE均为正，与表3中的均值结果一致。换言之，自适应权重带来的平均改善并不只由少数单次实验推动，而是在多数共同随机种子下都能观察到同方向变化。"
)
h25 = find("2.5 路由权重分析")
p_ablation_summary = h25.insert_paragraph_before(
    "从DLinear、固定等权多尺度模型到本文方法，模型结构逐步增加了两个因素：先加入多个时间尺度，再把固定权重替换为样本级权重。表3与图3共同说明，在已经具备多尺度专家的前提下，尺度融合方式仍会影响预测结果。这也是后续分析路由权重分布的原因：如果路由器始终输出接近1/3的权重，那么自适应模块与固定等权模型实际上不会形成明显区别。"
)
p_ablation_summary.style = find("图3按照相同随机种子").style

# 2.5 Router-weight analysis
repl(
    "图4统计随机种子42—49下全部测试窗口的尺度权重",
    "图4统计随机种子42—49下全部测试窗口的尺度权重，用于观察路由网络在测试阶段是否真正形成了不同于固定1/3的尺度分配。固定等权模型在所有样本上都使用同一组权重，而本文方法的权重由每个输入窗口的统计特征计算，因此测试集中的权重分布能够直接反映路由器对3个尺度的总体偏好及其变化范围。"
)
repl(
    "Abilene中α1、α2和α4的平均权重依次为0.257",
    "Abilene中α1、α2和α4的平均权重依次为0.257、0.319和0.424；GÉANT中依次为0.283、0.318和0.399。两个数据集都表现为尺度4的平均权重最高，尺度1最低，且三个尺度的平均值明显不同于固定等权的1/3。对于本文设置的24步预测任务，路由器整体上给予较粗尺度更高的权重，说明经过更强时间平滑后的趋势信息在最终融合中占有较大比例；与此同时，尺度1和尺度2仍保留非零权重，表明最终预测并不是只依赖单一粗尺度，而是继续组合不同时间分辨率的信息。"
)
repl(
    "表2和图2用于比较本文方法与外部基线",
    "综合表2、表3和图2—图4可以形成一条较清晰的实验链。表2和图2回答本文方法与外部轻量基线相比处于什么误差水平；表3和图3进一步控制专家结构，考察固定等权与样本级权重之间的差异；图4则从模型内部的尺度分配结果说明，路由器在测试样本上确实形成了非等权的融合方式。三部分结果分别对应外部性能比较、核心结构消融和内部权重行为，使实验分析与第1节提出的多尺度专家和样本级路由设计相互对应。"
)

# Experiment-section growth audit
paras_e = [p.text.strip() for p in doc.paragraphs]
i_e2 = next(i for i,t in enumerate(paras_e) if t.startswith("2 实验与结果分析"))
i_c2 = next(i for i,t in enumerate(paras_e) if t.startswith("3 结论"))
experiment_chars = sum(len(t) for t in paras_e[i_e2:i_c2] if t and not t.startswith("图") and not t.startswith("表"))
print("experiment_chars_after", experiment_chars)


# -------------------------
# Step 5: add two verified, publication-style figures
# -------------------------

ASSET_DIR = ROOT / "word_output" / "v22_assets"
ASSET_DIR.mkdir(parents=True, exist_ok=True)

TRUTH_COLOR = "#252525"
DLINEAR_COLOR = "#3569A8"
PROPOSED_COLOR = "#C9493E"
TEXT_COLOR = "#2A2A2A"
MUTED_COLOR = "#686868"
GRID_COLOR = "#D9D9D9"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Noto Serif CJK SC", "Noto Serif CJK JP", "DejaVu Serif"],
    "axes.unicode_minus": False,
    "font.size": 9.6,
    "axes.labelsize": 9.8,
    "axes.titlesize": 10.7,
    "xtick.labelsize": 8.8,
    "ytick.labelsize": 8.8,
    "legend.fontsize": 8.9,
    "axes.linewidth": 0.7,
    "xtick.direction": "out",
    "ytick.direction": "out",
})

def _clean_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#555555")
    ax.spines["bottom"].set_color("#555555")
    ax.tick_params(width=0.65, length=2.8, color="#555555", pad=2.5)
    ax.grid(axis="y", color=GRID_COLOR, lw=0.55, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)

def generate_multiscale_example():
    """Generate Figure 2 from the actual Abilene training split and verify pooling."""
    data_path = ROOT / "abilene_forecasting" / "data" / "processed" / "abilene_1hour.npz"
    with np.load(data_path, allow_pickle=False) as arrays:
        train = np.asarray(arrays["train"], dtype=float)
        active_indices = arrays["active_indices"].copy() if "active_indices" in arrays else None

    L, H = 96, 24
    channel_sd = train.std(axis=0)
    eligible = np.flatnonzero(channel_sd > 1e-8)
    if eligible.size == 0:
        raise RuntimeError("Abilene training split has no nonconstant OD channel")
    median_sd = float(np.median(channel_sd[eligible]))
    channel_idx = int(eligible[np.argmin(np.abs(channel_sd[eligible] - median_sd))])

    max_start = len(train) - L - H + 1
    if max_start <= 0:
        raise RuntimeError("Training split is shorter than the configured sliding window")
    series = train[:, channel_idx]
    window_sds = np.array([series[i:i+L].std() for i in range(max_start)])
    start = int(np.argmin(np.abs(window_sds - np.median(window_sds))))

    scale1 = series[start:start+L].copy()
    scale2 = scale1.reshape(-1, 2).mean(axis=1)
    scale4 = scale1.reshape(-1, 4).mean(axis=1)

    assert len(scale1) == 96 and len(scale2) == 48 and len(scale4) == 24
    assert np.allclose(scale2, scale1.reshape(-1, 2).mean(axis=1), atol=1e-10)
    assert np.allclose(scale4, scale1.reshape(-1, 4).mean(axis=1), atol=1e-10)

    csv_path = ASSET_DIR / "fig2_multiscale_example_source.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["scale", "scale_index", "normalized_flow"])
        for s, values in [(1, scale1), (2, scale2), (4, scale4)]:
            for idx, value in enumerate(values, start=1):
                writer.writerow([s, idx, f"{float(value):.10g}"])

    metadata = {
        "dataset": "abilene",
        "split": "train",
        "input_len": L,
        "pred_len": H,
        "window_start_zero_based": start,
        "active_channel_index_zero_based": channel_idx,
        "original_channel_index_zero_based": (
            int(active_indices[channel_idx]) if active_indices is not None else channel_idx
        ),
        "selection_rule": (
            "先在Abilene训练集的非恒定OD变量中选择全训练段标准差最接近通道中位数的变量；"
            "再在可形成L=96、H=24样本的历史窗口中，选择96步标准差最接近全部候选窗口中位数的窗口。"
            "该选择仅用于展示多尺度平均池化，不依据任何模型预测误差。"
        ),
        "pooling_check": {
            "scale2_max_abs_error": float(np.max(np.abs(scale2 - scale1.reshape(-1, 2).mean(axis=1)))),
            "scale4_max_abs_error": float(np.max(np.abs(scale4 - scale1.reshape(-1, 4).mean(axis=1)))),
        },
        "std_by_scale": {
            "scale1": float(np.std(scale1)),
            "scale2": float(np.std(scale2)),
            "scale4": float(np.std(scale4)),
        },
        "scale1_to_scale4_std_reduction_pct": float(
            (1.0 - np.std(scale4) / np.std(scale1)) * 100.0
        ),
    }
    (ASSET_DIR / "fig2_multiscale_example_selection.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Publication layout: three wide data panels + an independent pooling schematic.
    # The actual source values and the pooling audit above remain unchanged.
    from matplotlib.patches import FancyBboxPatch

    fig = plt.figure(figsize=(7.45, 5.05))
    gs = fig.add_gridspec(
        3, 2, width_ratios=[2.45, 1.10], hspace=0.44, wspace=0.25,
        left=0.105, right=0.985, bottom=0.105, top=0.965
    )
    axes = [fig.add_subplot(gs[i, 0]) for i in range(3)]
    y_min = min(np.min(scale1), np.min(scale2), np.min(scale4))
    y_max = max(np.max(scale1), np.max(scale2), np.max(scale4))
    pad = (y_max - y_min) * 0.08

    for i, (ax, values, scale, n) in enumerate(
        zip(axes, [scale1, scale2, scale4], [1, 2, 4], [96, 48, 24])
    ):
        x = np.arange(1, n + 1)
        ax.plot(x, values, lw=1.45, color=DLINEAR_COLOR, zorder=3)
        if scale > 1:
            ax.scatter(
                x, values, s=7.0, color=DLINEAR_COLOR,
                edgecolors="white", linewidths=0.25, zorder=4
            )
        ax.set_xlim(1, n)
        ax.set_ylim(y_min - pad, y_max + pad)
        ax.set_xticks({
            96: [1, 24, 48, 72, 96],
            48: [1, 12, 24, 36, 48],
            24: [1, 6, 12, 18, 24],
        }[n])
        if i < 2:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("时间步")
        ax.text(
            0.012, 0.91, f"({chr(97+i)})  尺度 {scale}  ·  {n} 步",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=9.9, fontweight="semibold", color=TEXT_COLOR
        )
        ax.text(
            0.988, 0.91, rf"$\sigma$={np.std(values):.3f}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=8.7, color=MUTED_COLOR
        )
        _clean_axes(ax)
    fig.supylabel("标准化流量", x=0.018, fontsize=9.8)

    axd = fig.add_subplot(gs[:, 1])
    axd.set_axis_off()
    axd.set_xlim(0, 1)
    axd.set_ylim(0, 1)
    axd.text(
        0.02, 0.975, "(d)  平均池化与尺度变化",
        ha="left", va="top", fontsize=9.9,
        fontweight="semibold", color=TEXT_COLOR
    )
    axd.text(
        0.02, 0.925,
        "同一 96 步历史窗口\n经非重叠平均形成三种时间分辨率",
        ha="left", va="top", fontsize=8.05,
        color=MUTED_COLOR, linespacing=1.25
    )
    levels = [
        (0.78, "尺度 1", "96 步", "保留细粒度波动", float(np.std(scale1))),
        (0.49, "尺度 2", "48 步", "相邻 2 点平均", float(np.std(scale2))),
        (0.20, "尺度 4", "24 步", "相邻 4 点平均", float(np.std(scale4))),
    ]
    for y, label, note, desc, sd in levels:
        box = FancyBboxPatch(
            (0.06, y - 0.073), 0.88, 0.142,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            ec=DLINEAR_COLOR, fc="#F7FAFD", lw=0.9
        )
        axd.add_patch(box)
        axd.text(
            0.11, y + 0.022, label, ha="left", va="center",
            fontsize=9.7, fontweight="semibold", color=DLINEAR_COLOR
        )
        axd.text(
            0.89, y + 0.022, note, ha="right", va="center",
            fontsize=9.0, color=TEXT_COLOR
        )
        axd.text(
            0.11, y - 0.031, desc, ha="left", va="center",
            fontsize=8.15, color=MUTED_COLOR
        )
        axd.text(
            0.89, y - 0.031, rf"$\sigma$={sd:.3f}",
            ha="right", va="center", fontsize=8.15, color=MUTED_COLOR
        )
    for y_start, y_end, label in [
        (0.690, 0.575, "2 点平均"),
        (0.400, 0.285, "再按 2 点平均"),
    ]:
        axd.annotate(
            "", xy=(0.43, y_end), xytext=(0.43, y_start),
            arrowprops=dict(
                arrowstyle="-|>", lw=0.9, color="#555555",
                shrinkA=0, shrinkB=0
            )
        )
        axd.text(
            0.51, (y_start + y_end) / 2, label,
            ha="left", va="center", fontsize=8.1, color=MUTED_COLOR
        )
    sd_drop = (1.0 - np.std(scale4) / np.std(scale1)) * 100.0
    axd.text(
        0.50, 0.045,
        f"示例窗口中：尺度 1 → 4，σ下降 {sd_drop:.1f}%\n"
        "局部波动减弱，较慢变化趋势更突出",
        ha="center", va="center", fontsize=8.0,
        color=TEXT_COLOR, linespacing=1.35
    )

    out = ASSET_DIR / "fig2_multiscale_compact.png"
    fig.savefig(out, dpi=420, facecolor="white")
    plt.close(fig)
    return out, metadata


def load_representative_forecast_source():
    source_csv = ROOT / "abilene_forecasting" / "paper_figures" / "source_data_v2" / "fig5_representative_forecasts.csv"
    meta_json = ROOT / "abilene_forecasting" / "paper_figures" / "source_data_v2" / "fig5_representative_forecasts_selection.json"
    rows = []
    with source_csv.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    metadata = json.loads(meta_json.read_text(encoding="utf-8"))
    return rows, metadata

def generate_representative_forecast_figure():
    """Generate Figure 4 directly from the committed source-data CSV and verify case MAE."""
    rows, metadata = load_representative_forecast_source()
    grouped = {}
    for row in rows:
        grouped.setdefault(row["dataset"], []).append(row)

    # Derive the overall three-seed MSE reduction from the committed baseline source data.
    baseline_csv = (
        ROOT / "abilene_forecasting" / "paper_figures" /
        "source_data_v15" / "fig2_external_baseline_paired_seed42_44.csv"
    )
    baseline_values = {}
    with baseline_csv.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["metric"] != "MSE" or row["model"] not in ("dlinear", "dlinear_scale"):
                continue
            baseline_values.setdefault(row["dataset"], {}).setdefault(row["model"], []).append(
                float(row["value"])
            )
    overall_mse_reduction = {}
    for dataset in ("abilene", "geant"):
        d_mean = float(np.mean(baseline_values[dataset]["dlinear"]))
        p_mean = float(np.mean(baseline_values[dataset]["dlinear_scale"]))
        overall_mse_reduction[dataset] = (d_mean - p_mean) / d_mean * 100.0
    assert abs(overall_mse_reduction["abilene"] - 4.06) < 0.02
    assert abs(overall_mse_reduction["geant"] - 4.43) < 0.02

    audits = {}
    for dataset in ("abilene", "geant"):
        frame = sorted(grouped[dataset], key=lambda r: int(r["forecast_hour"]))
        hours = np.array([int(r["forecast_hour"]) for r in frame])
        truth = np.array([float(r["truth"]) for r in frame])
        dlinear = np.array([float(r["dlinear_seed42"]) for r in frame])
        proposed = np.array([float(r["adaptive_multiscale_seed42"]) for r in frame])
        assert np.array_equal(hours, np.arange(1, 25)), f"{dataset}: forecast hours are not 1..24"

        mae_d = float(np.mean(np.abs(dlinear-truth)))
        mae_p = float(np.mean(np.abs(proposed-truth)))
        meta = next(m for m in metadata if m["dataset"] == dataset)
        assert abs(mae_d - float(meta["dlinear_case_mae_standardized"])) < 1e-6
        assert abs(mae_p - float(meta["adaptive_case_mae_standardized"])) < 1e-6
        audits[dataset] = {
            "n_forecast_steps": 24,
            "dlinear_case_mae_standardized": mae_d,
            "adaptive_case_mae_standardized": mae_p,
            "dlinear_max_abs_error_standardized": float(np.max(np.abs(dlinear-truth))),
            "adaptive_max_abs_error_standardized": float(np.max(np.abs(proposed-truth))),
            "overall_3seed_mse_reduction_vs_dlinear_pct": float(
                overall_mse_reduction[dataset]
            ),
        }

    (ASSET_DIR / "fig4_representative_forecast_audit.json").write_text(
        json.dumps(audits, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Publication layout: prediction trajectories above, per-step error advantage below.
    # Representative-window data remain unchanged; column titles report the independent
    # three-seed aggregate MSE reduction derived from the baseline source CSV.
    fig, axes = plt.subplots(
        2, 2, figsize=(7.55, 5.18), sharex="col",
        gridspec_kw={"height_ratios": [1.60, 1.0]}
    )
    fig.subplots_adjust(
        left=0.095, right=0.985, bottom=0.12, top=0.845,
        wspace=0.18, hspace=0.30
    )

    all_delta = []
    for dataset in ("abilene", "geant"):
        frame = sorted(grouped[dataset], key=lambda r: int(r["forecast_hour"]))
        truth = np.array([float(r["truth"]) for r in frame])
        dlinear = np.array([float(r["dlinear_seed42"]) for r in frame])
        proposed = np.array([float(r["adaptive_multiscale_seed42"]) for r in frame])
        all_delta.extend(np.abs(dlinear - truth) - np.abs(proposed - truth))
    delta_lim = max(abs(np.min(all_delta)), abs(np.max(all_delta))) * 1.10

    for col, dataset in enumerate(("abilene", "geant")):
        frame = sorted(grouped[dataset], key=lambda r: int(r["forecast_hour"]))
        x = np.array([int(r["forecast_hour"]) for r in frame])
        truth = np.array([float(r["truth"]) for r in frame])
        dlinear = np.array([float(r["dlinear_seed42"]) for r in frame])
        proposed = np.array([float(r["adaptive_multiscale_seed42"]) for r in frame])
        title = "Abilene" if dataset == "abilene" else "GÉANT"

        mae_d = audits[dataset]["dlinear_case_mae_standardized"]
        mae_p = audits[dataset]["adaptive_case_mae_standardized"]
        case_gain = (mae_d - mae_p) / mae_d * 100.0

        ax = axes[0, col]
        ax.plot(x, truth, color=TRUTH_COLOR, lw=1.35, label="真实值", zorder=4)
        ax.plot(
            x, dlinear, color=DLINEAR_COLOR, lw=1.25,
            ls=(0, (4, 2)), label="DLinear", zorder=2
        )
        ax.plot(
            x, proposed, color=PROPOSED_COLOR, lw=1.55,
            label="本文方法", zorder=3
        )
        ax.scatter(
            x[::3], proposed[::3], s=12, color=PROPOSED_COLOR,
            edgecolors="white", linewidths=0.35, zorder=5
        )
        ax.set_title(
            f"{title}  ·  总体3种子MSE较DLinear ↓ "
            f"{overall_mse_reduction[dataset]:.2f}%",
            pad=9, fontweight="semibold", fontsize=10.2
        )
        if col == 0:
            ax.set_ylabel("标准化流量")
        else:
            ax.tick_params(labelleft=False)

        if case_gain > 0:
            badge = (
                f"代表窗口 MAE  {mae_d:.3f} → {mae_p:.3f}  "
                f"(↓{case_gain:.1f}%)"
            )
        else:
            badge = (
                f"代表窗口 MAE  {mae_d:.3f} ↔ {mae_p:.3f}  "
                "(近似持平)"
            )
        ax.text(
            0.02, 0.04, badge, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.1, color=TEXT_COLOR,
            bbox=dict(
                boxstyle="round,pad=0.20", fc="white",
                ec="#CFCFCF", lw=0.55, alpha=0.92
            )
        )
        ax.text(
            0.015, 0.965, f"({chr(97+col)})",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=10.0, fontweight="semibold"
        )
        _clean_axes(ax)

        e_d = np.abs(dlinear - truth)
        e_p = np.abs(proposed - truth)
        delta = e_d - e_p
        ax2 = axes[1, col]
        ax2.axhline(0, color="#6E6E6E", lw=0.75, zorder=1)
        ax2.plot(x, delta, color=PROPOSED_COLOR, lw=1.35, zorder=3)
        ax2.fill_between(
            x, 0, delta, where=delta >= 0, interpolate=True,
            color=PROPOSED_COLOR, alpha=0.14, zorder=2
        )
        ax2.fill_between(
            x, 0, delta, where=delta < 0, interpolate=True,
            color=DLINEAR_COLOR, alpha=0.10, zorder=2
        )
        ax2.set_xlim(1, 24)
        ax2.set_ylim(-delta_lim, delta_lim)
        ax2.set_xticks([1, 4, 8, 12, 16, 20, 24])
        ax2.set_xlabel("预测步长")
        if col == 0:
            ax2.set_ylabel("逐步误差差值 ΔAE")
        else:
            ax2.tick_params(labelleft=False)
        ax2.text(
            0.015, 0.95, f"({chr(99+col)})",
            transform=ax2.transAxes, ha="left", va="top",
            fontsize=10.0, fontweight="semibold"
        )
        _clean_axes(ax2)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.975),
        ncol=3, frameon=False, handlelength=2.6, columnspacing=2.0
    )
    fig.text(
        0.5, 0.025,
        "ΔAE = |DLinear−真实值| − |本文方法−真实值|；"
        "正值表示本文方法在该预测步的绝对误差更小。",
        ha="center", va="bottom", fontsize=8.05, color=MUTED_COLOR
    )

    out = ASSET_DIR / "fig4_representative_prediction_error.png"
    fig.savefig(out, dpi=420, facecolor="white")
    plt.close(fig)
    return out, audits


def insert_picture_before(anchor, image_path, caption_text, width_inches=6.25):
    pic_p = anchor.insert_paragraph_before()
    pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic_p.add_run().add_picture(str(image_path), width=Inches(width_inches))
    cap_p = anchor.insert_paragraph_before(caption_text)
    cap_p.style = caption1.style
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return pic_p, cap_p

# Figure 2: verified multiscale construction from real Abilene training data.
fig2_path, fig2_meta = generate_multiscale_example()
h13_for_fig = find("1.3 DLinear尺度专家")
p_fig2_intro = h13_for_fig.insert_paragraph_before(
    "为直观说明式（5）的尺度变换，图2选取Abilene训练集中一个非恒定OD变量的96步历史窗口。"
    "该变量和窗口均按波动程度的中位水平确定，选择过程不使用模型预测误差。"
    "图2(a)～(c)分别给出尺度1、2和4下的实际序列，图2(d)给出非重叠平均池化的对应关系。"
)
p_fig2_intro.style = find("尺度集合采用1、2和4").style
insert_picture_before(
    h13_for_fig,
    fig2_path,
    "图2 Abilene单个OD变量的多尺度序列构造与平均池化示意",
    width_inches=6.15,
)
p_fig2_analysis = h13_for_fig.insert_paragraph_before(
    "尺度1保留原始96步输入；尺度2对相邻2点取平均后得到48步序列；尺度4对相邻4点取平均后得到24步序列。"
    "核对源数据可知，尺度2和尺度4分别与尺度1的2点、4点非重叠平均结果一致。"
    f"在该示例窗口中，3个尺度的标准差依次为"
    f"{fig2_meta['std_by_scale']['scale1']:.3f}、"
    f"{fig2_meta['std_by_scale']['scale2']:.3f}和"
    f"{fig2_meta['std_by_scale']['scale4']:.3f}，"
    f"尺度1到尺度4下降约{fig2_meta['scale1_to_scale4_std_reduction_pct']:.1f}%。"
    "这说明随着尺度增大，局部波动逐渐被平滑，而较慢的变化趋势仍被保留，从而为后续3个DLinear专家提供侧重点不同的时间分辨率输入。"
)
p_fig2_analysis.style = p_fig2_intro.style

# Renumber existing figures after inserting Figure 2.
repl(
    "图2 Abilene与GÉANT上三随机种子外部基线配对结果",
    "图3 Abilene与GÉANT上三随机种子外部基线配对结果"
)
repl(
    "图3 固定等权与自适应权重的八随机种子配对MSE及配对差值分布",
    "图5 固定等权与自适应权重的八随机种子配对MSE及配对差值分布"
)
repl(
    "图4 八随机种子下样本级自适应路由权重分布",
    "图6 八随机种子下样本级自适应路由权重分布"
)

# Update in-text figure references to their new numbers.
repl(
    "图2进一步给出了随机种子42—44的单次实验结果",
    "图3进一步给出了随机种子42—44的单次实验结果，用于观察表2中的平均值由哪些重复实验构成。Abilene上，本文方法在3次实验中的MSE和MAE均低于DLinear和LightTS。GÉANT上，相对LightTS的3次结果同样保持较低误差；与DLinear相比则存在个别随机种子的波动，但3次结果取平均后仍低于DLinear。由此可见，表2中的平均改善并非完全来自某一个随机种子的异常结果，尤其在Abilene上，3次重复实验的变化方向较一致。"
)
repl(
    "图3按照相同随机种子对固定等权模型和本文方法进行配对比较",
    "图5按照相同随机种子对固定等权模型和本文方法进行配对比较，以避免把不同随机初始化之间的自然波动混入模型差异。Abilene的8个随机种子中，本文方法有6次取得更低MSE；GÉANT中有7次取得更低MSE。两个数据集的平均ΔMSE均为正，与表3中的均值结果一致。换言之，自适应权重带来的平均改善并不只由少数单次实验推动，而是在多数共同随机种子下都能观察到同方向变化。"
)
repl(
    "从DLinear、固定等权多尺度模型到本文方法",
    "从DLinear、固定等权多尺度模型到本文方法，模型结构逐步增加了两个因素：先加入多个时间尺度，再把固定权重替换为样本级权重。表3与图5共同说明，在已经具备多尺度专家的前提下，尺度融合方式仍会影响预测结果。这也是后续分析路由权重分布的原因：如果路由器始终输出接近1/3的权重，那么自适应模块与固定等权模型实际上不会形成明显区别。"
)
repl(
    "图4统计随机种子42—49下全部测试窗口的尺度权重",
    "图6统计随机种子42—49下全部测试窗口的尺度权重，用于观察路由网络在测试阶段是否真正形成了不同于固定1/3的尺度分配。固定等权模型在所有样本上都使用同一组权重，而本文方法的权重由每个输入窗口的统计特征计算，因此测试集中的权重分布能够直接反映路由器对3个尺度的总体偏好及其变化范围。"
)

# Figure 4: representative prediction curves + per-step absolute errors from committed source data.
h24_for_fig = find("2.4 八随机种子核心消融与稳定性")
p_fig4_intro = h24_for_fig.insert_paragraph_before(
    "平均指标能够反映整体误差水平，但不容易展示24步预测过程中预测轨迹与真实序列之间的局部差异。"
    "因此，图4给出随机种子42下的代表性测试窗口，并在下方绘制逐步误差差值，用于直接观察两个模型在各预测步上的误差差异。"
    "样本选择不依据本文方法相对DLinear的提升幅度，而是先选择本文方法绝对误差接近全部测试窗口中位数的窗口，"
    "再选择该窗口中真实值波动程度接近通道中位数的非恒定OD变量，以避免只展示最有利案例。"
)
p_fig4_intro.style = find("两个数据集上的相对降幅并不完全相同").style
fig4_path, fig4_audit = generate_representative_forecast_figure()
insert_picture_before(
    h24_for_fig,
    fig4_path,
    "图4 Abilene与GÉANT代表性测试窗口的24步预测及逐步误差差值",
    width_inches=6.25,
)
p_fig4_analysis = h24_for_fig.insert_paragraph_before(
    "图4(a)、(b)展示真实值、DLinear和本文方法在24个预测步上的标准化预测轨迹；"
    "图4(c)、(d)绘制逐步误差差值ΔAE=|DLinear−真实值|−|本文方法−真实值|，正值表示本文方法在该预测步的绝对误差更小。"
    f"列标题同时给出全部测试样本、随机种子42—44上的总体MSE结果："
    f"本文方法相对DLinear在Abilene和GÉANT上分别降低"
    f"{fig4_audit['abilene']['overall_3seed_mse_reduction_vs_dlinear_pct']:.2f}%和"
    f"{fig4_audit['geant']['overall_3seed_mse_reduction_vs_dlinear_pct']:.2f}%。"
    f"在图示代表性窗口中，Abilene上DLinear与本文方法的MAE分别为"
    f"{fig4_audit['abilene']['dlinear_case_mae_standardized']:.4f}和"
    f"{fig4_audit['abilene']['adaptive_case_mae_standardized']:.4f}；"
    f"GÉANT上分别为{fig4_audit['geant']['dlinear_case_mae_standardized']:.4f}和"
    f"{fig4_audit['geant']['adaptive_case_mae_standardized']:.4f}。"
    "因此，Abilene示例中本文方法的局部优势较明显，而GÉANT代表窗口基本持平；总体性能判断仍以全部测试样本和多个随机种子的统计结果为准。"
)
p_fig4_analysis.style = p_fig4_intro.style

repl(
    "综合表2、表3和图2—图4",
    "综合表2、表3和图3—图6可以形成一条较清晰的实验链。表2和图3用于比较本文方法与外部轻量基线的总体误差水平；"
    "图4补充展示代表性测试窗口中的24步预测轨迹和逐步误差差值；表3和图5进一步控制专家结构，考察固定等权与样本级权重之间的差异；"
    "图6则从模型内部的尺度分配结果说明路由器在测试样本上形成了非等权的融合方式。各部分分别对应总体性能、局部预测形态、核心结构消融和内部权重行为，"
    "与第1节提出的多尺度专家和样本级路由设计相互对应。"
)

assert fig2_path.exists()
assert fig4_path.exists()



# Guardrails
full = "\n".join(p.text for p in doc.paragraphs)
for token in [
    "源—目的节点对", "OD", "DLinear", "Softmax", "Abilene", "GÉANT",
    "LightTS", "CycleLLH", "TimeMixer",
    "Lohrasbinasab等[1]", "Qin等[2]", "Zhou等[3]", "韦烜等[10]", "唐文杰等[11]",
    "L=96", "H=24", "6∶2∶2", "4656", "8208", "8339", "131",
    "4.06%", "4.43%", "29.89%", "46.83%", "2.77%", "2.37%", "1.67%", "4.68%",
    "0.186", "0.434", "0.257", "0.319", "0.424", "0.283", "0.318", "0.399"
]:
    assert token in full, token

assert len(doc.tables) == 3
assert len(doc.inline_shapes) == 6
for expected_caption in [
    "图1 自适应多尺度网络流量预测方法框架",
    "图2 Abilene单个OD变量的多尺度序列构造与平均池化示意",
    "图3 Abilene与GÉANT上三随机种子外部基线配对结果",
    "图4 Abilene与GÉANT代表性测试窗口的24步预测及逐步绝对误差",
    "图5 固定等权与自适应权重的八随机种子配对MSE及配对差值分布",
    "图6 八随机种子下样本级自适应路由权重分布",
]:
    assert expected_caption in full, expected_caption

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

# Rebuild after methodology expansion.

# Rebuild after adding evidence-based figures.
