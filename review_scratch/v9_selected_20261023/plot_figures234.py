from pathlib import Path
import json
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
contract=json.loads((QA/'data_audit.json').read_text(encoding='utf-8'))
DATA=Path(contract['assets'])
OUT=Path('C:\\Users\\Quant\\Desktop\\Paper2026_1\\paper_template\\长春工程学院学报(自然科学版)\\逐项修订_20261023\\V9_图表源文件')
sys.path.insert(0,r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment

mpl.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','SimSun'],'font.sans-serif':['Arial','SimSun'],'font.size':7.5,
    'axes.labelsize':7.5,'axes.titlesize':7.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
    'legend.fontsize':7.5,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
    'xtick.major.width':.6,'ytick.major.width':.6,'figure.facecolor':'white','savefig.facecolor':'white'})
BLUE='#237B98'; ORANGE='#B77B35'; GREY='#AAB3BA'; DARK='#39434A'
MODELS=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
NAMES=['DLinear','固定等权','全局权重','恒定路由','本文方法']
panels=[]

def polish(fig):
    for t in fig.findobj(match=Text):
        t.set_fontfamily(['SimSun'] if any('\u4e00'<=c<='\u9fff' for c in t.get_text()) else ['Times New Roman'])
        t.set_fontsize(7.5)

def export(fig,number,stem):
    polish(fig)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        fig.canvas.draw()
        missing=[str(w.message) for w in captured if 'Glyph' in str(w.message)]
    assert not missing, missing
    alignment=require_matplotlib_panel_alignment(fig,json_out=QA/f'figure{number}_alignment.json',
        overlay_svg=QA/f'figure{number}_alignment.svg',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    assert alignment['verdict']=='PASS'

    for axis in fig.axes:
        for tick in axis.xaxis.get_major_ticks():
            assert tick._tickdir == 'in'
    (QA/f'figure{number}_geometry.json').write_text(json.dumps([
        {'xlim': list(axis.get_xlim()), 'ylim': list(axis.get_ylim()),
         'xticks': list(axis.get_xticks()), 'yticks': list(axis.get_yticks()),
         'lines': [{'x': list(line.get_xdata()), 'y': list(line.get_ydata())} for line in axis.lines],
         'collections': [collection.get_offsets().tolist() for collection in axis.collections]}
        for axis in fig.axes], ensure_ascii=False, indent=2, default=float), encoding='utf-8')

    prefix=OUT/stem
    fig.savefig(prefix.with_suffix('.pdf'))
    fig.savefig(prefix.with_suffix('.svg'))
    fig.savefig(prefix.with_suffix('.png'),dpi=600)
    fig.savefig(prefix.with_suffix('.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(QA/f'figure{number}_preview.png',dpi=300)
    # Grayscale is a QA-only view of the authoritative Python render.
    with Image.open(QA/f'figure{number}_preview.png') as im:
        im.convert('L').save(QA/f'figure{number}_grayscale.png')
    width,height=fig.get_size_inches()*25.4
    panels.append(dict(figure=number,stem=stem,width_mm=float(width),height_mm=float(height),alignment='PASS',glyph_warnings=missing))
    plt.close(fig)


def figure2():
    data=pd.read_csv(DATA/'图2_配对相对降幅.csv')
    assert len(data)==64
    fig,axes=plt.subplots(1,2,figsize=(138/25.4,54.61/25.4))
    fig.subplots_adjust(left=.175,right=.985,bottom=.29,top=.81,wspace=.76)
    rows=[('dlinear','mse'),('dlinear','mae'),('lightts','mse'),('lightts','mae')]
    ticks=['DLinear · MSE','DLinear · MAE','LightTS · MSE','LightTS · MAE']
    all_values=data.reduction_pct.to_numpy()
    low=min(-5,np.floor(all_values.min()/10)*10)
    high=max(60,np.ceil(all_values.max()/10)*10)
    for ax,ds,title,ratio in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT'],[6.41,2.17]):
        for y,(control,metric) in enumerate(rows):
            g=data[(data.dataset==ds)&(data.baseline==control)&(data.metric==metric)].sort_values('seed')
            assert g.seed.tolist()==list(range(42,50))
            v=g.reduction_pct.to_numpy();mean=v.mean();sd=v.std(ddof=1)
            ax.scatter(v,y+np.linspace(-.065,.065,8),s=7,color=GREY,linewidth=0,zorder=2)
            ax.errorbar(mean,y,xerr=sd,fmt='D',markersize=3.8,color=BLUE,elinewidth=.85,capsize=1.7,
                markeredgecolor='white',markeredgewidth=.35,zorder=3)
            ax.text(.98,y-.27,f'{mean:.2f}%',transform=ax.get_yaxis_transform(),ha='right',va='bottom',color=BLUE)
        ax.axvline(0,color='#7B8389',ls=(0,(3,2)),lw=.65,zorder=0)
        ax.set(xlim=(low,high),ylim=(3.48,-.8),yticks=np.arange(4),yticklabels=ticks,
            xlabel='相对误差降低率/%')
        ax.set_xticks(np.arange(np.ceil(low/20)*20,high+.1,20))
        ax.set_title(title,loc='left',pad=10)
        ax.tick_params(axis='y',length=0,pad=3)
        ax.tick_params(axis='x',direction='in',length=2.5,pad=3)
        ax.text(.5,-.45,f'参数量 / LightTS = {ratio:.2f}%',transform=ax.transAxes,ha='center',va='bottom')
    fig.legend(handles=[Line2D([],[],marker='o',ls='none',color=GREY,markersize=3,label='单次配对'),
        Line2D([],[],marker='D',color=BLUE,markersize=3.8,lw=.85,label='均值 ± 样本标准差')],
        loc='upper center',bbox_to_anchor=(.56,1.01),ncol=2,frameon=False,handlelength=1.8,columnspacing=1.6)
    export(fig,2,'图2_多基线误差降幅与参数比例')


def figure3():
    data=pd.read_csv(DATA/'图3_高需求全部种子.csv')
    assert len(data)==80
    fig,axes=plt.subplots(1,2,figsize=(138/25.4,67.31/25.4))
    fig.subplots_adjust(left=.135,right=.985,bottom=.255,top=.82,wspace=.52)
    metrics=[('mae','MAE','o',BLUE,-.13),('mean_shortfall','AUE','s',ORANGE,.13)]
    for ax,ds,title in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
        endpoints=[]
        for metric,label,marker,color,offset in metrics:
            ref=data[(data.dataset==ds)&(data.model=='dlinear')][metric].mean()
            ax.axvline(ref,color=color,ls=(0,(3,3)),lw=.6,alpha=.65,zorder=0)
            for y,model in enumerate(MODELS):
                g=data[(data.dataset==ds)&(data.model==model)].sort_values('seed')
                assert g.seed.tolist()==list(range(42,50))
                v=g[metric].to_numpy();mean=v.mean();sd=v.std(ddof=1)
                endpoints.extend([v.min(),v.max(),mean-sd,mean+sd])
                proposed=model=='dlinear_scale'
                ax.scatter(v,y+offset+np.linspace(-.037,.037,8),marker=marker,s=6,
                    color=color if proposed else GREY,alpha=.55,linewidth=0,zorder=2)
                ax.errorbar(mean,y+offset,xerr=sd,fmt=marker,markersize=4.2 if proposed else 3.5,
                    color=color if proposed else '#76838E',markerfacecolor=color if proposed else 'white',
                    markeredgewidth=.7,elinewidth=1 if proposed else .65,capsize=1.7,zorder=3)
        step=.02 if ds=='abilene' else .1
        lower=np.floor((min(endpoints)-step*.25)/step)*step
        upper=np.ceil((max(endpoints)+step*.25)/step)*step
        ax.set(xlim=(lower,upper),ylim=(4.55,-.55),yticks=np.arange(5),yticklabels=NAMES,
            xlabel='标准化误差（局部范围）')
        ax.set_xticks(np.arange(lower,upper+step/2,step if ds=='geant' else step*2))
        ax.set_title(title,loc='left',pad=10)
        ax.tick_params(axis='y',length=0,pad=4)
        ax.tick_params(axis='x',direction='in',length=2.5,pad=3)
        ax.get_yticklabels()[-1].set_color(BLUE)
    handles=[Line2D([],[],marker='o',color=DARK,markerfacecolor='white',ls='none',markersize=3.5,label='MAE'),
        Line2D([],[],marker='s',color=DARK,markerfacecolor='white',ls='none',markersize=3.5,label='AUE'),
        Line2D([],[],marker='o',color=GREY,ls='none',markersize=2.6,label='单次重复'),
        Line2D([],[],marker='o',color=DARK,lw=.7,markersize=3,label='均值 ± 样本标准差')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,1.01),ncol=4,frameon=False,
        handlelength=1.4,columnspacing=.8,handletextpad=.35)
    fig.text(.54,.035,'Abilene相对DLinear：MAE降低13.96%，AUE降低16.07%',ha='center',va='bottom')
    export(fig,3,'图3_高需求局部范围点图')


def figure4():
    absolute=pd.read_csv(DATA/'图4_168h绝对误差全部种子.csv')
    paired=pd.read_csv(DATA/'图4_168h配对降幅.csv')
    assert len(absolute)==40 and len(paired)==64
    fig,axes=plt.subplots(2,2,figsize=(138/25.4,66/25.4))
    fig.subplots_adjust(left=.15,right=.89,bottom=.12,top=.855,wspace=.55,hspace=.75)
    for row,metric in enumerate(['mse','mae']):
        ax=axes[row,0];bounds=[]
        for y,model in enumerate(MODELS):
            g=absolute[absolute.model==model].sort_values('seed')
            assert g.seed.tolist()==list(range(42,50))
            v=g['all_'+metric].to_numpy();mean=v.mean();sd=v.std(ddof=1)
            proposed=model=='dlinear_scale';color=BLUE if proposed else '#75818B'
            bounds.extend([v.min(),v.max(),mean-sd,mean+sd])
            ax.scatter(v,y+np.linspace(-.06,.06,8),s=5.5,color=BLUE if proposed else GREY,
                alpha=.6,linewidth=0,zorder=2)
            ax.errorbar(mean,y,xerr=sd,fmt='D' if proposed else 'o',color=color,
                markersize=4 if proposed else 3.2,markerfacecolor=color if proposed else 'white',
                markeredgewidth=.65,elinewidth=.9 if proposed else .65,capsize=1.6,zorder=3)
        unit=.1 if metric=='mse' else .05
        low=np.floor((min(bounds)-unit*.3)/unit)*unit
        high=np.ceil((max(bounds)+unit*.3)/unit)*unit
        ax.set(xlim=(low,high),ylim=(4.65,-.55),yticks=np.arange(5),yticklabels=NAMES,
            xlabel='标准化误差（越小越好）')
        tickstep=.2 if metric=='mse' else .1
        ax.set_xticks(np.arange(np.ceil(low/tickstep)*tickstep,high+.001,tickstep))
        proposed_mean=absolute[absolute.model=='dlinear_scale']['all_'+metric].mean()
        ax.set_title(f'({"a" if row==0 else "c"}) {metric.upper()}（本文{proposed_mean:.3f}）',loc='left',pad=8)
        ax.tick_params(axis='y',length=0,pad=4)
        ax.tick_params(axis='x',direction='in',length=2,pad=2)
        ax.get_yticklabels()[-1].set_color(BLUE)
        ax=axes[row,1]
        for y,model in enumerate(MODELS[:-1]):
            g=paired[(paired.baseline==model)&(paired.metric==metric)].sort_values('seed')
            v=g.reduction_pct.to_numpy();assert len(v)==8 and (v>0).all()
            mean=v.mean();sd=v.std(ddof=1)
            ax.scatter(v,y+np.linspace(-.06,.06,8),s=6,color=GREY,linewidth=0,zorder=2)
            ax.errorbar(mean,y,xerr=sd,fmt='D',color=BLUE,markersize=3.7,
                markeredgecolor='white',markeredgewidth=.35,elinewidth=.85,capsize=1.6,zorder=3)
            ax.text(1.035,y,f'{mean:.2f}%',transform=ax.get_yaxis_transform(),ha='left',va='center',color=BLUE)
        maximum=50 if metric=='mse' else 25
        assert paired[paired.metric==metric].reduction_pct.max()<maximum
        ax.axvline(0,color='#7B8389',ls=(0,(3,2)),lw=.65,zorder=0)
        ax.set(xlim=(-maximum*.025,maximum),ylim=(3.43,-.85),yticks=np.arange(4),yticklabels=NAMES[:-1],
            xlabel='相对误差降低率/%')
        ax.set_xticks(np.arange(0,maximum+.01,10 if metric=='mse' else 5))
        ax.set_title(f'({"b" if row==0 else "d"}) {metric.upper()}配对降幅',loc='left',pad=8)
        ax.tick_params(axis='y',length=0,pad=4)
        ax.tick_params(axis='x',direction='in',length=2,pad=2)
    fig.legend(handles=[Line2D([],[],marker='o',color=GREY,ls='none',markersize=2.7,label='单次重复'),
        Line2D([],[],marker='D',color=BLUE,markersize=3.5,lw=.85,label='均值 ± 样本标准差')],
        loc='upper center',bbox_to_anchor=(.55,1.015),ncol=2,frameon=False,
        handlelength=1.5,columnspacing=1.5)
    export(fig,4,'图4_一周绝对误差与配对降幅')


if __name__=='__main__':
    figure2();figure3();figure4()
    (QA/'figure_export_audit.json').write_text(json.dumps(panels,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(panels,ensure_ascii=False))
