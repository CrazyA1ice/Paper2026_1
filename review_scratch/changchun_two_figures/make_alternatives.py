from pathlib import Path
import hashlib, json, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/改投内容修改第一版_20261020/图4备选'
OUT.mkdir(exist_ok=True)
SKILL=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
sys.path.insert(0,str(SKILL))
from audit_panel_alignment import require_matplotlib_panel_alignment

for font_file in [r'C:\Windows\Fonts\simsun.ttc',r'C:\Windows\Fonts\times.ttf']:
    font_manager.fontManager.addfont(font_file)
plt.rcParams.update({'font.family':['Times New Roman','SimSun','Arial'],
    'font.size':7.5,'axes.labelsize':7.5,'axes.titlesize':8.5,
    'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,
    'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,
    'axes.linewidth':.65,'axes.spines.top':False,'axes.spines.right':False})

def decorate(ax,title,letter):
    ax.set_title(title,pad=8)
    ax.text(0,1.04,letter,transform=ax.transAxes,fontsize=8.5,fontweight='bold',va='bottom')
    ax.tick_params(direction='out',length=2.5,width=.65)
    ax.grid(axis='y',color='#E1E5E8',linewidth=.45)
    ax.set_axisbelow(True)

def save(fig,stem):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=QA/(stem+'.alignment.json'),
        overlay_svg=QA/(stem+'.alignment.svg'),tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
    prefix=OUT/stem
    fig.savefig(prefix.with_suffix('.pdf'),dpi=600,facecolor='white')
    fig.savefig(prefix.with_suffix('.svg'),dpi=600,facecolor='white')
    fig.savefig(prefix.with_suffix('.png'),dpi=600,facecolor='white')
    fig.savefig(prefix.with_suffix('.tiff'),dpi=600,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
    plt.close(fig)

selection=json.loads((ROOT/'abilene_forecasting/paper_figures/source_data_v2/fig5_representative_forecasts_selection.json').read_text(encoding='utf8'))
case_rows=[];seed_rows=[];source_records=[]
width_mm=138
fig,axes=plt.subplots(1,2,figsize=(width_mm/25.4,2.55))
fig.subplots_adjust(left=.09,right=.985,bottom=.2,top=.78,wspace=.31)
for ax,info,title,letter in zip(axes,selection,['Abilene','GÉANT'],['a','b']):
    ds=info['dataset'];w=info['window_index_zero_based'];c=info['active_channel_index_zero_based']
    predictions=[];truth=None
    for seed in range(42,50):
        path=ROOT/f'abilene_forecasting/results/{ds}/dlinear_scale_seed{seed}/predictions.npz'
        with np.load(path) as raw:
            p=raw['prediction'];t=raw['truth']
            assert p.shape==t.shape==(813 if ds=='abilene' else 451,24,144 if ds=='abilene' else 524)
            assert np.isfinite(p[w,:,c]).all() and np.isfinite(t[w,:,c]).all()
            if truth is None:truth=t[w,:,c].copy()
            else:assert np.array_equal(truth,t[w,:,c])
            predictions.append(p[w,:,c].copy())
            if seed==42:
                errors=np.abs(p-t).mean(axis=(1,2))
                assert w==int(np.argmin(np.abs(errors-np.median(errors))))
                sds=t[w].std(axis=0);eligible=np.flatnonzero(sds>1e-8)
                assert c==int(eligible[np.argmin(np.abs(sds[eligible]-np.median(sds[eligible])))])
        source_records.append({'dataset':ds,'seed':seed,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        for h,(actual,pred) in enumerate(zip(truth,predictions[-1]),1):
            seed_rows.append([ds,seed,w,c,h,float(actual),float(pred)])
    matrix=np.asarray(predictions,dtype=np.float64)
    mean=matrix.mean(axis=0);sd=matrix.std(axis=0,ddof=1)
    x=np.arange(1,25)
    ax.fill_between(x,mean-sd,mean+sd,color='#238D98',alpha=.16,linewidth=0)
    ax.plot(x,truth,color='#252D35',lw=1.15,ls='--',label='真实值',zorder=3)
    ax.plot(x,mean,color='#15838F',lw=1.5,label='本文方法',zorder=4)
    ax.set(xlim=(1,24),xticks=[1,6,12,18,24],xlabel='预测时长 / h',ylabel='标准化流量')
    decorate(ax,title,letter)
    for h,a,m,s in zip(x,truth,mean,sd):case_rows.append([ds,w,c,int(h),float(a),float(m),float(s)])
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.995),ncol=2,frameon=False,handlelength=2.8,columnspacing=2.3)
save(fig,'备选A_预测曲线')
pd.DataFrame(case_rows,columns=['dataset','window_index','active_od_index','forecast_hour','truth','prediction_mean','prediction_sample_sd']).to_csv(OUT/'备选A_曲线汇总.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(seed_rows,columns=['dataset','seed','window_index','active_od_index','forecast_hour','truth','prediction']).to_csv(OUT/'备选A_全部种子.csv',index=False,encoding='utf-8-sig')

data=pd.read_csv(ROOT/'abilene_forecasting/results/high_demand_analysis/per_seed.csv')
assert len(data)==80 and not data.duplicated(['dataset','model','seed']).any()
models=['dlinear','dlinear_scale_static','dlinear_scale_global','dlinear_scale_constant_router','dlinear_scale']
names=['DLinear','固定\n等权','全局\n权重','恒定\n路由','本文\n方法']
fig,axes=plt.subplots(1,2,figsize=(width_mm/25.4,2.85))
fig.subplots_adjust(left=.09,right=.985,bottom=.23,top=.78,wspace=.3)
bar_rows=[]
for ax,ds,title,letter in zip(axes,['abilene','geant'],['Abilene','GÉANT'],['a','b']):
    for metric,label,color,offset in [('mae','MAE','#5D91B5',-.18),('mean_shortfall','平均低估误差','#DAAA70',.18)]:
        values=[];sds=[]
        for model in models:
            group=data[(data.dataset==ds)&(data.model==model)].sort_values('seed')
            assert group.seed.tolist()==list(range(42,50))
            values.append(float(group[metric].mean()));sds.append(float(group[metric].std(ddof=1)))
            bar_rows.append([ds,model,metric,values[-1],sds[-1],8])
        positions=np.arange(5)+offset
        ax.bar(positions,values,width=.34,color=color,edgecolor='#FFFFFF',linewidth=.45,label=label,zorder=3)
        ax.errorbar(positions,values,yerr=sds,fmt='none',ecolor='#424B53',elinewidth=.65,capsize=1.8,capthick=.65,zorder=4)
    ax.set(xlim=(-.6,4.6),ylim=(0,.22 if ds=='abilene' else .82),xticks=np.arange(5),xticklabels=names,ylabel='标准化误差')
    ax.set_yticks([0,.05,.10,.15,.20] if ds=='abilene' else [0,.2,.4,.6,.8])
    decorate(ax,title,letter)
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.52,.995),ncol=2,frameon=False,handlelength=1.4,columnspacing=2.2)
save(fig,'备选B_高需求柱状图')
pd.DataFrame(bar_rows,columns=['dataset','model','metric','mean','sample_sd','n_seeds']).to_csv(OUT/'备选B_绘图数据.csv',index=False,encoding='utf-8-sig')
data.to_csv(OUT/'备选B_全部种子.csv',index=False,encoding='utf-8-sig')

note='''图4备选说明

备选A 真实值与预测值曲线（案例展示方向）
黑色虚线为真实值，青色实线为本文方法在八个训练种子上的平均预测，阴影为种子间±1样本标准差。两个面板均展示完整24步预测。沿用此前材料已经确定的案例：Abilene测试窗口104、有效OD索引29；GÉANT测试窗口403、有效OD索引186（均从0计数）。原案例先取种子42下本文方法窗口MAE最接近中位数的窗口，再取该窗口内真实值标准差最接近非恒定通道中位数的OD；本轮未按与其他方法的优劣重新挑选。该图说明具体预测形态，不承担总体方法排名的证明。

备选B 高需求误差柱状图（更适合保留当前正文的分析内容）
与现有图4使用同一套数据、模型、指标和八个种子。柱高为种子均值，误差线为±1样本标准差；全局权重与恒定路由分别对应正文的全局可学习权重、恒定输入路由。该版保留现有高需求分析的论证内容，仅调整图形表达。

当前Word稿未替换。两版均保存PDF、SVG、600 dpi PNG、TIFF及CSV源数据，供选择后插入正文。
'''
(OUT/'备选说明.txt').write_text(note,encoding='utf8')
(QA/'alternative_data_audit.json').write_text(json.dumps({'source_files':source_records,'case_indices':selection,'curve_rows':len(case_rows),'curve_seed_rows':len(seed_rows),'high_demand_seed_rows':len(data),'changes_to_word':False},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'folder':str(OUT),'curve_rows':len(case_rows),'curve_seed_rows':len(seed_rows),'high_demand_rows':len(data)},ensure_ascii=False))
