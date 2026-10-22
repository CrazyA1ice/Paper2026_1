from pathlib import Path
from hashlib import sha256
import json
import warnings
import sys

import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import MaxNLocator
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
JOURNAL=ROOT/'paper_template/长春工程学院学报(自然科学版)'
SOURCE=JOURNAL/'图表组织优化修订_20261022/自适应多尺度加权的多变量网络流量预测_图表优化稿.docx'
SOURCE_SHA='ea996d638e7b11f4a02863b5c0de681f8511dbc7b2ead96a16bbaba79ac49d89'
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
INPUT=SOURCE.parent/'图表与核验数据'
OUT=JOURNAL/'图2-4参考方案_20261022'
OUT.mkdir(parents=True,exist_ok=True)
DATA=OUT/'数据与说明';DATA.mkdir(exist_ok=True)
SEEDS=list(range(42,50))
DS=['abilene','geant'];DS_NAMES=['Abilene','GÉANT']
MODELS=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
NAMES=['DLinear','固定等权','全局权重','恒定路由','本文方法']
BASELINES=['dlinear','lightts','dlinear_scale']
BLUE='#247D91'; INK='#253943'; GREY='#A8B3BA'; LIGHT='#ECF3F5'
COLORS=['#657784','#8C959D','#9C8F81','#738A87',BLUE]
MARKERS=['o','^','s','v','D']
CMAP=LinearSegmentedColormap.from_list('gain',['#F3F7F8','#D4E6EA','#A4CAD3','#79ACBA'])
core=pd.read_csv(INPUT/'全部24h逐种子指标.csv')
gains=pd.read_csv(INPUT/'图2_配对相对降幅.csv')
high=pd.read_csv(INPUT/'图3_高需求全部种子.csv')
week=pd.read_csv(INPUT/'图4_168h绝对误差全部种子.csv')
wg=pd.read_csv(INPUT/'图4_168h配对降幅.csv')
assert [len(x) for x in [core,gains,high,week,wg]]==[96,64,80,40,64]
assert not core.duplicated(['dataset','model','seed']).any()
hi=high.set_index(['dataset','model','seed'])
high_gains=[]
for ds in DS:
    for model in MODELS[:-1]:
        for metric in ['mae','mean_shortfall']:
            for seed in SEEDS:
                b=hi.loc[(ds,model,seed),metric];p=hi.loc[(ds,'dlinear_scale',seed),metric]
                assert b>0
                high_gains.append(dict(dataset=ds,baseline=model,metric=metric,seed=seed,reduction_pct=100*(b-p)/b))
hg=pd.DataFrame(high_gains)
assert len(hg)==128 and hg.groupby(['dataset','baseline','metric']).reduction_pct.mean().gt(0).all()
assert wg.reduction_pct.gt(0).all()
for frame,name in [(core,'24h全部指标'),(gains,'24h配对降幅'),(high,'高需求全部指标'),(hg,'高需求配对降幅'),(week,'168h全部指标'),(wg,'168h配对降幅')]:
    frame.to_csv(DATA/(name+'.csv'),index=False,encoding='utf-8-sig')

mpl.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','SimSun'],
    'font.size':7.5,'axes.labelsize':7.5,'axes.titlesize':7.5,'xtick.labelsize':7.5,
    'ytick.labelsize':7.5,'legend.fontsize':7.5,'pdf.fonttype':42,'svg.fonttype':'none',
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
    'axes.unicode_minus':False,'xtick.major.width':.6,'ytick.major.width':.6,
    'figure.facecolor':'white','savefig.facecolor':'white'})
sys.path.insert(0,r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment

EXPORTS=[]
SUITES={'A':'A_紧凑矩阵','B':'B_误差平面','C':'C_配对小倍图'}
PANEL_NOTES={}

def stats(values):
    a=np.asarray(values,dtype=float)
    assert len(a)==8 and np.isfinite(a).all()
    return float(a.mean()),float(a.std(ddof=1))

def subset(frame,**keys):
    out=frame
    for k,v in keys.items():out=out[out[k]==v]
    out=out.sort_values('seed')
    assert out.seed.tolist()==SEEDS
    return out

def clean_fonts(fig):
    for t in fig.findobj(match=Text):
        t.set_fontfamily(['SimSun'] if any('\u4e00'<=c<='\u9fff' for c in t.get_text()) else ['Times New Roman'])

def export(fig,suite,number,stem,axes=None):
    clean_fonts(fig)
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter('always');fig.canvas.draw()
        missing=[str(w.message) for w in records if 'Glyph' in str(w.message)]
    assert not missing,missing
    tag=f'{suite}{number}'
    alignment=require_matplotlib_panel_alignment(fig,axes=axes,json_out=QA/f'{tag}_alignment.json',
        overlay_svg=QA/f'{tag}_alignment.svg',strict=True,tolerance_pt=1.5,gutter_tolerance_pt=1.5)
    folder=OUT/SUITES[suite];folder.mkdir(exist_ok=True)
    prefix=folder/f'图{number}_{stem}'
    fig.savefig(prefix.with_suffix('.pdf'))
    fig.savefig(prefix.with_suffix('.svg'))
    fig.savefig(prefix.with_suffix('.png'),dpi=600)
    fig.savefig(QA/f'{tag}_preview.png',dpi=220)
    with Image.open(QA/f'{tag}_preview.png') as im:im.convert('L').save(QA/f'{tag}_grayscale.png')
    EXPORTS.append(dict(tag=tag,suite=suite,figure=number,prefix=str(prefix),width_mm=float(fig.get_figwidth()*25.4),height_mm=float(fig.get_figheight()*25.4),alignment=alignment['verdict'],notes=PANEL_NOTES.get(tag,[])))
    plt.close(fig)
    print(tag,alignment['verdict'],flush=True)

def heat_axis(ax,values,rows,columns,title,norm):
    # Matrix cells encode means. Every cell separately reports its sample SD.
    image=ax.imshow(values,cmap=CMAP,norm=norm,aspect='auto',interpolation='nearest')
    ax.set(xticks=np.arange(len(columns)),xticklabels=columns,yticks=np.arange(len(rows)),yticklabels=rows)
    ax.tick_params(axis='both',length=0,pad=5)
    ax.xaxis.tick_top()
    for s in ax.spines.values():s.set_visible(False)
    ax.set_xticks(np.arange(-.5,len(columns),1),minor=True)
    ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
    ax.grid(which='minor',color='white',linewidth=2)
    ax.tick_params(which='minor',length=0)
    ax.set_title(title,loc='left',pad=25)
    return image

def cell(ax,x,y,mean,sd):
    ax.text(x,y-.12,f'{mean:.2f}%',ha='center',va='center',color=INK)
    ax.text(x,y+.19,f'± {sd:.2f}',ha='center',va='center',color=INK)

def colorbar(fig,mappable,y=.08):
    ax=fig.add_axes([.30,y,.52,.023])
    cb=fig.colorbar(mappable,cax=ax,orientation='horizontal')
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2,pad=2)
    cb.set_label('配对平均降幅/%',labelpad=1)


def a2():
    fig,axs=plt.subplots(1,2,figsize=(138/25.4,58/25.4))
    fig.subplots_adjust(left=.12,right=.98,bottom=.40,top=.72,wspace=.42)
    for ax,ds,name,letter,ratio in zip(axs,DS,DS_NAMES,'ab',[6.41,2.17]):
        means=np.zeros((2,2));sds=means.copy()
        for y,metric in enumerate(['mse','mae']):
            for x,b in enumerate(['dlinear','lightts']):
                means[y,x],sds[y,x]=stats(subset(gains,dataset=ds,baseline=b,metric=metric).reduction_pct)
        m=heat_axis(ax,means,['MSE','MAE'],['对DLinear','对LightTS'],f'({letter}) {name}',Normalize(0,50))
        for y in range(2):
            for x in range(2):cell(ax,x,y,means[y,x],sds[y,x])
        ax.text(.5,-.25,f'参数量 / LightTS = {ratio:.2f}%',transform=ax.transAxes,ha='center',va='top')
    fig.text(.55,.96,'8次配对；单元格为均值 ± 样本标准差',ha='center',va='top')
    colorbar(fig,m,y=.14)
    export(fig,'A',2,'多基线增益矩阵',axes=list(axs))

def a3():
    fig,axs=plt.subplots(1,2,figsize=(138/25.4,72/25.4))
    fig.subplots_adjust(left=.16,right=.98,bottom=.25,top=.77,wspace=.45)
    for ax,ds,name,letter in zip(axs,DS,DS_NAMES,'ab'):
        means=np.zeros((4,2));sds=means.copy()
        for y,b in enumerate(MODELS[:-1]):
            for x,metric in enumerate(['mae','mean_shortfall']):
                means[y,x],sds[y,x]=stats(subset(hg,dataset=ds,baseline=b,metric=metric).reduction_pct)
        m=heat_axis(ax,means,NAMES[:-1],['MAE','AUE'],f'({letter}) {name}',Normalize(0,25))
        for y in range(4):
            for x in range(2):cell(ax,x,y,means[y,x],sds[y,x])
    fig.text(.56,.965,'本文方法相对各行对照的高需求误差降幅；n=8',ha='center',va='top')
    colorbar(fig,m,y=.10)
    export(fig,'A',3,'高需求配对增益矩阵',axes=list(axs))

def a4():
    fig,ax=plt.subplots(figsize=(138/25.4,78/25.4))
    fig.subplots_adjust(left=.20,right=.97,bottom=.23,top=.77)
    means=np.zeros((4,2));sds=means.copy()
    for y,b in enumerate(MODELS[:-1]):
        for x,metric in enumerate(['mse','mae']):means[y,x],sds[y,x]=stats(subset(wg,baseline=b,metric=metric).reduction_pct)
    p=week[week.model=='dlinear_scale']
    columns=[]
    for metric in ['mse','mae']:
        mean,sd=stats(p['all_'+metric]);columns.append(f'{metric.upper()}\n本文 {mean:.3f}±{sd:.3f}')
    m=heat_axis(ax,means,NAMES[:-1],columns,'',Normalize(0,30))
    for y,b in enumerate(MODELS[:-1]):
        for x,metric in enumerate(['mse','mae']):
            am,asd=stats(subset(week,model=b)['all_'+metric])
            ax.text(x,y-.18,f'对照 {am:.3f}±{asd:.3f}',ha='center',va='center',color=INK)
            ax.text(x,y+.16,f'降低 {means[y,x]:.2f}% ± {sds[y,x]:.2f}',ha='center',va='center',color=INK)
    fig.text(.57,.97,'GÉANT · 168 h：绝对误差与配对降幅联合呈现',ha='center',va='top')
    fig.text(.58,.185,'全部8次配对均降低；误差与降幅均报告均值 ± 样本标准差',ha='center',va='center')
    colorbar(fig,m,y=.105)
    export(fig,'A',4,'一周绝对误差与增益联合矩阵',axes=[ax])


def cloud(ax,frame,xcol,ycol,model_index,proposed=False):
    c=BLUE if proposed else COLORS[model_index]
    marker=MARKERS[model_index]
    xm,xs=stats(frame[xcol]);ym,ys=stats(frame[ycol])
    ax.scatter(frame[xcol],frame[ycol],marker=marker,s=9,c=c,alpha=.40,linewidths=0,zorder=2)
    ax.errorbar(xm,ym,xerr=xs,yerr=ys,fmt=marker,color=c,elinewidth=.85 if proposed else .65,
        markersize=5 if proposed else 4,markerfacecolor=c if proposed else 'white',markeredgewidth=.75,
        capsize=1.8,zorder=4 if proposed else 3)
    return xm,ym

def bounds2d(ax,frame,xcol,ycol,groups):
    xb=[];yb=[]
    for group in groups:
        g=frame[frame.model==group]
        for col,bs in [(xcol,xb),(ycol,yb)]:
            mean,sd=stats(g[col]);bs.extend([g[col].min(),g[col].max(),mean-sd,mean+sd])
    xpad=(max(xb)-min(xb))*.15;ypad=(max(yb)-min(yb))*.18
    ax.set_xlim(min(xb)-xpad,max(xb)+xpad);ax.set_ylim(min(yb)-ypad,max(yb)+ypad)
    ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))

def b2():
    fig,axs=plt.subplots(1,2,figsize=(138/25.4,70/25.4))
    fig.subplots_adjust(left=.105,right=.98,bottom=.24,top=.73,wspace=.50)
    for ax,ds,name,letter,ratio in zip(axs,DS,DS_NAMES,'ab',[6.41,2.17]):
        frame=core[(core.dataset==ds)&core.model.isin(BASELINES)]
        for model,i in [('dlinear',0),('lightts',2),('dlinear_scale',4)]:cloud(ax,subset(frame,model=model),'mse','mae',i,model=='dlinear_scale')
        bounds2d(ax,frame,'mse','mae',BASELINES)
        ax.set(xlabel='MSE（越小越好）',ylabel='MAE（越小越好）')
        ax.set_title(f'({letter}) {name}',loc='left',pad=9)
        ax.text(.98,.97,'左下方：两项误差同时较低',transform=ax.transAxes,ha='right',va='top',color=INK)
        ax.text(.5,-.30,f'本文参数量 / LightTS = {ratio:.2f}%',transform=ax.transAxes,ha='center',va='top')
    handles=[Line2D([],[],marker=MARKERS[i],color=COLORS[i],markerfacecolor=COLORS[i] if i==4 else 'white',ls='none',label=n,markersize=4.5) for i,n in [(0,'DLinear'),(2,'LightTS'),(4,'本文方法')]]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,1.005),ncol=3,frameon=False)
    fig.text(.55,.87,'小点：8次重复；大点与双向误差线：均值 ± 样本标准差',ha='center',va='center')
    export(fig,'B',2,'MSE与MAE综合误差平面',axes=list(axs))

def b3():
    fig,axs=plt.subplots(1,2,figsize=(138/25.4,66/25.4))
    fig.subplots_adjust(left=.105,right=.98,bottom=.21,top=.76,wspace=.50)
    for ax,ds,name,letter in zip(axs,DS,DS_NAMES,'ab'):
        frame=high[high.dataset==ds]
        for i,model in enumerate(MODELS):cloud(ax,subset(frame,model=model),'mae','mean_shortfall',i,model=='dlinear_scale')
        bounds2d(ax,frame,'mae','mean_shortfall',MODELS)
        ax.set(xlabel='高需求MAE',ylabel='高需求AUE')
        ax.set_title(f'({letter}) {name}',loc='left',pad=9)
    handles=[Line2D([],[],marker=MARKERS[i],color=COLORS[i],markerfacecolor=COLORS[i] if i==4 else 'white',ls='none',label=n,markersize=4) for i,n in enumerate(NAMES)]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,1.005),ncol=5,frameon=False,handletextpad=.35,columnspacing=.7)
    fig.text(.55,.86,'小点：8次重复；大点与双向误差线：均值 ± 样本标准差',ha='center',va='center')
    fig.text(.55,.035,'左下方同时对应较低MAE与较低需求低估幅度',ha='center',va='bottom')
    export(fig,'B',3,'高需求双指标误差平面',axes=list(axs))

def b4():
    fig,axs=plt.subplots(1,2,figsize=(138/25.4,67/25.4))
    fig.subplots_adjust(left=.105,right=.98,bottom=.20,top=.74,wspace=.48)
    wi=week.set_index(['model','seed'])
    for ax,metric,title,letter in zip(axs,['mse','mae'],['MSE','MAE'],'ab'):
        values=[]
        for i,model in enumerate(MODELS[:-1]):
            x=np.array([wi.loc[(model,s),'all_'+metric] for s in SEEDS]);y=np.array([wi.loc[('dlinear_scale',s),'all_'+metric] for s in SEEDS])
            assert (y<x).all()
            frame=pd.DataFrame({'x':x,'y':y});cloud(ax,frame,'x','y',i)
            values.extend([x.min(),x.max(),y.min(),y.max(),x.mean()-x.std(ddof=1),x.mean()+x.std(ddof=1),y.mean()-y.std(ddof=1),y.mean()+y.std(ddof=1)])
        span=max(values)-min(values);lo=min(values)-.1*span;hi=max(values)+.1*span
        ax.plot([lo,hi],[lo,hi],ls=(0,(3,2)),color='#84929A',lw=.7,zorder=0)
        ax.set(xlim=(lo,hi),ylim=(lo,hi),xlabel='对照模型误差',ylabel='本文方法误差')
        ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.set_title(f'({letter}) {title}',loc='left',pad=9)
        ax.text(.04,.96,'全部配对点均在y=x下方',transform=ax.transAxes,ha='left',va='top')
    handles=[Line2D([],[],marker=MARKERS[i],color=COLORS[i],markerfacecolor='white',ls='none',label=n,markersize=4) for i,n in enumerate(NAMES[:-1])]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,1.005),ncol=4,frameon=False,columnspacing=1.0,handletextpad=.35)
    fig.text(.55,.865,'每点为同一种子的一次配对；大点与误差线为均值 ± 样本标准差',ha='center',va='center')
    fig.text(.55,.03,'MSE平均降幅23.16%～26.11%；MAE平均降幅11.16%～12.39%',ha='center',va='bottom')
    export(fig,'B',4,'一周配对误差一致性平面',axes=list(axs))


def c2():
    fig,axs=plt.subplots(1,2,figsize=(138/25.4,61/25.4))
    fig.subplots_adjust(left=.17,right=.895,bottom=.25,top=.80,wspace=.69)
    rows=[('dlinear','mse'),('dlinear','mae'),('lightts','mse'),('lightts','mae')]
    labels=['DLinear · MSE','DLinear · MAE','LightTS · MSE','LightTS · MAE']
    norm_values=100-gains.reduction_pct
    low=np.floor(norm_values.min()/10)*10-5;highlim=max(110,np.ceil(norm_values.max()/10)*10+5)
    for ax,ds,name,letter,ratio in zip(axs,DS,DS_NAMES,'ab',[6.41,2.17]):
        ax.axvline(100,color='#7E8990',ls=(0,(3,2)),lw=.7)
        for y,(base,metric) in enumerate(rows):
            vals=100-subset(gains,dataset=ds,baseline=base,metric=metric).reduction_pct.to_numpy()
            mean,sd=stats(vals)
            ax.plot([mean,100],[y,y],color=BLUE,lw=1.3,zorder=1)
            ax.scatter(vals,y+np.linspace(-.05,.05,8),s=7,color=GREY,zorder=2)
            ax.errorbar(mean,y,xerr=sd,fmt='D',color=BLUE,markersize=4,capsize=1.7,elinewidth=.8,zorder=3)
            ax.scatter([100],[y],s=17,facecolors='white',edgecolors='#71818C',zorder=4)
            ax.text(.03,y-.27,f'↓{100-mean:.2f}%',transform=ax.get_yaxis_transform(),ha='left',va='bottom',color=BLUE)
        ax.set(xlim=(low,highlim),ylim=(3.5,-.75),yticks=np.arange(4),yticklabels=labels,xlabel='配对误差指数（对照=100）')
        ax.set_xticks([50,75,100,125] if highlim>=125 else [50,75,100])
        ax.tick_params(axis='y',length=0,pad=4)
        ax.set_title(f'({letter}) {name}',loc='left',pad=10)
        ax.text(.5,-.32,f'参数量 / LightTS = {ratio:.2f}%',transform=ax.transAxes,ha='center',va='top')
    fig.text(.55,.98,'空心圆：对照；菱形与误差线：本文均值 ± 样本标准差；灰点：单次配对',ha='center',va='top')
    export(fig,'C',2,'基线归一化哑铃图',axes=list(axs))

def c3():
    fig,axs=plt.subplots(2,2,figsize=(138/25.4,84/25.4))
    fig.subplots_adjust(left=.105,right=.985,bottom=.16,top=.84,wspace=.37,hspace=.95)
    for r,metric in enumerate(['mae','mean_shortfall']):
        for c,ds in enumerate(DS):
            ax=axs[r,c];ends=[]
            for x,model in enumerate(MODELS):
                vals=subset(high,dataset=ds,model=model)[metric].to_numpy();mean,sd=stats(vals)
                ends.extend([vals.min(),vals.max(),mean-sd,mean+sd])
                proposed=model=='dlinear_scale'
                ax.scatter(x+np.linspace(-.12,.12,8),vals,color=BLUE if proposed else GREY,s=6,alpha=.6,linewidth=0,zorder=2)
                ax.errorbar(x,mean,yerr=sd,fmt='D' if proposed else 'o',color=BLUE if proposed else '#75838D',
                    markerfacecolor=BLUE if proposed else 'white',markersize=4 if proposed else 3.2,capsize=1.8,elinewidth=.8,zorder=3)
            ref=subset(high,dataset=ds,model='dlinear')[metric].mean()
            ax.axhline(ref,color='#809099',lw=.6,ls=(0,(3,3)),zorder=0)
            span=max(ends)-min(ends);lo=min(ends)-.1*span;hi=max(ends)+.28*span
            ax.set(ylim=(lo,hi),xlim=(-.45,4.55),xticks=np.arange(5),xticklabels=['DLinear','固定\n等权','全局\n权重','恒定\n路由','本文\n方法'])
            ax.yaxis.set_major_locator(MaxNLocator(3))
            ax.tick_params(axis='x',length=0,pad=4)
            ax.get_xticklabels()[-1].set_color(BLUE)
            metricname='MAE' if metric=='mae' else 'AUE'
            reduction=subset(hg,dataset=ds,baseline='dlinear',metric=metric).reduction_pct.mean()
            ax.set_title(f'({"abcd"[r*2+c]}) {DS_NAMES[c]} · {metricname}',loc='left',pad=7)
            ax.text(.98,.96,f'较DLinear降低{reduction:.2f}%',transform=ax.transAxes,ha='right',va='top',color=BLUE)
    fig.text(.55,.985,'小点：8次重复；大点与误差线：均值 ± 样本标准差；虚线：DLinear均值',ha='center',va='top')
    fig.text(.55,.028,'两个指标分别呈现，本文方法的平均误差均最低',ha='center',va='bottom')
    export(fig,'C',3,'高需求双指标小倍图',axes=list(axs.flat))

def c4():
    fig,axs=plt.subplots(2,4,figsize=(138/25.4,86/25.4),sharey='row')
    fig.subplots_adjust(left=.115,right=.98,bottom=.13,top=.77,wspace=.26,hspace=.84)
    wi=week.set_index(['model','seed'])
    for r,metric in enumerate(['mse','mae']):
        all_values=week['all_'+metric].to_numpy();span=all_values.max()-all_values.min()
        lo=all_values.min()-.15*span;hi=all_values.max()+.15*span
        for c,model in enumerate(MODELS[:-1]):
            ax=axs[r,c]
            x=np.array([wi.loc[(model,s),'all_'+metric] for s in SEEDS])
            y=np.array([wi.loc[('dlinear_scale',s),'all_'+metric] for s in SEEDS])
            assert (x>y).all()
            for a,b in zip(x,y):ax.plot([0,1],[a,b],color='#B7C7CE',alpha=.7,lw=.65,marker='o',markersize=1.9,zorder=1)
            for pos,vals,color,marker in [(0,x,'#71818C','o'),(1,y,BLUE,'D')]:
                mean,sd=stats(vals)
                ax.errorbar(pos,mean,yerr=sd,fmt=marker,color=color,markersize=3.5,
                    markerfacecolor=color if pos else 'white',capsize=1.7,elinewidth=.85,zorder=3)
                lo=min(lo,mean-sd-.05*span);hi=max(hi,mean+sd+.05*span)
            gain=subset(wg,baseline=model,metric=metric).reduction_pct.mean()
            ax.set(xlim=(-.3,1.3),ylim=(lo,hi),xticks=[0,1],xticklabels=['对照','本文'])
            ax.tick_params(axis='x',length=0,pad=4)
            ax.yaxis.set_major_locator(MaxNLocator(3))
            ax.set_title(f'({"abcdefgh"[r*4+c]}) {NAMES[c]}\n降低{gain:.2f}%',loc='left',pad=5)
            if c==0:ax.set_ylabel('标准化'+metric.upper())
    fig.text(.55,.985,'GÉANT · 168 h：细线连接同一种子的对照与本文结果',ha='center',va='top')
    fig.text(.55,.925,'圆/菱形与误差线：均值 ± 样本标准差；每个面板保留全部8次配对',ha='center',va='top')
    fig.text(.55,.028,'每次配对均降低：4种对照 × 2项指标 × 8个种子',ha='center',va='bottom')
    export(fig,'C',4,'一周逐种子配对小倍图',axes=list(axs.flat))


def main():
    (QA/'figure_contract.md').write_text('''# Alternative figure contracts

Use the established Python-only backend. This is a reference-figure task: never edit the accepted Word manuscript. All final-width plots are 138 mm with journal Songti/Times text at least 7.5 pt and editable PDF/SVG. Source record counts: 96 core/ablation records (48 baseline records eligible for figure 2), 80 high-demand records, 40 weekly absolute records, 64 baseline paired metric comparisons, 128 high-demand paired comparisons and 64 weekly comparisons. All displayed groups use every matched seed 42–49. Standard deviation is sample SD, not uncertainty of a mean or significance. No density estimation, significance badges, simulated data or exclusions.

A: tight evidence matrices. Figure 2 compares mean paired reductions and SD across two baselines and datasets, with deterministic LightTS parameter ratios. Figure 3 compares all four controls using mean paired high-demand reductions and SD. Figure 4 combines every control's absolute mean/SD and paired percentage mean/SD; proposed absolute mean/SD is in each metric heading. Matrix shading encodes paired mean percentage only and has a colorbar. Cell text retains variability; raw points are available in the other alternatives and complete CSV source data.

B: joint-error and pairing planes. Figure 2 has MSE on x and MAE on y; figure 3 MAE on x and AUE on y; all individual seeds, model means and both marginal SDs are plotted. Lower-left means lower errors; these are error-error planes, never claims of parameter dominance over DLinear. Parameter ratios to LightTS are deterministic footer statements. Figure 4 plots matched control error on x and proposed error on y. Its diagonal is the equality reference; all 32 matched points per metric lie below it, based on eight seeds and four controls, not 32 independent trials.

C: anchor comparisons and small multiples. Figure 2 uses per-seed error index 100×proposed/control; control=100 anchors each dumbbell, endpoint and SD are across all eight index values. Figure 3 separates metric and dataset in a 2×2 layout, with all raw values, means and sample SDs. Figure 4 uses four control columns and two metric rows; lines connect the same seed across the two models and are explicitly pairing links, never continuous-method trends. Common row scales retain all absolute errors. Means and sample SDs overlay each paired panel.

Export 9 reference figures plus 3 overview boards, source CSV, concise Chinese reading notes and a PDF comparison booklet. Authoritative scientific plots retain fixed physical dimensions; overview boards are comparison aids, not manuscript-ready figures. Run physical alignment, PDF glyph and collision audits and inspect every panel and grayscale before delivery. Keep any font-family source-linter mismatch documented: the provided Chinese journal typography takes precedence over generic sans-serif defaults.
''',encoding='utf-8')
    requested=sys.argv[1:] or ['A2','A3','A4','B2','B3','B4','C2','C3','C4']
    funcs={'A2':a2,'A3':a3,'A4':a4,'B2':b2,'B3':b3,'B4':b4,'C2':c2,'C3':c3,'C4':c4}
    for tag in requested:funcs[tag]()
    path=QA/'exports.json'
    existing=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    merged={r['tag']:r for r in existing}
    merged.update({r['tag']:r for r in EXPORTS})
    path.write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA

if __name__=='__main__':main()
