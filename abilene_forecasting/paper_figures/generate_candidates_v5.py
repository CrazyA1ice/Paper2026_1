from __future__ import annotations

from pathlib import Path
import math

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.patches import Polygon


ROOT = Path(__file__).resolve().parents[1]
FIGDIR = Path(__file__).resolve().parent
OUT = FIGDIR / "candidates_v5"
COLOR = OUT / "color"
GRAY = OUT / "grayscale"
SOURCE = OUT / "source_data"
for p in [OUT, COLOR, GRAY, SOURCE]:
    p.mkdir(parents=True, exist_ok=True)

mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.serif"] = [
    "Noto Serif CJK SC", "Noto Serif CJK JP", "SimSun",
    "Times New Roman", "Liberation Serif", "DejaVu Serif"
]
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["svg.fonttype"] = "none"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["font.size"] = 7.2
mpl.rcParams["axes.labelsize"] = 7.4
mpl.rcParams["axes.titlesize"] = 9.0
mpl.rcParams["xtick.labelsize"] = 6.6
mpl.rcParams["ytick.labelsize"] = 6.6
mpl.rcParams["legend.fontsize"] = 6.5
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["xtick.direction"] = "in"
mpl.rcParams["ytick.direction"] = "in"
mpl.rcParams["axes.linewidth"] = 0.8
mpl.rcParams["legend.frameon"] = False

BLUE = "#4F81BD"
ORANGE = "#D9782D"
GREEN = "#5A9A62"
PURPLE = "#7A6BAA"
DARK = "#222222"
MID = "#777777"
LIGHT = "#D9D9D9"
PALE = "#F2F2F2"
SCALE_COLORS = ["#4F81BD", "#6A9F58", "#D9782D"]


def save_both(fig, stem: str):
    base = COLOR / f"{stem}_color"
    fig.savefig(str(base) + ".png", dpi=600, bbox_inches="tight")
    fig.savefig(str(base) + ".jpg", dpi=600, bbox_inches="tight", pil_kwargs={"quality":95, "subsampling":0})
    fig.savefig(str(base) + ".pdf", bbox_inches="tight")
    fig.savefig(str(base) + ".svg", bbox_inches="tight")

    rgb = Image.open(str(base) + ".png").convert("RGB")
    gray = rgb.convert("L")
    gray.save(GRAY / f"{stem}_grayscale.png", dpi=(600,600))
    gray.save(GRAY / f"{stem}_grayscale.jpg", quality=95, subsampling=0, dpi=(600,600))
    plt.close(fig)


def panel_label(ax, label):
    ax.text(-0.12, 1.04, label, transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", ha="left", va="bottom")


def load_router_all():
    rows=[]
    for dataset in ["abilene","geant"]:
        for seed in range(42,50):
            p=ROOT/"results"/dataset/f"dlinear_scale_seed{seed}"/"router_weights.csv"
            arr=pd.read_csv(p,header=None).to_numpy(float)
            if arr.shape[1] != 3:
                raise RuntimeError(f"Unexpected shape {arr.shape}: {p}")
            if not np.allclose(arr.sum(axis=1),1.0,atol=1e-5):
                raise RuntimeError(f"Router weights not normalized: {p}")
            for wi in range(arr.shape[0]):
                rows.append({
                    "dataset":dataset,"seed":seed,"window":wi,
                    "alpha1":arr[wi,0],"alpha2":arr[wi,1],"alpha4":arr[wi,2]
                })
    df=pd.DataFrame(rows)
    df.to_csv(SOURCE/"router_all_8seeds.csv",index=False)
    return df


def candidate_a_router_distribution(router):
    fig,axes=plt.subplots(1,2,figsize=(6.70,3.15),sharey=True)
    rng=np.random.default_rng(20260920)
    for idx,(ax,dataset,title) in enumerate(zip(axes,["abilene","geant"],["Abilene","GÉANT"])):
        sub=router[router.dataset==dataset]
        groups=[sub[c].to_numpy() for c in ["alpha1","alpha2","alpha4"]]
        vp=ax.violinplot(groups,positions=[1,2,3],widths=0.68,
                         showmeans=False,showmedians=True,showextrema=False)
        for body,color in zip(vp["bodies"],SCALE_COLORS):
            body.set_facecolor(color); body.set_edgecolor(color)
            body.set_alpha(0.26); body.set_linewidth(0.9)
        vp["cmedians"].set_color(DARK); vp["cmedians"].set_linewidth(0.9)

        for pos,col,color in zip([1,2,3],["alpha1","alpha2","alpha4"],SCALE_COLORS):
            means=sub.groupby("seed")[col].mean().to_numpy()
            jit=rng.uniform(-0.065,0.065,len(means))
            ax.scatter(pos+jit,means,s=24,facecolor=color,edgecolor="white",
                       linewidth=0.55,zorder=4)
            ax.errorbar([pos],[means.mean()],yerr=[[means.std(ddof=1)],[means.std(ddof=1)]],
                        fmt="D",ms=4.3,color=DARK,mfc=DARK,mec=DARK,
                        capsize=2.5,lw=0.9,zorder=5)
        ax.axhline(1/3,color="#666666",lw=0.8,ls="--",dashes=(4,3))
        ax.set_xticks([1,2,3],[r"$\alpha_1$",r"$\alpha_2$",r"$\alpha_4$"])
        ax.set_xlabel("尺度权重")
        ax.set_title(title,fontweight="bold",fontfamily="serif")
        ax.set_ylim(0,0.82)
        ax.grid(axis="y",color="#dddddd",ls="--",lw=0.45,alpha=0.55)
        panel_label(ax,chr(ord("a")+idx))
    axes[0].set_ylabel("样本级路由权重")
    fig.subplots_adjust(left=0.09,right=0.99,bottom=0.18,top=0.88,wspace=0.14)
    save_both(fig,"candidate_A_router_weight_distribution")


def candidate_b_simplex(router):
    means=(router.groupby(["dataset","seed"])[["alpha1","alpha2","alpha4"]]
           .mean().reset_index())
    means.to_csv(SOURCE/"router_seed_mean_simplex.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(6.70,3.18))
    vertices=np.array([[0.0,0.0],[1.0,0.0],[0.5,math.sqrt(3)/2]])
    for idx,(ax,dataset,title,color) in enumerate(zip(
        axes,["abilene","geant"],["Abilene","GÉANT"],[BLUE,ORANGE]
    )):
        tri=Polygon(vertices,closed=True,fill=False,edgecolor=DARK,lw=0.9)
        ax.add_patch(tri)
        # Grid at 1/3 and 2/3 levels.
        for t in [1/3,2/3]:
            # alpha4 constant
            p1=(1-t)*vertices[0]+t*vertices[2]
            p2=(1-t)*vertices[1]+t*vertices[2]
            ax.plot([p1[0],p2[0]],[p1[1],p2[1]],color=LIGHT,lw=0.55,ls="--")
            # alpha1 constant
            p1=(1-t)*vertices[1]+t*vertices[0]
            p2=(1-t)*vertices[2]+t*vertices[0]
            ax.plot([p1[0],p2[0]],[p1[1],p2[1]],color=LIGHT,lw=0.55,ls="--")
            # alpha2 constant
            p1=(1-t)*vertices[0]+t*vertices[1]
            p2=(1-t)*vertices[2]+t*vertices[1]
            ax.plot([p1[0],p2[0]],[p1[1],p2[1]],color=LIGHT,lw=0.55,ls="--")
        sub=means[means.dataset==dataset]
        pts=[]
        for row in sub.itertuples(index=False):
            a1,a2,a4=row.alpha1,row.alpha2,row.alpha4
            xy=a1*vertices[0]+a2*vertices[1]+a4*vertices[2]
            pts.append(xy)
            ax.scatter(xy[0],xy[1],s=36,facecolor=color,edgecolor="white",linewidth=0.7,zorder=4)
            ax.text(xy[0]+0.012,xy[1]+0.010,str(row.seed),fontsize=5.8,color=DARK)
        pts=np.array(pts)
        centroid=pts.mean(axis=0)
        ax.scatter(centroid[0],centroid[1],s=52,marker="D",facecolor=DARK,edgecolor="white",linewidth=0.6,zorder=5)
        eq=(vertices[0]+vertices[1]+vertices[2])/3
        ax.scatter(eq[0],eq[1],s=38,marker="x",color="#777777",linewidth=1.1,zorder=3)
        ax.text(vertices[0,0]-0.03,vertices[0,1]-0.045,r"$\alpha_1$",ha="right",va="top")
        ax.text(vertices[1,0]+0.03,vertices[1,1]-0.045,r"$\alpha_2$",ha="left",va="top")
        ax.text(vertices[2,0],vertices[2,1]+0.045,r"$\alpha_4$",ha="center",va="bottom")
        ax.set_title(title,fontweight="bold")
        ax.set_xlim(-0.10,1.10); ax.set_ylim(-0.10,0.98)
        ax.set_aspect("equal"); ax.axis("off")
        panel_label(ax,chr(ord("a")+idx))
    fig.subplots_adjust(left=0.04,right=0.98,bottom=0.06,top=0.90,wspace=0.12)
    save_both(fig,"candidate_B_router_weight_simplex")


def candidate_c_parameter_mse_tradeoff():
    df=pd.read_csv(FIGDIR/"source_data_v2"/"table2_external_baseline_3seeds.csv")
    df=df[df.model.isin(["dlinear","lightts","dlinear_scale"])].copy()
    labels={"dlinear":"DLinear","lightts":"LightTS","dlinear_scale":"自适应多尺度"}
    colors={"dlinear":PURPLE,"lightts":ORANGE,"dlinear_scale":BLUE}
    markers={"dlinear":"s","lightts":"^","dlinear_scale":"o"}
    fig,axes=plt.subplots(1,2,figsize=(6.70,3.12))
    for idx,(ax,dataset,title) in enumerate(zip(axes,["abilene","geant"],["Abilene","GÉANT"])):
        sub=df[df.dataset==dataset]
        for row in sub.itertuples(index=False):
            ax.errorbar(row.parameters,row.mse_mean,yerr=row.mse_std,
                        fmt=markers[row.model],ms=6.0,mfc=colors[row.model],mec="white",
                        mew=0.6,color=colors[row.model],ecolor=colors[row.model],
                        capsize=2.5,lw=1.0,label=labels[row.model])
            ax.annotate(labels[row.model],(row.parameters,row.mse_mean),
                        xytext=(5,4),textcoords="offset points",fontsize=6.2)
        ax.set_xscale("log")
        ax.set_xlabel("可训练参数量（对数坐标）")
        ax.set_ylabel("均方误差（MSE）")
        ax.set_title(title,fontweight="bold")
        ax.grid(color="#dddddd",ls="--",lw=0.45,alpha=0.55)
        panel_label(ax,chr(ord("a")+idx))
    fig.subplots_adjust(left=0.10,right=0.99,bottom=0.19,top=0.88,wspace=0.28)
    save_both(fig,"candidate_C_parameter_mse_tradeoff")


def candidate_d_core_stability():
    df=pd.read_csv(ROOT/"results"/"core_v2_summary.csv")
    df=df[df.model.isin(["dlinear","dlinear_scale_static","dlinear_scale"]) & df.seed.between(42,49)].copy()
    labels=["DLinear","固定等权","自适应权重"]
    models=["dlinear","dlinear_scale_static","dlinear_scale"]
    colors=[PURPLE,ORANGE,BLUE]
    fig,axes=plt.subplots(1,2,figsize=(6.70,3.18))
    rng=np.random.default_rng(20260920)
    for idx,(ax,dataset,title) in enumerate(zip(axes,["abilene","geant"],["Abilene","GÉANT"])):
        for pos,(model,label,color) in enumerate(zip(models,labels,colors),start=1):
            vals=df[(df.dataset==dataset)&(df.model==model)].sort_values("seed").mse.to_numpy()
            parts=ax.violinplot([vals],positions=[pos],widths=0.62,showmeans=False,showmedians=False,showextrema=False)
            body=parts["bodies"][0]
            body.set_facecolor(color); body.set_edgecolor(color); body.set_alpha(0.20); body.set_linewidth(0.85)
            jitter=rng.uniform(-0.07,0.07,len(vals))
            ax.scatter(pos+jitter,vals,s=24,facecolor=color,edgecolor="white",linewidth=0.55,zorder=4)
            ax.errorbar([pos],[vals.mean()],yerr=[[vals.std(ddof=1)],[vals.std(ddof=1)]],
                        fmt="D",ms=4.5,color=DARK,mfc=DARK,mec=DARK,capsize=2.5,lw=0.9,zorder=5)
        ax.set_xticks([1,2,3],labels)
        ax.set_ylabel("均方误差（MSE）")
        ax.set_title(title,fontweight="bold")
        ax.grid(axis="y",color="#dddddd",ls="--",lw=0.45,alpha=0.55)
        panel_label(ax,chr(ord("a")+idx))
    fig.subplots_adjust(left=0.10,right=0.99,bottom=0.20,top=0.88,wspace=0.24)
    save_both(fig,"candidate_D_core_model_stability")


def main():
    router=load_router_all()
    candidate_a_router_distribution(router)
    candidate_b_simplex(router)
    candidate_c_parameter_mse_tradeoff()
    candidate_d_core_stability()
    print(OUT)


if __name__=="__main__":
    main()
