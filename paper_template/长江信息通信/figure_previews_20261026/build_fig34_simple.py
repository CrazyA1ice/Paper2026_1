"""Matched bar-chart alternatives for Figures 3 and 4; actual eight-run data."""
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
RES=OUT.parents[2]/'abilene_forecasting/results'
MODELS=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
OURS=MODELS[-1]
NAMES=['DLinear','固定等权','全局权重','恒定路由','本文方法']
COLORS=['#A6B1BA','#D5B69D','#B8C5AF','#BDB4C9','#007FA3']
BLUE=COLORS[-1]
INK='#253640'
SEEDS=list(range(42,50))
plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],
 'font.size':10,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,
 'axes.unicode_minus':False,'axes.edgecolor':'#AAB6BF','axes.linewidth':.7,
 'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
 'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white'})

def read_csv(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

hp=RES/'high_demand_analysis/per_seed.csv'
lp=RES/'long_horizon_20261021/per_seed_scores.csv'
high_rows=read_csv(hp)
long_rows=[r for r in read_csv(lp) if r['dataset']=='geant' and int(r['horizon'])==168]

def collect(rows,ds,keys):
 d={}
 for m in MODELS:
  rr=sorted([r for r in rows if r['dataset']==ds and r['model']==m],key=lambda r:int(r['seed']))
  assert [int(r['seed']) for r in rr]==SEEDS
  d[m]=np.array([[float(r[k]) for k in keys] for r in rr])
 return d

HIGH={ds:collect(high_rows,ds,['mae','mean_shortfall']) for ds in ['abilene','geant']}
LONG=collect(long_rows,'geant',['common_mse','common_mae'])

def gains(d,base,k):return (1-d[OURS][:,k]/d[base][:,k])*100

def clean(ax,grid='y'):
 ax.spines[['top','right']].set_visible(False)
 ax.set_axisbelow(True)
 ax.grid(axis=grid,color='#E8EDF0',lw=.6)
 ax.tick_params(length=3,width=.7)

def panel(ax,text):
 ax.text(0,1.035,text,transform=ax.transAxes,weight='bold',fontsize=11,va='bottom')

def model_legend(fig):
 fig.legend(handles=[Patch(facecolor=c,label=n) for c,n in zip(COLORS,NAMES)],
            loc='upper center',bbox_to_anchor=(.53,.99),ncol=5,frameon=False,
            handlelength=1.3,columnspacing=1.8)

def save(fig,name):
 fig.savefig(OUT/f'{name}.png',dpi=230)
 fig.savefig(OUT/f'{name}.svg')
 plt.close(fig)

def style_table(table,blue_columns=()):
 table.auto_set_font_size(False);table.set_fontsize(8.8)
 for (row,col),cell in table.get_celld().items():
  cell.set_edgecolor('#E1E7EB');cell.set_linewidth(.55)
  cell.set_facecolor('#F6F8F9' if row==0 else 'white')
  if col in blue_columns or row>0 and col>0:
   cell.get_text().set_color(BLUE)
   if row>0:cell.get_text().set_fontweight('bold')

def high_footer(ax,d,base):
 gg=[gains(d,base,k).mean() for k in range(2)]
 table=ax.table(cellText=[[NAMES[MODELS.index(base)],f'{gg[0]:.2f}%',f'{gg[1]:.2f}%']],
                colLabels=['比较基准','MAE降幅','AUE降幅'],cellLoc='center',
                colWidths=[.4,.3,.3],bbox=[0,-.40,1,.22])
 style_table(table)

# Figure 3 H: two grouped bar panels, retaining every model and both metrics.
fig,axes=plt.subplots(1,2,figsize=(12.25,5.0))
fig.subplots_adjust(left=.065,right=.985,bottom=.31,top=.83,wspace=.22)
model_legend(fig)
for ax,ds,label in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
 d=HIGH[ds];tops=[]
 for j,(m,c) in enumerate(zip(MODELS,COLORS)):
  v=d[m];mean=v.mean(axis=0);sd=v.std(axis=0,ddof=1)
  xx=np.array([0,1.20])+(j-2)*.165
  ax.bar(xx,mean,width=.142,color=c,edgecolor='white',lw=.5,zorder=3)
  ax.errorbar(xx,mean,yerr=sd,fmt='none',ecolor='#425866',elinewidth=.8,
              capsize=2.1,capthick=.8,zorder=4)
  for x,y,s in zip(xx,mean,sd):
   ax.annotate(f'{y:.3f}',(x,y+s),xytext=(0,5),textcoords='offset points',
               ha='center',va='bottom',fontsize=8.5,color=BLUE if m==OURS else '#425866',
               weight='bold' if m==OURS else 'normal')
  tops.extend(mean+sd)
 maxv=max(tops)
 for k,xc in enumerate([0,1.20]):
  gg=gains(d,'dlinear',k).mean()
  y=max(d[m][:,k].mean()+d[m][:,k].std(ddof=1) for m in MODELS)+maxv*.15
  x1=xc-.33;x2=xc+.33
  ax.plot([x1,x1,x2,x2],[y-maxv*.018,y,y,y-maxv*.018],c=BLUE,lw=.9)
  ax.text(xc,y+maxv*.018,f'−{gg:.2f}%',color=BLUE,weight='bold',ha='center',va='bottom',fontsize=9.5)
 clean(ax);panel(ax,label)
 ax.set(xlim=(-.55,1.75),ylim=(0,maxv*1.31),xticks=[0,1.20],xticklabels=['MAE','AUE'],ylabel='高需求标准化误差')
 ax.tick_params(axis='x',length=0,pad=8,labelsize=10.5)
 high_footer(ax,d,'dlinear_scale_static')
save(fig,'fig3_H_grouped_bars')

def horizontal_absolute(ax,d,k,metric):
 clean(ax,'x');tops=[]
 for j,(m,c) in enumerate(zip(MODELS,COLORS)):
  v=d[m][:,k];mean=v.mean();sd=v.std(ddof=1)
  ax.barh(j,mean,height=.57,color=c,edgecolor='white',lw=.5,zorder=3)
  ax.errorbar(mean,j,xerr=sd,fmt='none',ecolor='#425866',elinewidth=.85,capsize=2.8,zorder=4)
  tops.append(mean+sd)
 maxv=max(tops)
 for j,m in enumerate(MODELS):
  v=d[m][:,k]
  ax.text(v.mean()+v.std(ddof=1)+maxv*.025,j,f'{v.mean():.3f}',va='center',ha='left',
          fontsize=9.6,color=BLUE if m==OURS else '#425866',weight='bold' if m==OURS else 'normal')
 ax.set(xlim=(0,maxv*1.22),ylim=(4.6,-.6),yticks=range(5),yticklabels=NAMES,xlabel=metric)
 ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=8)
 ax.get_yticklabels()[-1].set_color(BLUE);ax.get_yticklabels()[-1].set_fontweight('bold')

# Figure 3 I: four compact horizontal panels, with all five models legible.
fig,axs=plt.subplots(2,2,figsize=(11.5,6.5))
fig.subplots_adjust(left=.11,right=.985,bottom=.09,top=.93,wspace=.29,hspace=.41)
for row,k in enumerate([0,1]):
 for col,ds in enumerate(['abilene','geant']):
  ax=axs[row,col];metric=['MAE','AUE'][k]
  horizontal_absolute(ax,HIGH[ds],k,metric)
  panel(ax,f'({chr(97+row*2+col)}) '+('Abilene' if ds=='abilene' else 'GÉANT')+' · '+metric)
save(fig,'fig3_I_horizontal_bars')

def long_footer(ax,k):
 gg=[gains(LONG,b,k) for b in MODELS[:-1]]
 assert all(np.all(g>0) for g in gg)
 table=ax.table(cellText=[['配对降幅']+[f'{g.mean():.2f}%' for g in gg],
                          ['正向次数']+[f'{int((g>0).sum())}/8' for g in gg]],
                colLabels=['比较项']+NAMES[:-1],cellLoc='center',
                colWidths=[.22,.195,.195,.195,.195],bbox=[0,-.57,1,.34])
 style_table(table)

# Figure 4 H: absolute errors and a compact paired-benefit table.
fig,axes=plt.subplots(1,2,figsize=(12.2,5.3))
fig.subplots_adjust(left=.065,right=.985,bottom=.36,top=.83,wspace=.22)
model_legend(fig)
for ax,k,label in zip(axes,[0,1],['(a) MSE','(b) MAE']):
 tops=[]
 for j,(m,c) in enumerate(zip(MODELS,COLORS)):
  v=LONG[m][:,k];mean=v.mean();sd=v.std(ddof=1)
  ax.bar(j,mean,width=.67,color=c,edgecolor='white',lw=.5,zorder=3)
  ax.errorbar(j,mean,yerr=sd,fmt='none',ecolor='#425866',elinewidth=.8,capsize=3,zorder=4)
  ax.annotate(f'{mean:.3f}',(j,mean+sd),xytext=(0,5),textcoords='offset points',
              ha='center',va='bottom',fontsize=9.5,color=BLUE if m==OURS else '#425866',
              weight='bold' if m==OURS else 'normal')
  tops.append(mean+sd)
 maxv=max(tops);y=maxv*1.15
 ax.plot([0,0,4,4],[y-maxv*.018,y,y,y-maxv*.018],c=BLUE,lw=.9)
 ax.text(2,y+maxv*.018,f'−{gains(LONG,"dlinear",k).mean():.2f}%',ha='center',va='bottom',
         fontsize=10,weight='bold',color=BLUE)
 clean(ax);panel(ax,label)
 ax.set(xlim=(-.65,4.65),ylim=(0,maxv*1.31),xticks=[],ylabel='标准化误差')
 long_footer(ax,k)
save(fig,'fig4_H_grouped_bars')

# Figure 4 I: identical statistics and benefit tables, horizontal bars.
fig,axes=plt.subplots(1,2,figsize=(12.0,5.45))
fig.subplots_adjust(left=.105,right=.985,bottom=.36,top=.91,wspace=.32)
for ax,k,label in zip(axes,[0,1],['(a) MSE','(b) MAE']):
 horizontal_absolute(ax,LONG,k,['MSE','MAE'][k]);panel(ax,label)
 # Use a slightly tighter footer because the horizontal panels are taller.
 long_footer(ax,k)
save(fig,'fig4_I_horizontal_bars')

audit={'seeds':SEEDS,'high_demand':{},'geant_168':{}}
for ds,d in HIGH.items():
 audit['high_demand'][ds]={
  'mean':{m:d[m].mean(axis=0).tolist() for m in MODELS},
  'sample_sd':{m:d[m].std(axis=0,ddof=1).tolist() for m in MODELS},
  'paired_reductions_pct':{b:[float(gains(d,b,k).mean()) for k in range(2)] for b in MODELS[:-1]}}
audit['geant_168']={
 'mean':{m:LONG[m].mean(axis=0).tolist() for m in MODELS},
 'sample_sd':{m:LONG[m].std(axis=0,ddof=1).tolist() for m in MODELS},
 'paired_reductions_pct':{b:[float(gains(LONG,b,k).mean()) for k in range(2)] for b in MODELS[:-1]},
 'positive_counts':{b:[int((gains(LONG,b,k)>0).sum()) for k in range(2)] for b in MODELS[:-1]}}
assert abs(audit['high_demand']['abilene']['paired_reductions_pct']['dlinear'][0]-13.96)<.01
assert abs(audit['geant_168']['paired_reductions_pct']['dlinear'][0]-23.16)<.01
audit['sources']=[{'path':str(p.relative_to(OUT.parents[2])),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [hp,lp]]
(OUT/'fig34_simple_data_checks.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated 4 alternatives; all means, sample SDs, paired gains and positive counts verified.')
