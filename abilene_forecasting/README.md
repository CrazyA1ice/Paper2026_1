# Abilene 轻量多变量时间序列预测

这是面向 Windows + 6GB GTX 1060 的最小可复现实验工程。建议第一次使用时，按
[新手教程](docs/BEGINNER_TUTORIAL_CN.md)逐步操作，不要直接运行全部消融实验。

项目包含七个模型：

| 名称 | 作用 |
|---|---|
| `dlinear` | 最小基线 |
| `fits` | FITS 频率插值基线 |
| `dlinear_freq` | DLinear + FITS 风格频域滤波 |
| `dlinear_scale` | DLinear + 自适应多尺度融合 |
| `dlinear_scale_static` | DLinear + 固定等权多尺度融合 |
| `proposed` | 频域滤波 + 自适应多尺度融合 + DLinear |
| `proposed_static` | 频域滤波 + 固定等权多尺度融合 + DLinear |

快速命令（需先按教程安装环境）：

```powershell
python prepare_abilene.py
python train.py --model dlinear --epochs 2
python train.py --model proposed --epochs 2
```

确认冒烟实验无误后，才运行完整的 3 随机种子消融：

```powershell
.\run_ablation.ps1
```

结果保存在 `results/<模型名>_seed<随机种子>/`，汇总表为：

- `results/ablation_summary.csv`
- `results/ablation_mean_std.csv`

推荐实验与论文准备材料：

```powershell
.\run_recommended_experiments.ps1
.\run_final_cut075_weight_ablation.ps1
python analyze_recommended.py
```

- `docs/FORMAL_ABLATION_REPORT_CN.md`：正式消融与统计报告。
- `docs/PAPER_WRITING_INPUT_CN.md`：供后续论文写作使用的完整事实材料。
- `results/recommended_analysis/`：逐次结果、均值/标准差及配对检验。
