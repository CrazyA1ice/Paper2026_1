"""Three dense Figure 2 candidates using the original eight paired runs."""
from pathlib import Path
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle
from matplotlib.colors import LinearSegmentedColormap

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RES=ROOT/'abilene_forecasting/results'
SEEDS=list(range(42,50))
MODELS=['dlinear','lightts','dlinear_scale']
OURS=MODELS[-1]
NAMES={'dlinear':'DLinear','lightts':'LightTS',OURS:'本文方法'}
COLORS={'dlinear':'#82919D','lightts':'#BA8966',OURS:'#007FA3'}
MARKERS={'dlinear':'o','lightts':'s',OURS:'D'}
BLUE=COLORS[OURS]
INK='#263541'
GRID='#E5EBEF'
plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],
 'font.size':10,'axes.labelsize':10.5,'xtick.labelsize':9.3,'ytick.labelsize':9.3,
 'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
 'axes.edgecolor':'#ADBAC3','axes.linewidth':.7,'axes.unicode_minus':False,
 'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white'})

data={};inputs=[]
for ds in ['abilene','geant']:
 for model in MODELS:
  rr=[]
  for seed in SEEDS:
   path=RES/ds/f'{model}_seed{seed}'/'metrics.json'
   o=json.loads(path.read_text(encoding='utf-8'))
   assert o['seed']==seed and o['pred_len']==24
   rr.append([o['test_normalized']['mse'],o['test_normalized']['mae'],o['parameters']])
   inputs.append(path)
  data[ds,model]=np.array(rr,dtype=float)

def gain(ds,baseline,k):
 return (1-data[ds,OURS][:,k]/data[ds,baseline][:,k])*100

def clean(ax,grid='y'):
 ax.spines[['top','right']].set_visible(False)
 ax.tick_params(length=3,width=.7,pad=5)
 ax.set_axisbelow(True)
 if grid: ax.grid(axis=grid,color=GRID,lw=.65)

def panel(ax,label):
 ax.text(0,1.045,label,transform=ax.transAxes,weight='bold',fontsize=11.5,va='bottom')

def model_legend(fig):
 h=[Line2D([],[],color=COLORS[m],marker=MARKERS[m],lw=1.5,ms=6.5,label=NAMES[m]) for m in MODELS]
 fig.legend(handles=h,ncol=3,frameon=False,loc='upper center',bbox_to_anchor=(.53,.99),
            columnspacing=2.6,handlelength=2.3)

def save(fig,name):
 fig.savefig(OUT/f'{name}.png',dpi=220)
 fig.savefig(OUT/f'{name}.svg')
 plt.close(fig)

def error_distribution(ax,ds):
 clean(ax)
 all_values=[]
 for k in [0,1]:
  for j,m in enumerate(MODELS):
   x=k+[-.24,0,.24][j]
   v=data[ds,m][:,k];all_values.extend(v)
   vp=ax.violinplot(v,positions=[x-.024],widths=.20,showextrema=False,bw_method=.6)
   body=vp['bodies'][0]
   vertices=body.get_paths()[0].vertices
   vertices[:,0]=np.minimum(vertices[:,0],x-.024)
   body.set_facecolor(COLORS[m]);body.set_alpha(.30);body.set_edgecolor('none')
   # Eight deterministic offsets keep every observed run visible.
   xx=x+.018+np.linspace(0,.065,8)
   ax.scatter(xx,v,s=19,c=COLORS[m],alpha=.68,edgecolor='white',lw=.3,zorder=3)
   ax.errorbar(x-.012,v.mean(),yerr=v.std(ddof=1),fmt=MARKERS[m],color=COLORS[m],
               ms=6,capsize=2.4,lw=1.15,zorder=5)
   ax.annotate(f'{v.mean():.3f}',(x-.01,v.max()),xytext=(0,10),textcoords='offset points',
               ha='center',va='bottom',fontsize=9.1,color=COLORS[m],
               weight='bold' if m==OURS else 'normal')
 lo=min(all_values);hi=max(all_values);span=hi-lo
 ax.set(xticks=[0,1],xticklabels=['MSE','MAE'],ylabel='标准化误差',
        xlim=(-.43,1.44),ylim=(max(0,lo-span*.12),hi+span*.24))
 ax.tick_params(axis='x',length=0,pad=9,labelsize=11)

def gain_forest(ax,ds):
 clean(ax,'x')
 specs=[('dlinear',0,'DLinear · MSE'),('dlinear',1,'DLinear · MAE'),
        ('lightts',0,'LightTS · MSE'),('lightts',1,'LightTS · MAE'),('lightts',2,'LightTS · 参数量')]
 for i,(base,k,_) in enumerate(specs):
  v=gain(ds,base,k);color=BLUE if base=='lightts' else '#6F8490'
  ax.hlines(i,0,v.mean(),color=color,lw=6,alpha=.12,zorder=1)
  if k<2:
   ax.scatter(v,i+np.linspace(-.10,.10,8),s=17,color=color,alpha=.38,zorder=2)
   ax.errorbar(v.mean(),i,xerr=v.std(ddof=1),fmt=['D','o'][k],ms=6.5,
               color=color,capsize=3,lw=1.3,zorder=4)
  else:ax.scatter(v.mean(),i,s=60,c=color,marker='s',edgecolor='white',lw=.8,zorder=4)
  ax.text(127,i,f'{v.mean():.2f}%',ha='right',va='center',color=color,
          fontsize=10,weight='bold' if base=='lightts' else 'normal')
 ax.axvline(0,color='#9DAAB3',lw=.8)
 ax.set(yticks=range(5),yticklabels=[s[2] for s in specs],xticks=[0,20,40,60,80,100],
        xlim=(-15,130),ylim=(4.6,-.6),xlabel='相对降幅 / %')

# D: two raw-error panels and two paired-gain panels, with parameters included.
fig,axs=plt.subplots(2,2,figsize=(12.4,7.9),gridspec_kw={'height_ratios':[1.08,1]})
fig.subplots_adjust(left=.12,right=.98,bottom=.09,top=.87,wspace=.36,hspace=.43)
model_legend(fig)
for col,ds in enumerate(['abilene','geant']):
 error_distribution(axs[0,col],ds)
 panel(axs[0,col],f'({chr(97+col)}) '+('Abilene' if col==0 else 'GÉANT'))
 gain_forest(axs[1,col],ds)
 panel(axs[1,col],f'({chr(99+col)}) '+('Abilene' if col==0 else 'GÉANT'))
save(fig,'fig2_D_distribution_gain')

def hull(points):
 pp=sorted(set(map(tuple,points)))
 if len(pp)<=2:return np.array(pp)
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 low=[];up=[]
 for p in pp:
  while len(low)>=2 and cross(low[-2],low[-1],p)<=0:low.pop()
  low.append(p)
 for p in reversed(pp):
  while len(up)>=2 and cross(up[-2],up[-1],p)<=0:up.pop()
  up.append(p)
 return np.array(low[:-1]+up[:-1])

def gain_plane(ax,ds):
 clean(ax,'both')
 ax.axvline(0,color='#99AAB6',lw=.8);ax.axhline(0,color='#99AAB6',lw=.8)
 for base,color in [('dlinear','#8F9EAA'),('lightts',BLUE)]:
  x=gain(ds,base,0);y=gain(ds,base,1)
  poly=hull(np.c_[x,y])
  ax.add_patch(Polygon(poly,facecolor=color,edgecolor=color,lw=.9,alpha=.10,zorder=1))
  ax.scatter(x,y,c=color,s=37,alpha=.66,edgecolor='white',lw=.6,zorder=3)
  ax.scatter(x.mean(),y.mean(),marker='D' if base=='lightts' else 's',s=85,
             c=color,edgecolor='white',lw=1,zorder=5)
  if base=='lightts':
   ax.annotate(f'({x.mean():.2f}%, {y.mean():.2f}%)',(x.mean(),y.mean()),
               xytext=(0,-24),textcoords='offset points',ha='center',va='top',
               fontsize=10,weight='bold',color=color,
               bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1.2})
 ax.set(xlabel='MSE 配对降幅 / %',ylabel='MAE 配对降幅 / %',xlim=(-11,56),ylim=(-11,40))
 ax.set_xticks([0,10,20,30,40,50]);ax.set_yticks([0,10,20,30,40])

def parameter_bars(ax,ds):
 clean(ax,'x')
 base=data[ds,'lightts'][0,2]
 for i,m in enumerate(['lightts','dlinear',OURS]):
  value=data[ds,m][0,2];pct=value/base*100
  ax.barh(i,pct,height=.48,color=COLORS[m],alpha=.88 if m==OURS else .50,zorder=2)
  ax.scatter(pct,i,marker='D' if m==OURS else 'o',c=COLORS[m],s=35,zorder=4)
  ax.text(pct+2,i,f'{pct:.2f}%',ha='left',va='center',color=COLORS[m],
          fontsize=9.5,weight='bold' if m==OURS else 'normal')
 labels=[NAMES[m]+'\n'+f'{int(data[ds,m][0,2]):,}' for m in ['lightts','dlinear',OURS]]
 ax.set(xlim=(0,120),ylim=(3,-.65),yticks=[0,1,2],yticklabels=labels,
        xticks=[0,20,40,60,80,100],xlabel='相对 LightTS 的参数量 / %')
 # Bracket numerically labels the proposed parameter reduction, without prose.
 pct=data[ds,OURS][0,2]/base*100
 ax.annotate('',xy=(pct,2.66),xytext=(100,2.66),arrowprops={'arrowstyle':'|-|','color':BLUE,'lw':1.2})
 ax.text((pct+100)/2,2.50,f'−{100-pct:.2f}%',color=BLUE,weight='bold',ha='center',fontsize=11)
 ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
 for tick in ax.get_yticklabels():
  if tick.get_text().startswith('本文方法'):tick.set_color(BLUE);tick.set_fontweight('bold')

# E: two-dimensional paired benefits plus exact parameter compression.
fig,axs=plt.subplots(2,2,figsize=(12.3,7.8),gridspec_kw={'height_ratios':[1.35,.85]})
fig.subplots_adjust(left=.10,right=.98,bottom=.09,top=.87,wspace=.30,hspace=.50)
handles=[Line2D([],[],c='#8F9EAA',marker='s',linestyle='none',ms=7,label='相对 DLinear'),
         Line2D([],[],c=BLUE,marker='D',linestyle='none',ms=7,label='相对 LightTS')]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,.99),ncol=2,frameon=False,columnspacing=3)
for col,ds in enumerate(['abilene','geant']):
 gain_plane(axs[0,col],ds);panel(axs[0,col],f'({chr(97+col)}) '+('Abilene' if col==0 else 'GÉANT'))
 parameter_bars(axs[1,col],ds);panel(axs[1,col],f'({chr(99+col)}) '+('Abilene' if col==0 else 'GÉANT'))
save(fig,'fig2_E_joint_gain_compression')

def gain_profiles(ax,ds):
 clean(ax)
 for base,color in [('dlinear','#8B99A5'),('lightts',BLUE)]:
  for k,ls,mk in [(0,'-','o'),(1,'--','s')]:
   v=gain(ds,base,k)
   ax.plot(SEEDS,v,color=color,ls=ls,marker=mk,ms=4.6,lw=1.6 if base=='lightts' else 1.05,
           markeredgecolor='white',markeredgewidth=.45,zorder=3 if base=='lightts' else 2)
 ax.axhline(0,c='#A4AFB7',lw=.85)
 ax.set(xlabel='随机种子',ylabel='配对误差降幅 / %',xticks=SEEDS,xlim=(41.65,49.35),ylim=(-12,57))

cmap=LinearSegmentedColormap.from_list('relative',['#B0D8E1','#EEF5F7','#FFFFFF'])
def metric_matrix(ax,ds):
 means=np.array([data[ds,m].mean(axis=0) for m in MODELS])
 sd=np.array([data[ds,m].std(axis=0,ddof=1) for m in MODELS])
 relative=means/means[1]*100
 ax.imshow(relative,cmap=cmap,vmin=0,vmax=105,aspect='auto')
 for i in range(3):
  for k in range(3):
   s=f'{int(round(means[i,k])):,}' if k==2 else f'{means[i,k]:.3f} ± {sd[i,k]:.3f}'
   ax.text(k,i,s,ha='center',va='center',fontsize=9.6,
           color=BLUE if i==2 else INK,weight='bold' if i==2 else 'normal')
 ax.set(xticks=[0,1,2],xticklabels=['MSE','MAE','参数量'],yticks=[0,1,2],yticklabels=[NAMES[m] for m in MODELS])
 ax.xaxis.tick_top();ax.tick_params(which='both',length=0,pad=9)
 ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,3,1),minor=True)
 ax.grid(which='minor',c='white',lw=2.5)
 ax.add_patch(Rectangle((-.5,1.5),3,1,fill=False,edgecolor=BLUE,lw=1.5))
 for s in ax.spines.values():s.set_visible(False)
 for tick in ax.get_yticklabels():
  if tick.get_text()=='本文方法':tick.set_color(BLUE);tick.set_fontweight('bold')

# F: full paired-run trajectories and a compact table of absolute results.
fig,axs=plt.subplots(2,2,figsize=(12.6,7.6),gridspec_kw={'height_ratios':[1.5,.78]})
fig.subplots_adjust(left=.10,right=.98,bottom=.07,top=.85,wspace=.32,hspace=.65)
hh=[]
for base,color in [('dlinear','#8B99A5'),('lightts',BLUE)]:
 for k,ls,mk in [(0,'-','o'),(1,'--','s')]:
  hh.append(Line2D([],[],color=color,ls=ls,marker=mk,ms=5,label=f'相对{NAMES[base]} · '+['MSE','MAE'][k]))
fig.legend(handles=hh,loc='upper center',bbox_to_anchor=(.54,.99),ncol=4,frameon=False,columnspacing=1.7)
for col,ds in enumerate(['abilene','geant']):
 gain_profiles(axs[0,col],ds);panel(axs[0,col],f'({chr(97+col)}) '+('Abilene' if col==0 else 'GÉANT'))
 metric_matrix(axs[1,col],ds)
 # Keep the panel marker separate from column headings.
 axs[1,col].text(0,1.40,f'({chr(99+col)}) '+('Abilene' if col==0 else 'GÉANT'),
                 transform=axs[1,col].transAxes,weight='bold',fontsize=11.5,va='bottom')
save(fig,'fig2_F_seed_profiles_summary')

audit={'seeds':SEEDS,'datasets':{},'files':[]}
for ds in ['abilene','geant']:
 audit['datasets'][ds]={
  'absolute':{m:{'mean':data[ds,m].mean(axis=0).tolist(),'sd':data[ds,m].std(axis=0,ddof=1).tolist()} for m in MODELS},
  'paired_mean_reductions_pct':{b:{name:float(gain(ds,b,k).mean()) for k,name in enumerate(['mse','mae','parameters'])} for b in ['dlinear','lightts']}}
assert abs(audit['datasets']['abilene']['paired_mean_reductions_pct']['lightts']['mse']-25.77)<.01
assert abs(audit['datasets']['geant']['paired_mean_reductions_pct']['lightts']['mse']-43.74)<.01
audit['files']=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]
(OUT/'fig2_dense_data_checks.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated D, E, F from 48 original metrics files; paired gains verified.')
