# 图1：黑色边框三版方案

依据用户上传的 codex-clipboard-c85a1826-4c47-4228-a096-35cf1aa4107e.png，用 Python/matplotlib 绘制。正文文字与公式保持原图内容；没有在图内新增解释或脚注。

| 版本 | 配色 |
| --- | --- |
| A_black_gray | 黑色边框、灰色箭头与曲线，融合区浅灰 |
| B_black_blue | 黑色边框，融合区低饱和浅蓝灰，专家展开区域近白色 |
| C_black_sage | 黑色边框，融合区低饱和浅灰绿，路由区浅灰 |

三版结构与文字一致。专家卡片下缘至内部详图上缘的曲边过渡压缩至约3 mm，详图与路由区间距3 mm；保留外框、曲线展开、完整DLinear内部和窗口路由结构。画布180 × 110 mm。

每版导出600 dpi PNG、SVG、PDF、LZW TIFF。绘图采用可编辑的文字与矢量组件，无嵌入式生成图片。输入矩阵、小曲线和权重色条为机制示意，不是实验数据。

运行方式（项目根目录）：

```powershell
$env:MPLCONFIGDIR = Join-Path (Get-Location).Path '.mplconfig'
python .\paper_figures\fig1_blackborder_options_20261002\build_fig1.py
```

导出时检查文字裁切、文字相互重叠、PDF公式最小字形和图形碰撞。结果保存在qa_summary.json及各版本的审计JSON中。论文文件尚未修改。
