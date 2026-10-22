from pathlib import Path
import json,sys
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2];QA=Path(__file__).resolve().parent
ASSETS=ROOT/'paper_template/长春工程学院学报(自然科学版)/主稿独立投稿修订_20261021/存档数据与图表'
sys.path.insert(0,r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment

def main():
    assert json.loads((QA/'data_audit.json').read_text(encoding='utf8'))['metric_files_verified']==18
    summaries=pd.read_csv(ASSETS/'图2_均值与标准差.csv')
    seeds=pd.read_csv(ASSETS/'图2_逐种子相对降幅.csv')
    mpl.rcParams.update({'font.family':['Times New Roman','SimSun','Arial'],'font.size':8,'axes.titlesize':8.5,'xtick.labelsize':8,'ytick.labelsize':7.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'xtick.major.size':0,'ytick.major.size':3,'xtick.major.width':.6,'ytick.major.width':.6,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,'figure.facecolor':'white','savefig.facecolor':'white'})
    fig,axes=plt.subplots(1,3,figsize=(138/25.4,2.15))
    fig.subplots_adjust(left=.06,right=.985,bottom=.18,top=.83,wspace=.43)
    x=np.arange(2);labels=['Abilene','GÉANT'];audits=[]
    for ax,metric,title,upper in zip(axes[:2],['mse','mae'],['(a) MSE降低率/%','(b) MAE降低率/%'],[60,50]):
        g=summaries[summaries.metric==metric].set_index('dataset').loc[['abilene','geant']]
        means=g['mean'].to_numpy();sd=g.sample_sd.to_numpy()
        for ds,mean,spread in zip(['abilene','geant'],means,sd):
            values=seeds[(seeds.dataset==ds)&(seeds.metric==metric)].relative_reduction_pct
            assert len(values)==3 and np.isclose(mean,values.mean()) and np.isclose(spread,values.std(ddof=1))
        ax.bar(x,means,width=.52,color='#287B9A',edgecolor='#185A73',linewidth=.5,zorder=2)
        ax.errorbar(x,means,yerr=sd,fmt='none',ecolor='#202020',elinewidth=.7,capsize=2.2,capthick=.7,zorder=3)
        for xi,mean,spread in zip(x,means,sd):ax.text(xi,mean+spread+upper*.035,f'{mean:.2f}',ha='center',va='bottom',fontsize=8)
        ax.set_ylim(0,upper);ax.set_yticks(np.arange(0,upper+1,10));ax.set_title(title,loc='left',pad=9)
        audits.append({'panel':metric,'role':'paired relative error reduction','unit':'paired training seed','n':3,'summary':'mean and sample SD','all_seed_values_used':True})
    ax=axes[2]
    g=summaries[summaries.metric=='mse'].set_index('dataset').loc[['abilene','geant']]
    ratios=g.parameter_ratio_pct.to_numpy()
    ax.bar(x,ratios,width=.52,color='#287B9A',edgecolor='#185A73',linewidth=.5)
    ax.axhline(100,color='#727272',linewidth=.75,linestyle=(0,(3,2)))
    ax.text(.5,104,'LightTS = 100%',ha='center',va='bottom',fontsize=7.5)
    for xi,ratio in zip(x,ratios):ax.text(xi,ratio+4,f'{ratio:.2f}',ha='center',va='bottom',fontsize=8)
    ax.set_ylim(0,120);ax.set_yticks([0,25,50,75,100]);ax.set_title('(c) 参数比例/%',loc='left',pad=9)
    audits.append({'panel':'parameter ratio','role':'model size relative to LightTS','unit':'architecture parameter count','summary':'deterministic count ratio','error_bar':'not applicable'})
    for ax in axes:
        ax.set_xticks(x,labels);ax.set_xlim(-.65,1.65);ax.tick_params(axis='x',pad=7)
    fig.canvas.draw()
    alignment=require_matplotlib_panel_alignment(fig,json_out=QA/'figure2_alignment.json',overlay_svg=QA/'figure2_alignment.svg',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    prefix=ASSETS/'图2_LightTS误差降低率与参数比例'
    fig.savefig(prefix.with_suffix('.svg'))
    fig.savefig(prefix.with_suffix('.pdf'))
    fig.savefig(prefix.with_suffix('.png'),dpi=600)
    fig.savefig(prefix.with_suffix('.tiff'),dpi=600)
    (QA/'figure2_panels.json').write_text(json.dumps({'panels':audits,'width_mm':138,'height_mm':54.61,'alignment':alignment.get('verdict'),'literal_display_values':{'mse':summaries[summaries.metric=='mse']['mean'].round(2).tolist(),'mae':summaries[summaries.metric=='mae']['mean'].round(2).tolist(),'parameters':ratios.round(2).tolist()}},ensure_ascii=False,indent=2),encoding='utf8')
    print(str(prefix))

if __name__=='__main__':main()
