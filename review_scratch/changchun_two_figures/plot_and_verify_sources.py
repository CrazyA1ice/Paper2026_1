from pathlib import Path
import csv, hashlib, json, shutil, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FormatStrFormatter

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/改投内容修改第一版_20261020/补充图表'
OUT.mkdir(exist_ok=True)
DATA=ROOT/'abilene_forecasting/results/high_demand_analysis'
SKILL=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
sys.path.insert(0,str(SKILL))
from audit_panel_alignment import require_matplotlib_panel_alignment

MODEL_ORDER=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
MODEL_LABELS=['DLinear','固定等权','全局权重','恒定输入路由','本文方法']
SEEDS=list(range(42,50))
per_seed=pd.read_csv(DATA/'per_seed.csv')
summary=pd.read_csv(DATA/'summary.csv')
paired=pd.read_csv(DATA/'paired_reductions.csv')
assert len(per_seed)==80 and len(summary)==10
assert set(per_seed.seed)==set(SEEDS)
assert set(per_seed.model)==set(MODEL_ORDER)
assert not per_seed.duplicated(['dataset','model','seed']).any()
assert np.isfinite(per_seed[['mae','mean_shortfall']]).all().all()
primary=[]
computed={}
for ds in ['abilene','geant']:
    computed[ds]={}
    for model in MODEL_ORDER:
        group=per_seed[(per_seed.dataset==ds)&(per_seed.model==model)].sort_values('seed')
        assert group.seed.tolist()==SEEDS
        assert group.n_high_targets.nunique()==1
        record={'dataset':ds,'model':model,'n_seeds':8}
        old=summary[(summary.dataset==ds)&(summary.model==model)].iloc[0]
        for metric in ['mae','mean_shortfall']:
            record[metric+'_mean']=float(group[metric].mean())
            record[metric+'_sd']=float(group[metric].std(ddof=1))
            assert np.isclose(record[metric+'_mean'],old[metric+'_mean'],rtol=1e-12)
            assert np.isclose(record[metric+'_sd'],old[metric+'_sd'],rtol=1e-12)
        primary.append(record)
    prop=per_seed[(per_seed.dataset==ds)&(per_seed.model=='dlinear_scale')].sort_values('seed')
    for model in MODEL_ORDER[:-1]:
        other=per_seed[(per_seed.dataset==ds)&(per_seed.model==model)].sort_values('seed')
        for metric in ['mae','mean_shortfall']:
            mean_reduction=float(np.mean((other[metric].to_numpy()-prop[metric].to_numpy())/other[metric].to_numpy()*100))
            old=paired[(paired.dataset==ds)&(paired.baseline==model)&(paired.metric==metric)].iloc[0]
            assert np.isclose(mean_reduction,old.mean_reduction_pct,rtol=1e-12)
            assert prop[metric].mean()<other[metric].mean()
            computed[ds][model+'_'+metric]=mean_reduction
for ds,expected in [('abilene',[17.22,20.49]),('geant',[3.59,6.30])]:
    assert [round(computed[ds]['dlinear_scale_global_'+m],2) for m in ['mae','mean_shortfall']]==expected

weight_rows=[]; weight_summary=[]
for ds,expected in [('abilene',[.257,.319,.424]),('geant',[.283,.318,.399])]:
    by_seed=[]
    for seed in SEEDS:
        path=ROOT/f'abilene_forecasting/results/{ds}/dlinear_scale_seed{seed}/router_weights.csv'
        weights=np.loadtxt(path,delimiter=',')
        assert weights.shape==(813 if ds=='abilene' else 451,3)
        assert np.isfinite(weights).all() and (weights>=0).all() and (weights<=1).all()
        assert np.allclose(weights.sum(axis=1),1,atol=2e-6)
        by_seed.append(weights.mean(axis=0))
        for window,values in enumerate(weights):
            for scale,value in zip([1,2,4],values):
                weight_rows.append([ds,seed,window,scale,float(value)])
    means=np.array(by_seed).mean(axis=0)
    assert np.array_equal(np.round(means,3),expected),(ds,means)
    weight_summary.append({'dataset':ds,'mean':means.tolist(),'sd_of_seed_means':np.array(by_seed).std(axis=0,ddof=1).tolist()})
with open(OUT/'图3_尺度权重源数据.csv','w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['dataset','seed','test_window_index','scale','router_weight']);writer.writerows(weight_rows)
source_image=ROOT/'review_scratch/changchun_revision/source_media/image5.png'
shutil.copy2(source_image,OUT/'图3_尺度权重分布.png')
assert source_image.read_bytes()==(OUT/'图3_尺度权重分布.png').read_bytes()

plot_data=pd.DataFrame(primary)
plot_data.to_csv(OUT/'图4_高需求预测误差_汇总.csv',index=False,encoding='utf-8-sig')
shutil.copy2(DATA/'per_seed.csv',OUT/'图4_高需求预测误差_全部种子.csv')
shutil.copy2(DATA/'paired_reductions.csv',OUT/'图4_高需求预测误差_配对降幅.csv')
shutil.copy2(DATA/'analysis_audit.json',QA/'high_demand_existing_audit.json')
for file in [Path(r'C:\Windows\Fonts\simsun.ttc'),Path(r'C:\Windows\Fonts\times.ttf')]:
    if file.exists():font_manager.fontManager.addfont(str(file))
plt.rcParams.update({'font.family':['Times New Roman','SimSun','Arial'],'font.size':7.5,
                     'axes.labelsize':7.5,'axes.titlesize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
                     'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
                     'axes.unicode_minus':False,'axes.linewidth':.65,'legend.fontsize':7.5})
width_mm=138
fig,axes=plt.subplots(1,2,figsize=(width_mm/25.4,2.75),sharey=True)
fig.subplots_adjust(left=.205,right=.985,bottom=.18,top=.79,wspace=.27)
style=[('mae','MAE','#326C96','o',.12),('mean_shortfall','平均低估误差','#BD7838','s',-.12)]
for ax,ds,title,label,xmax in zip(axes,['abilene','geant'],['Abilene','GÉANT'],['a','b'],[.23,.82]):
    for metric,legend,color,marker,offset in style:
        rows=plot_data[plot_data.dataset==ds].set_index('model').loc[MODEL_ORDER]
        positions=np.arange(4,-1,-1)+offset
        ax.errorbar(rows[metric+'_mean'],positions,xerr=rows[metric+'_sd'],fmt=marker,
                    color=color,markersize=3.7,linestyle='none',elinewidth=.7,capsize=2,capthick=.7,label=legend)
    ax.set(yticks=np.arange(4,-1,-1),yticklabels=MODEL_LABELS,ylim=(-.55,4.55),xlim=(0,xmax),xlabel='标准化误差')
    ax.set_title(title,pad=9)
    ax.text(0,1.045,label,transform=ax.transAxes,fontweight='bold',fontsize=8.5,va='bottom')
    ax.set_xticks([0,.05,.10,.15,.20] if ds=='abilene' else [0,.2,.4,.6,.8])
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f' if ds=='abilene' else '%.1f'))
    ax.grid(axis='x',color='#DCE0E3',linewidth=.45,zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top','right']].set_visible(False)
    ax.tick_params(direction='out',length=2.5,width=.65)
    for tick in ax.get_yticklabels():
        if tick.get_text()=='本文方法':tick.set_fontweight('bold')
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.56,.995),ncol=2,frameon=False,handlelength=1.8,columnspacing=2.4)
fig.canvas.draw()
require_matplotlib_panel_alignment(fig,json_out=QA/'figure4_alignment.json',overlay_svg=QA/'figure4_alignment.svg',
                                  tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
prefix=OUT/'图4_高需求预测误差'
fig.savefig(prefix.with_suffix('.pdf'),dpi=600,facecolor='white')
fig.savefig(prefix.with_suffix('.svg'),dpi=600,facecolor='white')
fig.savefig(prefix.with_suffix('.png'),dpi=600,facecolor='white')
fig.savefig(prefix.with_suffix('.tiff'),dpi=600,facecolor='white')
plt.close(fig)
audit={'high_demand_seed_rows':80,'high_demand_summary_rows':10,'all_seeds_retained':SEEDS,
       'weight_source_rows':len(weight_rows),'weight_summaries':weight_summary,'paired_reductions':computed,
       'figure3_exact_reuse':True,'figure3_sha256':hashlib.sha256(source_image.read_bytes()).hexdigest(),
       'figure4_source_summary_sha256':hashlib.sha256((DATA/'summary.csv').read_bytes()).hexdigest(),
       'figure4_source_seed_sha256':hashlib.sha256((DATA/'per_seed.csv').read_bytes()).hexdigest(),
       'figure3_file':str(OUT/'图3_尺度权重分布.png'),'figure4_file':str(prefix)+'.png'}
(QA/'source_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(audit,ensure_ascii=False))
