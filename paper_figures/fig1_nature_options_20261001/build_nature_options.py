"""Three original model schematics with a shared publication-size contract."""
from pathlib import Path
import sys
import json
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SKILL = Path('C:/Users/Quant/.codex/skills/nature-figure/scripts')
sys.path.insert(0, str(SKILL))
sys.path.insert(0, str(ROOT/'review_scratch/figureqa_dependencies'))
from audit_panel_alignment import require_matplotlib_panel_alignment
from audit_pdf_text import audit_pdf as audit_text
from audit_figure_collisions import audit_pdf as audit_collisions

plt.rcParams.update({
    'font.family':'sans-serif', 'font.sans-serif':['Microsoft YaHei','Arial'],
    'font.size':8.5, 'svg.fonttype':'none', 'pdf.fonttype':42,
    'mathtext.fontset':'stix', 'axes.unicode_minus':False,
    'axes.spines.top':False, 'axes.spines.right':False,
})
INK='#263E49'
GRAY='#6C7B85'
EDGE='#CAD5DB'
LINE='#8E9FA9'
TEAL='#27828A'
SCALE=['#5A86B0','#719881','#C38860']
PALE=['#EFF4F8','#F0F5F1','#FAF2EB']
QA=[]


def canvas(h):
    fig=plt.figure(figsize=(7.08661417,h/25.4),facecolor='white')
    ax=fig.add_axes([0,0,1,1],xlim=(0,180),ylim=(0,h))
    ax.axis('off')
    return fig,ax


def text(ax,x,y,s,size=8.5,color=INK,bold=False,ha='center'):
    return ax.text(x,y,s,fontsize=size,color=color,fontweight='bold' if bold else 'normal',
                   ha=ha,va='center',linespacing=1.35,zorder=5)


def rect(ax,x,y,w,h,title='',sub='',edge=EDGE,fill='white',size=8.5,radius=.8):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={radius}',
                               ec=edge,fc=fill,lw=.75,zorder=2))
    if title: text(ax,x+w/2,y+h*(.66 if sub else .5),title,size,bold=True)
    if sub: text(ax,x+w/2,y+h*.28,sub,8.2,color=GRAY)


def arrow(ax,points,color=LINE,dashed=False,lw=.85):
    style='--' if dashed else '-'
    for a,b in zip(points[:-2],points[1:-1]):
        ax.plot([a[0],b[0]],[a[1],b[1]],lw=lw,color=color,ls=style,zorder=3)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=6.5,
                                 color=color,lw=lw,linestyle=style,shrinkA=0,shrinkB=.8,zorder=3))


def stage(ax,x,y,label):
    text(ax,x,y,label,9,bold=True)


def weighted_sum(ax,x,y,size=10.5):
    # Place the operator and its index explicitly in physical units, retaining
    # the equation while preventing stacked math glyph boxes from overlapping.
    width_mm=ax.bbox.width/ax.figure.dpi*25.4
    height_mm=ax.bbox.height/ax.figure.dpi*25.4
    dx=(ax.get_xlim()[1]-ax.get_xlim()[0])/width_mm
    dy=(ax.get_ylim()[1]-ax.get_ylim()[0])/height_mm
    text(ax,x-7*dx,y,'∑',size)
    text(ax,x-7*dx,y-3.7*dy,'s',6.5)
    text(ax,x+3*dx,y,r'$\alpha_s\hat Y^{(s)}$',size)


def save(fig,name):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    boxes=[]
    for ax in fig.axes:
        for t in ax.texts:
            bb=t.get_window_extent(renderer)
            assert bb.x0>=0 and bb.y0>=0 and bb.x1<=fig.bbox.width and bb.y1<=fig.bbox.height, t.get_text()
            for old,b in boxes:
                assert not bb.overlaps(b), (old,t.get_text())
            boxes.append((t.get_text(),bb))
    align=require_matplotlib_panel_alignment(fig,json_out=OUT/f'{name}.alignment.json',
                                             tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    with warnings.catch_warnings(record=True) as log:
        warnings.simplefilter('always')
        fig.savefig(OUT/f'{name}.png',dpi=600,facecolor='white')
        fig.savefig(OUT/f'{name}.pdf',facecolor='white')
        fig.savefig(OUT/f'{name}.svg',facecolor='white')
        fig.savefig(OUT/f'{name}.tiff',dpi=600,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
    assert not [str(w.message) for w in log if 'Glyph' in str(w.message)]
    pdf=OUT/f'{name}.pdf'
    glyph=audit_text(pdf.read_bytes(),minimum_pt=5)
    collision=audit_collisions(pdf)
    for suffix,result in [('text-audit',glyph),('collision-audit',collision)]:
        (OUT/f'{name}.{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    Image.open(OUT/f'{name}.png').convert('L').save(OUT/f'{name}_gray.png')
    assert glyph['below_minimum_count']==0
    assert collision['summary']['fail']==0, collision['findings']
    QA.append({'figure':name,'alignment':align.get('verdict'),'text':glyph,'collision':collision.get('verdict'),
               'collision_count':len(collision.get('findings',[]))})
    plt.close(fig)


def open_parallel():
    fig,ax=canvas(93)
    for x,s in [(14,'历史输入'),(51,'时间尺度'),(90,'尺度专家'),(138,'融合'),(169,'输出')]: stage(ax,x,87,s)
    rect(ax,2,32,25,40,'历史OD窗口',r'$96\times C$',fill='#F7F9FA',size=8.5)
    ax.plot([27,31,31],[52,52,71],color=LINE,lw=.85)
    ax.plot([31,31],[33,71],color=LINE,lw=.85)
    for j,(s,n,y) in enumerate([(1,96,71),(2,48,52),(4,24,33)]):
        # Slim nodes and open gutters emphasize the prediction path.
        rect(ax,36,y-6,30,12,f'尺度 {s} · {n}步',edge=SCALE[j],fill=PALE[j])
        text(ax,51,y-9,['原始序列','2点均值','4点均值'][j],8.2,color=GRAY)
        rect(ax,76,y-6,29,12,f'DLinear E{s}',edge=SCALE[j],fill=PALE[j])
        text(ax,90.5,y-9,'趋势＋余项',8.2,color=GRAY)
        arrow(ax,[(31,y),(36,y)])
        arrow(ax,[(66,y),(76,y)],color=SCALE[j])
        arrow(ax,[(105,y),(123,y)],color=SCALE[j])
        text(ax,114,y+4,r'$\hat Y^{('+str(s)+')}$',9.5,color=SCALE[j])
    rect(ax,123,25,29,54,edge=TEAL,fill='#F0F7F6')
    text(ax,137.5,68,'自适应加权',8.5,bold=True)
    weighted_sum(ax,137.5,51,11)
    text(ax,137.5,34,r'$\alpha_1+\alpha_2+\alpha_4=1$',8.5)
    rect(ax,160,42,18,20,'未来24步',r'$24\times C$',size=8)
    arrow(ax,[(152,52),(160,52)],color=INK)
    # The lower route is visually subordinate and retains all four statistics.
    ax.add_patch(Rectangle((35,2),117,17,fc='#F6F9F9',ec='none',zorder=1))
    text(ax,58,13,'窗口统计',8.5,bold=True)
    text(ax,58,6,'均值 · 标准差 · 末时均值\n平均绝对差分',8.2,color=GRAY)
    rect(ax,92,4,24,12,'两层MLP','4 → 16 → 3',size=8)
    rect(ax,124,4,25,12,'Softmax',r'$\alpha_1,\alpha_2,\alpha_4$',size=8)
    arrow(ax,[(84,10),(92,10)],color=TEAL)
    arrow(ax,[(116,10),(124,10)],color=TEAL)
    arrow(ax,[(14.5,32),(14.5,10),(35,10)],color=TEAL,dashed=True)
    arrow(ax,[(137.5,19),(137.5,25)],color=TEAL,dashed=True)
    save(fig,'N1_open_parallel')


def dual_stream():
    fig,ax=canvas(98)
    stage(ax,87,92,'多尺度预测分支')
    rect(ax,2,42,26,28,'历史OD窗口',r'$96\times C$',fill='#F7F9FA')
    for j,(s,n,y) in enumerate([(1,96,79),(2,48,64),(4,24,49)]):
        ax.add_patch(Rectangle((37,y-6),95,12,fc=PALE[j],ec='none',zorder=1))
        text(ax,51,y,f'尺度 {s}',8.5,color=SCALE[j],bold=True)
        text(ax,74,y,['原始96步','均值池化48步','均值池化24步'][j],8.2)
        rect(ax,96,y-5,29,10,f'DLinear E{s}',edge=SCALE[j],fill='white',size=8.5)
        arrow(ax,[(86,y),(96,y)],color=SCALE[j])
        arrow(ax,[(125,y),(145,y)],color=SCALE[j])
    arrow(ax,[(28,56),(32,56),(32,79),(37,79)])
    arrow(ax,[(32,64),(37,64)])
    arrow(ax,[(32,56),(32,49),(37,49)])
    stage(ax,87,35,'窗口路由分支')
    rect(ax,37,4,95,26,edge=TEAL,fill='#F5F9F8')
    text(ax,60,23,'4项统计量',8.5,bold=True)
    text(ax,60,12,'均值 · 标准差\n末时均值 · 平均绝对差分',8.2,color=GRAY)
    rect(ax,89,9,19,15,'MLP','4→16→3',size=8)
    rect(ax,114,9,15,15,'Softmax',size=8)
    arrow(ax,[(83,16.5),(89,16.5)],color=TEAL)
    arrow(ax,[(108,16.5),(114,16.5)],color=TEAL)
    arrow(ax,[(15,42),(15,17),(37,17)],color=TEAL,dashed=True)
    rect(ax,145,41,31,45,edge=TEAL,fill='#EEF6F5')
    text(ax,160.5,71,'尺度融合',9,bold=True)
    weighted_sum(ax,160.5,57,10.5)
    arrow(ax,[(132,17),(138,17),(138,45),(145,45)],color=TEAL,dashed=True)
    text(ax,160.5,47,r'$\alpha_1,\alpha_2,\alpha_4$',9,color=TEAL)
    rect(ax,146,14,29,17,'预测输出',r'$24\times C$',size=8.5)
    arrow(ax,[(160.5,41),(160.5,31)],color=INK)
    save(fig,'N2_dual_stream')


def mechanism_composite():
    fig=plt.figure(figsize=(7.08661417,4.48818898),facecolor='white')
    gs=fig.add_gridspec(2,2,left=.015,right=.985,bottom=.025,top=.985,
                        height_ratios=[1.55,1],wspace=.10,hspace=.18)
    top=fig.add_subplot(gs[0,:]);left=fig.add_subplot(gs[1,0]);right=fig.add_subplot(gs[1,1])
    for ax in (top,left,right): ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
    text(top,0,97,'a',9,bold=True,ha='left');text(top,4,97,'预测框架',9,bold=True,ha='left')
    rect(top,1,36,14,41,'历史窗口',r'$96\times C$',fill='#F7F9FA',size=8.5)
    for j,(s,n,y) in enumerate([(1,96,79),(2,48,57),(4,24,35)]):
        rect(top,21,y-8,18,16,['原始96步','2点均值48步','4点均值24步'][j],edge=SCALE[j],fill=PALE[j],size=8.2)
        rect(top,45,y-8,20,16,f'DLinear E{s}',edge=SCALE[j],fill=PALE[j],size=8.5)
        arrow(top,[(39,y),(45,y)],color=SCALE[j])
        arrow(top,[(65,y),(72,y)],color=SCALE[j])
    arrow(top,[(15,57),(18,57),(18,79),(21,79)])
    arrow(top,[(18,57),(21,57)])
    arrow(top,[(18,57),(18,35),(21,35)])
    rect(top,72,27,16,60,edge=TEAL,fill='#F0F7F6')
    text(top,80,69,'融合',9,bold=True)
    weighted_sum(top,80,44,10.5)
    rect(top,92,41,8,33,'输出',r'$24\times C$',size=8)
    arrow(top,[(88,57),(92,57)],color=INK)
    rect(top,21,1,44,18,'窗口统计 → MLP → Softmax',edge=TEAL,fill='#F5F9F8',size=8.5)
    arrow(top,[(8,36),(8,10),(21,10)],color=TEAL,dashed=True)
    arrow(top,[(65,10),(80,10),(80,27)],color=TEAL,dashed=True)
    text(top,84,16,r'$\alpha_1,\alpha_2,\alpha_4$',9,color=TEAL)
    # Complementary detail panels, drawn at equal physical sizes.
    text(left,0,95,'b',9,bold=True,ha='left');text(left,6,95,'DLinear尺度专家',9,bold=True,ha='left')
    text(left,50,82,'移动平均分解 · q=25',8.2,color=GRAY)
    rect(left,0,36,19,25,'输入',r'$96/s$',size=8)
    rect(left,29,58,26,18,'趋势项',size=8.2)
    rect(left,29,24,26,18,'余项',size=8.2)
    rect(left,65,58,26,18,'线性映射',size=8.2)
    rect(left,65,24,26,18,'线性映射',size=8.2)
    arrow(left,[(19,48.5),(24,48.5),(24,67),(29,67)])
    arrow(left,[(24,48.5),(24,33),(29,33)])
    arrow(left,[(55,67),(65,67)])
    arrow(left,[(55,33),(65,33)])
    text(left,96,49,'+',11)
    arrow(left,[(91,67),(96,67),(96,57)])
    arrow(left,[(91,33),(96,33),(96,41)])
    rect(left,29,1,61,17,'尺度预测 · 24 × C',size=8)
    arrow(left,[(99,49),(100,49),(100,9.5),(90,9.5)])
    text(right,0,95,'c',9,bold=True,ha='left');text(right,6,95,'样本级尺度路由',9,bold=True,ha='left')
    rect(right,0,55,100,27,'原历史窗口的4项统计量',
          '均值 · 标准差 · 末时均值 · 平均绝对差分',edge=TEAL,fill='#F3F8F7',size=8.5)
    rect(right,0,11,27,29,'隐藏层','16 · ReLU',size=8.2)
    rect(right,38,11,27,29,'尺度分数','3维',size=8.2)
    rect(right,76,11,24,29,'Softmax',r'$\alpha_s$',edge=TEAL,fill='#F3F8F7',size=8.2)
    arrow(right,[(13.5,55),(13.5,40)],color=TEAL)
    arrow(right,[(27,25.5),(38,25.5)],color=TEAL)
    arrow(right,[(65,25.5),(76,25.5)],color=TEAL)
    text(right,22,2,r'$s\in\{1,2,4\}$',9)
    text(right,73,2,r'$\alpha_1+\alpha_2+\alpha_4=1$',9)
    save(fig,'N3_framework_details')


if __name__=='__main__':
    open_parallel()
    dual_stream()
    mechanism_composite()
    (OUT/'qa_summary.json').write_text(json.dumps(QA,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(QA,ensure_ascii=False))
