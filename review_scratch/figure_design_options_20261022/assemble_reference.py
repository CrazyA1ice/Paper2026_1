from pathlib import Path
from hashlib import sha256
import json
import sys

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.text import Text
from PIL import Image

QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/图2-4参考方案_20261022'
items=json.loads((QA/'exports.json').read_text(encoding='utf-8'))
assert len(items)==9
titles={'A':('A　紧凑矩阵','集中比较降幅与数值，适合压缩篇幅'),
        'B':('B　误差平面','同时观察两个误差指标及模型间的位置'),
        'C':('C　配对小倍图','分别观察指标，再呈现每次配对变化')}
descriptions={
'A2':'图2　多基线增益矩阵', 'A3':'图3　高需求配对增益矩阵', 'A4':'图4　绝对误差与增益联合矩阵',
'B2':'图2　MSE与MAE综合误差平面','B3':'图3　高需求双指标误差平面','B4':'图4　一周配对误差一致性平面',
'C2':'图2　基线归一化哑铃图','C3':'图3　高需求双指标小倍图','C4':'图4　一周逐种子配对小倍图'}
mpl.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','SimSun'],
    'font.size':8,'pdf.fonttype':42,'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white'})
book=OUT/'图2-4_三套方案对照册.pdf'
pages=[]
with PdfPages(book) as pdf:
    for suite in 'ABC':
        rows=sorted([r for r in items if r['suite']==suite],key=lambda r:r['figure'])
        width=160;height=sum(r['height_mm'] for r in rows)+45
        fig=plt.figure(figsize=(width/25.4,height/25.4))
        fig.text(11/width,(height-5)/height,titles[suite][0],fontsize=10,weight='bold',color='#247D91',va='center')
        fig.text(11/width,(height-11)/height,titles[suite][1],fontsize=8,va='center')
        cursor=height-17
        for row in rows:
            fig.text(11/width,cursor/height,descriptions[row['tag']],fontsize=8.5,va='center',color='#253943')
            h=row['height_mm']
            with Image.open(Path(row['prefix']).with_suffix('.png')) as im:
                ax=fig.add_axes([11/width,(cursor-4-h)/height,138/width,h/height])
                ax.imshow(im,aspect='auto',interpolation='none');ax.axis('off')
            cursor-=h+7
        assert cursor>=6
        fig.text(11/width,3/height,'参考方案，主稿未改；单图另存矢量版。±表示8次训练的样本标准差。',fontsize=7.5,va='center',color='#5F6F78')
        for t in fig.findobj(match=Text):
            t.set_fontfamily(['SimSun'] if any('\u4e00'<=c<='\u9fff' for c in t.get_text()) else ['Times New Roman'])
        fig.canvas.draw()
        stem={'A':'A_紧凑矩阵_总览','B':'B_误差平面_总览','C':'C_配对小倍图_总览'}[suite]
        fig.savefig(OUT/(stem+'.png'),dpi=180)
        fig.savefig(QA/(stem+'.pdf'),dpi=300)
        pdf.savefig(fig,dpi=300)
        pages.append(dict(suite=suite,path=str(OUT/(stem+'.png')),width_mm=width,height_mm=height))
        plt.close(fig)

notes='''# 图2—4参考方案

已制作三套、共九张参考图，全部沿用现有真实实验结果，主稿未改动。每套包含图2、图3、图4；可整套采用，也可分别选图。

## 怎么选

- A：紧凑矩阵。图2把对两个基线的MSE/MAE降幅放在同一矩阵；图3展开高需求配对降幅；图4同时给出绝对误差与相对降幅。适合迅速读数和控制篇幅。
- B：误差平面。图2、图3将两个指标放进同一坐标平面；图4用同一种子的对照误差与本文误差组成坐标，点位于等值线下方即表示本文误差较低。适合展示综合表现，需要读者理解二维坐标。
- C：配对小倍图。图2以对照=100作为统一标尺；图3将数据集和指标分开，减少标记重叠；图4保留全部逐种子连线，展示一周任务中的配对变化。适合突出实验依据。

优先推荐的混合组合：B的图2、C的图3、C的图4。这样依次回答“综合精度处于什么位置”“高需求点表现如何”“一周任务是否每次配对都降低”。若更重视快速读出百分比，图2可选A；若偏好统一的视觉形式，也可整套选C。

## 统一读图规则

使用随机种子42—49的全部8次训练结果。均值与±均为跨种子的均值及样本标准差；图中的误差线不是置信区间，图中不新增显著性检验。相对降幅先在相同种子下计算，再取均值，故不一定等于两组均值之比所得的降幅。

A套使用均值与标准差概括全部重复；B、C套保留种子点或配对连线。B套误差平面的双向误差线分别表示两项指标的样本标准差。C套图2对每个种子计算100×本文误差/对照误差，数值小于100表示该次本文误差较低；百分比仍为原配对平均降幅。

参数比例仅以对应LightTS配置为基准：Abilene为6.41%，GÉANT为2.17%。所有方案使用相同观测记录，没有为图形效果挑选种子。周预测包含4种对照×2项指标×8个种子，共64个配对比较。

## 文件

- 三套方案对照册：便于逐页浏览整体安排。
- A/B/C子文件夹：每张图均提供600 dpi PNG及可编辑PDF、SVG，单图宽138 mm、正文图字7.5 pt。
- 数据与说明子文件夹：原始指标及配对降幅CSV，供核对与后续修改使用。

本次仅输出参考图；选定方案后再调整主稿中的图注、说明和分页。
'''
(OUT/'方案说明与建议.md').write_text(notes,encoding='utf-8')
(QA/'boards.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(book=str(book),pages=pages),ensure_ascii=False))
