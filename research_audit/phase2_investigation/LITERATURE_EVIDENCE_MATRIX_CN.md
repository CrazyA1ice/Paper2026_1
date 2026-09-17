# 文献调查与证据矩阵

## 1. 检索边界

- 检索日期：2026-09-13。
- 主时间范围：2022—2026；保留正式刊期或在线发表在2021年、但对方法分类具有基础作用的少量文献。
- 中文检索概念：网络流量预测、流量矩阵、多变量时间序列、多尺度、自适应加权、频域、离散傅里叶变换。
- 英文检索概念：network traffic forecasting、traffic matrix prediction、multivariate time-series forecasting、multi-scale、adaptive weighting/pathways、frequency domain、decomposition。
- 来源优先级：期刊官网/正式会议页面/DOI元数据 > CNKI、万方、维普定位页 > 其他学术索引页。
- 纳入原则：能够直接解释网络流量任务、本文三个方法模块或实验结论边界；不因模型名称中含有“traffic”就纳入道路交通论文。
- 排除原则：只有交通运输含义而非通信网络流量、只有预印本且已有正式版本、与本文方法和应用均无直接关系。

## 2. 新增文献及理由

本轮在原有25篇不重复题录基础上补入7篇，形成32篇候选文献。新增条目已经导入Zotero分类“2026Paper1时间序列”。

| 文献 | 类型 | 与本文关系 | 纳入判断 |
|---|---|---|---|
| Zhou et al., FEDformer, ICML 2022 | 频域/分解 | 明确指出仅保留低频可能丢失与重要事件有关的变化，可解释本文cut ratio敏感性 | 核心反证 |
| Wu et al., TimesNet, ICLR 2023 | 多周期 | 由频谱发现主要周期并聚合多周期表征 | 方法背景 |
| Zhang et al., OneNet, NeurIPS 2023 | 动态组合 | 面向概念漂移动态组合两类预测器 | 邻近证据 |
| Lu et al., RSTIF, Computer Networks 2023 | 网络流量 | 在GEANT、Abilene和CERNET上融合动态时空特征 | 核心直接证据 |
| Qin et al., FlowDiviner, Information Sciences 2024 | 网络流量 | 显式利用拓扑图和注意力建模时空依赖 | 核心对照路线 |
| Wang et al., Intelligent Computing 2024 | 蜂窝流量综述 | 系统梳理数据、时序/时空模型、应用与挑战 | 核心综述 |
| Tang et al., STMLP, Computer Networks 2025 | 频域+多尺度流量预测 | 频域MLP和多尺度注意力用于蜂窝流量，是与题目最接近的现有工作 | 最高相关，必须讨论 |

## 3. 核心证据矩阵

相关性等级：A为直接决定本文研究定位；B为支撑具体方法模块；C为背景或对照。

| ID | 文献 | 等级 | 可支持的论断 | 不能据此声称 |
|---|---|---:|---|---|
| C1 | 唐文杰等，CycleLLH，计算机学报，2024 | A | 网络流量具有可利用的自然周期；长回溯窗口和轻量预测头具有价值 | 本文复现了CycleLLH或达到其六数据集结果 |
| C2 | 王菁等，DDCIGNN，计算机应用研究，2023 | A | 通信网络流量同时存在动态空间与时间依赖 | 本文显式使用了网络拓扑 |
| C3 | 何迎利等，局部信息增强注意力，2023 | B | 局部波动和动态注意力是网络流量预测的重要方向 | 注意力必然优于线性模型 |
| C4 | 韦烜等，大型IP网络流量矩阵分析预测，2024 | A | OD流量矩阵预测可服务网络规划和运维 | 运营商私有数据结果可直接迁移到Abilene |
| C5 | 韩璐等，FFANet，计算机工程，2023 | B | 不同感受野可提取多尺度特征并按重要性融合 | 其道路/通用Traffic数据等同于骨干网OD流量 |
| C6 | 任烈弘等，FSDformer，计算机应用，2024 | B | DFT可用于趋势、季节和余项分解及时频联合建模 | 低频截断在所有数据上都有益 |
| C7 | 范艺扬等，分解和频域特征提取，2024 | B | 分解与频域特征可作为多变量预测模块 | 本文采用了相同网络结构 |
| C8 | 潘金伟等，统计特征搜索，电子与信息学报，2024 | B | 简单统计特征可以指导时序模型设计 | 本文路由器等同于其搜索方法 |
| E1 | Zeng et al., DLinear, AAAI 2023 | A | 简单分解线性模型可成为强基线，复杂Transformer并非天然占优 | DLinear在任意数据集都最优 |
| E2 | Xu et al., FITS, ICLR 2024 | B | 复数频域插值可用极少参数完成预测 | 本文低通门控就是原始FITS |
| E3 | Chen et al., Pathformer, ICLR 2024 | A | 不同输入动态可能需要不同尺度路径和自适应聚合 | 本文实现了Pathformer的双注意力和路径机制 |
| E4 | Yi et al., FreTS, NeurIPS 2023 | B | 频域具有全局视野和能量集中性质，可在变量间及时间维学习 | 频域处理必然提升Abilene精度 |
| E5 | Wang et al., TimeMixer, ICLR 2024 | A | 细尺度和粗尺度分别包含微观与宏观信息，多预测器可形成互补 | 本文采用了其PDM/FMM结构 |
| E6 | Liu et al., iTransformer, ICLR 2024 | C | 变量标记可显式学习多变量相关性 | 本文DLinear共享权重显式建模了OD变量间关系 |
| E7 | Zhou et al., Deep ESN, IEEE IoTJ 2022 | A | 多尺度、非线性和尺度依赖是网络流量预测的直接问题 | 其IoT结论自动适用于Abilene全部场景 |
| E8 | Yang et al., Diviner, Communications Engineering 2023 | A | 非平稳网络流量包含多尺度稳定规律，预测可支持容量规划 | 本文完成了月级5G预测或在线部署 |
| E9 | Lu et al., RSTIF, Computer Networks 2023 | A | Abilene等流量矩阵可通过时空交互融合预测 | 本文轻量时序模型比图模型更强 |
| E10 | Qin et al., FlowDiviner, Information Sciences 2024 | A | 网络拓扑和动态图相关性是另一条强路线 | 本文无需拓扑仍具有普适优势 |
| E11 | Wang et al., cellular traffic survey, 2024 | A | 蜂窝流量预测常分时序与时空两类，应用包括资源分配、节能与优化 | 蜂窝网格流量与骨干网OD矩阵相同 |
| E12 | Zhou et al., FEDformer, ICML 2022 | A | 只丢弃高频可能损失重要事件信息，频率选择本身需要检验 | 本文已证明随机频率选择更优 |
| E13 | Wu et al., TimesNet, ICLR 2023 | B | 多周期可通过频域发现并自适应聚合 | 本文已识别Abilene的真实周期集合 |
| E14 | Zhang et al., OneNet, NeurIPS 2023 | B | 动态权重有助于组合具有不同假设的预测器 | 本文进行了在线学习或概念漂移适配 |
| E15 | Tang et al., STMLP, Computer Networks 2025 | A | 频域MLP和多尺度注意力已经用于蜂窝流量预测 | “首次将频域与多尺度用于网络流量” |

## 4. 来源核验结果

- 原有及新增英文文献中可用的DOI条目均通过Crossref或出版商页面核验，题名对应一致。
- 8条中文DOI未被Crossref收录，不能据此判为错误；已通过《计算机学报》《计算机应用研究》《科学技术与工程》《系统工程与电子技术》《计算机工程》《计算机应用》等期刊官方页面核对题名、作者、年份与DOI。
- FITS、Pathformer、TimeMixer、iTransformer、TimesNet等无常规期刊DOI的会议论文，以OpenReview正式接收页面核验；DLinear以AAAI官网核验；FreTS和OneNet以NeurIPS官网核验。
- 6篇原有核心英文正文PDF已核验为正式论文正文且已关联Zotero；本轮新增文献至少保留正式论文页或DOI链接，不包含SI。
- Zotero导入请求曾在客户端侧超时，但随后逐题名检索确认7条均已写入，条目键为：FEDformer `AAH5JCET`、TimesNet `79NN2VHS`、OneNet `RCYJIPGL`、RSTIF `J6MTLB9V`、FlowDiviner `676JK7BM`、蜂窝流量综述 `VQKBE3JI`、STMLP `FMKH8NDC`。

## 5. 调查阶段结论

1. 研究问题成立，但创新属于面向特定数据与计算约束的轻量组合创新，而非首次提出多尺度、动态加权或频域预测。
2. 最强的直接先例是STMLP；必须正面比较数据形态、预测主干和权重生成方式。
3. 文献同时支持并限制频域模块：FITS和FreTS说明频域表征有价值，FEDformer则说明简单低通可能丢失重要变化；这与本文频域消融未优于无频域模型的结果一致。
4. 图神经网络路线强调拓扑与变量关联；本文没有利用拓扑，优点是简单和参数少，代价是不能宣称充分建模空间依赖。
