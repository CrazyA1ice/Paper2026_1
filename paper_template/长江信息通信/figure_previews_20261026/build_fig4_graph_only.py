"""Graph-only Figure 4: absolute errors and every paired H=168 result."""
from pathlib import Path
import csv
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SOURCE=ROOT/'abilene_forecasting/results/long_horizon_20261021/per_seed_scores.csv'
MODELS=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
NAMES=['DLinear','固定等权','全局权重','恒定路由','本文方法']
COLORS=['#A6B1BA','#D5B69D','#B8C5AF','#BDB4C9','#007FA3']
BLUE=COLORS[-1]
SEEDS=list(range(42,50))
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
    rows=[r for r in csv.DictReader(f) if r['dataset']=='geant' and int(r['horizon'])==168]
data={}
for m in MODELS:
    rr=sorted([r for r in rows if r['model']==m],key=lambda r:int(r['seed']))
    assert [int(r['seed']) for r in rr]==SEEDS
    assert all(int(r['n_common_origins'])==307 for r in rr)
    data[m]=np.array([[float(r['common_mse']),float(r['common_mae'])] for r in rr])

plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],
    'font.size':10,'axes.labelsize':10,'axes.edgecolor':'#AAB6BF','axes.linewidth':.7,
    'xtick.labelsize':9,'ytick.labelsize':9,'text.color':'#253640',
    'axes.labelcolor':'#253640','xtick.color':'#253640','ytick.color':'#253640',
    'axes.unicode_minus':False,'svg.fonttype':'none','pdf.fonttype':42,
    'savefig.facecolor':'white'})

fig,axs=plt.subplots(2,2,figsize=(11.7,6.8),gridspec_kw={'height_ratios':[1,1]})
fig.subplots_adjust(left=.075,right=.985,bottom=.09,top=.875,wspace=.24,hspace=.39)
fig.legend(handles=[Patch(facecolor=c,label=n) for c,n in zip(COLORS,NAMES)],
           loc='upper center',bbox_to_anchor=(.53,.99),ncol=5,frameon=False,
           handlelength=1.3,columnspacing=1.8)

def clean(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y',color='#E8EDF0',lw=.6)
    ax.tick_params(length=3,width=.7)

def panel(ax,text):
    ax.text(0,1.035,text,transform=ax.transAxes,weight='bold',fontsize=11,va='bottom')

audit={'dataset':'geant','horizon':168,'n_common_origins':307,'seeds':SEEDS,
       'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'metrics':{},'tables_in_figure':0}
for k,metric in enumerate(['MSE','MAE']):
    ax=axs[0,k];clean(ax);panel(ax,f'({chr(97+k)}) {metric}')
    tops=[]
    for j,(m,c) in enumerate(zip(MODELS,COLORS)):
        v=data[m][:,k];mean=v.mean();sd=v.std(ddof=1)
        ax.bar(j,mean,width=.66,color=c,edgecolor='white',lw=.5,zorder=3)
        ax.errorbar(j,mean,yerr=sd,fmt='none',ecolor='#425866',elinewidth=.85,
                    capsize=3,capthick=.85,zorder=4)
        ax.annotate(f'{mean:.3f}',(j,mean+sd),xytext=(0,5),textcoords='offset points',
                    ha='center',va='bottom',fontsize=9.5,color=BLUE if m==MODELS[-1] else '#425866',
                    weight='bold' if m==MODELS[-1] else 'normal')
        tops.append(mean+sd)
    ax.set(xlim=(-.65,4.65),ylim=(0,max(tops)*1.19),xticks=[],ylabel='标准化误差')

    ax=axs[1,k];clean(ax);panel(ax,f'({chr(99+k)}) {metric} 配对降幅')
    gains=[]
    for b in MODELS[:-1]:
        g=(1-data[MODELS[-1]][:,k]/data[b][:,k])*100
        assert len(g)==8 and np.all(g>0)
        gains.append(g)
    ymax=50 if k==0 else 26
    for j,g in enumerate(gains):
        mean=g.mean();sd=g.std(ddof=1)
        ax.bar(j,mean,width=.65,color=BLUE,alpha=.24,edgecolor='none',zorder=2)
        ax.errorbar(j,mean,yerr=sd,fmt='D',ms=4.5,color=BLUE,elinewidth=1,
                    capsize=3,capthick=.9,zorder=5)
        # Eight real observations use fixed horizontal offsets; y remains exact.
        ax.scatter(j+np.linspace(-.22,.22,8),g,s=23,color=BLUE,alpha=.72,
                   edgecolor='white',linewidth=.45,zorder=4)
        ax.text(j,ymax*.055,f'{mean:.2f}%',ha='center',va='center',fontsize=10,
                color='#005E7C',weight='bold',zorder=6)
    ax.axhline(0,color='#8F9FA9',lw=.8,zorder=3)
    ax.set(xlim=(-.6,3.6),ylim=(0,ymax),xticks=range(4),xticklabels=NAMES[:-1],
           ylabel='相对误差降幅 / %')
    ax.tick_params(axis='x',length=0,pad=8)
    audit['metrics'][metric]={
        'absolute_mean':{m:float(data[m][:,k].mean()) for m in MODELS},
        'absolute_sample_sd':{m:float(data[m][:,k].std(ddof=1)) for m in MODELS},
        'paired_gains':{b:{'values':g.tolist(),'mean':float(g.mean()),'sample_sd':float(g.std(ddof=1)),
                           'positive_count':int((g>0).sum())} for b,g in zip(MODELS[:-1],gains)}}

assert abs(audit['metrics']['MSE']['paired_gains']['dlinear']['mean']-23.16)<.01
assert abs(audit['metrics']['MAE']['paired_gains']['dlinear']['mean']-11.16)<.01
assert len(fig.axes)==4 and all(len(ax.tables)==0 for ax in fig.axes)
stem='fig4_J_graph_only_20261027'
fig.savefig(OUT/f'{stem}.png',dpi=240)
fig.savefig(OUT/f'{stem}.svg')
plt.close(fig)
(OUT/f'{stem}_checks.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Figure 4 graph-only preview saved; 4 panels, 0 tables, 64 paired points; all paired gains positive.')
