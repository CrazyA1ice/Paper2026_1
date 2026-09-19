# 双数据集轻量多变量网络流量预测

这是面向 Windows + 6GB GTX 1060 的可复现实验工程。当前正式支持
CESNET TS-Zoo 的 **Abilene** 与 **GÉANT** 两个骨干网 OD 流量矩阵数据集。

## 模型

| 名称 | 作用 |
|---|---|
| `dlinear` | 最小基线 |
| `fits` | FITS 频率插值基线 |
| `lightts` | 外部轻量基线：THUML LightTS 固定版本适配 |
| `dlinear_freq` | DLinear + FITS 风格频域滤波 |
| `dlinear_scale` | DLinear + 自适应多尺度融合 |
| `dlinear_scale_static` | DLinear + 固定等权多尺度融合 |
| `proposed` | 频域滤波 + 自适应多尺度融合 + DLinear |
| `proposed_static` | 频域滤波 + 固定等权多尺度融合 + DLinear |

LightTS 源码固定到
`thuml/Time-Series-Library@4e938a1767106324dd753b2a44832bf870a0252e`。
上游 `models/LightTS.py` 原样放在 `external/lightts/models/LightTS.py`，
本仓库只通过 `src/lightts_adapter.py` 接入统一训练协议。上游许可证为 MIT。

当前 LightTS 适配配置使用官方默认 `d_model=512`、`dropout=0.1`，
以及模型默认 `chunk_size=24`。当 `input_len=96` 时无需额外补齐。

## 数据准备

统一入口：

```powershell
python prepare_dataset.py --dataset abilene
python prepare_dataset.py --dataset geant
```

兼容入口：

```powershell
python prepare_abilene.py
python prepare_geant.py
```

默认生成：

```text
data/processed/abilene_1hour.npz
data/processed/geant_1hour.npz
```

两套数据采用相同协议：按时间顺序 60%/20%/20% 划分，先做 `log1p`，
再仅使用训练集统计量按通道标准化。GÉANT 1 小时 Matrix 子集使用
`matrix_avg_bandwidth_kbps` 字段。

## 统一训练接口

Abilene：

```powershell
python train.py --dataset abilene --model dlinear_scale --seed 42 --input-len 96 --pred-len 24
```

GÉANT：

```powershell
python train.py --dataset geant --model dlinear_scale --seed 42 --input-len 96 --pred-len 24
```

LightTS 轻量外部基线冒烟测试：

```powershell
python train.py --dataset geant --model lightts --seed 42 --input-len 96 --pred-len 24 --epochs 2 --batch-size 16 --learning-rate 0.0001
```

Time-Series-Library 当前训练入口的默认优化设置为 Adam、MSE、
`learning_rate=0.0001`。正式实验应在冒烟测试后固定超参数，并对
Abilene/GÉANT 使用同一套 LightTS 设置。

## 结果目录

默认结构为：

```text
results/
  abilene/
    dlinear_scale_seed42/
      best_model.pt
      metrics.json
      predictions.npz
      router_weights.csv
  geant/
    lightts_seed42/
      best_model.pt
      metrics.json
      predictions.npz
```

`metrics.json` 同时记录 `dataset`、`data_path`、`n_channels`、
训练/验证/测试行数与窗口数、训练超参数以及外部模型配置，避免双数据集实验相互覆盖。

汇总指定实验根目录：

```powershell
python summarize.py --results results --output results/core_summary.csv
```

当给定目录中存在新的 `abilene/` 或 `geant/` 数据集子目录时，汇总脚本优先读取
新结构；否则兼容原有 `<model>_seed<seed>/metrics.json` 结构。

## 原有 Abilene 实验

原有消融、频率敏感性和权重消融结果仍保留在仓库中，不会被本次目录升级改写。
正式扩展实验建议先分别完成两个数据集的冒烟训练，再运行多随机种子比较。

- `docs/FORMAL_ABLATION_REPORT_CN.md`：原 Abilene 正式消融与统计报告。
- `docs/PAPER_WRITING_INPUT_CN.md`：原论文写作事实材料。
- `results/recommended_analysis/`：原 Abilene 逐次结果与统计分析。
