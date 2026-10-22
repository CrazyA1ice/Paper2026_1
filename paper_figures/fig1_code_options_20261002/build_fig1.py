"""Code-native method schematics. All miniature curves are mechanism illustrations."""
from pathlib import Path
import json
import sys
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch, Circle, Rectangle
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, 'C:/Users/Quant/.codex/skills/nature-figure/scripts')
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
from audit_panel_alignment import require_matplotlib_panel_alignment
from audit_pdf_text import audit_pdf as audit_text
from audit_figure_collisions import audit_pdf as audit_collisions

plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Microsoft YaHei', 'Arial'],
    'font.size': 8, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'mathtext.fontset': 'stix', 'axes.unicode_minus': False,
})

INK = '#2C2D2F'
GRAY = '#65686B'
EDGE = '#595D60'
LINE = '#74787C'
WIDTH, HEIGHT = 180, 110
STYLES = {
    'A_grayscale': dict(accent=EDGE, expert='white', fusion='#F3F3F3', router='white'),
    'B_pale_blue': dict(accent='#738492', expert='white', fusion='#EEF2F5', router='white'),
    'C_pale_sage': dict(accent='#7A887D', expert='white', fusion='white', router='#F0F4F0'),
}

# An explicit unitless sketch, not an experimental traffic record.
outline = np.array([.15,.3,.22,.4,.32,.5,.4,.35,.44,.6,.5,.57,
                    .42,.48,.61,.55,.65,.71,.6,.67,.58,.73,.77,.7])
RAW = np.repeat(outline, 4) + np.tile([-.035,.045,-.015,.005], len(outline))
TREND = np.array([.25,.29,.34,.4,.46,.51,.52,.5,.48,.5,.55,.59])
RESIDUAL = np.array([.4,.65,.35,.62,.32,.67,.4,.6,.36,.63,.4,.56])
PREDICTION = np.array([.2,.35,.3,.47,.4,.58,.64,.59])


def text(ax, x, y, value, size=8, bold=False, color=INK, ha='center'):
    return ax.text(x, y, value, fontsize=size, ha=ha, va='center', color=color,
                   fontweight='bold' if bold else 'normal', zorder=5)


def box(ax, x, y, w, h, fill='white', edge=EDGE, radius=.7):
    patch = FancyBboxPatch((x,y), w,h, boxstyle=f'round,pad=0,rounding_size={radius}',
                          facecolor=fill, edgecolor=edge, linewidth=.75, zorder=2)
    ax.add_patch(patch)
    return patch


def arrow(ax, points, dashed=False, color=LINE):
    style = (0,(3,2)) if dashed else '-'
    for a,b in zip(points[:-2], points[1:-1]):
        ax.plot([a[0],b[0]], [a[1],b[1]], color=color, linewidth=.75,
                linestyle=style, zorder=3)
    ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle='-|>',
                                mutation_scale=6.5, linewidth=.75, color=color,
                                linestyle=style, shrinkA=0, shrinkB=.65, zorder=3))


def curve(ax, x, y, w, h, values, dashed=False, points=False):
    values = np.asarray(values)
    scaled = (values - values.min()) / (values.max() - values.min())
    ax.plot(np.linspace(x,x+w,len(values)), y+scaled*h, color=GRAY, linewidth=.8,
            linestyle=(0,(2.2,1.5)) if dashed else '-',
            marker='o' if points else None, markersize=1.6, zorder=4)


def expert_outline(ax, fill):
    # The transition is only 3 mm high and contains no annotation or arrow.
    vertices = [(79,99),(114,99),(114,54),
                (114,51.5),(125,51),(134,51),
                (158,51),(158,23),(22,23),(22,51),(59,51),
                (69,51),(79,51.5),(79,54),(79,99)]
    codes = [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO,
             MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,
             MplPath.LINETO,MplPath.LINETO,MplPath.LINETO,MplPath.LINETO,MplPath.LINETO,
             MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(vertices,codes), facecolor=fill,
                           edgecolor='#929699', linewidth=.8, zorder=1))


def summation(ax, y, prediction=True):
    # Separate operator/index artists preserve editable, non-overlapping glyphs.
    if prediction:
        text(ax,126.5,y,r'$\hat Y=$',9.5)
    text(ax,134,y,'∑',13)
    text(ax,134,y-4,'s',6.5)
    text(ax,144.5,y,r'$\alpha_s\hat Y^{(s)}$' if prediction else r'$\alpha_s=1$',10)


def draw(style):
    fig = plt.figure(figsize=(7.08661417,4.33070866), facecolor='white')
    ax = fig.add_axes([0,0,1,1], xlim=(0,WIDTH), ylim=(0,HEIGHT))
    ax.axis('off')
    # One integrated schematic: its regions are not separate quantitative panels.
    for x,label in [(15.5,'历史输入'),(55.5,'多尺度构造'),(96.5,'独立尺度专家'),
                    (137,'自适应加权融合'),(169,'预测输出')]:
        text(ax,x,104,label,8.7,bold=True)

    expert_outline(ax, style['expert'])
    box(ax,3,59,25,38)
    for row in range(5):
        for col in range(6):
            shade = '#C8CBCF' if (row+2*col)%5==0 else '#E2E4E6'
            ax.add_patch(Rectangle((7+col*2.8,77+row*2.35),2.6,2.15,
                                   facecolor=shade,edgecolor='none',zorder=3))
    text(ax,15.5,70,r'$X\in\mathbb{R}^{96\times C}$',10)
    text(ax,15.5,63.5,'96步 · C变量',7.7)

    # Each scale enters one independent expert and produces its own prediction.
    ax.plot([28,31,31],[75,75,90], color=LINE, linewidth=.75, zorder=3)
    ax.plot([31,31],[60,90], color=LINE, linewidth=.75, zorder=3)
    for s,y,subtitle in [(1,90,'原始序列'),(2,75,'2点均值'),(4,60,'4点均值')]:
        box(ax,35,y-6,41,12)
        text(ax,37,y+2.5,f'尺度 {s} · {subtitle}',7.9,bold=True,ha='left')
        text(ax,37,y-2.1,f'{96//s}步',7.6,ha='left')
        curve(ax,46,y-3.5,27,3.5,RAW.reshape(-1,s).mean(axis=1))
        box(ax,82,y-6,29,12)
        text(ax,96.5,y+2.1,f'DLinear E{s}',8.5,bold=True)
        text(ax,96.5,y-2.3,'趋势＋余项',7.6,color=GRAY)
        arrow(ax,[(31,y),(35,y)])
        arrow(ax,[(76,y),(82,y)])
        arrow(ax,[(111,y),(121,y)])

    box(ax,121,55,32,43,fill=style['fusion'],edge=style['accent'])
    text(ax,137,90,'自适应加权融合',8.2,bold=True)
    summation(ax,76)
    summation(ax,63.5,prediction=False)
    box(ax,160,62,17,29)
    text(ax,168.5,85,'未来24步',7.8,bold=True)
    curve(ax,162,73.5,13,5.5,PREDICTION,points=True)
    text(ax,168.5,66.5,r'$24\times C$',9)
    arrow(ax,[(153,76),(160,76)])

    # Complete internal structure; the shape above expresses the zoom relation.
    text(ax,26,47.2,'DLinear',8.8,bold=True,ha='left')
    text(ax,84,47.2,'移动平均分解 · q=25',7.8,color=GRAY)
    box(ax,25,27,22,16)
    text(ax,36,39.5,'尺度输入',7.5,bold=True)
    text(ax,36,35,r'$96/s$',8.6)
    curve(ax,27,28.3,18,3.6,RAW)
    for label,values,y,dashed in [('趋势项',TREND,36,False),('余项',RESIDUAL,26,True)]:
        box(ax,56,y,25,7)
        text(ax,68.5,y+5,label,7.3,bold=True)
        curve(ax,58,y+1,21,1.6,values,dashed=dashed)
        box(ax,88,y,21,7)
        text(ax,98.5,y+3.5,'线性映射',7.5,bold=True)
        arrow(ax,[(81,y+3.5),(88,y+3.5)])
    arrow(ax,[(47,35),(51,35),(51,39.5),(56,39.5)])
    arrow(ax,[(51,35),(51,29.5),(56,29.5)])
    arrow(ax,[(109,39.5),(116,39.5),(116,36.3)])
    arrow(ax,[(109,29.5),(116,29.5),(116,32.7)])
    ax.add_patch(Circle((116,34.5),1.8,facecolor='white',edgecolor=EDGE,
                        linewidth=.75,zorder=3))
    text(ax,116,34.5,'+',8.5)
    box(ax,123,27,31,16)
    text(ax,138.5,39.5,'尺度预测',7.5,bold=True)
    curve(ax,125,33,27,3.5,PREDICTION,points=True)
    text(ax,138.5,29.5,r'$24\times C$',8.6)
    arrow(ax,[(117.8,34.5),(123,34.5)])

    box(ax,21,3,137,17,fill=style['router'],edge=style['accent'])
    text(ax,24,16,'窗口路由',8.4,bold=True,ha='left')
    box(ax,43,3.8,36,13.2)
    text(ax,61,14.5,'窗口特征',7.7,bold=True)
    text(ax,61,10.5,r'$z_n=[\mu_n,\sigma_n,\ell_n,d_n]$',8.2)
    text(ax,61,5.8,r'$z_n\in\mathbb{R}^4$',8.2)
    box(ax,88,5,29,12)
    text(ax,102.5,13,'两层MLP',8.2,bold=True)
    text(ax,102.5,8.5,'4 → 16 → 3',8.2)
    box(ax,125,5,30,12)
    text(ax,140,14,'Softmax',8.2,bold=True)
    text(ax,140,10.2,r'$\alpha_1,\alpha_2,\alpha_4$',8.5)
    for j,shade in enumerate(['#8E9296','#B2B5B8','#D4D6D8']):
        ax.add_patch(Rectangle((129+j*7.2,5.8),7,1.8,facecolor=shade,
                               edgecolor='none',zorder=3))
    arrow(ax,[(79,11),(88,11)])
    arrow(ax,[(117,11),(125,11)])
    arrow(ax,[(15.5,59),(15.5,11),(21,11)],dashed=True)
    arrow(ax,[(155,11),(178.5,11),(178.5,57),(153,57)],dashed=True)
    text(ax,90,1.25,'曲线与权重条仅作机制示意',6.5,color=GRAY)
    return fig


def export(fig,name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    text_boxes=[]
    for ax in fig.axes:
        for t in ax.texts:
            bb=t.get_window_extent(renderer)
            assert bb.x0>=0 and bb.y0>=0 and bb.x1<=fig.bbox.width and bb.y1<=fig.bbox.height, t.get_text()
            for previous,other in text_boxes:
                assert not bb.overlaps(other), (previous,t.get_text())
            text_boxes.append((t.get_text(),bb))
    alignment=require_matplotlib_panel_alignment(fig,json_out=OUT/f'{name}.alignment.json',strict=True)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        fig.savefig(OUT/f'{name}.png',dpi=600,facecolor='white')
        fig.savefig(OUT/f'{name}.pdf',facecolor='white')
        fig.savefig(OUT/f'{name}.svg',facecolor='white')
        fig.savefig(OUT/f'{name}.tiff',dpi=600,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
    assert not [str(w.message) for w in captured if 'Glyph' in str(w.message)]
    pdf=OUT/f'{name}.pdf'
    glyphs=audit_text(pdf.read_bytes(),minimum_pt=5)
    collisions=audit_collisions(pdf)
    for suffix,report in [('text-audit',glyphs),('collision-audit',collisions)]:
        (OUT/f'{name}.{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert glyphs['below_minimum_count']==0, glyphs
    assert collisions['summary']['fail']==0, collisions['findings']
    plt.close(fig)
    return dict(figure=name,alignment=alignment.get('verdict'),
                minimum_glyph_pt=glyphs['minimum_found_pt'],collision_summary=collisions['summary'])


if __name__=='__main__':
    results=[export(draw(style),name) for name,style in STYLES.items()]
    (OUT/'qa_summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))
