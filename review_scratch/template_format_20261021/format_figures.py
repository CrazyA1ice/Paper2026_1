from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2];QA=Path(__file__).resolve().parent
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/模板规范修订_20261021'
ASSETS=OUT/'图表源文件';ASSETS.mkdir(parents=True,exist_ok=True)
SKILL=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
sys.path.insert(0,str(SKILL))
from audit_panel_alignment import require_matplotlib_panel_alignment
mpl.rcParams.update({'font.family':['Times New Roman','SimSun'],'font.size':7.5,'axes.labelsize':7.5,'axes.titlesize':7.5,'legend.fontsize':7.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'xtick.direction':'in','ytick.direction':'in','xtick.major.width':.6,'ytick.major.width':.6,'xtick.major.size':0,'ytick.major.size':3,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,'figure.facecolor':'white','savefig.facecolor':'white','mathtext.fontset':'stix'})
records=[]

def save(fig,number,desc,multi=True):
    for obj in fig.findobj(match=Text):
        obj.set_fontfamily(['SimSun'] if any('\u4e00'<=c<='\u9fff' for c in obj.get_text()) else ['Times New Roman'])
        obj.set_fontsize(7.5)
    for ax in fig.axes:
        ax.grid(False);ax.tick_params(direction='in')
    fig.canvas.draw()
    if multi:
        result=require_matplotlib_panel_alignment(fig,json_out=QA/f'figure{number}_alignment.json',overlay_svg=QA/f'figure{number}_alignment.svg',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
        assert result['verdict']=='PASS'
    prefix=ASSETS/f'图{number}'
    for suffix in ['svg','pdf']:
        fig.savefig(prefix.with_suffix('.'+suffix))
    fig.savefig(prefix.with_suffix('.png'),dpi=600)
    fig.savefig(prefix.with_suffix('.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    records.append({'figure':number,'width_cm':13.8,'height_cm':float(fig.get_figheight()*2.54),'nominal_font_pt':7.5,'evidence':desc,'png':str(prefix.with_suffix('.png')),'pdf':str(prefix.with_suffix('.pdf'))})
    plt.close(fig)

source=ROOT/'paper_figures/fig1_A_border_spacing_20261007/render_source.py'
code=source.read_text(encoding='utf8').split('    compact.OUT = OUT\n')[0]
code=code.replace('OUT = Path(__file__).resolve().parent','OUT = TASK_ASSETS').replace('ROOT = OUT.parents[1]','ROOT = TASK_ROOT')
namespace={'__file__':str(source),'TASK_ASSETS':ASSETS,'TASK_ROOT':ROOT}
exec(compile(code,str(source),'exec'),namespace)
fig=namespace['fig'];fig.set_size_inches(138/25.4,88/25.4)
for label in fig.findobj(match=Text):
    if '未来' in label.get_text():label.set_text('未来24步')
save(fig,1,'Original schematic: all labels, example curves and connections preserved; typography only.',False)

prior=ROOT/'paper_template/长春工程学院学报(自然科学版)/主稿独立投稿修订_20261021/存档数据与图表'
summary=pd.read_csv(prior/'图2_均值与标准差.csv');paired=pd.read_csv(prior/'图2_逐种子相对降幅.csv')
assert len(paired)==12
fig,axes=plt.subplots(1,3,figsize=(138/25.4,2.15));fig.subplots_adjust(left=.06,right=.985,bottom=.18,top=.83,wspace=.43)
x=np.arange(2)
for ax,metric,title,upper in zip(axes[:2],['mse','mae'],['(a) MSE降低率/%','(b) MAE降低率/%'],[60,50]):
    g=summary[summary.metric==metric].set_index('dataset').loc[['abilene','geant']]
    means=g['mean'].to_numpy();sd=g.sample_sd.to_numpy()
    for ds,mean,spread in zip(['abilene','geant'],means,sd):
        values=paired[(paired.dataset==ds)&(paired.metric==metric)].relative_reduction_pct
        assert len(values)==3 and np.isclose(mean,values.mean()) and np.isclose(spread,values.std(ddof=1))
    ax.bar(x,means,width=.52,color='#287B9A',edgecolor='#185A73',linewidth=.5,zorder=2)
    ax.errorbar(x,means,yerr=sd,fmt='none',ecolor='#202020',elinewidth=.7,capsize=2.2,capthick=.7,zorder=3)
    for xi,mean,spread in zip(x,means,sd):ax.text(xi,mean+spread+upper*.035,f'{mean:.2f}',ha='center',va='bottom')
    ax.set_ylim(0,upper);ax.set_yticks(np.arange(0,upper+1,10));ax.set_title(title,loc='left',pad=9)
g=summary[summary.metric=='mse'].set_index('dataset').loc[['abilene','geant']]
ratios=g.parameter_ratio_pct.to_numpy();ax=axes[2]
ax.bar(x,ratios,width=.52,color='#287B9A',edgecolor='#185A73',linewidth=.5)
ax.axhline(100,color='#727272',linewidth=.75,linestyle=(0,(3,2)))
ax.text(.5,104,'LightTS = 100%',ha='center',va='bottom')
for xi,value in zip(x,ratios):ax.text(xi,value+4,f'{value:.2f}',ha='center',va='bottom')
ax.set_ylim(0,120);ax.set_yticks(np.arange(0,121,20));ax.set_title('(c) 参数比例/%',loc='left',pad=9)
for ax in axes:ax.set_xticks(x,['Abilene','GÉANT']);ax.set_xlim(-.65,1.65);ax.tick_params(axis='x',pad=7)
save(fig,2,'Same twelve paired reductions, three seeds per dataset/metric; sample SD. Deterministic parameter ratios unchanged.')

models=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
names=['DLinear','固定\n等权','全局\n权重','恒定\n路由','本文\n方法']
data_path=ROOT/'abilene_forecasting/results/high_demand_analysis/per_seed.csv';data=pd.read_csv(data_path)
assert len(data)==80 and not data.duplicated(['dataset','model','seed']).any()
fig,axes=plt.subplots(1,2,figsize=(138/25.4,2.65));fig.subplots_adjust(left=.09,right=.985,bottom=.23,top=.79,wspace=.3)
plotted=[]
for ax,ds,title,upper,ticks in zip(axes,['abilene','geant'],['(a) Abilene','(b) GÉANT'],[.25,.8],[np.arange(0,.251,.05),np.arange(0,.801,.2)]):
    for metric,label,color,offset in [('mae','MAE','#5D91B5',-.18),('mean_shortfall','平均低估误差','#DAAA70',.18)]:
        means=[];sd=[]
        for model in models:
            values=data[(data.dataset==ds)&(data.model==model)].sort_values('seed')
            assert values.seed.tolist()==list(range(42,50))
            means.append(values[metric].mean());sd.append(values[metric].std(ddof=1))
            plotted.append({'dataset':ds,'model':model,'metric':metric,'mean':means[-1],'sd':sd[-1],'n':8})
        positions=np.arange(5)+offset
        ax.bar(positions,means,width=.34,color=color,edgecolor='white',linewidth=.45,label=label,zorder=2)
        ax.errorbar(positions,means,yerr=sd,fmt='none',ecolor='#424B53',elinewidth=.65,capsize=1.8,capthick=.65,zorder=3)
        assert np.max(np.asarray(means)+sd)<upper
    ax.set(xlim=(-.6,4.6),ylim=(0,upper),xticks=np.arange(5),xticklabels=names,yticks=ticks,ylabel='标准化误差')
    ax.set_title(title,loc='left',pad=8);ax.tick_params(axis='x',pad=6)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.52,1),ncol=2,frameon=False,handlelength=1.4,columnspacing=2.2)
save(fig,3,'All eighty high-demand dataset/model/seed rows. Same means and sample SD; only fonts, tick direction and grid styling changed.')
pd.DataFrame(plotted).to_csv(ASSETS/'图3绘图数据.csv',index=False,encoding='utf-8-sig')

week=ROOT/'paper_template/长春工程学院学报(自然科学版)/长预测核验与修订_20261021/数据与图表'
frame=pd.read_csv(week/'图5_全部八种子数据.csv');summary_week=pd.read_csv(week/'图5_均值与样本标准差.csv')
assert len(frame)==40 and summary_week.model.tolist()==models
fig,axes=plt.subplots(1,2,figsize=(138/25.4,2.4));fig.subplots_adjust(left=.075,right=.992,bottom=.215,top=.86,wspace=.28)
x=np.arange(5)
for ax,metric,title,upper,ticks in zip(axes,['mse','mae'],['(a) MSE','(b) MAE'],[1.4,.72],[np.arange(0,1.41,.2),np.arange(0,.721,.12)]):
    means=summary_week[f'common_{metric}_mean'].to_numpy();sd=summary_week[f'common_{metric}_sd'].to_numpy()
    for i,model in enumerate(models):
        values=frame[frame.model==model][f'common_{metric}']
        assert len(values)==8 and np.isclose(values.mean(),means[i]) and np.isclose(values.std(ddof=1),sd[i])
    ax.bar(x,means,width=.64,color=['#AEB8C2']*4+['#287B9A'],edgecolor=['#66717B']*4+['#185A73'],linewidth=.5,zorder=2)
    ax.errorbar(x,means,yerr=sd,fmt='none',ecolor='#252525',elinewidth=.7,capsize=2.2,capthick=.7,zorder=3)
    for xi,mean,spread in zip(x,means,sd):ax.text(xi,mean+spread+upper*.026,f'{mean:.3f}',ha='center',va='bottom')
    ax.set_xticks(x,names);ax.set_xlim(-.65,4.65);ax.set_ylim(0,upper);ax.set_yticks(ticks);ax.set_title(title,loc='left',pad=8);ax.tick_params(axis='x',pad=6)
save(fig,4,'Same forty GÉANT H168 model/seed rows; all five models and eight seeds; mean and sample SD unchanged.')
audit={'figures':records,'high_demand_source_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'paired_seed_rows':12,'high_demand_seed_rows':80,'weekly_seed_rows':40,'new_experiments':False,'changed_numeric_results':False}
(QA/'figure_manifest.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(audit,ensure_ascii=False))
