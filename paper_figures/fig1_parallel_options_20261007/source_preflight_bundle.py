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

INK = '#181818'
GRAY = '#505050'
EDGE = '#111111'
LINE = '#555555'
WIDTH, HEIGHT = 180, 110
STYLES = {
    'A_compact_formula': dict(expert='white', fusion='#F1F4F3', router='white', layout='formula'),
    'B_weighted_branches': dict(expert='white', fusion='#F1F4F3', router='white', layout='branches'),
    'C_weight_prediction': dict(expert='white', fusion='#F1F4F3', router='white', layout='pairs'),
}
SCALE_COLORS = ['#829CAA', '#99AD9E', '#B5A696']
SCALE_FILLS = ['#E9EFF2', '#ECF1ED', '#F1ECE6']

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
                          facecolor=fill, edgecolor=edge, linewidth=.9, zorder=2)
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
    vertices = [(81,99),(112,99),(114,99),(114,98),(114,97),(114,54),
                (114,51.5),(125,51),(134,51),
                (156,51),(158,51),(158,50),(158,49),
                (158,25),(158,23),(157,23),(156,23),
                (24,23),(22,23),(22,24),(22,25),
                (22,49),(22,51),(23,51),(24,51),(59,51),
                (69,51),(79,51.5),(79,54),(79,97),(79,99),(80,99),(81,99),(81,99)]
    codes = [MplPath.MOVETO, MplPath.LINETO,
             MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.LINETO,
             MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,
             MplPath.LINETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,
             MplPath.LINETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,
             MplPath.LINETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,
             MplPath.LINETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.LINETO,
             MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.LINETO,
             MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(vertices,codes), facecolor=fill,
                           edgecolor=EDGE, linewidth=.9, zorder=1))


def summation(ax, y, prediction=True, size=10):
    # Measure glyph runs and join them with a small physical gap; keep the
    # operator index separate so PDF extraction also preserves its position.
    scale = size/10
    parts = ([(r'$\hat Y=$',9.5*scale)] if prediction else [])
    parts += [('∑',12*scale),
              (r'$\alpha_s\hat Y^{(s)}$' if prediction else r'$\alpha_s=1$',size)]
    artists = [text(ax,0,y,label,pt,ha='left') for label,pt in parts]
    renderer = ax.figure.canvas.get_renderer()
    unit = ax.transData.transform((1,0))[0]-ax.transData.transform((0,0))[0]
    widths = [t.get_window_extent(renderer).width/unit for t in artists]
    gap = .55*scale
    x = 137-(sum(widths)+gap*(len(widths)-1))/2
    for t,width,(label,_) in zip(artists,widths,parts):
        t.set_position((x,y))
        if label == '∑':
            t.set_zorder(4.2)
            index = text(ax,x+width/2,y-4.1*scale,'s',6.5*scale)
            index.set_zorder(4.1)
        x += width+gap


def fusion_contents(ax, layout):
    if layout == 'formula':
        text(ax,137,91,'尺度预测加权',8,bold=True)
        text(ax,137,84,r'$s\in\{1,2,4\}$',8.7,color=GRAY)
        summation(ax,75)
        summation(ax,63,prediction=False)
    elif layout == 'branches':
        # Three contributions join a sum; these are symbolic mechanism components.
        for j,(s,y) in enumerate([(1,91),(2,83.5),(4,76)]):
            box(ax,124,y-2.7,17,5.4,fill=SCALE_FILLS[j],edge=EDGE)
            text(ax,132.5,y,rf'$\alpha_{s}\hat Y^{{({s})}}$',8.5)
            target = 85.3 if y>83.5 else 81.7 if y<83.5 else 83.5
            arrow(ax,[(141,y),(145.5,y),(145.5,target)] if y!=83.5
                  else [(141,y),(143.7,y)])
        ax.add_patch(Circle((145.5,83.5),1.8,facecolor='white',edgecolor=EDGE,
                            linewidth=.75,zorder=3))
        text(ax,145.5,83.5,'+',8.5)
        summation(ax,65.5)
        summation(ax,58.3,prediction=False,size=8.5)
    else:
        text(ax,129,92,'权重',7.6,bold=True)
        text(ax,144,92,'尺度预测',7.6,bold=True)
        for j,(s,y) in enumerate([(1,86),(2,78.5),(4,71)]):
            box(ax,124,y-2.6,8,5.2,fill=SCALE_FILLS[j])
            text(ax,128,y,rf'$\alpha_{s}$',8.5)
            text(ax,136,y,'×',8.5,color=GRAY)
            text(ax,144,y,rf'$\hat Y^{{({s})}}$',9)
        summation(ax,65.5)
        summation(ax,58.3,prediction=False,size=8.5)


def draw(style):
    fig = plt.figure(figsize=(7.08661417,4.33070866), facecolor='white')
    ax = fig.add_axes([0,0,1,1], xlim=(0,WIDTH), ylim=(0,HEIGHT))
    ax.axis('off')
    ax.add_patch(FancyBboxPatch((.9,.9),178.2,108.2,
                              boxstyle='round,pad=0,rounding_size=.7',
                              facecolor='none',edgecolor=EDGE,linewidth=.8,zorder=0))
    # One integrated schematic: its regions are not separate quantitative panels.
    for x,label in [(15.5,'历史输入'),(55.5,'多尺度构造'),(96.5,'独立尺度专家'),
                    (137,'自适应加权融合'),(169,'预测输出')]:
        text(ax,x,104,label,8.7,bold=True)

    expert_outline(ax, style['expert'])
    box(ax,3,59,25,38)
    for row in range(5):
        for col in range(6):
            shade = ['#DCE6EB','#B5C8D1','#8CA6B3'][(row+2*col)%3]
            ax.add_patch(Rectangle((7+col*2.8,77+row*2.35),2.6,2.15,
                                   facecolor=shade,edgecolor='none',zorder=3))
    text(ax,15.5,70,r'$X\in\mathbb{R}^{96\times C}$',10)
    text(ax,15.5,63.5,r'96步 · $C$ 变量',7.7)

    # Each scale enters one independent expert and produces its own prediction.
    ax.plot([28,31,31],[75,75,90], color=LINE, linewidth=.75, zorder=3)
    ax.plot([31,31],[60,90], color=LINE, linewidth=.75, zorder=3)
    for s,y,subtitle in [(1,90,'原始序列'),(2,75,'2点均值'),(4,60,'4点均值')]:
        box(ax,35,y-6,41,12)
        text(ax,37,y+2.5,f'尺度 {s}：{subtitle}',7.9,bold=True,ha='left')
        text(ax,37,y-2.1,f'{96//s}步',7.6,ha='left')
        curve(ax,46,y-3.5,27,3.5,RAW.reshape(-1,s).mean(axis=1))
        box(ax,82,y-6,29,12)
        text(ax,96.5,y+2.1,f'DLinear E{s}',8.5,bold=True)
        text(ax,96.5,y-2.3,'趋势 + 余项',7.6,color=GRAY)
        arrow(ax,[(31,y),(35,y)])
        arrow(ax,[(76,y),(82,y)])
        arrow(ax,[(111,y),(121,y)])

    box(ax,121,53.5,32,44.5,fill=style['fusion'])
    fusion_contents(ax,style['layout'])
    box(ax,160,62,17,29)
    text(ax,168.5,85,'未来 24 步',7.8,bold=True)
    curve(ax,162,73.5,13,5.5,PREDICTION,points=True)
    text(ax,168.5,66.5,r'$24\times C$',9)
    arrow(ax,[(153,76),(160,76)])

    # Complete internal structure; the shape above expresses the zoom relation.
    text(ax,26,47.2,'DLinear',8.8,bold=True,ha='left')
    text(ax,84,47.2,r'移动平均分解 · $q=25$',7.8,color=GRAY)
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

    box(ax,21,3,137,17,fill=style['router'])
    text(ax,24,16,'窗口路由',8.4,bold=True,ha='left')
    box(ax,43,3.8,36,13.2)
    text(ax,61,14.5,'窗口特征',7.7,bold=True)
    text(ax,61,10.5,r'$z_n=[\mu_n,\sigma_n,\ell_n,d_n]$',8.2)
    text(ax,61,5.8,r'$z_n\in\mathbb{R}^4$',8.2)
    box(ax,88,5,29,12)
    text(ax,102.5,13,'两层 MLP',8.2,bold=True)
    text(ax,102.5,8.5,'4 → 16 → 3',8.2)
    box(ax,125,5,30,12)
    text(ax,140,14,'Softmax',8.2,bold=True)
    text(ax,140,10.2,r'$\alpha_1,\alpha_2,\alpha_4$',8.5)
    for j,shade in enumerate(SCALE_COLORS):
        ax.add_patch(Rectangle((129+j*7.2,5.8),7,1.8,facecolor=shade,
                               edgecolor='none',zorder=3))
    arrow(ax,[(79,11),(88,11)])
    arrow(ax,[(117,11),(125,11)])
    arrow(ax,[(15.5,59),(15.5,11),(21,11)],dashed=True)
    arrow(ax,[(155,11),(171.5,11),(171.5,57),(153,57)],dashed=True)
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


"""Compact Figure 1 previews; preserve every label, formula and connection."""
from pathlib import Path
from collections import Counter
import importlib.util
import json
import re
import warnings
import os

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.transforms import Transform
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, PathPatch, Circle, Rectangle
import numpy as np

spec = importlib.util.spec_from_file_location(
    'original_figure', ROOT / 'paper_figures/fig1_fusion_options_20261002/build_fig1.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

WIDTH_MM = 161.925
FONT = FontProperties(family=['Times New Roman', 'SimSun'], size=7.5)
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'SimSun'],
                     'font.size': 7.5, 'svg.fonttype': 'none',
                     'pdf.fonttype': 42, 'mathtext.fontset': 'stix'})

# Compress the spacing and geometry, never the glyphs. Original region order
# remains: scale experts -> curved internal expansion -> independent router.
SOURCE_Y = np.array([0, 3, 20, 23, 26, 43, 51, 53.5, 54, 66, 69, 81, 84, 96, 99, 104, 110])
COMPACT_Y = np.array([0, 2.5, 18.5, 20.5, 23, 38, 44, 46, 46.5, 56.5, 59, 69.5, 72, 82.5, 85, 89, 94])
STYLES = {
    'A_gray_hierarchy': dict(height=97, module='#343434', inner='#777777', outer='#9B9B9B',
        expert_fill='white', fusion_fill='#F5F5F4', router_fill='#FAFAFA',
        fusion_edge='#343434', router_edge='#555555', branch_fill=['#F1F1F0']*3),
    'B_bluegray_hierarchy': dict(height=94, module='#4B626E', inner='#818A8E', outer='#999E9F',
        expert_fill='#FAFBFC', fusion_fill='#F0F4F5', router_fill='#F8FAFA',
        fusion_edge='#415A67', router_edge='#5C717A', branch_fill=['#E9EFF2', '#EDF1EF', '#F1EEE9']),
    'C_teal_emphasis': dict(height=91, module='#555B5D', inner='#8C9393', outer='#A0A4A4',
        expert_fill='white', fusion_fill='#F0F5F2', router_fill='#F7FAF8',
        fusion_edge='#48685D', router_edge='#48685D', branch_fill=['#E9EFF2', '#EDF1EC', '#F1EEE9']),
}


class VerticalLayout(Transform):
    input_dims = output_dims = 2
    is_separable = True
    has_inverse = True

    def __init__(self, source, target):
        super().__init__()
        assert np.all(np.diff(source) > 0) and np.all(np.diff(target) > 0)
        self.source, self.target = source, target

    def transform_non_affine(self, values):
        mapped = np.array(values, dtype=float, copy=True)
        mapped[..., 1] = np.interp(mapped[..., 1], self.source, self.target)
        return mapped

    def inverted(self):
        return VerticalLayout(self.target, self.source)


original_text = base.text


def journal_text(ax, x, y, value, size=8, bold=False, color=base.INK, ha='center'):
    value = value.replace('z_n', r'\boldsymbol{z}_n').replace(r'\hat Y', r'\hat{\boldsymbol{Y}}')
    if value.startswith('$X'):
        value = value.replace('$X', r'$\boldsymbol{X}', 1)
    artist = original_text(ax, x, y, value, size, bold, color, ha)
    artist.set_fontproperties(FONT)
    if '$' in value and re.search(r'[\u4e00-\u9fff]', value):
        artist.set_fontfamily('SimSun')
    artist.set_fontsize(9 if value == '∑' else 7.5)
    artist.set_fontweight('bold' if bold else 'normal')
    return artist


base.text = journal_text


def draw(name, style):
    height = style['height']
    target_y = COMPACT_Y * height / 94
    mapper = VerticalLayout(SOURCE_Y, target_y)
    make_figure = plt.figure

    def physical_figure(*args, **kwargs):
        kwargs['figsize'] = (WIDTH_MM / 25.4, WIDTH_MM * height / 180 / 25.4)
        return make_figure(*args, **kwargs)

    # Render at the final physical width so the summation glyph spacing uses
    # the same metrics as the final export.
    plt.figure = physical_figure
    try:
        fig = base.draw(base.STYLES['B_weighted_branches'])
    finally:
        plt.figure = make_figure
    ax = fig.axes[0]
    content = Counter(t.get_text() for t in ax.texts)
    topology = {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    ax.set_ylim(0, height)
    layout_transform = mapper + ax.transData
    for line in ax.lines:
        line.set_transform(layout_transform)
        line.set_linewidth(.65 if line.get_linestyle() == '--' else .72)
    for patch in ax.patches:
        patch.set_transform(layout_transform)
        if isinstance(patch, FancyBboxPatch):
            x, y = patch.get_x(), patch.get_y()
            patch.set_edgecolor(style['inner'])
            patch.set_linewidth(.55)
            if x < 2:
                patch.set_edgecolor(style['outer'])
                patch.set_linewidth(.4)
            elif (x, y) == (121, 53.5):
                patch.set_edgecolor(style['fusion_edge'])
                patch.set_linewidth(1.0)
                patch.set_facecolor(style['fusion_fill'])
            elif (x, y) == (21, 3):
                patch.set_edgecolor(style['router_edge'])
                patch.set_linewidth(.85)
                patch.set_facecolor(style['router_fill'])
            elif x in (3, 35, 82, 160):
                patch.set_edgecolor(style['module'])
                patch.set_linewidth(.8 if x == 82 else .7)
            elif x == 124:
                center_y = mapper.transform((x, y + patch.get_height()/2))[1]
                patch.set_y(center_y - 2.7)
                patch.set_height(5.4)
                patch.set_transform(ax.transData)
                patch.set_facecolor(style['branch_fill'][[88.3, 80.8, 73.3].index(round(y, 1))])
                patch.set_edgecolor(style['module'])
                patch.set_linewidth(.6)
        elif isinstance(patch, PathPatch):
            patch.set_facecolor(style['expert_fill'])
            patch.set_edgecolor(style['module'])
            patch.set_linewidth(.85)
        elif isinstance(patch, Circle):
            patch.set_center(mapper.transform(patch.get_center()))
            patch.set_transform(ax.transData)
            patch.set_edgecolor(style['module'])
            patch.set_linewidth(.65)
        elif not isinstance(patch, Rectangle):
            patch.set_color('#62686A' if name != 'A_gray_hierarchy' else '#606060')
            patch.set_linewidth(.65)
    for artist in ax.texts:
        x, old_y = artist.get_position()
        new_x, new_y = mapper.transform((x, old_y))
        # Keep the summation indices below their operators with adequate room
        # between the two equations after the surrounding box is shortened.
        if abs(old_y - 65.5) < .001:
            new_y = 59.3 * height / 94
        elif abs(old_y - 58.3) < .001:
            new_y = 52 * height / 94
        elif artist.get_text() == 's':
            new_y = (59.3 if old_y > 58.3 else 52) * height / 94 - 3.9
        artist.set_position((new_x, new_y))
        artist.set_transform(ax.transData)
    assert content == Counter(t.get_text() for t in ax.texts)
    assert topology == {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    return fig, content, topology


def export(fig, name, content, topology):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for artist in fig.axes[0].texts:
        bounds = artist.get_window_extent(renderer)
        assert bounds.x0 >= 0 and bounds.y0 >= 0 and bounds.x1 <= fig.bbox.width and bounds.y1 <= fig.bbox.height, artist.get_text()
        for previous, other in boxes:
            assert not bounds.overlaps(other), (previous, artist.get_text())
        boxes.append((artist.get_text(), bounds))
    stem = OUT / name
    alignment = base.require_matplotlib_panel_alignment(fig, json_out=f'{stem}.alignment.json', strict=True)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        fig.savefig(f'{stem}.png', dpi=300, facecolor='white')
        fig.savefig(f'{stem}.pdf', facecolor='white')
        fig.savefig(f'{stem}.svg', facecolor='white')
    assert not [str(w.message) for w in captured if 'Glyph' in str(w.message)]
    glyphs = base.audit_text(Path(f'{stem}.pdf').read_bytes(), minimum_pt=5)
    collisions = base.audit_collisions(Path(f'{stem}.pdf'))
    for suffix, report in [('text-audit', glyphs), ('collision-audit', collisions)]:
        Path(f'{stem}.{suffix}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    assert glyphs['below_minimum_count'] == 0, glyphs
    assert collisions['summary']['fail'] == 0, collisions['findings']
    height = STYLES[name]['height']
    result = dict(figure=name, width_mm=WIDTH_MM, height_mm=WIDTH_MM*height/180,
        height_reduction_pct=round((1-height/110)*100, 1), unchanged_text=dict(content),
        preserved_topology=topology, minimum_glyph_pt=glyphs['minimum_found_pt'],
        alignment=alignment.get('verdict'), collision_summary=collisions['summary'])
    plt.close(fig)
    return result


if __name__ == '__main__':
    results = []
    for name, style in STYLES.items():
        fig, content, topology = draw(name, style)
        results.append(export(fig, name, content, topology))
    (OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in row.items() if k != 'unchanged_text'} for row in results], ensure_ascii=False))


"""Keep the selected schematic unchanged except for its expansion boundary."""
from pathlib import Path
from collections import Counter
import importlib.util
import json
import os
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))
spec = importlib.util.spec_from_file_location(
    'compact', ROOT / 'paper_figures/fig1_compact_hierarchy_20261003/build_variants.py')
compact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compact)
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch

BASE_NAME = 'B_bluegray_hierarchy'
STYLE = compact.STYLES[BASE_NAME]
OPTIONS = {
    'A_standard': {'closed': False, 'inset': 0, 'linewidth': .70, 'dash': (4.0, 2.5)},
    'B_closed': {'closed': True, 'inset': 0, 'linewidth': .70, 'dash': (4.0, 2.5)},
    'C_inset': {'closed': False, 'inset': 5, 'linewidth': .60, 'dash': (3.0, 2.0)},
}

def centered_pluses(fig):
    ax = fig.axes[0]
    circles = [p for p in ax.patches if isinstance(p, compact.Circle)]
    pluses = [t for t in ax.texts if t.get_text() == '+']
    assert len(circles) == len(pluses) == 2
    for circle in circles:
        cx, cy = circle.get_center()
        artist = min(pluses, key=lambda t: abs(t.get_position()[0]-cx) + abs(t.get_position()[1]-cy))
        pluses.remove(artist)
        artist.remove()
        ax.plot([cx-.8, cx+.8], [cy, cy], color=compact.base.INK,
                linewidth=.55, solid_capstyle='butt', zorder=5)
        ax.plot([cx, cx], [cy-.8, cy+.8], color=compact.base.INK,
                linewidth=.55, solid_capstyle='butt', zorder=5)

def fingerprint(ax, excluded=()):
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = [(t.get_text(), t.get_position(), t.get_fontproperties().get_fontconfig_pattern(),
              t.get_color(), t.get_window_extent(renderer).bounds) for t in ax.texts]
    lines = [(tuple(line.get_xdata()), tuple(line.get_ydata()), line.get_color(),
              line.get_linewidth(), line.get_linestyle(), line.get_transform().get_matrix().tolist())
             for line in ax.lines]
    patches = [(p.get_path().vertices.tolist(), p.get_path().codes.tolist(),
                p.get_facecolor(), p.get_edgecolor(), p.get_linewidth(),
                p.get_transform().transform(p.get_path().vertices).tolist())
               for p in ax.patches if p not in excluded]
    return {'texts': texts, 'lines': lines, 'patches': patches}

def draw_outline(ax, original, option):
    transform = original.get_transform()
    original.remove()
    artists = []

    def path(vertices, closed=False, fill='none', dashed=False):
        codes = [PlotPath.MOVETO] + [PlotPath.LINETO] * (len(vertices)-1)
        if closed:
            vertices = vertices + [vertices[0]]
            codes += [PlotPath.CLOSEPOLY]
        artist = PathPatch(PlotPath(vertices, codes), transform=transform, facecolor=fill,
                           edgecolor=STYLE['module'], linewidth=option['linewidth'] if dashed else .85,
                           linestyle=(0, option['dash']) if dashed else '-',
                           joinstyle='miter', capstyle='butt', zorder=1)
        ax.add_patch(artist)
        artists.append(artist)

    # Same upper and lower extents as the selected curved outline.
    if option['closed']:
        path([(79,54),(79,99),(114,99),(114,54)])
        path([(22,51),(22,23),(158,23),(158,51)])
        path([(79,54),(114,54),(158,51),(22,51)], closed=True, dashed=True)
        # Region fills sit behind the open stroked frames and the dashed trapezoid.
        for points in [[(79,54),(114,54),(114,99),(79,99)],
                       [(22,23),(158,23),(158,51),(22,51)]]:
            vertices = points + [points[0]]
            artist = PathPatch(PlotPath(vertices, [PlotPath.MOVETO]+[PlotPath.LINETO]*3+[PlotPath.CLOSEPOLY]),
                               transform=transform, facecolor=STYLE['expert_fill'],
                               edgecolor='none', zorder=.9)
            ax.add_patch(artist)
            artists.append(artist)
    else:
        path([(79,54),(114,54),(114,99),(79,99)], closed=True, fill=STYLE['expert_fill'])
        path([(22,23),(158,23),(158,51),(22,51)], closed=True, fill=STYLE['expert_fill'])
        inset = option['inset']
        path([(79+inset,54),(22+inset,51)], dashed=True)
        path([(114-inset,54),(158-inset,51)], dashed=True)
    return artists

results = []
for name, option in OPTIONS.items():
    fig, _, _ = compact.draw(BASE_NAME, STYLE)
    centered_pluses(fig)
    ax = fig.axes[0]
    outlines = [p for p in ax.patches if isinstance(p, PathPatch)]
    assert len(outlines) == 1
    original = outlines[0]
    before = fingerprint(ax, [original])
    added = draw_outline(ax, original, option)
    assert before == fingerprint(ax, added), 'Content outside the expansion boundary changed'
    for artist in added:
        assert not any(c in (PlotPath.CURVE3, PlotPath.CURVE4) for c in artist.get_path().codes)
    content = Counter(t.get_text() for t in ax.texts)
    topology = {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    fig.savefig(OUT / f'{name}_highres.png', dpi=600, facecolor='white')
    compact.OUT = OUT
    compact.STYLES[name] = STYLE
    record = compact.export(fig, name, content, topology)
    record['unchanged_outside_expansion_boundary'] = True
    record['expansion_geometry'] = option
    results.append(record)

(OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{k: v for k, v in row.items() if k != 'unchanged_text'} for row in results], ensure_ascii=False))


"""Clarify the parallel forecast and routing branches of the selected schematic."""
from pathlib import Path
from collections import Counter
import json
import os
import types

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))
source = ROOT / 'paper_figures/fig1_trapezoid_options_20261007/build_options.py'
helper = types.ModuleType('outline_helpers')
helper.__file__ = str(source)
# Load the existing drawing helpers without running the preview export loop.
exec(compile(source.read_text(encoding='utf-8').split('\nresults = []\n')[0], str(source), 'exec'), helper.__dict__)
compact = helper.compact
from matplotlib.patches import FancyArrowPatch, Circle, PathPatch

mapper = compact.VerticalLayout(compact.SOURCE_Y, compact.COMPACT_Y)

def annotation(ax, x, y, label, size=7.0):
    ax.text(*mapper.transform((x, y)), label, fontproperties=compact.FONT,
            fontsize=size, color=helper.STYLE['module'], va='center', ha='center', zorder=5)

def routed_arrow(ax, points, transform):
    old_lines, old_patches = set(ax.lines), set(ax.patches)
    compact.base.arrow(ax, points, dashed=True, color='#62686A')
    for artist in (set(ax.lines)-old_lines) | (set(ax.patches)-old_patches):
        artist.set_transform(transform)
        artist.set_linewidth(.65)

def remove_arrow(ax, start):
    matches = [p for p in ax.patches if isinstance(p, FancyArrowPatch)
               and tuple(p._posA_posB[0]) == start]
    assert len(matches) == 1, start
    matches[0].remove()

results = []
for name, common_fork in [('A_branch_labels', False), ('B_shared_fork', True)]:
    fig, _, _ = compact.draw(helper.BASE_NAME, helper.STYLE)
    helper.centered_pluses(fig)
    ax = fig.axes[0]
    old_text = Counter(t.get_text() for t in ax.texts)
    old_curves = [(tuple(line.get_xdata()), tuple(line.get_ydata())) for line in ax.lines
                  if len(line.get_xdata()) > 2]
    outline = [p for p in ax.patches if isinstance(p, PathPatch)]
    assert len(outline) == 1
    helper.draw_outline(ax, outline[0], helper.OPTIONS['A_standard'])
    transform = ax.lines[0].get_transform()

    # Both variants return the weights to the fusion module via a shorter outer track.
    for line in list(ax.lines):
        x, y = list(line.get_xdata()), list(line.get_ydata())
        if (x, y) in [([155,171.5],[11,11]), ([171.5,171.5],[11,57])]:
            line.remove()
    remove_arrow(ax, (171.5,57))
    routed_arrow(ax, [(155,11),(166,11),(166,57),(153,57)], transform)

    if common_fork:
        old_input = [line for line in ax.lines
                     if list(line.get_xdata()) == [15.5,15.5]
                     and list(line.get_ydata()) == [59,11]]
        assert len(old_input) == 1
        old_input[0].remove()
        remove_arrow(ax, (15.5,11))
        # The two branches visibly leave the same junction on the history-input path.
        routed_arrow(ax, [(30.5,75),(30.5,57),(15.5,57),(15.5,11),(21,11)], transform)
        ax.add_patch(Circle(mapper.transform((30.5,75)), .35,
                            facecolor='#62686A', edgecolor='none', zorder=6))

    annotation(ax, 31, 99.5, '预测分支')
    annotation(ax, 8.3, 46.8, '路由分支')
    annotation(ax, 170, 36, '权重', size=6.5)
    content = Counter(t.get_text() for t in ax.texts)
    assert content == old_text + Counter(['预测分支','路由分支','权重'])
    assert old_curves == [(tuple(line.get_xdata()), tuple(line.get_ydata())) for line in ax.lines
                          if len(line.get_xdata()) > 2]
    compact.OUT = OUT
    compact.STYLES[name] = helper.STYLE
    topology = {'patches': len(ax.patches), 'lines': len(ax.lines), 'labels': len(ax.texts)}
    fig.savefig(OUT / f'{name}_highres.png', dpi=600, facecolor='white')
    record = compact.export(fig, name, content, topology)
    record['shared_input_junction'] = common_fork
    record['preserved_original_labels_and_curves'] = True
    results.append(record)

(OUT / 'qa_summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{k:v for k,v in row.items() if k!='unchanged_text'} for row in results], ensure_ascii=False))
