# 自适应多尺度网络流量预测文献检索报告

## 检索范围

- 时间：2022—2026；另保留2篇正式刊期为2022但Crossref在线日期记为2021的综述/基准文献。
- 中文主题：网络流量预测、多元时间序列、多尺度特征、自适应融合、频域分解、流量矩阵。
- 英文主题：network traffic forecasting、multivariate time-series forecasting、multi-scale、adaptive weighting/pathways、frequency domain、decomposition。
- 中文来源：CNKI、万方、维普可定位记录及期刊官网交叉核验。
- 英文来源：AAAI、ICLR、IEEE、Nature Portfolio、Elsevier、Wiley等正式论文页面及Crossref元数据。
- 去重规则：优先按DOI，缺少DOI时按规范化题名与第一作者。

## 与本研究最直接相关的中文文献

1. 唐文杰等. CycleLLH：一种基于周期性整合的新型网络流量预测模型. 计算机学报, 2024. DOI: 10.11897/SP.J.1016.2024.02867。直接说明网络流量周期性、长回溯窗口和轻量线性头。
2. 王菁等. 基于动态扩散卷积交互图神经网络的网络流量预测. 计算机应用研究, 2023, 40(1): 97-101. DOI: 10.19734/j.issn.1001-3695.2022.05.0255。使用ESnet数据，适合说明网络流量的时空依赖。
3. 何迎利等. 基于局部信息增强注意力机制的网络流量预测. 科学技术与工程, 2023, 23(30): 13014-13022. DOI: 10.12404/j.issn.1671-1815.2023.23.30.13014。适合支持动态注意力和局部波动建模。
4. 韦烜等. 大型IP网络流量矩阵分析预测的探讨研究. 系统工程与电子技术, 2024, 46(6): 2164-2173. DOI: 10.12305/j.issn.1001-506X.2024.06.35。与本文OD流量矩阵应用场景最接近。
5. 韩璐等. 基于多尺度特征融合与双注意力机制的多元时间序列预测. 计算机工程, 2023, 49(9): 99-108. DOI: 10.19678/j.issn.1000-3428.0065846。与“多尺度+自适应重要性”最直接相关。
6. 任烈弘等. 基于DFT的频率敏感双分支Transformer多变量长时间序列预测方法. 计算机应用, 2024. DOI: 10.11772/j.issn.1001-9081.2023091320。与本文频率保留比例实验直接相关。
7. 范艺扬等. 基于分解和频域特征提取的多变量长时间序列预测模型. 计算机应用, 2024。用于频域分解、趋势和周期特征相关论述。
8. 潘金伟等. 基于统计特征搜索的多元时间序列预测方法. 电子与信息学报, 2024, 46(8): 3276-3284. DOI: 10.11999/JEIT231264。与本文利用均值、标准差和差分构造路由特征相关。
9. 张晗. 用于多元时间序列预测的图神经网络模型. 浙江大学学报（工学版）, 2024, 58(12): 2500-2509. DOI: 10.3785/j.issn.1008-973X.2024.12.009。用于说明多变量相关性建模路线。

## 与本研究最直接相关的英文文献

1. Zeng A, et al. Are Transformers Effective for Time Series Forecasting? AAAI, 2023. DOI: 10.1609/aaai.v37i9.26317。DLinear来源，是本文预测主干的直接依据。
2. Xu Z, et al. FITS: Modeling Time Series with 10k Parameters. ICLR, 2024。本文频域处理路线的直接来源。
3. Chen P, et al. Pathformer: Multi-scale Transformers with Adaptive Pathways for Time Series Forecasting. ICLR, 2024。本文自适应尺度路由思想的直接来源。
4. Yi K, et al. Frequency-domain MLPs are More Effective Learners in Time Series Forecasting. NeurIPS, 2023。为频域多变量预测提供依据。
5. Wang S, et al. TimeMixer: Decomposable Multiscale Mixing for Time Series Forecasting. ICLR, 2024。为多尺度分解和混合提供依据。
6. Liu Y, et al. iTransformer: Inverted Transformers Are Effective for Time Series Forecasting. ICLR, 2024。为多变量相关性建模提供对比路线。
7. Zhou J, et al. Multiscale Network Traffic Prediction Method Based on Deep Echo-State Network for Internet of Things. IEEE Internet of Things Journal, 2022, 9(21): 21862-21874. DOI: 10.1109/JIOT.2022.3181807。与“多尺度网络流量预测”最直接相关。
8. Yang Y, et al. Long Term 5G Network Traffic Forecasting via Modeling Non-stationarity with Deep Learning. Communications Engineering, 2023, 2. DOI: 10.1038/s44172-023-00081-4。支持网络流量非平稳性、多尺度稳定特征和资源规划应用。
9. Nan H, et al. An Efficient Data-Driven Traffic Prediction Framework for Network Digital Twin. IEEE Network, 2024, 38(1): 22-29. DOI: 10.1109/MNET.2023.3335952。支持预测在网络数字孪生、优化和管理中的作用。
10. Wu J, et al. Network Traffic Prediction Based on a CNN-LSTM with Attention Mechanism. ICCIA, 2022: 205-209. DOI: 10.1109/ICCIA55271.2022.9828411。用于说明CNN-LSTM及注意力网络流量预测路线。
11. Jiang W. Internet Traffic Prediction with Deep Neural Networks. Internet Technology Letters, 2022, 5(2): e314. DOI: 10.1002/itl2.314。用于深度预测基线和网络资源管理背景。
12. Lohrasbinasab I, et al. From Statistical- to Machine Learning-Based Network Traffic Prediction. Transactions on Emerging Telecommunications Technologies, 2022, 33(4): e4394. DOI: 10.1002/ett.4394。用于相关工作综述和方法分类。
13. Hou M, et al. Parallel Multi-Scale Dynamic Graph Neural Network for Multivariate Time Series Forecasting. Pattern Recognition, 2025, 158: 111037. DOI: 10.1016/j.patcog.2024.111037。用于多尺度动态图与本文轻量路线比较。
14. Tian R, et al. Multi-scale Spatial-temporal Aware Transformer for Traffic Prediction. Information Sciences, 2023, 648: 119557. DOI: 10.1016/j.ins.2023.119557。用于多尺度预测的一般理论支持。
15. Nie L, et al. Digital Twin for Transportation Big Data: A Reinforcement Learning-Based Network Traffic Prediction Approach. IEEE TITS, 2024, 25(1): 896-906. DOI: 10.1109/TITS.2022.3232518。属于扩展应用背景，相关性低于前14篇。
16. Wang S, et al. TimeMixer++: A General Time Series Pattern Machine for Universal Predictive Analysis. 2025。用于了解最新多尺度通用模型，不作为本文必须复现的基线。

## 推荐优先阅读顺序

1. DLinear → 理解本文主干。
2. FITS → 理解FFT、低频保留和轻量频域建模。
3. Pathformer → 理解多尺度和自适应路由。
4. CycleLLH → 理解网络流量的周期特性及中文论文写法。
5. IEEE IoT Journal 2022多尺度网络流量预测 → 建立与英文网络流量研究的直接联系。
6. 大型IP网络流量矩阵分析预测 → 对接Abilene OD矩阵应用场景。
7. FFANet与两篇中文频域论文 → 写相关工作和方法差异。

## Zotero状态

- 目标分类：`2026Paper1时间序列`。
- 已存在：FITS、FreTS、Pathformer、TimeMixer、TimeMixer++、iTransformer。
- 本次新增：10篇英文题录、9篇中文题录。
- 已发现1个重复条目：中文DFT双分支Transformer论文因Zotero导入接口超时后实际已写入，又被导入一次。后续应在Zotero中保留题录较完整的一条。
- PDF下载范围：用户明确要求“不要SI”，因此只处理论文正文，不下载任何补充材料、补充数据或SI附件。
- 已下载并核验6篇核心英文正文PDF：DLinear、FITS、Pathformer、FreTS、TimeMixer、iTransformer。逐篇通过PDF文本抽取核验，页数依次为8、24、19、24、27、25页，均不是登录页、摘要页或损坏文件。
- 其余英文论文：Zotero题录中均保留DOI或正式论文页；IEEE、Elsevier、Wiley等非开放全文不绕过付费墙。Diviner/Nature正文的公开PDF地址已记录，但本机直连下载失败。
- 中文论文：题录中保留CNKI/万方/维普或期刊官网定位信息。由于当前未配置学校图书馆入口，也没有可复用的机构认证会话，未绕过权限下载中文全文。
- Zotero附件复核：DLinear、FITS、Pathformer、FreTS、TimeMixer和iTransformer共6篇核心英文论文的正文PDF均已关联到对应的已有条目，没有为关联PDF而新建重复题录。
- 新增附件键：DLinear=`TV9ZKQ8A`，Pathformer=`NAFAARKJ`，TimeMixer=`E7W5IN53`，iTransformer=`3H4FKE99`；FITS=`XS752PCH`，FreTS=`N53DI8NL`。

## 2026-09-13 深化检索补充

为服务论文综述和创新性核查，本轮新增7篇高相关文献：FEDformer、TimesNet、OneNet、RSTIF、FlowDiviner、蜂窝流量深度学习综述和STMLP。Zotero连接器在导入时返回超时，但逐题名复核确认7条均已写入目标分类。

其中最重要的新发现是Tang等发表于Computer Networks 2025的STMLP（DOI: 10.1016/j.comnet.2025.111593）。该文已将频域MLP与多尺度注意力用于蜂窝流量预测，因此本文不能使用“首次融合频域与多尺度”的表述。本文仍可成立的差异是：研究对象为Abilene骨干网OD矩阵；以尺度1/2/4的DLinear专家为主干；以四个窗口统计量产生样本级尺度权重；并通过固定等权模型作严格消融。

详细筛选、核验和可直接使用的综述文本见：

- `research_audit/phase2_investigation/LITERATURE_EVIDENCE_MATRIX_CN.md`
- `research_audit/phase2_investigation/SOURCE_VERIFICATION_REPORT_CN.md`
- `research_audit/phase3_synthesis/LITERATURE_REVIEW_SECTION_CN.md`
