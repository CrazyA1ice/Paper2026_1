"""Reproducible vector architecture alternatives for manuscript V54, Fig. 1."""
from pathlib import Path
import json
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Microsoft YaHei'],
    'font.size': 8.5, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'mathtext.fontset': 'stix', 'axes.unicode_minus': False,
})
INK = '#243C4A'
MUTED = '#647684'
LINE = '#9BABB4'
EDGE = '#D5DFE4'
TEAL = '#28858A'
COLORS = ['#5184B6', '#6D9D78', '#CC8B5E']
FILLS = ['#EEF4FA', '#F0F6EF', '#FBF2EA']
AUDITS = []


def canvas(height):
    fig = plt.figure(figsize=(180 / 25.4, height / 25.4), facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 180), ylim=(0, height))
    ax.axis('off')
    return fig, ax


def label(ax, x, y, text, size=8.5, color=INK, bold=False, ha='center'):
    return ax.text(x, y, text, ha=ha, va='center', fontsize=size,
                   fontweight='bold' if bold else 'normal', color=color,
                   linespacing=1.5)


def box(ax, x, y, w, h, title=None, subtitle=None, color=EDGE, fill='white', size=8.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=1.4',
                              ec=color, fc=fill, lw=.85, zorder=2))
    if title:
        label(ax, x+w/2, y+h*(.67 if subtitle else .5), title, size, bold=True)
    if subtitle:
        label(ax, x+w/2, y+h*.29, subtitle, 8, MUTED)


def path(ax, points, color=LINE, dashed=False, lw=.9):
    for a, b in zip(points[:-2], points[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw,
                ls='--' if dashed else '-', zorder=2.5, solid_capstyle='round')
    ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle='-|>',
                                mutation_scale=7, color=color, lw=lw,
                                linestyle='--' if dashed else '-', shrinkA=0,
                                shrinkB=.7, zorder=2.5))


def arrow(ax, a, b, **kw):
    path(ax, [a, b], **kw)


def grid_icon(ax, x, y, w, h):
    # A neutral dimension icon, not a data heatmap or an experiment result.
    for i in range(6):
        for j in range(5):
            ax.add_patch(Rectangle((x+i*w/6, y+j*h/5), w/6-.25, h/5-.25,
                                   fc='#E7EFF3' if (i+j)%3 else '#C9DAE4', ec='none', zorder=3))


def legend(ax, x, y):
    arrow(ax, (x, y), (x+8, y))
    label(ax, x+10, y, '预测分支', 8, MUTED, ha='left')
    arrow(ax, (x+29, y), (x+37, y), color=TEAL, dashed=True)
    label(ax, x+39, y, '路由分支', 8, MUTED, ha='left')


def save(fig, name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    issues = []
    for ax in fig.axes:
        for t in ax.texts:
            bb = t.get_window_extent(renderer)
            if bb.x0 < 0 or bb.y0 < 0 or bb.x1 > fig.bbox.width or bb.y1 > fig.bbox.height:
                issues.append('outside canvas: '+t.get_text())
            for text, prev in boxes:
                if bb.overlaps(prev):
                    issues.append('text overlap: '+text+' / '+t.get_text())
            boxes.append((t.get_text(), bb))
    assert not issues, issues
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        fig.savefig(OUT/f'{name}.png', dpi=300, facecolor='white')
        fig.savefig(OUT/f'{name}.pdf', facecolor='white')
        fig.savefig(OUT/f'{name}.svg', facecolor='white')
    glyph_warnings = [str(w.message) for w in caught if 'Glyph' in str(w.message)]
    assert not glyph_warnings, glyph_warnings
    Image.open(OUT/f'{name}.png').convert('L').save(OUT/f'{name}_gray.png')
    AUDITS.append({'name':name, 'width_mm':180, 'height_mm':fig.get_figheight()*25.4,
                   'min_font_pt':min(t.get_fontsize() for ax in fig.axes for t in ax.texts),
                   'text_overlap':issues, 'missing_glyphs':glyph_warnings})
    plt.close(fig)


def horizontal():
    fig, ax = canvas(106)
    for x, text in [(15,'历史输入'),(51.5,'多尺度构造'),(92.5,'独立尺度专家'),(136.5,'加权融合'),(169,'预测输出')]:
        label(ax,x,100,text,9,bold=True)
    box(ax,2,35,27,54,fill='#F7F9FA')
    grid_icon(ax,7,59,17,18)
    label(ax,15.5,50,r'$X\in\mathbb{R}^{96\times C}$',10)
    label(ax,15.5,41,'历史OD窗口',8)
    ax.plot([29,32,32],[62,62,83],color=LINE,lw=.9)
    ax.plot([32,32],[37,83],color=LINE,lw=.9)
    for j,(s,n,y) in enumerate([(1,96,81),(2,48,59),(4,24,37)]):
        box(ax,36,y-8,31,16,f'尺度 {s}  ·  {n}步',
            ['原始序列','2点均值','4点均值'][j],COLORS[j],FILLS[j])
        box(ax,75,y-8,35,16,f'DLinear E{s}','趋势＋余项',COLORS[j],FILLS[j])
        arrow(ax,(32,y),(36,y))
        arrow(ax,(67,y),(75,y),color=COLORS[j])
        arrow(ax,(110,y),(121,y),color=COLORS[j])
    box(ax,121,29,31,60,color=TEAL,fill='#F0F7F6')
    label(ax,136.5,75,'自适应融合',9,bold=True)
    label(ax,136.5,59,r'$\sum_s\alpha_s\hat{Y}^{(s)}$',12)
    label(ax,136.5,42,r'$\sum_s\alpha_s=1$',10)
    box(ax,159,44,20,30,'未来24步',r'$24\times C$',size=8)
    arrow(ax,(152,59),(159,59),color=INK,lw=1.1)
    box(ax,35,3,117,22,color=TEAL,fill='#F6FAF9')
    label(ax,40,22,'窗口路由',8.5,bold=True,ha='left')
    label(ax,59,11,'均值 · 标准差\n末时均值 · 平均绝对差分',8)
    box(ax,91,6,23,12,'两层MLP','4 → 16 → 3',size=8)
    box(ax,122,6,26,12,'Softmax',r'$\alpha_1,\alpha_2,\alpha_4$',size=8)
    arrow(ax,(84,12),(91,12),color=TEAL)
    arrow(ax,(114,12),(122,12),color=TEAL)
    path(ax,[(15.5,35),(15.5,12),(35,12)],color=TEAL,dashed=True)
    arrow(ax,(136.5,25),(136.5,29),color=TEAL,dashed=True)
    label(ax,169,80,r'$\hat{Y}$',11)
    legend(ax,113,94)
    save(fig,'A_parallel')


def vertical():
    fig, ax = canvas(126)
    box(ax,83,108,72,15,'历史OD窗口',r'$X\in\mathbb{R}^{96\times C}$',fill='#F7F9FA')
    ax.plot([119,119],[108,103],color=LINE,lw=.9)
    ax.plot([79,159],[103,103],color=LINE,lw=.9)
    for j,(s,n,x) in enumerate([(1,96,63),(2,48,103),(4,24,143)]):
        cx=x+16
        box(ax,x,43,32,54,color=COLORS[j],fill=FILLS[j])
        label(ax,cx,91,f'尺度 {s}',9,bold=True)
        box(ax,x+3,73,26,13,['原始序列','2点均值','4点均值'][j],f'{n}步',size=8)
        box(ax,x+3,52,26,14,f'DLinear E{s}','趋势＋余项',size=8)
        label(ax,cx,47,r'$\hat{Y}^{('+str(s)+r')}$',10)
        arrow(ax,(cx,103),(cx,97),color=COLORS[j])
        arrow(ax,(cx,73),(cx,66),color=COLORS[j])
        destination = [96,119,142][j]
        path(ax,[(cx,43),(cx,39),(destination,39),(destination,34)],color=COLORS[j])
    box(ax,3,44,47,54,color=TEAL,fill='#F5FAF9')
    label(ax,26.5,94,'样本级尺度路由',9,bold=True)
    label(ax,26.5,83,'均值 · 标准差\n末时均值 · 平均绝对差分',8)
    box(ax,12,63,29,12,'两层MLP','4 → 16 → 3',size=8)
    box(ax,10,47,33,11,'Softmax',r'$\alpha_1,\alpha_2,\alpha_4$',size=8)
    arrow(ax,(26.5,78),(26.5,75),color=TEAL)
    arrow(ax,(26.5,63),(26.5,58),color=TEAL)
    path(ax,[(83,115),(26.5,115),(26.5,98)],color=TEAL,dashed=True)
    box(ax,84,18,70,16,'自适应尺度融合',r'$\hat{Y}=\sum_s\alpha_s\hat{Y}^{(s)}$',color=TEAL,fill='#EEF7F5')
    path(ax,[(26.5,44),(26.5,26),(84,26)],color=TEAL,dashed=True)
    label(ax,163,14,r'$\sum_s\alpha_s=1$',8)
    box(ax,91,1,56,9,'未来24步预测  ·  24 × C',size=8.5)
    arrow(ax,(119,18),(119,10),color=INK)
    legend(ax,4,8)
    save(fig,'B_vertical')


def detailed():
    fig, ax = canvas(132)
    label(ax,3,128,'a  整体预测框架',9,bold=True,ha='left')
    box(ax,2,90,25,28,'历史窗口',r'$96\times C$',fill='#F7F9FA')
    box(ax,35,87,67,35,color=EDGE,fill='#FAFBFC')
    for j,(s,n,y) in enumerate([(1,96,115),(2,48,104),(4,24,93)]):
        pool_text = ['原始 · 96步','2点均值 · 48步','4点均值 · 24步'][j]
        box(ax,38,y-4,21,8,pool_text,color=COLORS[j],fill=FILLS[j],size=8)
        box(ax,65,y-4,28,8,f'DLinear E{s}',color=COLORS[j],fill=FILLS[j],size=8)
        arrow(ax,(59,y),(65,y),color=COLORS[j])
        arrow(ax,(93,y),(114,y),color=COLORS[j])
    path(ax,[(27,104),(31,104),(31,115),(38,115)])
    arrow(ax,(31,104),(38,104))
    path(ax,[(31,104),(31,93),(38,93)])
    box(ax,114,89,32,30,'加权融合',r'$\sum_s\alpha_s\hat Y^{(s)}$',color=TEAL,fill='#EEF7F5')
    box(ax,155,92,23,24,'预测输出',r'$24\times C$',size=8)
    arrow(ax,(146,104),(155,104),color=INK)
    box(ax,35,69,67,12,'统计量 → MLP → Softmax',color=TEAL,fill='#F5FAF9',size=8.5)
    path(ax,[(14.5,90),(14.5,75),(35,75)],color=TEAL,dashed=True)
    path(ax,[(102,75),(130,75),(130,89)],color=TEAL,dashed=True)
    label(ax,139,80,r'$\alpha_1,\alpha_2,\alpha_4$',9,color=TEAL)
    ax.plot([2,178],[63,63],color=EDGE,lw=.65)
    box(ax,2,4,90,53,color=EDGE,fill='#FAFBFC')
    label(ax,6,51,'b  DLinear专家内部',9,bold=True,ha='left')
    box(ax,6,23,18,16,'尺度输入',r'$96/s$',size=8)
    box(ax,32,35,23,9,'趋势项',size=8)
    box(ax,32,16,23,9,'余项',size=8)
    box(ax,62,35,19,9,'线性映射',size=8)
    box(ax,62,16,19,9,'线性映射',size=8)
    path(ax,[(24,31),(28,31),(28,39.5),(32,39.5)])
    path(ax,[(28,31),(28,20.5),(32,20.5)])
    arrow(ax,(55,39.5),(62,39.5))
    arrow(ax,(55,20.5),(62,20.5))
    label(ax,84,29.5,'+',12,color=INK)
    path(ax,[(81,39.5),(84,39.5),(84,33)],color=LINE)
    path(ax,[(81,20.5),(84,20.5),(84,26)],color=LINE)
    box(ax,32,6,44,7,'尺度预测 · 24 × C',size=8)
    path(ax,[(86,29.5),(90,29.5),(90,9.5),(76,9.5)],color=LINE)
    label(ax,45,46.5,'移动平均分解 · q=25',8,color=MUTED)
    box(ax,94,4,84,53,color=TEAL,fill='#F5FAF9')
    label(ax,98,51,'c  样本级尺度路由器',9,bold=True,ha='left')
    box(ax,99,31,74,13,'4项窗口统计量','均值 · 标准差 · 末时均值 · 平均绝对差分',size=8.5)
    box(ax,100,10,34,13,'两层MLP','4 → 16 → 3',size=8)
    box(ax,143,10,29,13,'Softmax',r'$\alpha_1,\alpha_2,\alpha_4$',size=8)
    path(ax,[(117,31),(117,23)],color=TEAL)
    arrow(ax,(134,16.5),(143,16.5),color=TEAL)
    legend(ax,108,127)
    save(fig,'C_overview_detail')


if __name__ == '__main__':
    horizontal()
    vertical()
    detailed()
    (OUT/'layout_audit.json').write_text(json.dumps(AUDITS,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(AUDITS,ensure_ascii=False))
