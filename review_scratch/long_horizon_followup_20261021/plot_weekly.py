from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
ASSETS=ROOT/'paper_template/长春工程学院学报(自然科学版)/长预测核验与修订_20261021/数据与图表'
sys.path.insert(0,str(Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')))
from audit_panel_alignment import require_matplotlib_panel_alignment

def main():
    # Fixed condition and complete seed set are specified in artifact.md.
    assert (QA/'data_verification.json').exists()
    frame=pd.read_csv(ASSETS/'图5_全部八种子数据.csv')
    summary=pd.read_csv(ASSETS/'图5_均值与样本标准差.csv')
    assert len(frame)==40 and len(summary)==5
    mpl.rcParams.update({
        'font.family':['Times New Roman','SimSun','Arial'],
        'font.size':8.5,'axes.titlesize':9,'xtick.labelsize':7.5,'ytick.labelsize':8,
        'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
        'xtick.major.width':.6,'ytick.major.width':.6,'xtick.major.size':0,
        'ytick.major.size':3,'pdf.fonttype':42,'svg.fonttype':'none',
        'axes.unicode_minus':False,'figure.facecolor':'white','savefig.facecolor':'white',
    })
    fig,axes=plt.subplots(1,2,figsize=(138/25.4,2.5))
    fig.subplots_adjust(left=.075,right=.992,bottom=.215,top=.86,wspace=.28)
    x=np.arange(5)
    labels=['DLinear','固定\n等权','全局\n权重','恒定\n路由','本文\n方法']
    panel_audits=[]
    for ax,metric,title,upper,ticks in zip(axes,['mse','mae'],['(a) MSE','(b) MAE'],[1.4,.72],[np.arange(0,1.41,.2),np.arange(0,.721,.12)]):
        mean=summary[f'common_{metric}_mean'].to_numpy()
        sd=summary[f'common_{metric}_sd'].to_numpy()
        for i,model in enumerate(summary.model):
            values=frame[frame.model==model][f'common_{metric}']
            assert len(values)==8 and np.isclose(values.mean(),mean[i])
            assert np.isclose(values.std(ddof=1),sd[i])
        ax.bar(x,mean,width=.64,color=['#AEB8C2']*4+['#287B9A'],edgecolor=['#66717B']*4+['#185A73'],linewidth=.5,zorder=2)
        ax.errorbar(x,mean,yerr=sd,fmt='none',ecolor='#252525',elinewidth=.7,capsize=2.2,capthick=.7,zorder=3)
        for xi,m,s in zip(x,mean,sd):
            ax.text(xi,m+s+upper*.026,f'{m:.3f}',ha='center',va='bottom',fontsize=8)
        ax.set_xticks(x,labels)
        ax.set_xlim(-.65,4.65);ax.set_ylim(0,upper);ax.set_yticks(ticks)
        ax.set_title(title,loc='left',pad=8)
        ax.tick_params(axis='x',pad=6)
        panel_audits.append({'panel':title,'endpoint':metric,'center':'mean','spread':'sample SD ddof=1','unit':'training seed','n':8,'all_models':5,'all_seed_rows':40,'baseline_zero':True,'label_clearance':'mean + sample SD + 2.6% of y-axis range'})
    fig.canvas.draw()
    alignment=require_matplotlib_panel_alignment(fig,json_out=QA/'figure5_alignment.json',overlay_svg=QA/'figure5_alignment.svg',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    prefix=ASSETS/'图5_GEANT一周预测误差'
    fig.savefig(prefix.with_suffix('.svg'))
    fig.savefig(prefix.with_suffix('.pdf'))
    fig.savefig(prefix.with_suffix('.png'),dpi=600)
    fig.savefig(prefix.with_suffix('.tiff'),dpi=600)
    (QA/'figure5_panels.json').write_text(json.dumps({'panels':panel_audits,'width_mm':138,'height_mm':63.5,'alignment_verdict':alignment.get('verdict'),'selection_scope':'GÉANT H168, user-selected after complete-grid analysis; complete grid retained in supplement'},ensure_ascii=False,indent=2),encoding='utf8')
    print(str(prefix))

if __name__=='__main__':main()
