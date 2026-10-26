from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
import hashlib
import json
import re
from collections import Counter

from lxml import etree
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
SOURCE = BASE / '自适应多尺度加权的多变量网络流量预测_czxxtx20261024.docx'
OUTPUT = BASE / '自适应多尺度加权的多变量网络流量预测_czxxtx20261026_结构精简稿.docx'
source = Document(SOURCE)
doc = Document(SOURCE)
old = list(source.paragraphs)
body = doc._element.body
sect = deepcopy(body.sectPr)
for e in list(body):
    body.remove(e)
body.append(sect)
for c in list(sect):
    if c.tag == qn('w:cols'):
        c.set(qn('w:num'), '1')
        for sub in list(c):
            c.remove(sub)

records = []
formula_groups = []

def append(e):
    body.insert(len(body)-1, e)

def clean_p(p):
    for e in p._p.xpath('./w:pPr/w:sectPr'):
        e.getparent().remove(e)
    for e in p._p.xpath('.//w:lastRenderedPageBreak'):
        e.getparent().remove(e)
    return p

def copy_p(i):
    e = deepcopy(old[i]._p)
    for n in e.xpath('./w:pPr/w:sectPr'):
        n.getparent().remove(n)
    append(e)
    records.append({'kind':'copy','source':i})
    return e

def add(text, style='JournalBody', keep=False):
    p = clean_p(doc.add_paragraph(style=style))
    if style == 'JournalBody':
        for token in re.split(r'(\[\d+(?:[-,，]\d+)*\])', text):
            r = p.add_run(token)
            if re.fullmatch(r'\[\d+(?:[-,，]\d+)*\]', token):
                r.font.superscript = True
    else:
        p.add_run(text)
    p.paragraph_format.keep_with_next = keep or style in ['JournalHeading1','JournalHeading2','JournalReferenceHeading']
    if style == 'JournalBody':
        p.paragraph_format.widow_control = True
    records.append({'kind':'text','style':style,'text':text})
    return p

def math_nodes(i):
    return old[i]._p.xpath('./m:oMath | ./m:oMathPara/m:oMath')

def eq(indices):
    n = len(formula_groups)+1
    p = clean_p(doc.add_paragraph(style='JournalEquation'))
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.keep_together = True
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.tab_stops.clear_all()
    p.paragraph_format.tab_stops.add_tab_stop(Inches(3.35), WD_TAB_ALIGNMENT.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.93), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run('\t')
    originals=[m for i in indices for m in math_nodes(i)]
    if len(originals)==1:
        p._p.append(deepcopy(originals[0]))
    else:
        om=OxmlElement('m:oMath')
        arr=OxmlElement('m:eqArr')
        pr=OxmlElement('m:eqArrPr')
        base=OxmlElement('m:baseJc'); base.set(qn('m:val'),'center'); pr.append(base)
        arr.append(pr)
        for original in originals:
            e=OxmlElement('m:e')
            for child in original:
                e.append(deepcopy(child))
            arr.append(e)
        om.append(arr); p._p.append(om)
    p.add_run('\t（'+str(n)+'）')
    formula_groups.append({'number':n,'source_paragraphs':indices,
        'math_tokens':[t.text or '' for i in indices for t in old[i]._p.xpath('.//m:t')]})
    records.append({'kind':'equation','number':n,'sources':indices})
    return p

def table(i):
    append(deepcopy(source.tables[i]._tbl))
    records.append({'kind':'table','source':i})

def figure(i, caption):
    copy_p(i)
    add(caption,'JournalCaption')

# 题录集中到正文前；保留作者、单位和关键词的原始内容。
copy_p(0); copy_p(3); copy_p(4)
add('摘要：针对骨干网小时级源—目的（OD）流量的多尺度变化，提出自适应多尺度加权预测方法。通过1、2、4尺度的独立分解线性模型（DLinear）生成候选预测，利用四维窗口统计特征计算融合权重，并在OD变量间共享时间映射。Abilene和GÉANT的24 h预测MSE较LightTS平均降低25.77%和43.74%，参数量为其6.41%和2.17%；Abilene高需求MAE与平均低估误差较DLinear降低13.96%和16.07%；GÉANT一周预测MSE降低23.16%。该方法以低参数量实现多尺度流量预测。','JournalAbstract')
copy_p(6)
add('中图分类号：TP393    文献标志码：A','JournalMetadata')
copy_p(108); copy_p(109); copy_p(110)
add('Abstract: An adaptive multiscale weighting method was developed for hourly origin-destination (OD) traffic forecasting in backbone networks. Three independent decomposition linear (DLinear) experts generated forecasts at scales of 1, 2, and 4. Four window statistics determined the fusion weights, while temporal mappings were shared across OD variables. On Abilene and GÉANT, the mean paired reductions in 24-hour mean squared error (MSE) relative to LightTS were 25.77% and 43.74%, with parameter counts equivalent to 6.41% and 2.17% of the respective LightTS configurations. On Abilene, high-demand mean absolute error (MAE) and average underestimation error decreased by 13.96% and 16.07% relative to DLinear. For one-week forecasting on GÉANT, MSE decreased by 23.16% relative to DLinear. The method combines multiscale forecasts with a small parameter budget.','JournalAbstract')
copy_p(113)

add('0　引言','JournalHeading1')
add('骨干网容量配置与资源管理需要提前估计源—目的节点对（origin-destination，OD）的流量需求。多变量OD预测以节点对为变量，在同一历史输入下预测多个节点对的未来变化。小时级流量兼有逐小时波动与较慢演化趋势，不同历史窗口的变化幅度和末端状态也各不相同。预测模型既需从同一历史范围提取不同时间分辨率的信息，也需根据当前窗口确定各尺度的贡献。对于数百维OD序列，如何在控制参数规模的同时完成上述预测与融合，是本文研究的主要问题。')
add('已有网络流量预测研究从时间依赖、变量关联和周期结构等方面展开。Lohrasbinasab等[1]梳理了统计方法与机器学习方法，Qin等[2]采用图神经网络建模时空关联，韦烜等[3]和唐文杰等[4]分别研究流量矩阵的变量关系与周期整合；Zhou等[5]利用深度回声状态网络开展多尺度预测。在轻量时序建模方面，分解线性模型（DLinear）[6]分别映射趋势项和余项，结构简洁；TimeMixer[7]和LightTS[8]则提供了多尺度混合与采样建模思路。对于小时级OD流量，单一时间分辨率难以同时利用细粒度波动与粗粒度趋势，固定等权或全局静态权重又难以随窗口状态调整尺度贡献，需要将多尺度信息提取与轻量自适应融合结合。')
add('为此，本文构建由三个独立DLinear专家和四维统计路由组成的预测模型。首先，以1、2、4三种聚合尺度形成同一历史范围内的多分辨率输入，各专家在OD变量间共享时间映射参数；随后，以窗口均值、标准差、末时刻均值和平均绝对一阶差分生成样本级融合权重，将候选预测组合为最终输出。该结构以低维路由完成窗口自适应加权，参数量不随OD变量数增加。实验在Abilene和GÉANT上比较24 h预测精度与参数量，并通过融合消融、高需求目标点评价和168 h预测验证模型表现。')

add('1　自适应多尺度网络流量预测方法','JournalHeading1')
add('模型由多尺度预测分支与窗口路由分支组成，如图1所示。预测分支从同一历史窗口构造三种时间分辨率的序列，并独立输出未来H步候选预测；路由分支提取四项窗口统计量，经两层网络生成尺度权重。两分支联合训练，最终逐元素融合为H×C的OD流量预测，其中C为OD变量数。')
figure(17,'图1 自适应多尺度加权网络流量预测模型（图示为24 h基础任务，一周任务的输出长度为168步）')
add('1.1　多尺度输入与线性专家','JournalHeading2')
add('记对数变换和逐变量标准化后的流量向量为xₜ。沿时间轴以1 h步长生成滑动窗口，第n个样本的历史输入Xₙ包含L个时间点，其后H个时间点构成目标Yₙ，行、列分别对应时间和OD变量：')
eq([20,21])
add('设置尺度集合S={1,2,4}，对Xₙ沿时间维进行非重叠平均池化，聚合长度与步长均为s：')
eq([29])
add('式中，s∈S，i为聚合窗口内的时间索引。L=96时，三种尺度均覆盖过去96 h，分别以1 h输入值、2 h均值和4 h均值形成96、48、24步序列。各尺度配置结构相同、参数独立的DLinear专家[6]，统一输出未来H步预测，使细粒度变化与较平滑趋势进入同一融合过程。')
add('各专家采用长度q=25的中心移动平均分解序列，两端以端点复制补齐。设m=12，趋势项T与余项R为')
eq([32,33])
add('式中，移动平均使用端点补齐后的输入。趋势项与余项分别经线性层沿时间维映射，输出相加得到尺度预测：')
eq([35])
add('式中，W、b为线性层权重和偏置，下标T、R表示趋势与余项。权重矩阵为H×(L/s)，偏置为H维，并在全部OD变量之间共享。因此，各尺度均输出H×C的预测矩阵，模型可在144维或524维OD序列上保持相同的时间映射参数规模。')

add('1.2　窗口特征与自适应加权','JournalHeading2')
add('路由分支从原始时间分辨率的预处理窗口提取均值μₙ、标准差σₙ、末时刻均值ℓₙ和平均绝对一阶差分dₙ，组成四维特征向量zₙ：')
eq([40,41])
add('均值反映窗口相对训练期均值的整体偏移，标准差概括时间与变量维度的离散程度，末时刻均值描述窗口末端状态，平均绝对一阶差分刻画相邻小时的变化幅度。四项特征共同表征当前窗口的水平与波动，将高维OD窗口压缩为固定的4维路由输入。以此生成逐窗口权重，可在细粒度变化与粗粒度趋势之间分配尺度贡献。')
add('两层路由网络先将zₙ映射至16维隐藏层，经修正线性单元（rectified linear unit，ReLU）激活后输出三个尺度分数aₙ，再通过归一化指数函数（Softmax）得到权重：')
eq([44,46])
add('式中，W₁、W₂分别为16×4和3×16的权重矩阵，b₁、b₂为16维和3维偏置；αₙ,ₛ为窗口n在尺度s上的融合权重，j为尺度集合的求和索引。三个权重非负且和为1，在当前窗口的全部OD变量和预测步之间共享。最终预测为')
eq([48])
add('该融合方式以窗口统计量驱动尺度权重，既保留各专家的独立预测能力，又以较小的路由网络完成样本级适配。预测输出仍保留每个OD变量与每个未来时间点，形成统一的多变量多步预测结果。')

add('1.3　模型训练与参数规模','JournalHeading2')
add('各尺度专家与路由网络联合训练，以均方误差（mean squared error，MSE）为损失函数，对N个训练样本、H个预测步和C个变量取平均：')
eq([51])
add('采用自适应矩估计（adaptive moment estimation，Adam）优化器更新参数，并依据验证集MSE选择检查点。每个尺度包含两个线性层，参数量为2H(L/s+1)；4→16→3路由网络含4×16+16+16×3+3=131个参数。当L=96、H=24时，总参数量为')
eq([53])
add('变量间共享时间映射使参数量不随OD维数增加。24 h配置共8339个参数，路由仅占1.57%；H=168时共57587个参数，路由仍为131个，占比降至0.23%。该结构以固定规模的窗口特征和路由网络完成不同OD维数及预测长度下的自适应融合。')

add('2　实验分析','JournalHeading1')
add('2.1　实验数据与参数设置','JournalHeading2')
add('实验采用CESNET TS-Zoo[9]中的Abilene[10]和GÉANT[11]小时级流量矩阵，分别含4656、2849个时间点。使用CESNET TS-Zoo 2.2.0读取matrix子集的1_hour聚合文件，字段分别为小时级平均OD流量matrix_avg_realOD和平均带宽matrix_avg_bandwidth_kbps。按UTC时间戳，Abilene覆盖2004年3月1日0时至9月10日23时，GÉANT覆盖2004年12月31日23时30分至2005年4月29日15时30分。数据按时间顺序以6∶2∶2划分训练、验证和测试集，划分后在各子集中独立生成滑动窗口。')
add('缺失值和无穷值置0，负值截为0。对原始流量v先进行自然对数变换，再按变量标准化：')
eq([23,24])
add('式中，u为对数变换后的流量，t、c分别为时间和变量索引；μᵗʳ、σᵗʳ为训练集各变量的均值与标准差，验证和测试集沿用该统计量。对数变换后仅保留训练集标准差大于10⁻⁸的变量，Abilene保留144维，GÉANT保留524维。两套数据均以96 h历史预测未来24 h，GÉANT另开展168 h预测，数据划分与窗口数见表1。')
copy_p(58); table(0)
add('各模型采用相同的数据划分、预处理、输入与预测目标，批量大小为16。DLinear及多尺度模型的学习率为0.001，最多训练30轮，早停耐心值为6；LightTS采用Time-Series-Library公开实现[12]，分块长度24、模型维度512，学习率0.0001，最多训练50轮，早停耐心值为10。各模型均按验证集MSE选择检查点，使用42～49八个共同随机种子重复训练。软件环境为Python 3.11.9、PyTorch 2.5.1。')
add('误差报告均值±样本标准差，图中误差线表示样本标准差。相对降幅先按相同随机种子的结果配对计算，再取八次重复的均值。评价指标在对数变换与逐变量标准化后的空间计算，测试集MSE按式（8）计算，N取测试窗口数；平均绝对误差（mean absolute error，MAE）为')
eq([63])
add('式中，Nₜₑ为测试窗口数。MSE反映平方偏差，MAE反映平均绝对偏差，两者越小表示预测越准确。')

add('2.2　预测精度与参数量比较','JournalHeading2')
add('以单尺度DLinear和轻量时序模型LightTS为基线，分别考察多尺度自适应融合的预测收益及参数代价，结果见表2。图2给出同一种子下的相对误差降幅与参数量比例。')
copy_p(67); table(1)
add('本文方法在两套数据上的平均MSE与MAE均低于两种基线，Abilene为0.189±0.003和0.173±0.008，GÉANT为0.426±0.029和0.366±0.018。相对单尺度DLinear，两套数据的MSE平均降低2.77%和2.35%，MAE平均降低8.01%和1.32%。这一结果表明，同窗多尺度预测与窗口自适应融合能够提高小时级OD流量预测精度。')
figure(70,'图2 24 h预测误差的逐种子配对降幅与参数量比例（散点为单次配对，菱形及误差线为均值±样本标准差）')
add('相对LightTS，Abilene和GÉANT的MSE平均降低25.77%和43.74%，MAE平均降低12.66%和29.09%。对应LightTS模型分别含130162、384382个参数，本文方法均为8339个，分别为其6.41%和2.17%，即减少93.59%和97.83%。通过变量间参数共享和四维路由，本文方法以较少参数获得了更低的平均预测误差，在不同OD规模下保持了精度与参数量优势。')

add('2.3　自适应加权消融分析','JournalHeading2')
add('保持尺度集合与三个独立DLinear专家不变，比较固定等权、全局可学习权重和恒定输入路由。固定等权将各尺度权重设为1/3；全局权重以三个可训练分数生成所有窗口共用的权重；恒定路由保留与本文相同的两层网络，输入全零特征。三种对照均由真实历史序列驱动专家，结果见表3。')
copy_p(74); table(2)
add('本文方法在两套数据上的平均MSE与MAE均为所设对照中的最低值。相对全局可学习权重，Abilene和GÉANT的MSE平均降低1.80%和4.31%，其中Abilene的MAE降低8.91%。GÉANT上本文方法MSE为0.426，低于固定等权、全局权重和恒定路由的0.447、0.446、0.449，也低于单尺度DLinear的0.437。')
add('恒定路由与本文方法具有相同网络结构和参数量，两者差别在于是否输入真实窗口统计特征。本文方法取得更低误差，说明窗口信息驱动的权重计算为融合带来了预测收益。在三个多尺度对照之上，本文方法通过样本级尺度调整取得了进一步改善，体现了四维统计特征与自适应加权的作用。')

add('2.4　高需求目标点预测分析','JournalHeading2')
add('高需求目标点的预测有助于提前估计较大流量需求。以训练集各OD变量的第90百分位值为阈值，将测试集中超过相应阈值的目标点组成集合Ω，计算其MAE与平均低估误差（average underestimation error，AUE）：')
eq([79])
add('式中，|Ω|为高需求目标点数；AUE对正向低估量取平均，数值越小表示低估幅度越小。两项指标均在标准化空间计算，结果见图3。')
figure(81,'图3 高需求目标点的MAE与平均低估误差（散点为单次重复，误差线为样本标准差）')
add('本文方法在Abilene上的高需求MAE与AUE分别为0.147、0.137，GÉANT上分别为0.632、0.577，均低于图中所设对照。Abilene上相对DLinear，两项指标分别降低13.96%和16.07%；相对固定等权，分别降低约17.47%和20.84%。与总体精度结果相结合，自适应多尺度加权在降低平均预测误差的同时，也减小了高需求目标点的低估幅度，为小时级流量需求估计提供了更准确的预测结果。')

add('2.5　一周预测结果分析','JournalHeading2')
add('将GÉANT预测长度扩展至168 h，历史输入仍为96 h，各模型按新输出长度独立训练，数据划分、预处理与评价口径保持一致。在307个共同测试窗口上比较DLinear、固定等权、全局权重、恒定路由和本文方法，绝对误差见表4，逐种子结果及配对降幅见图4。')
copy_p(86); table(3)
figure(87,'图4 GÉANT一周预测误差与逐种子配对降幅（散点为单次重复，菱形及误差线为均值±样本标准差）')
add('本文方法的一周预测MSE为0.841±0.088，MAE为0.536±0.028，均为五种方法中的最低平均误差。相对DLinear，MSE与MAE平均降低23.16%和11.16%；相对固定等权、全局权重和恒定路由，MSE分别降低26.11%、26.02%和23.77%，MAE分别降低12.39%、12.34%和11.19%。八个共同随机种子下，相对四种对照的MSE与MAE配对降幅均为正，显示出一致的预测收益。')
add('预测长度由24 h扩展至168 h后，路由网络仍仅含131个参数，占总参数量57587的0.23%。较长预测区间上的误差改善与固定路由规模相结合，进一步体现了该结构在多步OD流量预测中的精度与轻量化优势。')

add('3　结语','JournalHeading1')
add('本文提出自适应多尺度加权网络流量预测方法，以三个独立DLinear专家提取同一历史范围内不同时间分辨率的信息，通过四维窗口统计特征生成融合权重，并在OD变量间共享时间映射，以低参数量完成多变量多步预测。')
add('Abilene和GÉANT的24 h预测MSE较LightTS平均降低25.77%和43.74%，参数量分别为其6.41%和2.17%；融合消融验证了窗口自适应加权的预测收益。Abilene高需求MAE与AUE较DLinear降低13.96%和16.07%，GÉANT一周预测MSE与MAE降低23.16%和11.16%。该方法兼顾总体精度、高需求预测和较长预测区间，为骨干网小时级OD流量需求分析提供了轻量预测方法。')
copy_p(94)
for i in range(95,107):
    copy_p(i)
copy_p(2)

# 沿用原稿字体、页宽和表格；标题设为黑色，图表与图题成组。
for name in ['Title','JournalHeading1','JournalHeading2','JournalReferenceHeading']:
    doc.styles[name].font.color.rgb=RGBColor(0,0,0)
for p in doc.paragraphs:
    if p.style.name in ['Title','JournalHeading1','JournalHeading2','JournalReferenceHeading']:
        for r in p.runs:
            r.font.color.rgb=RGBColor(0,0,0)
    if p.style.name=='JournalFigure':
        p.paragraph_format.keep_with_next=True
        p.paragraph_format.keep_together=True
        p.paragraph_format.space_after=Pt(0)
    if p.style.name=='JournalCaption':
        p.paragraph_format.keep_together=True
        p.paragraph_format.first_line_indent=Pt(0)
        p.paragraph_format.space_after=Pt(4)
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=p.text.startswith('表')
    if p.style.name=='JournalEquation':
        for r in p.runs:
            r.font.size=Pt(10)

# 清除过时的自动分页缓存与外部文档链接引用缓存，保持正文内容不变。
for n in doc._element.xpath('.//w:lastRenderedPageBreak'):
    n.getparent().remove(n)
settings=doc.settings.element
u=settings.find(qn('w:updateFields'))
if u is None:
    u=OxmlElement('w:updateFields'); settings.append(u)
u.set(qn('w:val'),'true')
doc.core_properties.title=old[0].text
doc.core_properties.subject='长江信息通信投稿结构精简稿'
doc.save(OUTPUT)

# 直接对最终文件核对表格、图像、参考文献及所有独立公式的完整性。
result=Document(OUTPUT)
table_ok=[[[c.text for c in row.cells] for row in a.rows]==[[c.text for c in row.cells] for row in b.rows] for a,b in zip(source.tables,result.tables)]
with ZipFile(SOURCE) as za, ZipFile(OUTPUT) as zb:
    media=[n for n in za.namelist() if n.startswith('word/media/')]
    media_ok={n:hashlib.sha256(za.read(n)).hexdigest()==hashlib.sha256(zb.read(n)).hexdigest() for n in media}
refs_old=[p.text for p in source.paragraphs if p.style.name=='JournalReference']
refs_new=[p.text for p in result.paragraphs if p.style.name=='JournalReference']
eq_ps=[p for p in result.paragraphs if p.style.name=='JournalEquation']
math_ok=[]
for p,g in zip(eq_ps,formula_groups):
    tokens=[t.text or '' for t in p._p.xpath('.//m:t')]
    math_ok.append(tokens==g['math_tokens'])
old_texts=[p.text for p in source.paragraphs if p.style.name in ['JournalHeading1','JournalHeading2','JournalBody','JournalCaption']]
new_texts=[p.text for p in result.paragraphs if p.style.name in ['JournalHeading1','JournalHeading2','JournalBody','JournalCaption']]
# 新增的四个图题不计入与前轮相同的正文叙述压缩统计口径。
new_count_texts=[p.text for p in result.paragraphs if p.style.name in ['JournalHeading1','JournalHeading2','JournalBody','JournalCaption'] and not (p.style.name=='JournalCaption' and p.text.startswith('图'))]
count=lambda ss:len(re.sub(r'\s+','',''.join(ss)))
old_count=count(old_texts)
new_count=count(new_count_texts)
all_text='\n'.join(p.text for p in result.paragraphs)
important=['25.77%','43.74%','6.41%','2.17%','93.59%','97.83%',
    '2.77%','2.35%','8.01%','1.32%','12.66%','29.09%','1.80%','4.31%','8.91%',
    '0.147','0.137','0.632','0.577','13.96%','16.07%','17.47%','20.84%',
    '23.16%','11.16%','26.11%','26.02%','23.77%','12.39%','12.34%','11.19%',
    '8339','57587','131','1.57%','0.23%']
advantage_checks={value:value in all_text for value in important}
checks={
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'output_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    'tables':{'count':len(result.tables),'cell_text_identical':table_ok},
    'images':{'count':len(media),'byte_identical':media_ok},
    'references':{'count':len(refs_new),'text_identical':refs_old==refs_new},
    'formulas':{'source_expressions':sum(len(g['source_paragraphs']) for g in formula_groups),'new_numbered_groups':len(eq_ps),'token_sequences_identical':math_ok},
    'advantage_result_tokens_retained':advantage_checks,
    'narrative_count':{'before':old_count,'after':new_count,'reduction_percent':round((old_count-new_count)/old_count*100,2),'excludes_new_figure_captions':True},
    'headings':[p.text for p in result.paragraphs if p.style.name in ['JournalHeading1','JournalHeading2']],
    'paragraph_count':len(result.paragraphs),
}
assert len(result.tables)==4 and all(table_ok)
assert len(media)==4 and all(media_ok.values())
assert len(refs_new)==12 and refs_old==refs_new
assert len(eq_ps)==12 and all(math_ok)
assert all(advantage_checks.values())
(ROOT/'revision_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'revision_operations.json').write_text(json.dumps({'source':str(SOURCE),'output':str(OUTPUT),'operations':records,'formula_groups':formula_groups},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'revised_text.txt').write_text('\n\n'.join(p.text if p.style.name!='JournalEquation' else p.text+' [公式: '+''.join(t.text or '' for t in p._p.xpath('.//m:t'))+']' for p in result.paragraphs),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
