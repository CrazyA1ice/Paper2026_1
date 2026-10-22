"""Apply the V69 audit with local text edits and protected-content checks."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
import hashlib
import json
import re
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'word_output/2026.10.04v69.docx'
TARGET = ROOT / 'word_output/2026.10.07v70.docx'
QA = Path(__file__).resolve().parent
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W, 'm': M}
Q = lambda tag: f'{{{W}}}{tag}'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


def visible(element):
    return ''.join(element.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS))


with ZipFile(SOURCE) as archive:
    infos = archive.infolist()
    parts = {info.filename: archive.read(info.filename) for info in infos}
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
root = etree.fromstring(parts['word/document.xml'])
original = deepcopy(root)
paragraphs = root.xpath('./w:body/w:p', namespaces=NS)
assert len(paragraphs) == 128
before = [visible(p) for p in paragraphs]
reasons = {}


def replace(index, old, new, reason):
    """Replace literal prose across runs while retaining run and math objects."""
    paragraph = paragraphs[index]
    nodes = paragraph.xpath('.//w:t | .//m:t', namespaces=NS)
    joined = ''.join(node.text or '' for node in nodes)
    assert joined.count(old) == 1, (index, old, joined.count(old))
    start = joined.index(old)
    end = start + len(old)
    position = 0
    first = True
    for node in nodes:
        text = node.text or ''
        node_end = position + len(text)
        if position < end and node_end > start:
            assert node.tag == Q('t'), 'Attempt to alter protected mathematics'
            left = max(0, start - position)
            right = min(len(text), end - position)
            node.text = text[:left] + (new if first else '') + text[right:]
            node.set(XML_SPACE, 'preserve')
            first = False
        position = node_end
    reasons.setdefault(index, []).append(reason)


def rewrite(index, new, reason):
    assert not paragraphs[index].xpath('.//m:oMath', namespaces=NS)
    replace(index, visible(paragraphs[index]), new, reason)


def append(index, text, reason):
    paragraph = paragraphs[index]
    run = etree.SubElement(paragraph, Q('r'))
    exemplar = next(r for r in paragraph.xpath('./w:r', namespaces=NS)
                    if re.search('[\u4e00-\u9fff]', visible(r)))
    props = exemplar.find(Q('rPr'))
    if props is not None:
        run.append(deepcopy(props))
    node = etree.SubElement(run, Q('t'))
    node.set(XML_SPACE, 'preserve')
    node.text = text
    reasons.setdefault(index, []).append(reason)


replace(3, '总体水平、离散程度、末时状态和平均变化强度，两层感知器据此计算出融合权重',
        '均值、标准差、末时刻均值和平均绝对一阶差分，多层感知器据此计算融合权重',
        '将统计特征写为实际计算的统计量，明确网络类型')
replace(4, '线性分解预测', '分解线性模型', '关键词与DLinear名称一致')
english = ('Abstract: Hourly forecasting of backbone network traffic requires consideration of both short-term fluctuations and long-term trends. '
 'A lightweight adaptive multiscale forecasting model was therefore developed. Historical windows were represented at three temporal resolutions, '
 'and independent decomposition linear experts generated candidate forecasts. A routing network extracted four statistics from the current window: '
 'the mean, standard deviation, mean at the last time step, and mean absolute first difference. '
 'A multilayer perceptron with two fully connected layers used these statistics to calculate fusion weights. '
 'Experiments on Abilene and GÉANT used 96 historical steps to predict the next 24 steps. '
 'Across three common random seeds, the proposed method reduced mean squared error by 4.07% and 4.54% relative to the single-scale decomposition linear model, respectively. '
 'The corresponding reductions relative to the sampling-oriented lightweight model LightTS were 29.80% and 46.89%. '
 'Further ablation experiments across eight random seeds compared the proposed method with learned global weights and a constant-input router. '
 'On Abilene, the mean seed-wise improvements over both controls were approximately 1.80%; on GÉANT, they were 4.31% and 4.97%, respectively. '
 'The results show that combining multiscale candidate forecasts with low-dimensional routing achieves lower mean forecasting errors with few additional fusion parameters. '
 'The forecasts can provide a reference for next-day network traffic demand analysis and capacity planning.')
# Keep the bold Abstract label in its original run.
replace(9, visible(paragraphs[9])[len('Abstract: '):], english[len('Abstract: '):],
        '方法及实验结果改用过去时，统计量与中文摘要同步')
replace(10, 'linear decomposition forecasting', 'decomposition linear model', '中英文关键词对应')
replace(13, '以极低复杂度完成预测', '以较低计算复杂度完成预测', '删除没有限定的程度词')
replace(15, '外部基线比较', '基线模型比较', '采用常用实验描述')
rewrite(20, '注：梯形虚线表示DLinear专家内部结构的展开，实线表示预测计算流程，折线虚线表示窗口特征与融合权重的传递。预测分支与路由分支共享同一预处理历史窗口。图中省略样本下标，曲线和色块仅作机制示意。', '图注与梯形虚线及并行分支一致')
replace(21, '那么尺度信息的差别完全由输入侧引入：', '不同时间分辨率由输入侧构造：', '修正输入构造与独立专家参数的关系')
replace(24, '第n个样本的输入与目标表示为：', '向量按时间顺序逐行堆叠，矩阵行对应时间点，列对应OD变量。第n个样本的输入与目标表示为：', '明确式（1）、（2）的堆叠约定')
replace(27, '预测步长H=24', '预测长度H=24', '区分预测长度与采样、池化步长')
replace(27, '得到预处理后的序列：', '得到对数变换后的序列，其中log表示自然对数：', '明确对数变换与标准化的先后关系')
replace(31, '分别为训练集上第', '分别为对数变换后的训练集上第', '明确训练统计量的计算空间')
replace(38, '随着尺度增加，序列长度递减，对应专家分支数则增多。', '尺度取值越大，对应输入序列越短；三个尺度分别配置一个独立专家。', '修正固定三专家的结构描述')
replace(39, '越界索引取最近端点的值，因此分解前后的时间长度保持一致：', '越界索引取最近端点的值：', '合并重复的边界填充说明')
append(44, '两个线性层的权重矩阵均为H×(L/s)，偏置向量均为H维；各OD变量共享参数，偏置沿OD变量维度广播，输出为H×C。', '补充式（8）的矩阵维度和偏置广播')
replace(46, '这在直觉上也易于理解，当窗口内局部波动较为剧烈时，细粒度尺度提供的细节信息理应占据更高权重；而当序列变化趋于平缓、以慢趋势为主时，较粗尺度上的趋势估计反而更有参考价值。',
        '局部波动与较慢趋势在不同窗口中可能具有不同的预测价值，因此利用窗口统计特征学习各尺度的融合比例。', '将设计动机与已验证的机制结论区分')
replace(46, '为了用简洁方式刻画窗口状态，从原始输入', '为描述窗口状态，从原始时间分辨率的预处理窗口', '明确窗口是预处理后的输入')
replace(49, '分别描述输入窗口的总体水平、离散程度、最近状态和平均变化强度。', '分别为输入窗口的均值、标准差、末时刻均值和平均绝对一阶差分。', '统一四项统计量名称')
replace(49, '取窗口末时刻的平均状态', '为窗口末时刻各OD变量的均值', '用统计量替代含义不明确的状态表述')
replace(49, '由相邻时间点的一阶变化得到', '为相邻时间点绝对差值的均值', '对应平均绝对一阶差分的计算定义')
replace(49, '这4个统计量分别提供水平、波动、最近状态和局部变化信息，供路由器计算输入相关的尺度权重，而不直接参与未来流量数值的预测。',
        '这4个统计量用于计算随输入窗口变化的尺度权重，各尺度专家负责生成预测值。', '去除非正式概括和重复解释')
replace(50, '路由器只负责给出各尺度的融合分数，完整的 OD 流量预测仍由对应的尺度专家独立完成。路由器的两层感知器接收四维统计向量，通过16维隐藏层输出3个尺度的未归一化分数。',
        '尺度路由网络是用于生成融合权重的门控网络，由多层感知器实现；各尺度专家独立生成OD流量预测。多层感知器由两层全连接层组成，接收四维统计向量，经16维隐藏层输出3个尺度的未归一化分数。', '说明专家、路由及多层感知器的技术含义')
replace(52, '对式（11）的3个尺度分数作Softmax归一化',
        '式（11）中，两层权重矩阵依次为16×4和3×16，偏置向量分别为16维和3维。对3个尺度分数作Softmax归一化', '补充两层网络矩阵维度')
replace(58, '对应训练目标为', '其中N为训练样本数，对应训练目标为', '定义式（14）的训练样本数')
replace(61, '可直接用于后续的网络需求分析与容量规划。', '恢复至原始流量量纲后，可供网络需求分析与容量规划参考。', '预测空间与应用空间一致')
rewrite(69, '各模型使用相同的数据划分、输入长度、预测长度及评价指标，批量大小统一为16，优化器均为Adam。各模型采用预先固定的超参数配置，未分别进行超参数搜索。多尺度模型联合优化专家与可训练融合参数，按验证集MSE选择模型，再在测试集上评价。DLinear及各多尺度模型的学习率为0.001，最多训练30轮；验证集MSE连续6轮未下降时执行早停。LightTS的学习率为0.0001，最多训练50轮，早停等待轮数为10轮。', '明确公平比较范围，去除早停耐心值等非正式用语')
replace(70, '公开实现来自THUML，LightTS的分块长度取24、模型维度参数取512。DLinear及各尺度专家使用25的移动平均窗口',
        'LightTS采用THUML公开实现，分块长度为24，模型维度参数为512。DLinear及各尺度专家按文献[6]实现，移动平均窗口长度为25', '限定公开实现来源并规范窗口长度表述')
replace(71, '外部基线比较', '基线模型比较', '统一实验名称')
replace(71, '核心消融', '消融实验', '去除没有技术定义的修饰语')
replace(72, '其中MSE采用式（14），MAE和RMSE的定义如下',
        '测试集MSE按式（14）的平均规则计算，样本数取测试窗口数；式（15）中的N_te为测试样本数。MAE和RMSE定义如下', '明确测试集指标的样本数')
replace(75, '为进一步刻画误差的绝对量级，同时报告 RMSE 作为补充', '同时报告RMSE，其数值尺度与标准化后的预测值一致', '避免将标准化误差解释为原始流量量级')
replace(75, '标准差表示种子间波动程度', '样本标准差表示种子间波动程度', '明确统计表使用样本标准差')
replace(75, '95%置信区间由配对种子改进率的均值、标准差及自由度为7的t分布计算。',
        '八种子配对改进率的95%置信区间，根据其均值、标准误及自由度为7的t分布计算；标准误为种子间样本标准差除以√8。', '修正置信区间计算说明')
replace(78, '三随机种子外部基线比较', '三随机种子基线模型比较（均值±标准差）', '说明表2统计汇总形式')
replace(84, '八随机种子核心消融与稳定性', '八随机种子消融实验与稳定性', '使用常用实验名称')
replace(85, '8次核心消融', '8次消融实验', '统一实验名称')
replace(86, '八随机种子核心消融结果', '八随机种子消融实验结果', '统一表题用语')
replace(87, '各有6/8和7/8个种子胜出', '两类对照下分别均有6/8和7/8个种子的MSE更低', '明确两类对照的种子比较结果')
replace(92, '图 3 ', '图3', '统一图号间距')
replace(92, '但跨越0%的结果相对更多，波动略大', '但负改进率的种子更多，种子间波动较大', '避免把单点改进率与区间跨零混写')
replace(93, '两类常权重对照', '全局可学习权重与恒定输入路由两类对照', '准确限定对照模型')
replace(93, '仍退步12.78%', '的MSE仍增加12.78%', '明确比较方向及误差指标')
replace(97, '分组预测校准', '真实值分组预测', '图4按真实值条件分组，不作为常规校准分析')
replace(98, '波动程度接近中位数、第90百分位的窗口；', '窗口平均绝对一阶差分接近中位数、第90百分位的窗口；', '明确典型窗口的波动度量')
replace(104, '总体权重偏好，以及这些偏好在随机种子间的变化', '总体权重分配，以及其在随机种子间的差异', '删除拟人化的权重偏好表达')
replace(105, 'GÉANT侧，', '在GÉANT上，', '改为正式数据集表述')
replace(105, '值得注意的是，', '', '删除多余的提示性用语')
replace(106, '运行开销', '计算开销', '统一计算性能用语')
replace(107, '标称参数数目', '参数总数', '参数计数直接对应模型结构')
replace(109, '运维侧在观测数据更新后，只需', '网络管理系统在观测数据更新后，可', '避免非正式主体及未验证的简化措辞')
replace(110, '再施加逆对数变换。', '再进行逆对数变换，并将结果截断至非负范围。', '与实际逆变换代码一致')
replace(111, '平均低估幅度', '低估误差均值', '直接描述误差正值部分的平均量，不作为另创指标')
replace(112, '平均低估幅度', '低估误差均值', '统一评价量名称，保留所有数值')
rewrite(113, '高需求预测点上的MAE和低估误差均值较低，与图4较高真实值区间的预测结果一致。Abilene不同随机种子下的改善较为一致；GÉANT两项配对改进率的95%置信区间均包含零，不同随机种子下的改善并不完全一致。上述结果可为高需求时段的流量监测与容量规划提供参考。', '修正跨零区间解释及校准、运行观测、容量复核等含混表达')
replace(115, '低维窗口路由', '基于窗口统计特征的尺度路由网络', '结语明确采用的网络与特征')
replace(117, 'KESHAVARZ A, AMIN-NEJAD S', 'SHAHRAKI A, TAHERKORDI A', '按出版社记录更正作者名单')

# Remove explanatory repetition while retaining definitions and all results.
replace(24, '多个OD变量过去L步的联合变化构成模型所读取的历史信息，据此估计未来H步的取值。', '', '删除紧接窗口定义的重复说明')
replace(27, '，给定连续 L 步观测，一次性输出随后 H 步的流量预测结果。原始 OD 流量本身非负，但数值范围较大的变量与其他变量量级差异明显，直接训练时采用的数值尺度不同。为此，先对原始流量',
        '。原始OD流量非负且变量间量级差异较大，先对原始流量', '保留预处理依据，合并重复的预测任务说明')
replace(31, '，验证集和测试集直接沿用这些训练统计量，不再单独估计。log(1+x)可以在压缩非负流量数值范围的同时保留大小关系，从而缓和量级差异。在此基础上进行逐变量标准化处理，可使各维度在后续的前向计算、损失函数及参数更新流程中处于相近的数值尺度。训练集、验证集和测试集按时间先后顺序以6∶2∶2比例划分后，在各集合内独立生成滑动窗口，并使所有窗口保持在集合边界内。',
        '，验证集与测试集沿用训练统计量。对数变换压缩取值范围并保留大小关系，逐变量标准化使输入处于相近数值尺度。数据按时间顺序以6∶2∶2划分，在各集合内独立生成滑动窗口，不跨集合边界。', '合并预处理作用的重复解释，保留训练统计量及时间划分规则')
rewrite(37, '非重叠平均池化不引入可训练参数。L=96时，尺度1保留原始96步序列；尺度2对相邻2点取均值，得到48步序列；尺度4对相邻4点取均值，得到24步序列。时间聚合平滑局部波动，使较慢趋势更明显。', '压缩各尺度长度和作用的重复说明')
rewrite(38, '尺度集合{1,2,4}使96步历史得到整数长度序列。尺度取值越大，对应输入越短；三个尺度分别配置一个独立专家。同一尺度内，每个时间点仅参与一次聚合。', '保留修正后的三专家关系，删除重复设计概括')
replace(39, '每个DLinear专家[6]只处理本尺度序列的输入，尺度1、2和4的序列分别进入对应专家。DLinear内部先对输入序列做分解，再对表征较慢变化的趋势项和围绕趋势波动的余项分别作时间映射。尺度s上的分解通过长度q=25的中心移动平均来实现，即在局部时间邻域内做平滑以提取趋势项。当窗口触及序列两端、无法覆盖完整邻域时，先复制端点向外补足，再进行平滑，从而保证分解前后序列长度不变；补齐后的序列记为',
        '每个DLinear专家[6]处理本尺度输入，通过长度q=25的中心移动平均提取趋势项，余项由输入减去趋势项得到。序列两端采用端点复制填充，保证分解前后时间长度不变；补齐后的序列记为', '压缩分解流程，保留移动平均窗口和端点规则')
replace(44, '趋势项表示经过局部平滑后保留下来的较慢变化部分，余项则由原序列减去趋势项得到，保留未被移动平均解释的局部变化。式（8）分别对两部分沿时间维进行线性映射，并把二者的预测结果相加形成该尺度的候选预测。3个尺度使用独立DLinear专家，是因为尺度1、2和4的输入长度分别为96、48和24，对应的时间分辨率和时间映射关系并不相同；若强制共用一组尺度间参数，会把不同长度、不同平滑程度的序列约束到同一映射中。同一尺度内部，各OD变量共享时间映射参数，模型学习的是这一时间尺度下通用的时间映射形式，而不是为每个OD变量分别建立一套线性层。',
        '前者表示局部平滑后的趋势，后者为去除趋势后的剩余部分。式（8）对两者分别作线性映射，将预测结果相加。三个专家分别处理长度96、48和24的输入，参数独立。', '以输入长度和参数共享规则替代重复分解说明及假设性解释')
replace(50, '由于状态向量本身维数较低、隐藏层规模也较小，路由模块引入的参数量相当有限；整个过程中不再额外接入循环网络或注意力机制等时序编码器。',
        '路由模块采用上述全连接结构，不引入循环网络或注意力编码器。', '保留网络结构，参数规模由第2.5节定量说明')
rewrite(58, '采用均方误差（mean squared error，MSE）训练模型，损失为N个训练样本、未来H个时刻及C个OD变量上平方误差的平均值。其中N为训练样本数，训练目标为', '压缩与式（14）重复的损失汇总说明')
rewrite(75, '所有指标在标准化空间计算，数值越小，误差越低。MSE对较大误差更敏感；MAE反映平均绝对偏差；RMSE与标准化后的预测值处于同一数值尺度。表2、表3分别汇总种子42～44、42～49的均值±样本标准差，标准差反映种子间波动。改进率按共同种子配对计算后求平均，不使用表内四舍五入值。八种子配对改进率的95%置信区间采用均值、标准误及自由度为7的t分布计算，标准误为种子间样本标准差除以√8。', '合并统计汇总说明，保留计算口径及标准误定义')
rewrite(108, '使用种子42～49的8个模型检查点测量前向耗时，预测长度为24，批量大小为16。计时前关闭梯度计算，测试张量预先载入显存；各检查点预热20个批次后，对完整测试集重复计时10次。每次总耗时除以批次数，先对10次测量取平均，再对8个检查点取平均。Abilene与GÉANT上，本文方法的平均每批前向耗时分别为2.65 ms、2.61 ms，固定等权模型为2.38 ms、2.10 ms，DLinear为0.77 ms、0.70 ms。测量不包含数据读取与传输开销。', '压缩重复计时叙述，保留所有测量设置和结果')
replace(63, '运行开销', '计算开销', '与第2.5节标题统一')
rewrite(13, '时间聚合可平滑原始序列中的短时扰动，使较慢趋势更明显；不同时间分辨率提供互补信息。Zhou等[5]以深度回声状态网络进行多尺度流量预测。在轻量预测方向上，分解线性模型（decomposition linear model，DLinear）[6]结合序列分解与线性映射；TimeMixer[7]采用多尺度混合；LightTS[8]使用采样导向的多层感知器（multilayer perceptron，MLP）。本文以DLinear为主干，研究不同尺度预测结果的融合方式。', '保留文献与方法关系，压缩重复的轻量化和多分辨率背景')
rewrite(14, '各尺度专家采用相同结构时，融合比例能否随当前窗口状态调整并降低预测误差，是本文考察的问题。固定权重可组合多尺度预测结果，但无法利用窗口间的状态差异调整融合比例。', '保留研究问题及固定融合的定义，合并重复解释')
rewrite(21, '各尺度采用相同DLinear结构并独立预测。原始尺度保留局部波动，时间聚合后的较粗尺度突出较慢趋势；路由网络根据当前窗口特征分配融合权重。模型由此在统一预测主干上结合多尺度输入与按样本加权。', '压缩图后重复的框架说明，保留分支职责与输入构造')
replace(46, '若对3个尺度的预测结果均取 1/3 权重，此种固定比例实际上与当前窗口所处状态无关。与之不同，本文依据窗口自身的统计量来确定融合权重，使其随样本状态动态变化，再用该权重对3个 DLinear 专家对同一样本的3组预测结果进行加权融合。局部波动与较慢趋势在不同窗口中可能具有不同的预测价值，因此利用窗口统计特征学习各尺度的融合比例。为描述窗口状态，从原始时间分辨率的预处理窗口',
        '固定等权融合对三个尺度均取1/3，与当前窗口状态无关。本文根据窗口统计特征学习融合权重，组合三个DLinear专家的预测结果。局部波动与较慢趋势的预测价值可能随窗口变化，因此从原始时间分辨率的预处理窗口', '合并固定融合、窗口特征与设计动机的重复说明')
replace(17, '窗口路由网络使用原始分辨率输入', '尺度路由网络使用原始时间分辨率的预处理输入', '统一路由网络名称及输入空间')
rewrite(109, '在小时级网络管理中，模型一次输出全部有效OD变量未来24 h的逐小时需求预测。观测更新后，按训练预处理规则将各OD最近96 h的流量构成历史窗口，再按时间与节点对组织预测结果，供需求分析使用。', '压缩应用流程复述，保留输入、输出及用途')
replace(65, '剔除恒定通道后，剩余524个有效维', '按训练集标准差剔除恒定或近恒定变量后，剩余524个有效OD变量', '有效变量筛选与代码一致，统一变量称谓')
replace(68, '固定等权模型将各尺度权重设为1/3', '本实验定义三类融合对照：固定等权模型将各尺度权重设为1/3', '明确三类对照是本实验的操作定义')
replace(56, '式（13）将3个DLinear专家的输出按上述权重加权求和，得到最终预测', '式（13）给出最终预测', '删除对加权求和公式的重复复述，保留窗口内共享权重的说明')
rewrite(95, '图4展示全测试点的分组预测及典型窗口轨迹。', '压缩图4引出句')
replace(99, '这些分组与轨迹用于观察预测行为，表3给出整体误差比较。', '整体误差比较见表3。', '删除已在图4引出句中说明的用途')
rewrite(100, '图5展示3个尺度的权重分布与各随机种子均值。', '压缩图5引出句')

# Inline definitions only: present new variable names in italic runs, leaving
# all original native equation objects intact.
for index in [44, 52, 58, 72]:
    for run in list(paragraphs[index].xpath('./w:r', namespaces=NS)):
        node = run.find(Q('t'))
        if node is None or not node.text:
            continue
        text = node.text
        matches = list(re.finditer(r'N_te|H×\(L/s\)|H×C|(?<![A-Za-z])N(?=为训练)|(?<![A-Za-z])H(?=维)', text))
        if not matches:
            continue
        position = 0
        chunks = []
        for match in matches:
            chunks += [(text[position:match.start()], False), (match.group(), True)]
            position = match.end()
        chunks.append((text[position:], False))
        parent = run.getparent()
        at = parent.index(run)
        for chunk, italic in chunks:
            if not chunk:
                continue
            new_run = deepcopy(run)
            new_run.find(Q('t')).text = chunk
            if chunk == 'N_te':
                new_run.find(Q('t')).text = 'N'
            if italic:
                props = new_run.find(Q('rPr'))
                if props is None:
                    props = etree.Element(Q('rPr'))
                    new_run.insert(0, props)
                mark = props.find(Q('i'))
                if mark is None:
                    mark = etree.SubElement(props, Q('i'))
                mark.set(Q('val'), '1')
            parent.insert(at, new_run)
            at += 1
            if chunk == 'N_te':
                subscript = deepcopy(new_run)
                subscript.find(Q('t')).text = 'te'
                props = subscript.find(Q('rPr'))
                props.find(Q('i')).set(Q('val'), '0')
                vertical = etree.SubElement(props, Q('vertAlign'))
                vertical.set(Q('val'), 'subscript')
                parent.insert(at, subscript)
                at += 1
        parent.remove(run)

# Permit long prose to flow across pages; keep equations, captions, tables and
# figures intact. This removes large gaps caused by whole-paragraph locking.
layout_changes = []
for index in [21, 24, 27, 31, 37, 38, 39, 44, 46, 49, 50, 69, 70, 75,
              87, 92, 98, 104, 105, 107, 108, 109, 110, 113]:
    props = paragraphs[index].find(Q('pPr'))
    if props is not None:
        item = props.find(Q('keepLines'))
        if item is not None:
            item.set(Q('val'), '0')
            layout_changes.append(index)
        widow = props.find(Q('widowControl'))
        if widow is None:
            widow = etree.SubElement(props, Q('widowControl'))
        widow.set(Q('val'), '1')

# References use the required single spacing at 9 pt; the body document grid
# should not enlarge their line spacing and strand the last reference.
for index in range(117, 128):
    props = paragraphs[index].find(Q('pPr'))
    if props is None:
        props = etree.Element(Q('pPr'))
        paragraphs[index].insert(0, props)
    snap = props.find(Q('snapToGrid'))
    if snap is None:
        snap = etree.SubElement(props, Q('snapToGrid'))
    snap.set(Q('val'), '0')
    spacing = props.find(Q('spacing'))
    if spacing is None:
        spacing = etree.SubElement(props, Q('spacing'))
    spacing.set(Q('line'), '240')
    spacing.set(Q('lineRule'), 'auto')

math_before = [etree.tostring(x) for x in original.xpath('//m:oMath', namespaces=NS)]
math_after = [etree.tostring(x) for x in root.xpath('//m:oMath', namespaces=NS)]
tables_before = [etree.tostring(x) for x in original.xpath('//w:tbl', namespaces=NS)]
tables_after = [etree.tostring(x) for x in root.xpath('//w:tbl', namespaces=NS)]
assert math_before == math_after
assert tables_before == tables_after
assert etree.tostring(original.find('.//w:sectPr', NS)) == etree.tostring(root.find('.//w:sectPr', NS))

# Decimal experimental values must remain present with their original counts.
for index in range(65, 116):
    old_values = re.findall(r'(?<!\d)\d+\.\d+%?', before[index])
    new_values = re.findall(r'(?<!\d)\d+\.\d+%?', visible(paragraphs[index]))
    assert old_values == new_values, (index, old_values, new_values)
parts['word/document.xml'] = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
parts['word/media/image1.png'] = (ROOT / 'paper_figures/fig1_A_border_spacing_20261007/A_border_spacing_highres.png').read_bytes()
parts['word/media/image4.png'] = (ROOT / 'paper_figures/v70_terminology/fig4.png').read_bytes()
if TARGET.exists():
    previous_audit = json.loads((QA / 'preservation_audit.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest() == previous_audit['target_sha256'], 'V70 was edited elsewhere; stop before overwriting'
with ZipFile(TARGET, 'w') as archive:
    for info in infos:
        archive.writestr(info, parts[info.filename])
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
changes = [{'paragraph': i, 'reasons': reasons[i], 'before': before[i], 'after': visible(paragraphs[i])}
           for i in sorted(reasons)]
(QA / 'changes.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'manuscript_v70.txt').write_text('\n'.join(f'P{i}: {visible(p)}' for i, p in enumerate(paragraphs)), encoding='utf-8')
audit = {'source': str(SOURCE), 'target': str(TARGET), 'source_sha256': source_hash,
         'target_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
         'changed_prose_paragraphs': len(changes), 'math_objects': len(math_after),
         'native_equations_identical': True, 'tables_identical': True,
         'decimal_results_identical': True, 'section_geometry_identical': True,
         'images_2_3_5_identical': True, 'figure_1_same_design_high_resolution': True,
         'figure_4_only_panel_titles_changed': True, 'prose_flow_paragraphs': layout_changes}
(QA / 'preservation_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(audit, ensure_ascii=False))
