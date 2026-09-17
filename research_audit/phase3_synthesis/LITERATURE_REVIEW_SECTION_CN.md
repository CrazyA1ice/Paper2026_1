# 论文综述部分（文献审计长版，已由压缩稿替代）

> 说明：本文件保留完整文献调查轨迹，不建议直接放入约 5000 字论文。1000 字以内的投稿用版本见 `research_audit/phase4_drafting/MANUSCRIPT_FRONT_HALF_CN.md` 中“1 相关工作”。

## 2 相关工作

### 2.1 网络流量预测研究

网络流量预测可根据历史观测估计未来链路、节点或源—目的节点对的流量，是容量规划、拥塞预警、路由优化和资源调度的重要基础。Lohrasbinasab等[1]将相关方法概括为统计预测、机器学习和深度学习路线；Wang等[2]进一步指出，蜂窝流量预测通常既要处理非线性时间依赖，也要考虑区域或基站之间的空间相关性。面向骨干网络，流量矩阵以源节点到目的节点的业务量描述网络状态。韦烜等[3]利用运营级IP网络的OD数据验证了流量矩阵直接预测对网络规划和运维的意义。

近年来，网络流量预测逐渐从单纯时间建模转向周期、尺度和时空关系的联合建模。王菁等[4]以动态扩散卷积和卷积交互模块提取ESnet流量的空间动态特征和时间特征；Lu等[5]在GEANT、Abilene和CERNET数据上利用分阶段特征交互与融合建模动态时空依赖；Qin等[6]则用图卷积和多头注意力显式描述网络拓扑及动态时间相关性。这类图模型能够利用拓扑先验，但结构和计算开销相对较大。另一类研究强调网络流量的周期性和多尺度性。Zhou等[7]针对物联网流量的多尺度、非线性和尺度依赖设计深层回声状态网络；Yang等[8]通过层次化平稳过程提取5G流量的多尺度稳定特征；唐文杰等[9]提出CycleLLH，通过周期整合和小型线性预测头增强网络流量周期特征的利用。这些研究说明，多时间尺度是通信网络流量中的真实建模需求，但现有方法多采用较复杂的循环、图或Transformer结构。

### 2.2 轻量多变量时间序列预测

在通用长序列预测中，Zeng等[10]发现简单线性模型在多个基准上可以超过复杂Transformer，并提出将序列分解为趋势项和余项后分别线性预测的DLinear。这一结果说明，模型复杂度不等同于预测精度，也为计算资源有限条件下选择轻量主干提供了依据。另一方面，iTransformer通过把变量作为标记来学习变量间相关性[11]，代表显式多变量关联建模路线。本文使用共享权重DLinear处理144维OD序列，重点研究时间尺度融合，不显式使用OD拓扑或变量注意力，因此其结论应限定为轻量时间建模效果，而不能解释为已经充分学习网络空间结构。

### 2.3 频域建模与多尺度自适应融合

频域方法通过傅里叶变换把时间序列表示为不同频率的幅值与相位。FEDformer将分解与频域模块结合，并指出若只保留低频，可能丢失与重要事件有关的变化[12]。FITS利用复数线性层进行频域插值，以较少参数完成预测[13]；FreTS则在频域通过MLP学习时间维和变量维依赖，强调频谱的全局视野与能量集中性质[14]。国内研究中，任烈弘等[15]利用DFT将序列划分为低频趋势、中频季节和高频余项并分别预测。上述工作证明频域表征具有建模价值，但并不意味着低通截断对所有数据均有益；保留比例需要通过验证数据和消融实验确定。

多尺度方法试图同时利用细粒度波动和粗粒度趋势。TimeMixer在多个下采样尺度上分解并混合季节和趋势信息，再融合多个预测器[16]；Pathformer利用不同尺度的分块和自适应路径，根据输入动态调整尺度特征的聚合[17]；TimesNet从频谱中发现多个主要周期并进行自适应聚合[18]。韩璐等[19]通过多种膨胀卷积感受野和双注意力融合多尺度特征；OneNet则从概念漂移角度动态组合时间依赖与变量依赖预测器[20]。这些研究共同说明固定单尺度或固定模型假设难以覆盖所有输入状态，但其自适应机制通常依赖注意力、强化学习或较深网络。

值得注意的是，Tang等[21]已经在蜂窝流量预测中结合频域MLP与多尺度注意力，用于提取网格化蜂窝业务的时空特征。这是与本文表面结构最接近的工作，但两者研究对象和实现不同：STMLP面向Milan蜂窝网格数据，以二维时空频域学习、季节—趋势分解、多尺度注意力和卷积前馈网络为核心；本文面向Abilene骨干网144维OD流量矩阵，以三个不同下采样尺度的DLinear专家为主干，并根据每个输入窗口的均值、标准差、末时刻均值和平均绝对差分产生样本级Softmax权重。潘金伟等[22]关于统计特征搜索的研究也表明，低维统计描述可为时序结构选择提供信息，但本文的统计量仅用于尺度路由而非模型搜索。

### 2.4 现有研究不足与本文定位

综上，在本次检索范围内，现有研究分别验证了网络流量的周期与时空依赖、频域表示、多尺度预测以及动态组合的有效性，但面向公开骨干网OD流量矩阵、以轻量线性专家实现样本级尺度加权并通过固定等权对照进行归因的研究仍较少。为此，本文不追求构建更复杂的通用模型，而是在DLinear基础上设置尺度1、2和4的预测专家，用窗口统计状态生成非负且和为1的尺度权重，并在CESNET TS-Zoo的Abilene数据上检验其相对单尺度和固定等权融合的误差变化。同时，本文将频域低通门控作为辅助敏感性模块，用不同频率保留比例考察平滑降噪与突发信息损失之间的权衡，而不预设频域处理必然带来精度提升。

## 参考文献（与正文编号对应）

[1] LOHRASBINASAB I, KESHAVARZ A, AMIN-NEJAD S, et al. From statistical- to machine learning-based network traffic prediction[J]. Transactions on Emerging Telecommunications Technologies, 2022, 33(4): e4394. DOI: 10.1002/ett.4394.

[2] WANG X, WANG Z, YANG K, et al. A survey on deep learning for cellular traffic prediction[J]. Intelligent Computing, 2024, 3: 0054. DOI: 10.34133/icomputing.0054.

[3] 韦烜, 刘志华, 李青, 等. 大型IP网络流量矩阵分析预测的探讨研究[J]. 系统工程与电子技术, 2024, 46(6): 2164-2173. DOI: 10.12305/j.issn.1001-506X.2024.06.35.

[4] 王菁, 文晓东, 王春枝. 基于动态扩散卷积交互图神经网络的网络流量预测[J]. 计算机应用研究, 2023, 40(1): 97-101. DOI: 10.19734/j.issn.1001-3695.2022.05.0255.

[5] LU Y, NING Q, HUANG L, et al. A network traffic prediction model based on reinforced staged feature interaction and fusion[J]. Computer Networks, 2023, 227: 109719. DOI: 10.1016/j.comnet.2023.109719.

[6] QIN L, GU H, WEI W, et al. Spatio-temporal communication network traffic prediction method based on graph neural network[J]. Information Sciences, 2024, 679: 121003. DOI: 10.1016/j.ins.2024.121003.

[7] ZHOU J, HAN T, XIAO F, et al. Multiscale network traffic prediction method based on deep echo-state network for Internet of Things[J]. IEEE Internet of Things Journal, 2022, 9(21): 21862-21874. DOI: 10.1109/JIOT.2022.3181807.

[8] YANG Y, GENG S, ZHANG B, et al. Long term 5G network traffic forecasting via modeling non-stationarity with deep learning[J]. Communications Engineering, 2023, 2: 33. DOI: 10.1038/s44172-023-00081-4.

[9] 唐文杰, 肖一磊, 孔祥宇, 等. CycleLLH：一种基于周期性整合的新型网络流量预测模型[J]. 计算机学报, 2024, 47(12): 2867-2888. DOI: 10.11897/SP.J.1016.2024.02867.

[10] ZENG A, CHEN M, ZHANG L, et al. Are transformers effective for time series forecasting?[C]//Proceedings of the AAAI Conference on Artificial Intelligence. 2023, 37(9): 11121-11128. DOI: 10.1609/aaai.v37i9.26317.

[11] LIU Y, HU T, ZHANG H, et al. iTransformer: inverted transformers are effective for time series forecasting[C]//International Conference on Learning Representations. 2024.

[12] ZHOU T, MA Z, WEN Q, et al. FEDformer: frequency enhanced decomposed transformer for long-term series forecasting[C]//Proceedings of the 39th International Conference on Machine Learning. 2022: 27268-27286.

[13] XU Z, ZENG A, XU Q. FITS: modeling time series with 10k parameters[C]//International Conference on Learning Representations. 2024.

[14] YI K, ZHANG Q, FAN W, et al. Frequency-domain MLPs are more effective learners in time series forecasting[C]//Advances in Neural Information Processing Systems. 2023, 36.

[15] 任烈弘, 黄铝文, 田旭, 等. 基于DFT的频率敏感双分支Transformer多变量长时间序列预测方法[J]. 计算机应用, 2024, 44(9): 2739-2746. DOI: 10.11772/j.issn.1001-9081.2023091320.

[16] WANG S, WU H, SHI X, et al. TimeMixer: decomposable multiscale mixing for time series forecasting[C]//International Conference on Learning Representations. 2024.

[17] CHEN P, ZHANG Y, CHENG Y, et al. Pathformer: multi-scale transformers with adaptive pathways for time series forecasting[C]//International Conference on Learning Representations. 2024.

[18] WU H, HU T, LIU Y, et al. TimesNet: temporal 2D-variation modeling for general time series analysis[C]//International Conference on Learning Representations. 2023.

[19] 韩璐, 霍纬纲, 张永会, 等. 基于多尺度特征融合与双注意力机制的多元时间序列预测[J]. 计算机工程, 2023, 49(9): 99-108. DOI: 10.19678/j.issn.1000-3428.0065846.

[20] ZHANG Y, WEN Q, WANG X, et al. OneNet: enhancing time series forecasting models under concept drift by online ensembling[C]//Advances in Neural Information Processing Systems. 2023, 36: 69949-69980. DOI: 10.52202/075280-3066.

[21] TANG C, LU J, YANG W, et al. A frequency-domain multilayer perceptron with multiscale attention network for cellular traffic prediction[J]. Computer Networks, 2025, 271: 111593. DOI: 10.1016/j.comnet.2025.111593.

[22] 潘金伟, 等. 基于统计特征搜索的多元时间序列预测方法[J]. 电子与信息学报, 2024, 46(8): 3276-3284. DOI: 10.11999/JEIT231264.

## 写作使用说明

- 本节约2200字，若整篇论文严格控制在5000字，可压缩2.1和2.3各约250字，保留2.4完整段落。
- 参考文献[5]、[12]、[21]是新增后最关键的三篇：分别对应Abilene直接证据、频域反证和最高相似先例。
- 引文编号需在整篇论文合并时重新排序；不要直接沿用到最终稿而不检查。
