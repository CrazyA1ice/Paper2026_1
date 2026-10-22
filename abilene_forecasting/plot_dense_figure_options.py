"""Dense figure options for forecast-horizon and OD-channel evidence."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "results/global_weight_ablation/analysis"
OUT = ROOT.parent / "paper_figures/dense_options"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

FONT = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
GAIN, LOSS, INK = "#287C82", "#BF7664", "#243748"


def setup():
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7.2, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#ACB9BF", "axes.labelcolor": INK,
        "text.color": INK, "xtick.color": "#62727F", "ytick.color": "#62727F",
    })


def export(fig, stem):
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.svg")
    fig.savefig(f"{stem}.png", dpi=600)
    fig.savefig(f"{stem}.tiff", dpi=600)
    plt.close(fig)


def horizon_atlas(data):
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.3),
                             gridspec_kw={"height_ratios": [1.45, 1]},
                             sharex="col")
    for col, (dataset, title) in enumerate((("abilene", "Abilene"), ("geant", "GÉANT"))):
        part = data[data.dataset == dataset]
        matrix = part.pivot(index="seed", columns="horizon", values="reduction_pct")
        assert matrix.shape == (8, 24) and not matrix.isna().any().any()
        x = matrix.columns.to_numpy()
        values = matrix.to_numpy()
        ax = axes[0, col]
        for row in values:
            ax.plot(x, row, color="#9AAEB5", lw=.65, alpha=.65, zorder=1)
        lo, hi = np.quantile(values, [.25, .75], axis=0)
        ax.fill_between(x, lo, hi, color=GAIN, alpha=.16, linewidth=0, zorder=2)
        ax.plot(x, values.mean(axis=0), color=INK, lw=1.9, zorder=3)
        ax.axhline(0, color="#8D9BA2", lw=.8, ls=(0, (4, 3)))
        ax.set_title(title, loc="left", fontsize=9.2, fontweight="bold", pad=7)
        ax.set_xlim(.5, 24.5)
        ax.set_xticks([1, 4, 8, 12, 16, 20, 24])
        ax.set_ylabel("MSE 降低率 (%)", fontproperties=FONT, fontsize=7.8)
        ax.grid(axis="y", color="#EDF0F2", lw=.6)
        ax.tick_params(length=0, pad=3)
        ax.set_ylim((-50, 62) if dataset == "abilene" else (-31, 24))
        heat = axes[1, col]
        binary = (values > 0).astype(int)
        heat.pcolormesh(np.arange(.5, 25.5, 1), np.arange(9), binary,
                        cmap=ListedColormap([LOSS, GAIN]), vmin=0, vmax=1,
                        shading="flat", edgecolors="white", linewidth=.4)
        heat.set_ylim(8, 0)
        heat.set_yticks(np.arange(8) + .5, matrix.index.astype(str))
        heat.set_ylabel("随机种子", fontproperties=FONT, fontsize=7.8)
        heat.set_xlabel("预测步长 (h)", fontproperties=FONT, fontsize=7.8)
        heat.tick_params(length=0, pad=3)
    fig.legend(
        handles=[Line2D([0], [0], color=INK, lw=1.9, label="八种子均值"),
                 Patch(facecolor=GAIN, alpha=.22, label="种子间四分位区间"),
                 Patch(facecolor=GAIN, label="路由误差更低"),
                 Patch(facecolor=LOSS, label="全局权重误差更低")],
        loc="upper center", bbox_to_anchor=(.53, .995), ncol=4,
        prop=FONT, frameon=False, handlelength=1.4, columnspacing=1.2,
    )
    fig.subplots_adjust(left=.08, right=.985, top=.86, bottom=.11, wspace=.18, hspace=.14)
    export(fig, OUT / "option_C_horizon_atlas")


def channel_atlas(data):
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.25),
                             gridspec_kw={"height_ratios": [1, 1.35]})
    for col, (dataset, title) in enumerate((("abilene", "Abilene"), ("geant", "GÉANT"))):
        part = data[data.dataset == dataset]
        sign = part.pivot(index="seed", columns="channel", values="difference")
        baseline = part.groupby("channel").global_mse.mean()
        order = baseline.sort_values().index
        sign = sign[order]
        assert sign.shape[0] == 8 and not sign.isna().any().any()
        wins = (sign > 0).sum(axis=0)
        share = 100 * wins.value_counts().reindex(range(9), fill_value=0).sort_index() / len(wins)
        majority = 100 * (wins >= 5).mean()
        ax = axes[0, col]
        colors = [LOSS if k <= 3 else "#B5C0C4" if k == 4 else GAIN for k in range(9)]
        ax.bar(range(9), share.to_numpy(), color=colors, width=.78, zorder=2)
        ax.set_title(f"{title}   {len(wins)} OD通道 · {majority:.1f}% 多数种子改善",
                     loc="left", fontproperties=FONT, fontsize=8, pad=7)
        ax.set_ylabel("OD通道占比 (%)", fontproperties=FONT, fontsize=7.7)
        ax.set_xlabel("取得较低MSE的随机种子数（共8个）", fontproperties=FONT, fontsize=7.7)
        ax.set_xticks(range(9))
        ax.set_ylim(0, 34)
        ax.grid(axis="y", color="#EDF0F2", lw=.6)
        ax.tick_params(length=0, pad=3)
        hm = axes[1, col]
        binary = (sign.to_numpy() > 0).astype(int)
        hm.imshow(binary, aspect="auto", interpolation="nearest",
                  cmap=ListedColormap([LOSS, GAIN]), vmin=0, vmax=1,
                  extent=(0, 100, 8, 0))
        hm.set_yticks(np.arange(8) + .5, sign.index.astype(str))
        hm.set_xticks([0, 25, 50, 75, 100])
        hm.set_ylabel("随机种子", fontproperties=FONT, fontsize=7.7)
        hm.set_xlabel("OD通道按全局模型MSE由低到高排序 (%)", fontproperties=FONT, fontsize=7.7)
        hm.tick_params(length=0, pad=3)
    fig.legend(
        handles=[Patch(facecolor=GAIN, label="路由误差更低"),
                 Patch(facecolor=LOSS, label="全局权重误差更低")],
        loc="upper center", bbox_to_anchor=(.5, .995), ncol=2,
        prop=FONT, frameon=False, handlelength=1.3, columnspacing=2,
    )
    fig.subplots_adjust(left=.08, right=.985, top=.86, bottom=.11, wspace=.18, hspace=.35)
    export(fig, OUT / "option_D_channel_atlas")


def main():
    horizons = pd.read_csv(DATA / "horizon_paired_errors.csv")
    channels = pd.read_csv(DATA / "channel_paired_errors.csv")
    assert len(horizons) == 2 * 8 * 24
    assert len(channels) == 8 * (144 + 524)
    setup()
    OUT.mkdir(parents=True, exist_ok=True)
    horizon_atlas(horizons)
    channel_atlas(channels)
    print(OUT)


if __name__ == "__main__":
    main()
