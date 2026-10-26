"""Compact grouped bars and parameter counts from eight actual runs."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

OUT=Path(__file__).resolve().parent
RES=OUT.parents[2]/'abilene_forecasting/results'
MODELS=['dlinear','lightts','dlinear_scale']
NAMES=['DLinear','LightTS','本文方法']
COLORS=['#A6B1BA','#D5B69D','#007FA3']
SEEDS=range(42,50)
plt.rcParams.update({'font.family':['Microsoft YaHei','DejaVu Sans'],
 'font.size':10,'axes.labelsize':10,'axes.unicode_minus':False,
 'axes.edgecolor':'#AAB6BF','axes.linewidth':.7,'text.color':'#253640',
 'axes.labelcolor':'#253640','xtick.color':'#253640','ytick.color':'#253640',
 'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white'})

fig,axes=plt.subplots(1,2,figsize=(10.7,4.95))
fig.subplots_adjust(left=.075,right=.985,bottom=.31,top=.84,wspace=.24)
fig.legend(handles=[Patch(facecolor=c,label=n) for c,n in zip(COLORS,NAMES)],
           loc='upper center',bbox_to_anchor=(.54,.985),ncol=3,frameon=False,
           handlelength=1.35,columnspacing=2.6)
audit={}
for ax,ds,label in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT']):
 values={};params=[]
 for m in MODELS:
  vv=[]
  for seed in SEEDS:
   o=json.loads((RES/ds/f'{m}_seed{seed}'/'metrics.json').read_text(encoding='utf-8'))
   vv.append([o['test_normalized']['mse'],o['test_normalized']['mae']])
  values[m]=np.array(vv);params.append(o['parameters'])
 alltop=[]
 for j,(m,c) in enumerate(zip(MODELS,COLORS)):
  vv=values[m];mean=vv.mean(axis=0);sd=vv.std(axis=0,ddof=1)
  xx=np.arange(2)+(j-1)*.23
  ax.bar(xx,mean,width=.195,color=c,edgecolor='white',linewidth=.5,zorder=3)
  ax.errorbar(xx,mean,yerr=sd,fmt='none',ecolor='#425866',elinewidth=.8,
              capsize=2.7,capthick=.8,zorder=4)
  for x,y,s in zip(xx,mean,sd):
   ax.annotate(f'{y:.3f}',(x,y+s),xytext=(0,5),textcoords='offset points',
               ha='center',va='bottom',fontsize=9.3,color='#007FA3' if j==2 else '#425866',
               weight='bold' if j==2 else 'normal')
  alltop.extend(mean+sd)
 maxv=max(alltop)
 for k in range(2):
  gain=(1-values['dlinear_scale'][:,k]/values['lightts'][:,k]).mean()*100
  y=max(values[m][:,k].mean()+values[m][:,k].std(ddof=1) for m in MODELS)+maxv*.15
  x1=k;x2=k+.23
  ax.plot([x1,x1,x2,x2],[y-maxv*.018,y,y,y-maxv*.018],c='#007FA3',lw=.9,zorder=5)
  ax.text((x1+x2)/2,y+maxv*.018,f'−{gain:.2f}%',color='#007FA3',weight='bold',
          fontsize=9.6,ha='center',va='bottom')
 ax.set(xlim=(-.49,1.49),ylim=(0,maxv*1.31),xticks=[0,1],xticklabels=['MSE','MAE'],ylabel='标准化误差')
 ax.text(0,1.035,label,transform=ax.transAxes,fontsize=11,weight='bold',va='bottom')
 ax.spines[['top','right']].set_visible(False)
 ax.set_axisbelow(True);ax.grid(axis='y',color='#E8EDF0',lw=.6)
 ax.tick_params(axis='x',length=0,pad=8,labelsize=10.5)
 ax.tick_params(axis='y',length=3,width=.7)
 table=ax.table(cellText=[[f'{p:,}' for p in params]],rowLabels=['参数量'],
                colLabels=NAMES,cellLoc='center',rowLoc='center',bbox=[0,-.40,1,.22])
 table.auto_set_font_size(False);table.set_fontsize(9.3)
 for (row,col),cell in table.get_celld().items():
  cell.set_edgecolor('#E1E7EB');cell.set_linewidth(.55)
  cell.set_facecolor('#F6F8F9' if row==0 else 'white')
  if col==2:
   cell.get_text().set_color('#007FA3');cell.get_text().set_fontweight('bold')
 audit[ds]={'parameters':dict(zip(MODELS,params)),
            'mean':{m:values[m].mean(axis=0).tolist() for m in MODELS},
            'paired_gain_vs_lightts_pct':((1-values['dlinear_scale']/values['lightts']).mean(axis=0)*100).tolist()}
fig.savefig(OUT/'fig2_G_compact_bars.png',dpi=240)
fig.savefig(OUT/'fig2_G_compact_bars.svg')
plt.close(fig)
(OUT/'fig2_G_data_checks.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
