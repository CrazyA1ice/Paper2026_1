# 图1：融合模块三种构图

以用户上传的 codex-clipboard-d7ae0e7a-a2cd-4cce-8e79-8bef0d7c60e9.png 为结构依据，使用Python/matplotlib生成。保留黑色边框与原有流程，局部修改融合模块、输入矩阵、Softmax色条及右侧虚线。

| 方案 | 融合模块组织 |
| --- | --- |
| A_compact_formula | 框外保留自适应加权融合标题；内部改为尺度预测加权、尺度集合和紧凑求和公式 |
| B_weighted_branches | 三个尺度的加权预测贡献汇入加号，下面保留紧凑融合与归一化公式 |
| C_weight_prediction | 每行显示尺度权重乘对应尺度预测，下面保留紧凑融合与归一化公式 |

共用修改：移除框内重复的“自适应加权融合”；求和公式按实际字形宽度排列；输入矩阵采用低饱和浅蓝灰；Softmax色块对应三个尺度，用蓝灰、灰绿、灰褐区分；右侧虚线从x=178.5 mm移至171.5 mm，离外框约7.6 mm。

新增的乘积与分支图只解释现有融合公式，没有增加新机制或实验结果。矩阵、小曲线与色条均为机制示意，不是实验数据。其他文字、DLinear展开和窗口路由流程保留。

每版导出600 dpi PNG、PDF、保留文字的SVG和LZW TIFF。PDF文字与碰撞检查保存在各版本的JSON文件中。论文尚未替换。

项目根目录运行：

```powershell
$env:MPLCONFIGDIR = Join-Path (Get-Location).Path '.mplconfig'
python .\paper_figures\fig1_fusion_options_20261002\build_fig1.py
```
