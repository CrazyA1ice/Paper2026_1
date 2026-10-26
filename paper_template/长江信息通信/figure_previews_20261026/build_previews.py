from pathlib import Path
import csv
import json
import re
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RES = ROOT / 'abilene_forecasting' / 'results'
MODELS = ['dlinear', 'dlinear_scale_static', 'dlinear_scale_global', 'dlinear_scale_constant_router', 'dlinear_scale']
NAMES = {'dlinear':'DLinear', 'lightts':'LightTS', 'dlinear_scale_static':'固定等权', 'dlinear_scale_global':'全局权重', 'dlinear_scale_constant_router':'恒定路由', 'dlinear_scale':'本文方法'}
COLORS = {'dlinear':'#7C8A96', 'lightts':'#C58A59', 'dlinear_scale_static':'#ABA798', 'dlinear_scale_global':'#839B9A', 'dlinear_scale_constant_router':'#8D89A5', 'dlinear_scale':'#007FA3'}
MARKERS = {'dlinear':'o', 'lightts':'s', 'dlinear_scale_static':'s', 'dlinear_scale_global':'^', 'dlinear_scale_constant_router':'P', 'dlinear_scale':'D'}
OURS = 'dlinear_scale'
SEEDS = list(range(42,50))
BLUE = COLORS[OURS]
INK = '#263541'
GRID = '#E4E9ED'
plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'], 'font.size':10.5,
    'axes.labelsize':11, 'axes.titlesize':12, 'axes.edgecolor':'#A9B4BD', 'axes.linewidth':.7,
    'xtick.color':INK, 'ytick.color':INK, 'text.color':INK, 'axes.labelcolor':INK,
    'svg.fonttype':'none', 'pdf.fonttype':42, 'axes.unicode_minus':False,
    'figure.facecolor':'white', 'savefig.facecolor':'white'})

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

inputs=[]
base24={}
for ds in ['abilene','geant']:
    for model in ['dlinear','lightts',OURS]:
        rows=[]
        for seed in SEEDS:
            path=RES/ds/f'{model}_seed{seed}'/'metrics.json'
            obj=json.loads(path.read_text(encoding='utf-8'))
            rows.append({'seed':seed, 'mse':obj['test_normalized']['mse'],
                         'mae':obj['test_normalized']['mae'], 'parameters':obj['parameters']})
            inputs.append(path)
        base24[(ds,model)]=rows
hp=RES/'high_demand_analysis/per_seed.csv'
lp=RES/'long_horizon_20261021/per_seed_scores.csv'
high=read_csv(hp)
long=[r for r in read_csv(lp) if int(r['horizon'])==168]
inputs.extend([hp,lp])

def vals(rows, ds, model, key):
    rr=sorted([r for r in rows if r['dataset']==ds and r['model']==model],key=lambda r:int(r['seed']))
    assert [int(r['seed']) for r in rr]==SEEDS
    return np.array([float(r[key]) for r in rr])

def v24(ds,model,key):
    return np.array([r[key] for r in base24[(ds,model)]])

def clean(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.tick_params(length=3, width=.7, pad=5)
    ax.set_axisbelow(True)

def panel(ax,label):
    ax.text(0,1.04,label,transform=ax.transAxes,fontsize=12,fontweight='bold',va='bottom')

def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=190)
    fig.savefig(OUT/f'{name}.svg')
    plt.close(fig)

def legend(fig,models):
    handles=[Line2D([],[],color=COLORS[m],marker=MARKERS[m],linestyle='none',
                    markersize=6.5,label=NAMES[m]) for m in models]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,.985),ncol=len(models),
               frameon=False,columnspacing=1.9,handletextpad=.4)

cmap=LinearSegmentedColormap.from_list('gain',['#C97663','#F0D8CF','#FAFBFC','#AEDBE2','#00779A'])
norm=TwoSlopeNorm(vmin=-45,vcenter=0,vmax=45)

def matrix(ax,arr,rowlabels,limit=45):
    norm_here=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit)
    ax.imshow(arr,cmap=cmap,norm=norm_here,aspect='auto',interpolation='nearest')
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            value=arr[i,j]
            ax.text(j,i,f'{value:.1f}',ha='center',va='center',fontsize=9.5,
                    color='white' if abs(value)>limit*.62 else INK,
                    fontweight='bold' if j==arr.shape[1]-1 else 'normal')
    ax.set(xticks=np.arange(9),xticklabels=[str(s) for s in SEEDS]+['均值'],
           yticks=np.arange(len(rowlabels)),yticklabels=rowlabels,xlabel='随机种子')
    ax.set_xticks(np.arange(-.5,arr.shape[1],1),minor=True)
    ax.set_yticks(np.arange(-.5,arr.shape[0],1),minor=True)
    ax.grid(which='minor',color='white',linewidth=2)
    ax.tick_params(which='both',length=0,pad=8)
    ax.axvline(7.5,color=INK,lw=1)
    for s in ax.spines.values():s.set_visible(False)
    return norm_here

# 图2 A：精度与参数量共同展示。两个数据集均使用相同的对数参数坐标。
fig,axes=plt.subplots(1,2,figsize=(12.4,4.7))
fig.subplots_adjust(left=.075,right=.985,bottom=.17,top=.79,wspace=.28)
legend(fig,['dlinear','lightts',OURS])
for ax,ds,label in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
    clean(ax);panel(ax,label)
    ax.grid(axis='y',color=GRID,lw=.7)
    for m in ['dlinear','lightts',OURS]:
        x=v24(ds,m,'parameters')[0]
        yy=v24(ds,m,'mse')
        ax.scatter(np.repeat(x,8),yy,s=16,color=COLORS[m],alpha=.22,zorder=2)
        ax.errorbar(x,yy.mean(),yerr=yy.std(ddof=1),color=COLORS[m],marker=MARKERS[m],
                    ms=9 if m==OURS else 7.5,capsize=4,elinewidth=1.5,zorder=4)
        ax.annotate(f'{x:,}',(x,yy.mean()),xytext=(0,-26 if m==OURS else 13),
                    textcoords='offset points',ha='center',fontsize=10,
                    color=COLORS[m],fontweight='bold' if m==OURS else 'normal')
    ax.set_xscale('log');ax.set_xlim(3300,650000)
    ax.set_xticks([5000,10000,50000,100000,500000],['5k','10k','50k','100k','500k'])
    ax.minorticks_off()
    ax.set(xlabel='参数量',ylabel='MSE')
    ymin=min(v24(ds,m,'mse').min() for m in ['dlinear','lightts',OURS])
    ymax=max(v24(ds,m,'mse').max() for m in ['dlinear','lightts',OURS])
    pad=(ymax-ymin)*.19
    ax.set_ylim(ymin-pad,ymax+pad)
save(fig,'fig2_A_accuracy_parameter')

# 图2 B：同种子配对降幅，保留全部MSE和MAE结果。
fig,axes=plt.subplots(1,2,figsize=(13.1,4.7))
fig.subplots_adjust(left=.14,right=.96,bottom=.30,top=.80,wspace=.47)
gain24={}
for ax,ds,label in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
    aa=[];labs=[]
    for b in ['dlinear','lightts']:
        for key in ['mse','mae']:
            g=(1-v24(ds,OURS,key)/v24(ds,b,key))*100
            gain24[f'{ds}/{b}/{key}']=float(g.mean())
            aa.append(np.r_[g,g.mean()]);labs.append(f'{NAMES[b]} · {key.upper()}')
    matrix(ax,np.array(aa),labs,70);panel(ax,label)
sm=plt.cm.ScalarMappable(cmap=cmap,norm=TwoSlopeNorm(vmin=-70,vcenter=0,vmax=70))
cax=fig.add_axes([.35,.12,.32,.028]);cb=fig.colorbar(sm,cax=cax,orientation='horizontal',ticks=[-60,-30,0,30,60])
cb.set_label('配对误差降幅 / %',labelpad=3);cb.outline.set_visible(False)
save(fig,'fig2_B_paired_gain_matrix')

# 图3 A：双指标平面，同时呈现MAE与AUE及不同种子分布。
fig,axes=plt.subplots(1,2,figsize=(12.4,5.15))
fig.subplots_adjust(left=.085,right=.98,bottom=.16,top=.79,wspace=.30)
legend(fig,MODELS)
for ax,ds,label in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
    clean(ax);panel(ax,label);ax.grid(color=GRID,lw=.65)
    for m in MODELS:
        x=vals(high,ds,m,'mae');y=vals(high,ds,m,'mean_shortfall')
        ax.scatter(x,y,color=COLORS[m],s=19,alpha=.24,zorder=2)
        ax.errorbar(x.mean(),y.mean(),xerr=x.std(ddof=1),yerr=y.std(ddof=1),
                    fmt=MARKERS[m],color=COLORS[m],ms=9 if m==OURS else 6.5,
                    capsize=3,elinewidth=1.2,alpha=1 if m==OURS else .85,zorder=5 if m==OURS else 3)
    xx=vals(high,ds,OURS,'mae').mean();yy=vals(high,ds,OURS,'mean_shortfall').mean()
    ax.annotate(f'({xx:.3f}, {yy:.3f})',(xx,yy),xytext=(14,-27),textcoords='offset points',
                color=BLUE,weight='bold',fontsize=10.5,arrowprops={'arrowstyle':'-','color':BLUE,'lw':.8})
    ax.set(xlabel='高需求 MAE',ylabel='高需求 AUE')
    ax.margins(.12)
save(fig,'fig3_A_joint_error_plane')

# 图3 B：逐种子配对迁移。每条细线连接同一个种子的基线与本文结果。
fig,axes=plt.subplots(2,2,figsize=(12.0,7.3))
fig.subplots_adjust(left=.08,right=.985,bottom=.10,top=.90,wspace=.27,hspace=.42)
for index,(key,metric) in enumerate([('mae','MAE'),('mean_shortfall','AUE')]):
    for j,ds in enumerate(['abilene','geant']):
        ax=axes[index,j];clean(ax);ax.grid(axis='y',color=GRID,lw=.65)
        panel(ax,f'({chr(97+index*2+j)}) '+('Abilene' if ds=='abilene' else 'GÉANT')+' · '+metric)
        x=np.arange(5)
        vv=np.array([vals(high,ds,m,key) for m in MODELS])
        for k in range(8):
            ax.plot(x,vv[:,k],lw=.8,color='#BECAD0',alpha=.70,zorder=1)
        for z,m in enumerate(MODELS):
            ax.scatter(np.full(8,z),vv[z],s=24,color=COLORS[m],alpha=.55,zorder=3)
        ax.plot(x,vv.mean(axis=1),lw=2.3,color=BLUE,zorder=4)
        ax.scatter(x,vv.mean(axis=1),s=65,c=[COLORS[m] for m in MODELS],
                   edgecolor='white',linewidth=1.0,zorder=5)
        ax.set(xticks=x,xticklabels=[NAMES[m] for m in MODELS],ylabel=metric,xlim=(-.25,4.25))
        ax.tick_params(axis='x',labelsize=9.7)
        ax.margins(y=.16)
save(fig,'fig3_B_paired_trajectories')

# 图4 A：8个种子乘4种基线，完整展示逐次配对收益。
fig,axes=plt.subplots(1,2,figsize=(12.8,4.7))
fig.subplots_adjust(left=.105,right=.965,bottom=.30,top=.80,wspace=.34)
gain168={}
for ax,key,label in zip(axes,['common_mse','common_mae'],['(a) MSE','(b) MAE']):
    aa=[]
    for b in MODELS[:-1]:
        g=(1-vals(long,'geant',OURS,key)/vals(long,'geant',b,key))*100
        assert np.all(g>0)
        gain168[f'{b}/{key}']=float(g.mean())
        aa.append(np.r_[g,g.mean()])
    matrix(ax,np.array(aa),[NAMES[m] for m in MODELS[:-1]],45);panel(ax,label)
sm=plt.cm.ScalarMappable(cmap=cmap,norm=norm)
cax=fig.add_axes([.35,.12,.32,.028]);cb=fig.colorbar(sm,cax=cax,orientation='horizontal',ticks=[-40,-20,0,20,40])
cb.set_label('配对误差降幅 / %',labelpad=3);cb.outline.set_visible(False)
save(fig,'fig4_A_seed_gain_matrix')

# 图4 B：8次重复的分布和均值，半小提琴为平滑展示，并叠加全部真实散点。
fig,axes=plt.subplots(1,2,figsize=(12.3,4.9))
fig.subplots_adjust(left=.12,right=.985,bottom=.16,top=.82,wspace=.32)
for ax,key,label in zip(axes,['common_mse','common_mae'],['(a) MSE','(b) MAE']):
    clean(ax);panel(ax,label);ax.grid(axis='x',color=GRID,lw=.65)
    for i,m in enumerate(MODELS):
        v=vals(long,'geant',m,key)
        vp=ax.violinplot(v,positions=[i+.16],orientation='horizontal',widths=.72,showextrema=False,bw_method=.65)
        body=vp['bodies'][0];verts=body.get_paths()[0].vertices
        verts[:,1]=np.maximum(verts[:,1],i+.16)
        body.set_facecolor(COLORS[m]);body.set_edgecolor('none');body.set_alpha(.25 if m!=OURS else .42)
        jitter=np.linspace(-.14,.08,8)
        ax.scatter(v,i+jitter,s=23,color=COLORS[m],alpha=.72,zorder=3,edgecolor='white',linewidth=.4)
        ax.errorbar(v.mean(),i-.29,xerr=v.std(ddof=1),fmt='D',ms=6,color=COLORS[m],capsize=3,lw=1.5,zorder=4)
        ax.text(v.mean(),i+.57,f'{v.mean():.3f}',ha='center',va='center',fontsize=9.5,
                color=BLUE if m==OURS else '#64737E',weight='bold' if m==OURS else 'normal')
    ax.set(yticks=range(5),yticklabels=[NAMES[m] for m in MODELS],xlabel=label[-3:],ylim=(-.6,4.85))
    ax.invert_yaxis();ax.margins(x=.1)
    for tick,m in zip(ax.get_yticklabels(),MODELS):
        if m==OURS:tick.set_color(BLUE);tick.set_fontweight('bold')
save(fig,'fig4_B_raincloud')

assert abs(gain24['abilene/lightts/mse']-25.77)<.01
assert abs(gain24['geant/lightts/mse']-43.74)<.01
assert abs(gain168['dlinear/common_mse']-23.16)<.01
manifest={'data':'actual_saved_eight_seed_results','seeds':SEEDS,'gain24':gain24,'gain168':gain168,
          'input_files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],
          'note':'No figure titles or prose explanations are embedded. Panel identifiers, legends, metric axes, raw values and color scales are retained.'}
(OUT/'data_checks.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'generated':[p.name for p in OUT.glob('*.png')], 'gain24':gain24,'gain168':gain168},ensure_ascii=False,indent=2))
