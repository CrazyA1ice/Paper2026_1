# 第二阶段论文图表数据源（v2）

本目录是第二阶段论文重构的唯一图表源数据目录。旧目录 `abilene_forecasting/paper_figures/source_data/` 继续保留历史频域实验和旧版论文图表证据，但新版投稿论文不再从旧目录取数。

## 数据源优先级

1. 核心逐次结果：`abilene_forecasting/results/core_v2_summary.csv`
2. 8 种子汇总复核：`abilene_forecasting/results/ablation_mean_std.csv`
3. GÉANT 数据来源与预处理：`abilene_forecasting/data/raw/tszoo/databases/GEANT/DATASET_SOURCE.md`
4. LightTS 来源与固定版本：`abilene_forecasting/external/lightts/README.md`

## 文件说明

### table1_datasets.csv

用于新版论文“表1 数据集与预测任务设置”。

包含 Abilene 与 GÉANT 的：
- 时间点数；
- 原始/有效变量数；
- 训练/验证/测试时间点；
- 训练/验证/测试滑动窗口数；
- 输入长度 96；
- 预测长度 24。

其中 GÉANT 原始为 529 维，去除恒定通道后使用 524 个有效变量。

### table2_external_baseline_3seeds.csv

用于新版论文“表2 外部模型公平比较”。

只使用所有模型共同拥有的随机种子 42、43、44，包含：
- DLinear；
- LightTS；
- AdaptiveMultiscale（本文方法）。

这样避免将 LightTS 的 3 次重复与核心模型的 8 次重复直接混合作统计比较。

### table3_core_8seeds.csv

用于新版论文“表3 8 随机种子核心模型结果”。

使用随机种子 42—49，包含：
- DLinear；
- FixedEqualMultiscale；
- AdaptiveMultiscale。

除均值和样本标准差外，还给出本文方法相对 DLinear、固定等权多尺度的 MSE/MAE 平均相对改善率。

### fig2_weight_pairing_8seeds.csv

用于新版“图2 固定等权—自适应配对结果”。

每个数据集、每个种子保存：
- fixed/adaptive MSE；
- adaptive - fixed 的差值；
- 相对改善率；
- fixed/adaptive MAE；
- MAE 差值及改善率；
- RMSE。

绘图必须保留所有种子，包括 GÉANT seed 43 等未改善运行，不得筛掉不利结果。

### build_source_data_v2.py

从 `results/core_v2_summary.csv` 自动重建 table2、table3 和 fig2 数据，并验证：
- 核心三模型在每个数据集均存在 seed 42—49；
- LightTS、DLinear、自适应多尺度均存在共同 seed 42—44。

表1包含数据集静态元数据，也由脚本统一输出。

## 新版论文禁止继续取数的旧项目

以下内容可以留在仓库用于研究过程追溯，但不得作为新版投稿论文主数据：
- `paper_figures/source_data/fig2_main_ablation.csv`
- `paper_figures/source_data/fig3_weight_ablation.csv`
- `paper_figures/source_data/fig4_frequency_sensitivity.csv`
- `results/recommended_analysis/`
- `results/frequency_sensitivity/`

特别禁止继续使用旧的 3 种子 4.06%、10.52%、3.95% 和 p=0.07401 作为新版结论。

## 数值解释边界

- 表2的统计重复数为 3。
- 表3和图2的核心统计重复数为 8。
- 两数据集平均结果支持自适应多尺度，但不能写成“所有随机种子均提升”。
- GÉANT 的自适应模型跨种子波动更大，应在正文讨论。
