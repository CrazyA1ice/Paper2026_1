# 图1代码重绘方案

使用 Python / matplotlib 从零绘制，图内没有嵌入生成式图片。

| 方案 | 配色 |
| --- | --- |
| A_grayscale | 黑灰白，融合区采用浅灰底 |
| B_pale_blue | 黑灰白为主，融合区采用低饱和浅蓝灰底 |
| C_pale_sage | 黑灰白为主，路由区采用低饱和浅灰绿底 |

三个方案的结构、文字和尺寸相同。专家组与内部详图采用连续曲边外框；专家卡片下边缘到内部详图上边缘的过渡为3 mm。详图到路由区间隔为3 mm。画布为180 × 110 mm。

每版包含600 dpi PNG、PDF、保留文本的SVG，以及LZW压缩TIFF。PDF字号与碰撞检查结果在对应JSON中；单一整体流程图的面板对齐检查记为不适用。

`build_fig1.py` 是全部图形与文字的源代码。小曲线、输入矩阵与权重条均为机制示意，不是实验结果；统计向量沿用论文的μ_n、σ_n、ℓ_n、d_n。论文文件尚未修改。

在项目根目录运行：

```powershell
$env:MPLCONFIGDIR = Join-Path (Get-Location).Path '.mplconfig'
python .\paper_figures\fig1_code_options_20261002\build_fig1.py
```
