"""Two manuscript-figure options from matched test-window predictions."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results/global_weight_ablation/analysis/window_error_differences.csv"
OUT = ROOT.parent / "paper_figures/window_level_options"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CHINESE = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
GAIN, LOSS = "#337E80", "#C27662"


def style():
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7.4, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#AAB4BC", "axes.labelcolor": "#253344",
        "text.color": "#253344", "xtick.color": "#5D6B79",
        "ytick.color": "#5D6B79",
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


def plot_temporal_map(data):
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 4.0), sharex=True)
    for ax, (dataset, title) in zip(axes, (("abilene", "Abilene"), ("geant", "GÉANT"))):
        part = data[data.dataset == dataset].copy()
        part["block"] = part.window // 24
        block = part.groupby(["seed", "block"], sort=True).mse_difference.mean().unstack()
        assert block.shape[0] == 8 and not block.isna().any().any()
        binary = (block.to_numpy() > 0).astype(int)
        x = np.linspace(0, 100, binary.shape[1] + 1)
        y = np.arange(9)
        ax.pcolormesh(x, y, binary, shading="flat", vmin=0, vmax=1,
                      cmap=ListedColormap([LOSS, GAIN]), edgecolors="white", linewidth=0.65)
        ax.set_yticks(np.arange(8) + .5, block.index.astype(str))
        ax.set_ylim(8, 0)
        ax.set_xlim(0, 100)
        ax.set_title(f"{title}   改善区块 {100 * binary.mean():.1f}%", loc="left",
                     fontproperties=CHINESE, fontsize=8.7, pad=7)
        ax.set_ylabel("随机种子", fontproperties=CHINESE, fontsize=8)
        ax.tick_params(length=0, pad=4)
        ax.set_xticks([0, 25, 50, 75, 100])
    axes[1].set_xlabel("测试进程 (%)", fontproperties=CHINESE, fontsize=8)
    fig.legend(
        handles=[Patch(facecolor=GAIN, label="样本级路由误差更低"),
                 Patch(facecolor=LOSS, label="全局固定权重误差更低")],
        loc="upper right", bbox_to_anchor=(.98, .985), ncol=2,
        prop=CHINESE, frameon=False, handlelength=1.3, columnspacing=1.5,
    )
    fig.subplots_adjust(left=.085, right=.985, top=.87, bottom=.12, hspace=.42)
    export(fig, OUT / "option_A_temporal_gain_map")


def plot_win_rate_vs_mean(data):
    summaries = data.groupby(["dataset", "seed"]).agg(
        global_mse=("global_window_mse", "mean"),
        adaptive_mse=("adaptive_window_mse", "mean"),
        win_rate=("mse_difference", lambda v: 100 * (v > 0).mean()),
    ).reset_index()
    summaries["mse_reduction"] = 100 * (summaries.global_mse - summaries.adaptive_mse) / summaries.global_mse
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.05), sharex=True, sharey=True)
    for ax, (dataset, title) in zip(axes, (("abilene", "Abilene"), ("geant", "GÉANT"))):
        part = summaries[summaries.dataset == dataset]
        ax.axhline(0, color="#6B7983", lw=.9, ls=(0, (4, 3)), zorder=1)
        ax.axvline(50, color="#ADB8BE", lw=.75, ls=(0, (2, 3)), zorder=1)
        ax.grid(color="#E9EEF0", linewidth=.6, zorder=0)
        colors = [GAIN if val >= 0 else LOSS for val in part.mse_reduction]
        ax.scatter(part.win_rate, part.mse_reduction, c=colors, s=55,
                   edgecolor="white", linewidth=.9, zorder=3)
        for row in part.itertuples():
            if dataset == "geant" and row.seed in (43, 45):
                ax.annotate(str(row.seed), (row.win_rate, row.mse_reduction),
                            xytext=(5, 3), textcoords="offset points", fontsize=6.8,
                            color="#8A4D40")
        ax.set_title(f"{title}   平均窗口胜率 {part.win_rate.mean():.1f}%", loc="left",
                     fontproperties=CHINESE, fontsize=8.4, pad=8)
        ax.set_xlabel("路由误差更低的测试窗口占比 (%)", fontproperties=CHINESE, fontsize=8)
        ax.set_xlim(0, 100)
        ax.set_ylim(-16, 16)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks([-15, -10, -5, 0, 5, 10, 15])
        ax.tick_params(length=0, pad=4)
    axes[0].set_ylabel("相对全局模型的整体 MSE 降低率 (%)", fontproperties=CHINESE, fontsize=8)
    fig.subplots_adjust(left=.095, right=.985, top=.86, bottom=.17, wspace=.12)
    export(fig, OUT / "option_B_win_rate_vs_mean")
    summaries.to_csv(OUT / "option_B_source_data.csv", index=False)


def main():
    data = pd.read_csv(SOURCE)
    assert len(data) == 8 * (813 + 451)
    assert not data.isna().any().any()
    style()
    OUT.mkdir(parents=True, exist_ok=True)
    plot_temporal_map(data)
    plot_win_rate_vs_mean(data)
    print(OUT)


if __name__ == "__main__":
    main()
