"""Three coordinated, real-data design pairs for manuscript Figures 3 and 5."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
PERFORMANCE = ROOT / "paper_figures/source_data_v24/fig5_relative_improvement_8seeds.csv"
WEIGHTS = ROOT / "results/global_weight_ablation/analysis/within_seed_weights.csv"
OUT = ROOT.parent / "paper_figures/fig3_fig5_redesigns"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

FONT = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
METRICS = ("MSE", "MAE", "RMSE")
SCALES = (1, 2, 4)
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
BASELINES = ("DLinear", "固定等权")
OFFSETS = np.array([-.16, -.115, -.07, -.025, .025, .07, .115, .16])
PALETTES = {
    "A": {"base": ("#335F72", "#BC7A61"), "scale": ("#335F72", "#5F9B94", "#BC7A61"), "ink": "#243947"},
    "B": {"base": ("#3D6775", "#B97563"), "scale": ("#3D6775", "#77A69B", "#B97563"), "ink": "#263946"},
    "C": {"base": ("#416A84", "#C78A69"), "scale": ("#416A84", "#7DAB9C", "#C78A69"), "ink": "#253B4D"},
}


def setup():
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7.2, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#AAB7BE", "axes.labelcolor": "#253B4D",
        "text.color": "#253B4D", "xtick.color": "#61727D", "ytick.color": "#61727D",
    })


def ci95(values):
    values = np.asarray(values, dtype=float)
    return stats.t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))


def save(fig, stem):
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.svg")
    fig.savefig(f"{stem}.png", dpi=600)
    fig.savefig(f"{stem}.tiff", dpi=600)
    plt.close(fig)


def perf_values(data, dataset, baseline, metric):
    part = data[(data.dataset == dataset) & (data.baseline == baseline) & (data.metric == metric)].sort_values("seed")
    assert part.seed.tolist() == list(range(42, 50))
    return part.relative_improvement_pct.to_numpy()


def weight_values(data, dataset, scale):
    part = data[(data.dataset == dataset) & (data.scale == scale)].sort_values("seed")
    assert part.seed.tolist() == list(range(42, 50))
    return part.adaptive_mean.to_numpy(), part.adaptive_within_seed_sd.to_numpy()


def common_axis(ax, title, xlim=(-15, 17)):
    ax.set_title(title, loc="left", fontsize=9.4, fontweight="bold", pad=7)
    ax.axvline(0, color="#8A979E", lw=.8, ls=(0, (4, 3)), zorder=0)
    ax.set_xlim(*xlim)
    ax.set_xticks([-15, -10, -5, 0, 5, 10, 15])
    ax.set_xlabel("相对改进率 (%)", fontproperties=FONT, fontsize=7.8)
    for x in (-5, 5, 10, 15):
        ax.axvline(x, color="#E9EEF0", lw=.55, zorder=0)
    ax.tick_params(length=0, pad=3)


def forest_pair(perf, weights):
    palette = PALETTES["A"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.35), sharex=True, sharey=True)
    yrows = (6.0, 5.0, 4.0, 2.5, 1.5, .5)
    for ax, (dataset, title) in zip(axes, DATASETS):
        common_axis(ax, title)
        ax.set_ylim(0, 7.1)
        ax.set_yticks(yrows, ["MSE", "MAE", "RMSE"] * 2)
        ax.axhline(3.25, color="#D5DEE2", lw=.8)
        ax.text(-14.6, 6.67, "DLinear", color=palette["base"][0], fontsize=7.5, fontweight="bold")
        ax.text(-14.6, 3.55, "固定等权", color=palette["base"][1], fontproperties=FONT, fontsize=7.5)
        for baseline_index, baseline in enumerate(BASELINES):
            for metric_index, metric in enumerate(METRICS):
                y = yrows[baseline_index * 3 + metric_index]
                values = perf_values(perf, dataset, baseline, metric)
                color = palette["base"][baseline_index]
                ax.scatter(values, y + OFFSETS, s=16, color=color, alpha=.75,
                           edgecolor="white", linewidth=.55, zorder=3)
                mean = values.mean()
                ax.errorbar(mean, y+.27, xerr=ci95(values), fmt="D", markersize=3.5,
                            markerfacecolor="white", markeredgecolor=palette["ink"],
                            ecolor=palette["ink"], capsize=2.3, capthick=.85,
                            elinewidth=.85, zorder=4)
    fig.subplots_adjust(left=.075, right=.985, top=.91, bottom=.16, wspace=.14)
    save(fig, OUT / "A_fig3_forest")

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.95), sharex=True, sharey=True)
    for ax, (dataset, title) in zip(axes, DATASETS):
        ax.set_title(title, loc="left", fontsize=9.4, fontweight="bold", pad=7)
        ax.axhline(1/3, color="#8999A0", ls=(0, (4, 3)), lw=.8, zorder=0)
        for index, scale in enumerate(SCALES):
            x = index + 1
            means, sd = weight_values(weights, dataset, scale)
            color = palette["scale"][index]
            q1, q3 = np.quantile(means, [.25, .75])
            ax.fill_between([x-.23, x+.23], q1, q3, color=color, alpha=.14, zorder=1)
            ax.plot([x, x], [means.min(), means.max()], color=color, lw=2.3,
                    alpha=.45, zorder=1)
            for xi, value, spread in zip(x + OFFSETS, means, sd):
                ax.plot([xi, xi], [max(0, value-spread), min(1, value+spread)],
                        color=color, lw=.7, alpha=.65, zorder=2)
            ax.scatter(x + OFFSETS, means, s=18, color=color, edgecolor="white",
                       linewidth=.6, zorder=3)
            ax.errorbar(x+.3, means.mean(), yerr=ci95(means), fmt="D", markersize=3.3,
                        markerfacecolor="white", markeredgecolor=palette["ink"],
                        ecolor=palette["ink"], elinewidth=.9, capsize=2.3, zorder=4)
        ax.set_xlim(.52, 3.5)
        ax.set_ylim(0, .85)
        ax.set_xticks([1, 2, 3], ["α₁", "α₂", "α₄"])
        ax.set_yticks(np.arange(0, .81, .2))
        ax.set_xlabel("尺度权重", fontproperties=FONT, fontsize=7.8)
        ax.grid(axis="y", color="#E9EEF0", lw=.55)
        ax.tick_params(length=0, pad=3)
    axes[0].set_ylabel("逐种子平均权重", fontproperties=FONT, fontsize=7.8)
    fig.subplots_adjust(left=.08, right=.985, top=.88, bottom=.18, wspace=.14)
    save(fig, OUT / "A_fig5_boxstrip")


def matrix_pair(perf, weights):
    palette = PALETTES["B"]
    cmap = LinearSegmentedColormap.from_list("gain", [palette["base"][1], "#F7F8F6", palette["base"][0]])
    norm = TwoSlopeNorm(vmin=-15, vcenter=0, vmax=16)
    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.0), sharex=True, sharey=True)
    for ax, (dataset, title) in zip(axes, DATASETS):
        matrix = np.array([perf_values(perf, dataset, baseline, metric)
                           for baseline in BASELINES for metric in METRICS])
        ax.imshow(matrix, cmap=cmap, norm=norm,
                  aspect="auto", interpolation="nearest", extent=(0, 8, 6, 0))
        ax.axhline(3, color="white", lw=2)
        ax.axvline(8.1, color="#B5C0C5", lw=.7)
        ax.set_xlim(0, 10.75)
        ax.set_yticks(np.arange(6)+.5, ["D·MSE", "D·MAE", "D·RMSE", "E·MSE", "E·MAE", "E·RMSE"])
        ax.set_xticks(np.arange(8)+.5, [str(s) for s in range(42, 50)])
        ax.set_title(title, loc="left", fontsize=9.4, fontweight="bold", pad=7)
        ax.tick_params(length=0, pad=3)
        for row, values in enumerate(matrix):
            ax.text(8.25, row+.5, f"{values.mean():+.2f}±{ci95(values):.2f}",
                    ha="left", va="center", fontsize=7, color=palette["ink"])
        ax.text(8.25, -.17, "均值±95%CI", ha="left", va="bottom",
                fontproperties=FONT, fontsize=7)
        ax.set_xlabel("随机种子（D：DLinear；E：固定等权）", fontproperties=FONT, fontsize=7.6)
    cax = fig.add_axes([.37, .955, .14, .012])
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                 orientation="horizontal", ticks=[-15, 0, 16])
    cax.tick_params(labelsize=5.8, length=0, pad=1)
    fig.text(.365, .962, "改进率 (%)", ha="right", va="center",
             fontproperties=FONT, fontsize=6.7)
    fig.subplots_adjust(left=.08, right=.985, top=.85, bottom=.18, wspace=.15)
    save(fig, OUT / "B_fig3_seedmatrix")

    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.05), sharex=True, sharey=True)
    xseed = np.arange(8)
    for ax, (dataset, title) in zip(axes, DATASETS):
        ax.set_title(title, loc="left", fontsize=9.4, fontweight="bold", pad=7)
        ax.axhline(1/3, color="#87969C", lw=.8, ls=(0, (4, 3)), zorder=0)
        for i, scale in enumerate(SCALES):
            values, sd = weight_values(weights, dataset, scale)
            color = palette["scale"][i]
            x = xseed + (i-1)*.16
            for xi, value, spread in zip(x, values, sd):
                ax.plot([xi, xi], [max(0,value-spread), min(1,value+spread)],
                        color=color, lw=.8, alpha=.55, zorder=1)
            ax.scatter(x, values, s=16, color=color, edgecolor="white", linewidth=.5,
                       label=f"α{scale}", zorder=2)
            ax.errorbar(8.45, values.mean(), yerr=ci95(values), fmt="D", markersize=3.6,
                        color=color, markerfacecolor="white", markeredgecolor=color,
                        capsize=2.3, elinewidth=.95, zorder=3)
        ax.axvline(7.9, color="#D3DDE0", lw=.75)
        ax.set_xlim(-.55, 8.9)
        ax.set_ylim(0, .85)
        ax.set_xticks(list(range(8))+[8.45], [str(s) for s in range(42,50)]+["μ"])
        ax.set_yticks(np.arange(0,.81,.2))
        ax.set_xlabel("随机种子（右侧为跨种子均值±95%CI）", fontproperties=FONT, fontsize=7.5)
        ax.grid(axis="y", color="#E9EEF0", lw=.55)
        ax.tick_params(length=0, pad=3)
    axes[0].set_ylabel("尺度权重", fontproperties=FONT, fontsize=7.8)
    fig.legend(handles=[Line2D([0],[0],marker="o",color=c,ls="",label=f"α{s}")
                        for c,s in zip(palette["scale"],SCALES)],
               loc="upper center", bbox_to_anchor=(.37,.985), ncol=3,
               frameon=False, handletextpad=.2, columnspacing=1.6)
    fig.subplots_adjust(left=.08, right=.985, top=.86, bottom=.18, wspace=.14)
    save(fig, OUT / "B_fig5_seedtracks")


def raincloud_pair(perf, weights):
    palette = PALETTES["C"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.3), sharex=True, sharey=True)
    yrows = (6,5,4,2.5,1.5,.5)
    for ax, (dataset, title) in zip(axes, DATASETS):
        common_axis(ax, title)
        ax.set_ylim(0,7.1)
        ax.set_yticks(yrows,["MSE","MAE","RMSE"]*2)
        ax.axhline(3.25,color="#D5DEE2",lw=.8)
        ax.text(-14.6,6.67,"DLinear",color=palette["base"][0],fontsize=7.5,fontweight="bold")
        ax.text(-14.6,3.55,"固定等权",color=palette["base"][1],fontproperties=FONT,fontsize=7.5)
        for j, baseline in enumerate(BASELINES):
            for k, metric in enumerate(METRICS):
                y = yrows[j*3+k]
                values = perf_values(perf,dataset,baseline,metric)
                color = palette["base"][j]
                body = ax.violinplot(values,positions=[y],vert=False,widths=.54,
                                     showmeans=False,showmedians=False,showextrema=False,
                                     bw_method=.4)["bodies"][0]
                verts = body.get_paths()[0].vertices
                verts[:,1] = np.maximum(verts[:,1],y)
                body.set_facecolor(color)
                body.set_edgecolor(color)
                body.set_alpha(.18)
                body.set_linewidth(.65)
                ax.scatter(values,y+OFFSETS-.18,s=15,color=color,alpha=.72,
                           edgecolor="white",linewidth=.5,zorder=3)
                ax.errorbar(values.mean(),y+.07,xerr=ci95(values),fmt="D",markersize=3.3,
                            color=palette["ink"],markerfacecolor="white",capsize=2.2,
                            elinewidth=.9,zorder=4)
    fig.subplots_adjust(left=.075,right=.985,top=.91,bottom=.16,wspace=.14)
    save(fig,OUT / "C_fig3_raincloud")

    fig, axes = plt.subplots(1,2,figsize=(7.0,2.95),sharex=True,sharey=True)
    for ax,(dataset,title) in zip(axes,DATASETS):
        ax.set_title(title,loc="left",fontsize=9.4,fontweight="bold",pad=7)
        ax.axhline(1/3,color="#8999A0",lw=.8,ls=(0,(4,3)),zorder=0)
        for i,scale in enumerate(SCALES):
            x=i+1
            values,sd=weight_values(weights,dataset,scale)
            color=palette["scale"][i]
            body=ax.violinplot(values,positions=[x],widths=.68,showmeans=False,
                               showmedians=False,showextrema=False,bw_method=.35)["bodies"][0]
            body.set_facecolor(color)
            body.set_edgecolor(color)
            body.set_alpha(.16)
            body.set_linewidth(.75)
            for xi,value,spread in zip(x+OFFSETS,values,sd):
                ax.plot([xi,xi],[max(0,value-spread),min(1,value+spread)],
                        color=color,lw=.7,alpha=.7,zorder=2)
            ax.scatter(x+OFFSETS,values,s=17,color=color,edgecolor="white",linewidth=.55,zorder=3)
            ax.errorbar(x+.3,values.mean(),yerr=ci95(values),fmt="D",markersize=3.3,
                        markerfacecolor="white",color=palette["ink"],capsize=2.2,
                        elinewidth=.9,zorder=4)
        ax.set_xlim(.52,3.5)
        ax.set_ylim(0,.85)
        ax.set_xticks([1,2,3],["α₁","α₂","α₄"])
        ax.set_yticks(np.arange(0,.81,.2))
        ax.set_xlabel("尺度权重",fontproperties=FONT,fontsize=7.8)
        ax.grid(axis="y",color="#E9EEF0",lw=.55)
        ax.tick_params(length=0,pad=3)
    axes[0].set_ylabel("逐种子平均权重",fontproperties=FONT,fontsize=7.8)
    fig.subplots_adjust(left=.08,right=.985,top=.88,bottom=.18,wspace=.14)
    save(fig,OUT / "C_fig5_violin")


def main():
    perf = pd.read_csv(PERFORMANCE)
    weights = pd.read_csv(WEIGHTS)
    assert len(perf)==96 and len(weights)==48
    assert not perf.isna().any().any() and not weights.isna().any().any()
    OUT.mkdir(parents=True,exist_ok=True)
    setup()
    forest_pair(perf,weights)
    matrix_pair(perf,weights)
    raincloud_pair(perf,weights)
    print(OUT)


if __name__=="__main__":
    main()
