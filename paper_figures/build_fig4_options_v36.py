"""Three truthful Figure 4 alternatives from all H=24 channel comparisons."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "abilene_forecasting/results/global_weight_ablation/analysis/channel_paired_errors.csv"
OUT = ROOT / "paper_figures/fig4_options_v36"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment


mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7,
    "axes.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#8C9AA3",
    "axes.labelcolor": "#203748",
    "xtick.color": "#455965",
    "ytick.color": "#455965",
    "text.color": "#203748",
})
TEAL = "#287F88"
CORAL = "#C47C68"
NAVY = "#1F4051"
GREY = "#A9B6BD"
GRID = "#E7ECEE"


def export(fig, name):
    dest = OUT / name
    require_matplotlib_panel_alignment(
        fig, json_out=str(dest) + ".alignment.json",
        overlay_svg=str(dest) + ".alignment.svg", strict=True,
        tolerance_pt=1.5, gutter_tolerance_pt=1.5,
    )
    fig.savefig(str(dest) + ".png", dpi=420)
    fig.savefig(str(dest) + ".pdf")
    fig.savefig(str(dest) + ".svg")
    fig.savefig(str(dest) + ".tiff", dpi=600)
    plt.close(fig)
    print(dest)


def option_a(data):
    fig, axes = plt.subplots(2, 2, figsize=(6.45, 3.7))
    fig.subplots_adjust(left=0.095, right=0.985, bottom=0.12, top=0.89,
                        wspace=0.24, hspace=0.57)
    for col, (dataset, label, n) in enumerate([
        ("abilene", "a  Abilene", 144), ("geant", "b  GÉANT", 524)
    ]):
        sub = data[data.dataset == dataset]
        wins = sub.groupby("channel").win.sum()
        freq = wins.value_counts().reindex(range(9), fill_value=0).to_numpy()
        assert int(freq.sum()) == n
        top = axes[0, col]
        top.bar(range(9), freq / n * 100, width=0.75,
                color=[CORAL if i < 4 else GREY if i == 4 else TEAL for i in range(9)])
        top.axvline(4.5, color="#B4C0C5", ls=(0, (3, 2)), lw=0.8)
        top.set_title(label, loc="left", fontsize=9, weight="bold", pad=6)
        top.text(0.98, 1.05, f"{(wins >= 5).sum()}/{n} 通道在多数种子改善",
                 transform=top.transAxes, ha="right", va="bottom", color=TEAL, fontsize=6.7)
        top.set_xticks(range(9))
        top.set_ylim(0, 34)
        top.set_yticks([0, 10, 20, 30])
        top.set_xlabel("通道改善的随机种子数（0—8）", labelpad=3)
        top.grid(axis="y", color=GRID, lw=0.6)
        top.set_axisbelow(True)
        if col == 0:
            top.set_ylabel("OD通道占比（%）")

        bottom = axes[1, col]
        seed_pct = sub.groupby("seed").win.mean().mul(100)
        y = np.arange(8)
        bottom.barh(y, seed_pct.values, height=0.6,
                    color=[TEAL if x >= 50 else CORAL for x in seed_pct.values])
        bottom.axvline(50, ls=(0, (3, 2)), lw=0.9, color="#96A5AD")
        bottom.set_yticks(y, seed_pct.index.astype(str))
        bottom.invert_yaxis()
        bottom.set_xlim(0, 110)
        bottom.set_xticks([0, 25, 50, 75, 100])
        bottom.set_xlabel("各随机种子下改善的OD通道占比（%）", labelpad=3)
        bottom.grid(axis="x", color=GRID, lw=0.6)
        bottom.set_axisbelow(True)
        if col == 0:
            bottom.set_ylabel("随机种子")
    export(fig, "A_覆盖与种子稳定性")


def option_b(data):
    frame = data.copy()
    frame["difficulty"] = frame.groupby(["dataset", "channel"]).global_mse.transform("mean")
    frame["quartile"] = frame.groupby("dataset").difficulty.transform(
        lambda x: pd.qcut(x.rank(method="dense"), 4, labels=False) + 1
    )
    cmap = LinearSegmentedColormap.from_list("coral_white_teal", [CORAL, "#F6F8F7", TEAL])
    norm = TwoSlopeNorm(vmin=0, vcenter=50, vmax=100)
    fig, axes = plt.subplots(1, 2, figsize=(6.45, 3.28))
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.22, top=0.84, wspace=0.22)
    for ax, (dataset, label, n) in zip(axes, [
        ("abilene", "a  Abilene", 144), ("geant", "b  GÉANT", 524)
    ]):
        sub = frame[frame.dataset == dataset]
        grid = sub.groupby(["seed", "quartile"]).win.mean().mul(100).unstack()
        assert grid.shape == (8, 4) and len(sub) == n * 8
        ax.imshow(grid.to_numpy(), cmap=cmap, norm=norm, aspect="auto")
        ax.set_title(label, loc="left", fontsize=9, weight="bold", pad=6)
        ax.text(0.98, 1.07, "单元格：通道改善占比（%）",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5, color="#5D6D76")
        ax.set_xticks(range(4), ["Q1 低", "Q2", "Q3", "Q4 高"])
        ax.set_yticks(range(8), [str(x) for x in grid.index])
        ax.set_xlabel("全局权重模型的平均通道MSE分位组", labelpad=7)
        for row in range(8):
            for col in range(4):
                value = grid.iloc[row, col]
                ax.text(col, row, f"{value:.0f}", ha="center", va="center",
                        color="white" if value < 25 or value > 77 else NAVY,
                        fontsize=7, weight="bold" if value < 25 or value > 77 else "normal")
        ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 8, 1), minor=True)
        ax.grid(which="minor", color="white", lw=1.1)
        ax.tick_params(which="minor", bottom=False, left=False)
        if dataset == "abilene":
            ax.set_ylabel("随机种子")
    export(fig, "B_按通道难度分层")


def option_c(data):
    seed_results = pd.read_csv(
        ROOT / "abilene_forecasting/results/global_weight_ablation/analysis/paired_seed_results.csv"
    )
    fig, axes = plt.subplots(2, 2, figsize=(6.45, 3.7))
    fig.subplots_adjust(left=0.095, right=0.985, bottom=0.12, top=0.89,
                        wspace=0.24, hspace=0.57)
    for col, (dataset, label, n) in enumerate([
        ("abilene", "a  Abilene", 144), ("geant", "b  GÉANT", 524)
    ]):
        sub = data[data.dataset == dataset]
        counts = sub.groupby("channel").win.sum()
        assert len(counts) == n
        top = axes[0, col]
        k = np.arange(1, 9)
        coverage = np.array([(counts >= value).mean() * 100 for value in k])
        top.axvspan(4.5, 8.5, color="#E9F3F3", lw=0)
        top.step(k, coverage, where="mid", color=TEAL, lw=1.8)
        top.scatter(k, coverage, s=18, color=TEAL, zorder=3)
        top.set_xlim(0.75, 8.25)
        top.set_ylim(0, 105)
        top.set_xticks(k)
        top.set_yticks([0, 25, 50, 75, 100])
        top.set_title(label, loc="left", fontsize=9, weight="bold", pad=6)
        top.text(0.98, 1.05, f"≥5种子：{(counts >= 5).sum()}/{n} 通道",
                 transform=top.transAxes, ha="right", va="bottom", fontsize=6.6, color=TEAL)
        top.set_xlabel("至少在多少个随机种子中改善", labelpad=3)
        top.grid(axis="y", color=GRID, lw=0.6)
        top.set_axisbelow(True)
        if col == 0:
            top.set_ylabel("满足条件的OD通道占比（%）")

        bottom = axes[1, col]
        seeds = seed_results[seed_results.dataset == dataset].sort_values("seed")
        assert len(seeds) == 8
        y = np.arange(8)
        values = seeds.adaptive_reduction_pct.to_numpy()
        bottom.axvline(0, color="#98A5AD", lw=0.9, ls=(0, (3, 2)))
        for yi, value in zip(y, values):
            color = TEAL if value > 0 else CORAL
            bottom.plot([0, value], [yi, yi], color=color, lw=1.3, alpha=0.75)
            bottom.scatter(value, yi, s=23, color=color, zorder=3)
        bottom.set_xlim(-15, 15)
        bottom.set_xticks([-15, -10, -5, 0, 5, 10, 15])
        bottom.set_yticks(y, seeds.seed.astype(str))
        bottom.invert_yaxis()
        bottom.set_xlabel("相对全局权重模型的整段MSE降低率（%）", labelpad=3)
        bottom.grid(axis="x", color=GRID, lw=0.6)
        bottom.set_axisbelow(True)
        if col == 0:
            bottom.set_ylabel("随机种子")
    export(fig, "C_覆盖与整体配对误差")


def main():
    data = pd.read_csv(SOURCE)
    assert len(data) == 5344
    assert not data[["global_mse", "adaptive_mse", "difference"]].isna().any().any()
    assert data.groupby("dataset").size().to_dict() == {"abilene": 1152, "geant": 4192}
    data["win"] = data.difference > 0
    option_a(data)
    option_b(data)
    option_c(data)


if __name__ == "__main__":
    main()
