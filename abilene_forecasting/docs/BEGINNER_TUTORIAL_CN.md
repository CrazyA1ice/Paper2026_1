# 从零复现 Abilene 网络流量多变量预测

## 1. 这个实验究竟在做什么

Abilene 是 Internet2 的骨干网络。网络中有多个节点，每隔一段时间记录各个起点到
终点（origin-destination, OD）之间的流量。把一个时刻的所有 OD 流量排成向量：

\[
$$
\mathbf{x}_t=[x_{t,1},x_{t,2},\ldots,x_{t,C}]\in\mathbb{R}^{C}.
$$
\]

其中，\(t\) 是时间，\(C\) 是 OD 通道数。连续 \(L\) 个历史时刻组成输入：

\[
$$
\mathbf{X}_t=[\mathbf{x}_{t-L+1},\ldots,\mathbf{x}_t]
\in\mathbb{R}^{L\times C}.
$$
\]

任务是根据它预测未来 \(H\) 个时刻：

\[
$$
\widehat{\mathbf{Y}}_t=f_\theta(\mathbf{X}_t)
\in\mathbb{R}^{H\times C}.
$$
\]

本项目默认 \(L=96\)、\(H=24\)、数据粒度为 1 小时。直观上就是“观察过去 4 天，
预测未来 1 天”。这叫多变量、多步时间序列预测。

## 2. 路线与原论文的对应关系

这不是某一篇顶会论文的逐行复现，而是四条公开路线的轻量组合：

1. **数据层**：CESNET TS-Zoo 负责下载和读取 Abilene。
2. **主干层**：DLinear（AAAI 2023）把序列分成趋势和季节/残差，再分别线性预测。
3. **频域层**：借鉴 FITS（ICLR 2024 Spotlight）的 RFFT、低频保留和频域学习思想。
4. **尺度层**：借鉴 Pathformer（ICLR 2024）的“多个时间尺度专家 + 输入相关路由”，
   但把完整 Transformer 专家和 noisy top-k 路由换成小型 DLinear 专家和 softmax 权重。

因此，最接近的两篇顶会论文是 FITS 和 Pathformer；DLinear 是为 GTX 1060 选择的
低成本主干。TimeMixer/TimeMixer++ 是相关思想来源，但本项目没有照搬其模块。

## 3. Windows 环境安装

本机已经检测到 Python 3.11.9、GTX 1060 6GB、NVIDIA 驱动 528.92。当前 Python
环境没有安装 PyTorch。推荐建立隔离环境，避免破坏其他软件。

在 PowerShell 中进入项目：

```powershell
cd C:\Users\Quant\Desktop\Paper2026_1\abilene_forecasting
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

GTX 1060 属于 Pascal 架构。为了保留对旧显卡的支持并兼容现有驱动，教程固定使用
PyTorch 2.5.1 的 CUDA 11.8 安装包，而不追随最新 CUDA 构建：

```powershell
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

验证显卡：

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

如果第二行是 `True`，说明训练会使用显卡。若为 `False`，先不要继续完整实验。

## 4. 获取与处理 Abilene

执行：

```powershell
python prepare_abilene.py
```

脚本通过 CESNET TS-Zoo 下载 1 小时聚合的真实 OD 矩阵，并读取
`matrix_realOD`，不使用重力模型估算矩阵。原始矩阵形状大致为：

\[
$$
\text{时间点}\times\text{源节点}\times\text{目的节点}.
$$
\]

随后把后两维展平：

\[
$$
\mathbf{X}\in\mathbb{R}^{T\times N\times N}
\longrightarrow
\mathbf{X}'\in\mathbb{R}^{T\times C},\quad C=N^2.
$$
\]

源节点等于目的节点的通道通常恒为零。脚本只利用训练集计算标准差，并删除训练期
间恒定的通道，避免大量零值人为降低误差。

### 4.1 为什么先做 log1p

网络流量通常右偏：大多数时刻流量较小，少数峰值很大。脚本先变换：

\[
$$
x'_{t,c}=\log(1+x_{t,c}).
$$
\]

它压缩极端峰值，同时 \(x=0\) 时仍有 \(x'=0\)。

### 4.2 为什么只能用训练集计算均值和标准差

对每个通道计算：

\[
$$
\mu_c=\frac{1}{T_{\mathrm{train}}}\sum_{t\in\mathrm{train}}x'_{t,c},
$$
\]

\[
$$
\sigma_c=\sqrt{\frac{1}{T_{\mathrm{train}}}
\sum_{t\in\mathrm{train}}(x'_{t,c}-\mu_c)^2},
$$
\]

\[
$$
z_{t,c}=\frac{x'_{t,c}-\mu_c}{\sigma_c}.
$$
\]

验证集和测试集只能使用训练集的 \(
$$
\mu_c,\sigma_c
$$
\)。若用全数据计算，测试集信息
会提前进入模型，这叫数据泄漏。

### 4.3 时间划分

数据按时间顺序划分为 60%/20%/20%：

```text
过去 ------------------------------> 未来
训练集 60% | 验证集 20% | 测试集 20%
```

训练集拟合参数，验证集选择训练轮次，测试集只做最终评价。时序数据不能随机打乱后
再切分，否则模型会在训练时看到“未来”。训练集内部的窗口可以打乱。

处理后的文件是 `data/processed/abilene_1hour.npz`。

## 5. 滑动窗口是什么

假设序列为 \(x_1,x_2,\ldots,x_T\)，输入长度 \(L=4\)，预测长度 \(H=2\)：

```text
样本1: [x1 x2 x3 x4] -> [x5 x6]
样本2: [x2 x3 x4 x5] -> [x6 x7]
样本3: [x3 x4 x5 x6] -> [x7 x8]
```

这就是 `SlidingWindowDataset` 的作用。每次移动一个时刻，可以从一条长序列制造
许多监督学习样本。

## 6. DLinear 公式与含义

首先用长度为 \(K\) 的移动平均提取趋势：

\[
$$
\mathbf{T}_t=\operatorname{AvgPool}_K(\mathbf{X}_t).
$$
\]

剩余部分定义为季节/残差：

\[
$$
\mathbf{S}_t=\mathbf{X}_t-\mathbf{T}_t.
$$
\]

然后分别用线性映射把历史长度 \(L\) 映射成未来长度 \(H\)：

\[
$$
\widehat{\mathbf{Y}}^{(T)}=\mathbf{W}_T\mathbf{T}+\mathbf{b}_T,
$$
\]

\[
$$
\widehat{\mathbf{Y}}^{(S)}=\mathbf{W}_S\mathbf{S}+\mathbf{b}_S,
$$
\]

\[
$$
\widehat{\mathbf{Y}}=
\widehat{\mathbf{Y}}^{(T)}+\widehat{\mathbf{Y}}^{(S)}.
$$
\]

直观解释：缓慢变化的基线由趋势分支预测，短期波动由残差分支预测。项目采用通道
共享权重，即所有 OD 流共享 \(
$$
\mathbf W_T,\mathbf W_S
$$
\)，显著减少参数量。

## 7. FITS 频域模块

### 7.1 离散傅里叶变换

对一个通道长度为 \(L\) 的序列：

\[
$$
X_k=\sum_{n=0}^{L-1}x_n e^{-j2\pi kn/L}.
$$
\]

\(X_k\) 是复数，模长表示该频率有多强，相位表示波峰在时间轴上的位置。低频对应
日常基线、昼夜或周周期，高频更多表示快速变化和噪声。

实数序列的频谱具有共轭对称性，所以代码使用 `torch.fft.rfft`，只保留
\(L/2+1\) 个非重复频率。

### 7.2 原始 FITS 基线

FITS 先进行实例归一化，截取前 \(K_f\) 个低频：

\[
$$
\mathbf{Z}=\operatorname{RFFT}(\widetilde{\mathbf X})_{0:K_f}.
$$
\]

再用复数线性层把输入频谱映射到“历史+未来”的频谱长度：

\[
$$
\widehat{\mathbf Z}=\mathbf W_f\mathbf Z+\mathbf b_f.
$$
\]

补零后逆变换：

\[
$$
\widehat{\mathbf X\mathbf Y}
=\operatorname{IRFFT}(\operatorname{Pad}(\widehat{\mathbf Z})).
$$
\]

最后取末尾 \(H\) 步作为预测。本项目中的 `fits` 用来复现这一基本思想。

### 7.3 本文组合中的频域块

为了与 DLinear 和多个尺度组合，`dlinear_freq`/`proposed` 不直接在频域产生未来，
而是先生成去噪后的历史。保留频率的门控为：

\[
$$
g_k=\sigma(a_k),\qquad
\widetilde Z_k=g_k Z_k,\quad k<K_f,
$$
\]

\[
$$
\widetilde Z_k=0,\quad k\ge K_f.
$$
\]

然后：

\[
$$
\widetilde{\mathbf X}=\operatorname{IRFFT}(\widetilde{\mathbf Z}).
$$
\]

\(a_k\) 是训练得到的参数，sigmoid 把权重限制在 0 到 1。其意义是让模型自己决定
某个低频周期应该保留多少，而不是把所有保留频率同等对待。

## 8. 多尺度与自适应权重

使用尺度集合：

\[
$$
\mathcal S=\{1,2,4\}.
$$
\]

尺度 1 查看原始小时序列，尺度 2 每两个小时平均一次，尺度 4 每四小时平均一次：

\[
$$
\mathbf X^{(s)}=operatorname{AvgPool}_s(\mathbf X).
$$
\]

每个尺度有一个轻量 DLinear 专家：

\[
$$
\widehat{\mathbf Y}^{(s)}=f_s(\mathbf X^{(s)}).
$$
\]

路由器从输入提取四个统计量：整体均值、标准差、最后时刻均值、平均绝对变化量，
得到尺度得分 \(q_s\)，再归一化：

\[
$$
\alpha_s=\frac{e^{q_s}}{\sum_{r\in\mathcal S}e^{q_r}}.
$$
\]

最终预测：

\[
$$
\widehat{\mathbf Y}=
\sum_{s\in\mathcal S}\alpha_s\widehat{\mathbf Y}^{(s)}.
$$
\]

因为 \(\alpha_s\) 由当前样本生成，所以工作日高峰、周末低谷、突发变化可以选择不同
的尺度组合。这是对 Pathformer 路由思想的低显存简化，不是 Pathformer 原始 AMS。

## 9. 损失函数和评价指标

训练最小化均方误差：

\[
$$
\mathcal L_{\mathrm{MSE}}
=\frac{1}{BHC}\sum_{b=1}^{B}\sum_{h=1}^{H}\sum_{c=1}^{C}
(y_{b,h,c}-\hat y_{b,h,c})^2.
$$
\]

MSE 对较大的错误惩罚更强。评价同时报告：

\[
$$
\mathrm{MAE}=\frac{1}{N}\sum_i|y_i-\hat y_i|,
$$
\]

\[
$$
\mathrm{RMSE}=\sqrt{\frac{1}{N}\sum_i(y_i-\hat y_i)^2}.
$$
\]

脚本同时报告标准化空间和还原到原流量空间后的结果。模型比较以标准化空间为主，
原始空间指标用于解释实际误差大小。

## 10. 第一次训练：只跑两轮

先运行最简单模型：

```powershell
python train.py --model dlinear --epochs 2 --batch-size 16
```

屏幕将显示：

```text
epoch=001 train_mse=... val_mse=...
epoch=002 train_mse=... val_mse=...
```

这次不追求准确率，只检查数据、显卡、前向传播、反向传播和文件保存能否完成。然后
检查组合模型：

```powershell
python train.py --model proposed --epochs 2 --batch-size 16
```

如果出现 CUDA out of memory，把 `--batch-size 16` 改成 8，再不够就改成 4。GTX
1060 没有 Tensor Core，本项目坚持 float32，不使用混合精度。

## 11. 正式消融实验

五个变体的逻辑如下：

| 模型 | 频域 | 多尺度 | 自适应权重 | 回答的问题 |
|---|---:|---:|---:|---|
| `dlinear` | 否 | 否 | 否 | 最简单主干能达到多少 |
| `fits` | 是 | 否 | 否 | 原始频率插值基线如何 |
| `dlinear_freq` | 是 | 否 | 否 | 频域预处理单独是否有效 |
| `dlinear_scale` | 否 | 是 | 是 | 尺度路由单独是否有效 |
| `proposed` | 是 | 是 | 是 | 两部分组合是否进一步有效 |

第一次正式实验可逐条运行：

```powershell
python train.py --model dlinear --seed 42 --epochs 30
python train.py --model fits --seed 42 --epochs 30
python train.py --model dlinear_freq --seed 42 --epochs 30
python train.py --model dlinear_scale --seed 42 --epochs 30
python train.py --model proposed --seed 42 --epochs 30
```

确认一轮没有异常后，运行三个随机种子：

```powershell
.\run_ablation.ps1
```

最后汇总：

```powershell
python summarize.py
```

论文主表应报告 `mean ± std`，不能只挑最好的一次结果。

## 12. 怎样判断结果是否支持方法

只有同时看到下面的证据，才能说组合“有效”：

1. `dlinear_freq` 优于 `dlinear`：支持频域块有贡献。
2. `dlinear_scale` 优于 `dlinear`：支持尺度路由有贡献。
3. `proposed` 优于两个单模块变体：支持二者存在互补性。
4. 三个随机种子的均值改善，且标准差没有大到覆盖改善。
5. 参数量和训练时间增长可接受。

若只满足第 3 条，可能只是随机波动；若 proposed 只比 DLinear 好、却不比单模块好，
则不能声称两个模块互补。

## 13. 相比原论文可以写成什么创新

### 与 FITS 相比

FITS 是单尺度频率插值，直接从历史频谱产生扩展频谱。本项目候选差异为：

- 在多个时间尺度上分别进行可学习低频门控；
- 频域块负责抑制噪声，DLinear 负责外推趋势与残差；
- 面向网络 OD 流量，而不是主要使用电力、天气、道路交通等通用基准。

### 与 Pathformer 相比

Pathformer 使用多尺度 Transformer 专家和 noisy top-k 路由。本项目候选差异为：

- 用三个 DLinear 专家替代注意力专家，适合 6GB 显存；
- 用连续 softmax 权重保留所有尺度，而不是稀疏 top-k；
- 路由依据可解释统计量，能够分析不同网络状态下的尺度偏好；
- 在每个尺度进入专家前加入频域去噪。

### 必须诚实限定

“把频域和多尺度组合”本身不能自动构成创新，TimeMixer++ 等工作已经研究多尺度时频
建模。正式论文应把贡献限定为：**面向通信流量的轻量、可解释、低算力自适应频域多
尺度预测**，并用参数量、速度、路由权重和消融结果证明。是否具有严格学术新颖性，
仍需在定稿前做更全面的同类检索，不能仅凭当前几篇论文下结论。

## 14. 后续正式论文还需要补什么

当前代码是第一阶段教学与机制验证。投稿前至少补充：

1. 预测长度 6、12、24、48 小时；
2. 第二个通信数据集，例如 GÉANT 或 CESNET-AGG23；
3. 三到五个随机种子；
4. 固定平均尺度权重与自适应权重的直接比较；
5. 不同尺度集合和截止频率的敏感性实验；
6. 参数量、训练时间和推理时间；
7. 至少一种配对统计检验和效应量；
8. 路由权重可视化及工作日/周末解释。

只有 Abilene 一个数据集和一个预测长度，适合学习，但还不足以支撑正式投稿。

## 15. 官方来源

- CESNET TS-Zoo：https://github.com/CESNET/cesnet-tszoo
- Abilene 说明：https://cesnet.github.io/cesnet-tszoo/datasets_overview/
- FITS：https://github.com/VEWOXIC/FITS
- Pathformer：https://github.com/decisionintelligence/pathformer
- DLinear：https://github.com/cure-lab/LTSF-Linear
