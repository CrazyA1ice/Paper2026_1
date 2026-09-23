from pathlib import Path
import re
from collections import Counter
from copy import deepcopy

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "2026.09.23v25.docx"
TARGET = ROOT / "word_output" / "2026.09.23v26.docx"
BEFORE_TXT = ROOT / "word_output" / "v26_audit_before.txt"
AFTER_TXT = ROOT / "word_output" / "v26_audit_after.txt"
REPORT = ROOT / "word_output" / "v26_ai_style_audit.txt"

doc = Document(SOURCE)

def find_prefix(prefix):
    found = [p for p in doc.paragraphs if p.text.strip().startswith(prefix)]
    if len(found) != 1:
        raise RuntimeError(f"Expected one paragraph beginning {prefix!r}, found {len(found)}")
    return found[0]

def set_text(p, text):
    if p.runs:
        p.runs[0].text = text
        for run in p.runs[1:]:
            run.text = ""
    else:
        p.add_run(text)

def dump_paragraphs(document, path):
    with path.open("w", encoding="utf-8") as f:
        for i, p in enumerate(document.paragraphs):
            t = p.text.replace("\n", " ").strip()
            if t:
                f.write(f"[{i:04d}] {t}\n")

def all_text(document):
    return "\n".join(p.text for p in document.paragraphs)

def table_snapshot(document):
    return [[ [cell.text for cell in row.cells] for row in tbl.rows ] for tbl in document.tables]

def heading_snapshot(document):
    out = []
    for p in document.paragraphs:
        t = p.text.strip()
        if re.match(r"^\d+(?:\.\d+)*\s", t) or t in {"参考文献"}:
            out.append(t)
    return out

def figure_caption_snapshot(document):
    return [p.text.strip() for p in document.paragraphs if p.text.strip().startswith("图") and re.match(r"^图\d+\s", p.text.strip())]

dump_paragraphs(doc, BEFORE_TXT)
before_text = all_text(doc)
before_tables = table_snapshot(doc)
before_headings = heading_snapshot(doc)
before_figcaps = figure_caption_snapshot(doc)
before_shapes = len(doc.inline_shapes)

# Targeted rewrites only: preserve technical meaning, numbers, citations, formulas and structure.
replacements = [
    (
        "摘要：骨干网络中的源—目的节点对流量随时间持续变化",
        "摘要：骨干网络中的源—目的节点对流量往往同时包含短时起伏、突发变化和较慢趋势，单一时间分辨率难以在不同流量状态下兼顾这些信息。本文据此设计样本级自适应多尺度预测方法。历史窗口经非重叠平均池化得到尺度1、2和4的序列，由3个DLinear专家分别预测；输入窗口的均值、标准差、末时刻均值和平均绝对一阶差分经轻量路由网络生成Softmax尺度权重，用于融合3个尺度的预测结果。实验采用Abilene和GÉANT两个骨干网流量数据集。3个共同随机种子下，所提方法的MSE相对DLinear分别降低4.06%和4.43%，相对LightTS分别降低29.89%和46.83%；8个随机种子的消融实验中，相对固定等权融合分别降低1.67%和4.68%。两个数据集均表明，路由模块只带来较小参数增量时，按输入样本调整尺度权重仍可降低平均预测误差。"
    ),
    (
        "随着云计算、视频业务、数据中心互联及智能网络应用不断扩展",
        "云计算、视频业务、数据中心互联及智能网络应用使骨干网络承载的数据规模持续增长，流量随时间变化的形态也更加复杂。源—目的节点对（origin-destination，OD）流量描述不同节点对之间的通信需求，其变化能够反映业务在网络内部的迁移和聚集情况。容量规划、拥塞预警、资源调度和流量工程都依赖对后续流量状态的判断；若能提前获得后一时段的OD流量估计，网络管理系统可在业务变化发生前调整资源。OD流量通常同时含有周期变化、局部波动和突发变化，不同OD变量的数值范围也存在明显差异。这类数据既要求模型描述较长时间范围内的变化趋势，也要求模型保留对短时状态变化的响应能力。"
    ),
    (
        "围绕网络流量的时间变化规律，相关研究经历了从统计模型到机器学习、深度学习方法的发展",
        "网络流量预测早期多采用统计模型，近年逐步转向机器学习和深度学习方法。Lohrasbinasab等[1]系统梳理了网络流量预测研究，指出数据驱动方法已成为处理复杂流量变化的重要路线。网络规模扩大后，只分析单一序列的时间变化难以覆盖OD变量之间的关联。Qin等[2]将图神经网络用于通信网络流量预测，把空间关联和时间依赖纳入同一模型；韦烜等[10]围绕大型IP网络流量矩阵开展分析与预测，讨论了不同OD变量之间的关联及其时间变化。周期规律也是网络流量的重要信息，唐文杰等[11]提出CycleLLH模型，将周期性信息引入预测过程。这些研究分别处理时间依赖、变量关联和周期结构，为继续分析更细粒度的时间结构提供了基础。"
    ),
    (
        "除变量关联和周期特征外，同一段网络流量在不同时间分辨率下呈现出的信息也并不完全相同",
        "时间分辨率会改变同一段网络流量的表现形式。原始分辨率保留较多细节，更容易反映短时起伏；经过时间聚合后，局部扰动减弱，较慢的变化趋势更加突出。Zhou等[3]利用深度回声状态网络开展多尺度网络流量预测，通过不同时间分辨率提取互补信息。模型复杂度也是实际预测中的一个因素。DLinear[4]采用时间序列分解和线性映射完成预测，结构较简洁；TimeMixer[5]通过多尺度混合机制处理不同分辨率序列；LightTS[6]利用采样导向的MLP结构进行快速多变量时间序列预测。现有工作由此提供了两条可结合的思路：一是利用不同时间尺度，二是控制预测模型的结构开销。对于骨干网络OD流量，本文关注如何在较小模型规模下同时利用多尺度信息。"
    ),
    (
        "基于上述考虑，本文构建一种样本级自适应多尺度网络流量预测方法",
        "本文采用样本级自适应多尺度结构处理上述问题。历史窗口按尺度1、2和4构造多分辨率序列，每个尺度由一个DLinear专家给出候选预测。路由网络不重新编码完整时序，而是读取当前输入窗口的总体水平、离散程度、最近状态和变化强度等统计量，生成Softmax尺度权重，并据此融合三个专家的结果。这样可以把尺度内预测与尺度间选择分开处理。实验在Abilene和GÉANT两个公开骨干网数据集上进行，并设置DLinear、LightTS、固定等权多尺度模型、多个随机种子重复实验和路由权重分析，用于检验预测误差、核心结构消融和尺度分配行为。"
    ),
    (
        "图1给出了自适应多尺度网络流量预测方法的整体流程",
        "图1给出模型的整体流程。方法把多尺度预测和尺度选择分成两个模块：尺度1、2和4的输入分别交给独立DLinear专家，路由网络根据当前窗口的统计特征估计3个尺度的融合权重。原始OD流量先进行对数变换和标准化，再形成3个时间分辨率的输入序列；3个专家得到候选预测后，由样本级权重完成融合。固定等权消融模型保留相同的尺度和专家，因此能够单独比较样本级权重带来的变化。"
    ),
    (
        "这一设计的出发点是，不同时间分辨率对同一流量窗口的描述侧重点不同",
        "三个时间尺度保留的信息并不相同。原始尺度包含更多局部变化，较粗尺度经过时间聚合后削弱部分短时扰动，更突出较慢的变化趋势。只使用一个尺度会舍弃其他分辨率的信息；长期采用固定比例又不能随输入窗口变化。本文保留3个尺度的独立预测，再由路由网络确定每个样本的组合比例。DLinear结构较简洁，可在控制模型规模的同时承担各尺度的预测任务，使实验重点落在多尺度输入和样本级融合本身。"
    ),
    (
        "选择DLinear作为尺度专家还有一个考虑",
        "采用DLinear作为尺度专家，主要是为了把预测主干与尺度融合的影响区分开。本文需要比较单尺度预测、固定等权多尺度和样本级自适应多尺度三种设置；若尺度专家本身过于复杂，误差变化会同时受到主干结构和融合机制影响。DLinear参数关系清晰，在保持基本预测能力的同时，更适合作为统一的尺度专家。"
    ),
    (
        "四维向量输入隐藏维数为16的两层感知器",
        "四维向量输入隐藏维数为16的两层感知器，输出3个尺度的未归一化分数。路由器只需判断尺度的相对重要性，不需要再次完成完整的OD流量预测，因此本文未引入循环网络、注意力网络等额外时序编码器。使用低维统计量和较小隐藏层，也能把路由模块的参数规模控制在较低水平。其尺度分数计算为"
    ),
    (
        "综上，本文方法先利用平均池化把同一输入窗口转换为3个时间分辨率",
        "模型的计算过程可以概括为三个环节：平均池化把同一历史窗口转换为3个时间分辨率，DLinear专家分别给出候选预测，路由网络再根据原始窗口的4个统计量确定融合权重。多尺度序列决定模型从哪些时间分辨率读取历史信息，尺度专家完成各自的预测，路由网络只负责组合结果。后续实验据此设置单尺度DLinear、固定等权多尺度模型和本文方法，用同一组专家结构区分多尺度信息与样本级加权的作用。"
    ),
    (
        "实验部分围绕三个问题展开",
        "实验按外部基线、核心消融和路由权重三个层次组织。DLinear和LightTS用于比较统一数据划分和预测任务下的误差水平；固定等权多尺度模型与本文方法共享尺度集合和DLinear专家，用来检验样本级融合方式的影响；随机种子重复实验与路由权重分布则用于观察结果波动和测试阶段的实际尺度分配。"
    ),
    (
        "实验数据来自CESNET TS-Zoo[7]",
        "实验数据取自CESNET TS-Zoo[7]，包括1 h聚合的Abilene[8]和GÉANT[9]骨干网流量矩阵。Abilene共有4656个时间点，保留144维有效OD流量；GÉANT共有2849个时间点，去除恒定通道后保留524维有效OD流量。两者在序列长度和变量规模上差异较大，能够在相同预测流程下提供不同的数据条件。两个数据集均按时间顺序以6∶2∶2划分为训练集、验证集和测试集，输入长度L=96，预测长度H=24，预处理方式与第1.1节一致。表1列出了数据规模和窗口数量。"
    ),
    (
        "所有对比模型采用相同的数据划分、输入长度、预测长度和评价指标",
        "所有对比模型使用相同的数据划分、输入长度、预测长度、评价指标和批量大小，batch size统一为16。实验不为各模型单独搜索最优超参数，而是在统一预测任务下控制数据与训练条件。DLinear、固定等权多尺度模型和本文方法最多训练30轮，LightTS最多训练50轮；训练过程中均根据验证集MSE选择测试所用模型参数，不直接采用最后一轮结果。验证集仅用于模型选择，测试集用于最终性能统计。"
    ),
    (
        "随机种子的设置分为两组",
        "外部基线比较使用随机种子42～44共3个共同随机种子，使DLinear、LightTS和本文方法在相同初始化编号下重复训练。核心消融扩展到随机种子42～49共8个随机种子，只比较DLinear、固定等权多尺度模型和本文方法。前者保证外部模型比较使用共同种子，后者通过增加重复次数观察多尺度结构和样本级加权在不同初始化下的变化。"
    ),
    (
        "MSE、MAE和RMSE均在标准化空间中计算",
        "MSE、MAE和RMSE均在标准化空间中计算，数值越小表示预测误差越低。MSE对较大误差更敏感，MAE反映绝对误差的平均水平，RMSE是MSE开方后的结果，可与误差幅值直接对照。正文以MSE和MAE作为主要比较指标，RMSE用于补充。表2统计随机种子42～44的均值±标准差，表3统计随机种子42～49的均值±标准差，同时给出平均水平和重复实验间的波动。"
    ),
    (
        "表2给出了3个共同随机种子下的总体基线结果",
        "表2列出3个共同随机种子下的总体基线结果。本文方法在Abilene上的MSE为0.186，在GÉANT上为0.434；相对DLinear分别降低4.06%和4.43%，相对LightTS分别降低29.89%和46.83%，MAE呈相同方向变化。DLinear与本文尺度专家采用同源结构，后续核心消融继续以它作为单尺度内部基线；LightTS属于独立外部结构基线，图3进一步给出逐随机种子、多指标和参数规模比较。"
    ),
    (
        "为避免与图5中DLinear和固定等权多尺度模型的八随机种子核心消融重复",
        "图3聚焦独立外部基线LightTS，并使用两种方法共同具备的随机种子42～44。按（LightTS误差−本文方法误差）/LightTS误差计算每次实验的相对降低率后，Abilene上的MSE、MAE和RMSE平均降低29.80%、17.57%和16.23%，GÉANT上分别降低46.89%、29.15%和27.18%。两个数据集的3个共同随机种子在三项指标上均为正向降低。参数量方面，本文方法为8339，LightTS在Abilene和GÉANT上分别为130162和384382，本文方法约为其6.41%和2.17%。图3因此只承担外部结构基线比较，DLinear和固定等权模型的内部比较放在表3和图5中。"
    ),
    (
        "两个数据集上的相对降幅并不完全相同",
        "两个数据集上的相对降幅存在差异。GÉANT的OD变量数高于Abilene，本文方法相对LightTS的MSE降幅也更大，但现有实验不足以把这种差异直接归因于变量规模。后续固定等权消融采用与本文方法相同的多尺度专家结构，更适合判断样本级融合本身是否带来变化。"
    ),
    (
        "为进一步区分多尺度结构和自适应权重各自带来的影响",
        "表3将核心模型扩展到随机种子42～49，共8次重复实验。与单尺度DLinear相比，本文方法在Abilene和GÉANT上的平均MSE分别降低2.77%和2.37%。固定等权多尺度模型与本文方法使用相同的尺度集合和3个DLinear专家，只采用固定等权融合；在这一对照下，本文方法的平均MSE仍分别降低1.67%和4.68%。这两组比较分别对应引入多尺度信息和改变尺度融合方式带来的结果变化。"
    ),
    (
        "图5进一步从随机种子42—49的逐次结果出发",
        "图5给出随机种子42～49下本文方法相对DLinear和固定等权多尺度模型的MSE、MAE和RMSE相对改进率。每个散点对应一次随机种子实验，半小提琴表示8次结果的分布，圆点和误差线表示逐随机种子改进率的均值及95%置信区间，0%虚线表示两种方法误差相同。相对DLinear时，Abilene的MSE、MAE和RMSE平均改进率为2.77%、8.01%和1.40%，MSE与RMSE在8次实验中均改善；GÉANT分别为2.35%、1.32%和1.22%，分布跨越0%的情况更多。相对固定等权模型时，Abilene三项指标的平均改进率为1.65%、8.92%和0.84%，GÉANT为4.54%、3.05%和2.37%。两组比较的平均改进率均为正，但GÉANT的跨随机种子波动更明显。"
    ),
    (
        "从DLinear、固定等权多尺度模型到本文方法",
        "固定等权多尺度模型与本文方法共享尺度集合和三个DLinear专家，两者的主要区别是融合权重是否随样本变化。表3给出三类核心模型的绝对误差均值和标准差，图5补充8个共同随机种子的相对改进分布，并将比较扩展到MSE、MAE和RMSE。相对固定等权模型时，两个数据集三项指标的平均改进率均为正，说明误差变化不能只由增加多尺度专家解释，融合权重的设定也会影响结果。后续继续检查路由器是否真正形成不同于1/3的尺度分配。"
    ),
    (
        "图6统计随机种子42—49下全部测试窗口的尺度权重",
        "图6汇总随机种子42～49下全部测试窗口的尺度权重。固定等权模型对所有样本使用同一组权重，本文方法则由每个输入窗口的统计特征计算权重，因此测试集上的分布可以直接显示路由器对三个尺度的总体偏好和变化范围。"
    ),
    (
        "Abilene中α1、α2和α4的平均权重依次为0.257",
        "Abilene中α1、α2和α4的平均权重依次为0.257、0.319和0.424，GÉANT中依次为0.283、0.318和0.399。两个数据集均表现为尺度4的平均权重最高、尺度1最低，且三个尺度的均值与固定等权的1/3存在差异。对于H=24的预测任务，路由器整体上更偏向经过较强时间平滑的尺度4，但尺度1和尺度2仍保持非零权重，最终预测仍由不同时间分辨率共同构成。"
    ),
    (
        "综合表2、表3以及图3、图5和图6形成互补的实验链",
        "表2、表3以及图3、图5和图6分别承担不同的比较任务。表2给出DLinear、LightTS与本文方法的总体误差统计；图3只比较独立外部基线LightTS，展示共同随机种子42～44上的多指标降低率和参数规模差异；表3和图5使用随机种子42～49比较DLinear、固定等权多尺度模型与本文方法，考察多尺度结构和样本级融合方式；图6再给出内部尺度权重分布。外部模型比较、内部消融和路由行为因此分开呈现，避免同一结论在多张图中重复表达。"
    ),
    (
        "本文围绕骨干网络OD流量的多时间尺度变化开展预测",
        "本文针对骨干网络OD流量中同时存在短时波动和较慢趋势的问题，引入尺度1、2和4的DLinear专家，并由轻量路由网络根据输入窗口统计量确定融合权重。Abilene和GÉANT实验中，本文方法相对DLinear、LightTS和固定等权多尺度模型均取得更低的平均预测误差；路由权重在三个尺度之间也呈现不同分布。路由模块仅增加131个参数，说明样本级尺度融合可以在较小参数增量下改善平均预测结果。"
    ),
]

changed = []
for prefix, new_text in replacements:
    p = find_prefix(prefix)
    old = p.text.strip()
    set_text(p, new_text)
    changed.append((old, new_text))

after_text = all_text(doc)
after_tables = table_snapshot(doc)
after_headings = heading_snapshot(doc)
after_figcaps = figure_caption_snapshot(doc)

# Strong preservation checks.
assert before_tables == after_tables, "Table contents changed"
assert before_headings == after_headings, "Heading structure changed"
assert before_figcaps == after_figcaps, "Figure captions changed"
assert before_shapes == len(doc.inline_shapes), "Inline figure count changed"

# Protect substantive scientific numbers while allowing harmless changes in repeated figure/table references.
# Decimal values, percentages, ratios and integers >=20 must remain unchanged as a multiset.
num_pat = re.compile(r"\d+(?:\.\d+)?%?|\d+∶\d+∶\d+")
def protected_numbers(text):
    out = []
    for tok in num_pat.findall(text):
        if "%" in tok or "." in tok or "∶" in tok:
            out.append(tok)
            continue
        try:
            if int(tok) >= 20:
                out.append(tok)
        except ValueError:
            pass
    return Counter(out)
before_nums = protected_numbers(before_text)
after_nums = protected_numbers(after_text)
if before_nums != after_nums:
    print("MISSING_PROTECTED_NUMBERS", dict(before_nums - after_nums))
    print("ADDED_PROTECTED_NUMBERS", dict(after_nums - before_nums))
assert before_nums == after_nums, "Protected scientific numeric tokens changed"
for expr in ["1/3", "L=96", "H=24", "S={1,2,4}"]:
    assert before_text.count(expr) == after_text.count(expr), f"Protected expression {expr} changed"

# Citations and formulas remain intact.
cite_pat = re.compile(r"\[\d+\]")
assert Counter(cite_pat.findall(before_text)) == Counter(cite_pat.findall(after_text)), "Citation markers changed"
for eq in [f"({i})" for i in range(1, 17)]:
    assert before_text.count(eq) == after_text.count(eq), f"Equation marker {eq} changed"

# References, URLs and DOI-bearing paragraphs must be byte-for-byte unchanged at paragraph text level.
before_refs = [p.text for p in Document(SOURCE).paragraphs if p.text.strip().startswith("[")]
after_refs = [p.text for p in doc.paragraphs if p.text.strip().startswith("[")]
assert before_refs == after_refs, "Reference list changed"

# Simple residual style audit, aligned with the requested de-AI pass.
patterns = [
    "基于上述", "综上", "首先", "其次", "最后", "由此可见",
    "这里可以按", "进一步给出了", "用于观察", "这样设置的目的不是",
    "形成互补的实验链", "基于这一问题"
]
before_counts = {pat: before_text.count(pat) for pat in patterns}
after_counts = {pat: after_text.count(pat) for pat in patterns}

dump_paragraphs(doc, AFTER_TXT)
doc.save(TARGET)

with REPORT.open("w", encoding="utf-8") as f:
    f.write("v25 -> v26 AI-style targeted audit\n")
    f.write(f"edited_paragraphs={len(changed)}\n")
    f.write(f"tables={len(doc.tables)}, inline_shapes={len(doc.inline_shapes)}\n")
    f.write("preservation: tables/headings/figure_captions/numbers/citations/equation_markers/references = PASS\n\n")
    f.write("Residual phrase counts (before -> after):\n")
    for pat in patterns:
        f.write(f"{pat}: {before_counts[pat]} -> {after_counts[pat]}\n")
    f.write("\nChanged paragraphs:\n")
    for i, (old, new) in enumerate(changed, 1):
        f.write(f"\n[{i}]\nBEFORE: {old}\nAFTER:  {new}\n")

print("saved", TARGET)
print("edited paragraphs", len(changed))
print("preservation checks PASS")
print("residual counts", before_counts, after_counts)
