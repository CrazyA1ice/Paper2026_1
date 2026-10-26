"""Figure 2 redesign: aligned parallel coordinates, real paired H=24 results."""
from pathlib import Path
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RES=ROOT/'abilene_forecasting/results'
SEEDS=list(range(42,50))
MODELS=['lightts','dlinear','dlinear_scale']
NAMES={'lightts':'LightTS','dlinear':'DLinear','dlinear_scale':'本文方法'}
COLORS={'lightts':'#B98864','dlinear':'#7F8D99','dlinear_scale':'#007FA3'}
MARKERS={'lightts':'s','dlinear':'o','dlinear_scale':'D'}
BLUE=COLORS['dlinear_scale']
INK='#263541'
plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],
    'font.size':10.5,'axes.labelsize':11,'text.color':INK,'axes.labelcolor':INK,
    'xtick.color':INK,'ytick.color':INK,'axes.unicode_minus':False,
    'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white',
    'savefig.facecolor':'white'})

data={};inputs=[]
for ds in ['abilene','geant']:
    for model in MODELS:
        rows=[]
        for seed in SEEDS:
            p=RES/ds/f'{model}_seed{seed}'/'metrics.json'
            o=json.loads(p.read_text(encoding='utf-8'))
            assert o['seed']==seed and o['pred_len']==24
            rows.append([o['test_normalized']['mse'],o['test_normalized']['mae'],o['parameters']])
            inputs.append(p)
        data[ds,model]=np.array(rows,dtype=float)

fig,axes=plt.subplots(1,2,figsize=(11.9,4.95))
fig.subplots_adjust(left=.077,right=.985,bottom=.18,top=.79,wspace=.24)
handles=[Line2D([],[],color=COLORS[m],marker=MARKERS[m],markersize=7,
                lw=2.2 if m=='dlinear_scale' else 1.4,
                linestyle='-' if m=='dlinear_scale' else '--',label=NAMES[m]) for m in MODELS]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,.972),
           ncol=3,frameon=False,columnspacing=3,handlelength=2.7)
audit={}
for ax,ds,label in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
    norm={m:data[ds,m]/data[ds,'lightts']*100 for m in MODELS}
    audit[ds]={m:{'paired_relative_mean_pct':norm[m].mean(axis=0).tolist(),
                  'paired_relative_sd_pct':norm[m].std(axis=0,ddof=1).tolist()}
               for m in MODELS}
    ax.text(0,1.075,label,transform=ax.transAxes,weight='bold',fontsize=12,va='bottom')
    ax.set_xlim(-.21,2.23);ax.set_ylim(-4,114)
    ax.set_xticks([0,1,2],['MSE','MAE','参数量'])
    ax.set_yticks([0,20,40,60,80,100])
    ax.set_ylabel('相对 LightTS 的比例 / %',labelpad=10)
    ax.spines[['top','right','bottom']].set_visible(False)
    ax.spines['left'].set_color('#B7C1C8');ax.spines['left'].set_linewidth(.7)
    ax.tick_params(axis='x',length=0,pad=13,labelsize=12)
    ax.tick_params(axis='y',length=3,color='#B7C1C8')
    ax.set_axisbelow(True)
    ax.grid(axis='y',color='#E9EDF0',lw=.65)
    for x in [0,1,2]:ax.axvline(x,color='#DFE6EB',lw=.75,zorder=0)
    ax.axhline(100,color=COLORS['lightts'],lw=1,linestyle=(0,(4,3)),alpha=.6,zorder=1)
    for m in MODELS:
        values=norm[m];mean=values.mean(axis=0);sd=values.std(axis=0,ddof=1)
        is_ours=m=='dlinear_scale'
        ax.plot([0,1,2],mean,color=COLORS[m],lw=2.6 if is_ours else 1.35,
                linestyle='-' if is_ours else (0,(4,3)),alpha=1 if is_ours else .9,
                zorder=5 if is_ours else 3)
        if m!='lightts':
            # Deterministic horizontal offsets separate eight paired observations.
            offset=np.linspace(-.05,.05,8)+(0.028 if is_ours else -.028)
            for k in [0,1]:
                ax.scatter(k+offset,values[:,k],s=15,color=COLORS[m],
                           alpha=.3 if is_ours else .19,zorder=2)
            ax.errorbar([0,1],mean[:2],yerr=sd[:2],fmt='none',capsize=3,
                        color=COLORS[m],lw=.9,alpha=.65,zorder=4)
        ax.scatter([0,1,2],mean,s=75 if is_ours else 43,marker=MARKERS[m],
                   color=COLORS[m],edgecolor='white',linewidth=1,zorder=7 if is_ours else 6)
        if is_ours:
            for k,y in enumerate(mean):
                xy=(0,-23) if k<2 else (0,11)
                ax.annotate(f'{y:.2f}%',(k,y),xytext=xy,textcoords='offset points',
                            ha='center',va='top' if k<2 else 'bottom',color=BLUE,
                            fontsize=11,weight='bold',zorder=9,
                            bbox={'facecolor':'white','edgecolor':'none','pad':1.0,'alpha':.92})
    ax.text(2.12,100,'100%',color=COLORS['lightts'],fontsize=10,ha='left',va='center')

name='fig2_C_parallel_profile'
fig.savefig(OUT/f'{name}.png',dpi=220)
fig.savefig(OUT/f'{name}.svg')
plt.close(fig)
assert abs(audit['abilene']['dlinear_scale']['paired_relative_mean_pct'][0]-(100-25.77))<.01
assert abs(audit['geant']['dlinear_scale']['paired_relative_mean_pct'][0]-(100-43.74))<.01
(OUT/'fig2_C_data_checks.json').write_text(json.dumps({
    'seeds':SEEDS,'metrics':['MSE','MAE','parameters'],
    'normalization':'For each seed, divide each metric by the corresponding LightTS value, multiply by 100, then summarize eight seeds.',
    'data':audit,'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]
},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
