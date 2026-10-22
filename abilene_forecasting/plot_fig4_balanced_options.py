"""Three compact Figure 4 layouts giving DLinear and equal fusion equal emphasis."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "paper_figures/fig4_channel_coverage_preview/fig4_channel_coverage_source.csv"
OUT = ROOT.parent / "paper_figures/fig4_balanced_options"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


BLUE = "#4F81BD"
ORANGE = "#D9782D"
CHINESE_FONT = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene", 144), ("geant", "GÉANT", 524))
BASELINES = (("DLinear", BLUE), ("固定等权", ORANGE))


def mix_white(color, strength):
    rgb = np.array(to_rgb(color))
    return tuple((1 - strength) + strength * rgb)


def export(fig, filename):
    stem = OUT / filename
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(stem)


def prepare():
    data = pd.read_csv(SOURCE)
    assert len(data) == 10688
    wins = data.groupby(["dataset", "baseline", "channel"]).router_better.sum()
    coverage = data.groupby(["dataset", "baseline", "seed"]).router_better.mean().mul(100)
    assert wins.groupby(["dataset", "baseline"]).size().to_dict() == {
        ("abilene", "DLinear"): 144, ("abilene", "固定等权"): 144,
        ("geant", "DLinear"): 524, ("geant", "固定等权"): 524,
    }
    return wins, coverage


def option_a(wins):
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.35), sharex=True, sharey=True)
    fig.subplots_adjust(left=.09, right=.99, bottom=.16, top=.80, wspace=.15)
    for panel, (ax, (dataset, name, total)) in enumerate(zip(axes, DATASETS)):
        ax.axhspan(4.5, 8.5, color="#F5F7F8", zorder=0)
        ax.axvline(0, color="#888888", lw=.75)
        ax.axhline(4.5, color="#B7B7B7", lw=.7, ls=(0, (3, 3)))
        for baseline, color in BASELINES:
            values = wins.loc[dataset, baseline]
            freq = values.value_counts().reindex(range(9), fill_value=0) / total * 100
            sign = -1 if baseline == "DLinear" else 1
            shift = -.17 if sign < 0 else .17
            ax.barh(np.arange(9) + shift, sign * freq.to_numpy(), height=.33,
                    color=color, alpha=.88, zorder=2)
        ax.set_xlim(-75, 75)
        ax.set_ylim(-.5, 8.5)
        ax.set_xticks([-75, -50, -25, 0, 25, 50, 75],
                      ["75", "50", "25", "0", "25", "50", "75"])
        ax.set_yticks(range(9))
        ax.set_title(f"{'ab'[panel]}  {name}", loc="left", y=1.15,
                     fontfamily="Times New Roman", fontweight="bold", fontsize=9)
        ax.text(.25, 1.035, "DLinear", transform=ax.transAxes, ha="center",
                color=BLUE, fontsize=7.5, fontweight="bold")
        ax.text(.75, 1.035, "固定等权", transform=ax.transAxes, ha="center",
                color=ORANGE, fontproperties=CHINESE_FONT, fontsize=7.5)
        ax.set_xlabel("OD通道占比（%）", fontproperties=CHINESE_FONT)
        ax.grid(axis="x", color="#E5E5E5", lw=.5, ls="--", zorder=0)
        if panel == 0:
            ax.set_ylabel("本文方法MSE更低的随机种子数", fontproperties=CHINESE_FONT)
    export(fig, "A_镜像通道分布")


def option_b(coverage):
    fig, axes = plt.subplots(2, 1, figsize=(7, 2.85), sharex=True)
    fig.subplots_adjust(left=.145, right=.985, bottom=.15, top=.89, hspace=.36)
    for panel, (ax, (dataset, name, total)) in enumerate(zip(axes, DATASETS)):
        for row, (baseline, color) in enumerate(BASELINES):
            values = coverage.loc[dataset, baseline].reindex(range(42, 50)).to_numpy()
            assert len(values) == 8 and np.isfinite(values).all()
            for col, value in enumerate(values):
                strength = .12 + .82 * value / 100
                ax.add_patch(Rectangle((col - .48, row - .46), .96, .92,
                                       facecolor=mix_white(color, strength),
                                       edgecolor="white", lw=1.2))
                ax.text(col, row, f"{value:.0f}", ha="center", va="center",
                        fontsize=7, color="white" if value >= 66 else "#263846",
                        fontweight="bold" if value >= 80 else "normal")
        ax.set_xlim(-.5, 7.5)
        ax.set_ylim(1.5, -.5)
        ax.set_yticks([0, 1], ["DLinear", "固定等权"])
        for tick, color in zip(ax.get_yticklabels(), [BLUE, ORANGE]):
            tick.set_fontproperties(CHINESE_FONT)
            tick.set_color(color)
        ax.set_title(f"{'ab'[panel]}  {name}  ·  {total} OD", loc="left", pad=5,
                     fontfamily="Times New Roman", fontweight="bold", fontsize=9)
        ax.set_ylabel("对照", fontproperties=CHINESE_FONT)
        ax.tick_params(axis="both", length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[1].set_xticks(range(8), [str(seed) for seed in range(42, 50)])
    axes[1].set_xlabel("随机种子 · 格内为本文方法MSE更低的OD通道占比（%）",
                       fontproperties=CHINESE_FONT)
    export(fig, "B_逐种子覆盖矩阵")


def option_c(wins):
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.75), sharex=True)
    fig.subplots_adjust(left=.115, right=.99, bottom=.20, top=.83, wspace=.16)
    labels = ["0—3", "4", "5—7", "8"]
    categories = [lambda v: v <= 3, lambda v: v == 4,
                  lambda v: (v >= 5) & (v <= 7), lambda v: v == 8]
    strengths = [.20, .37, .68, 1.0]
    for panel, (ax, (dataset, name, total)) in enumerate(zip(axes, DATASETS)):
        for row, (baseline, color) in enumerate(BASELINES):
            values = wins.loc[dataset, baseline]
            pieces = np.array([criterion(values).sum() / total * 100 for criterion in categories])
            assert abs(pieces.sum() - 100) < 1e-9
            left = 0.0
            for index, (part, strength) in enumerate(zip(pieces, strengths)):
                ax.barh(row, part, left=left, height=.54, color=mix_white(color, strength),
                        edgecolor="white", lw=.8)
                if part >= 6:
                    ax.text(left + part / 2, row, f"{part:.0f}", ha="center", va="center",
                            color="white" if strength > .65 else "#253746", fontsize=7)
                left += part
        ax.set_title(f"{'ab'[panel]}  {name}", loc="left", pad=6,
                     fontfamily="Times New Roman", fontweight="bold", fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_ylim(1.55, -.55)
        if panel == 0:
            ax.set_yticks([0, 1], ["DLinear", "固定等权"])
            for tick, color in zip(ax.get_yticklabels(), [BLUE, ORANGE]):
                tick.set_fontproperties(CHINESE_FONT)
                tick.set_color(color)
        else:
            ax.set_yticks([0, 1], ["", ""])
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel("OD通道占比（%）", fontproperties=CHINESE_FONT)
        ax.axvline(50, color="#BBBBBB", lw=.5, ls="--", zorder=0)
    fig.text(.5, .93, "本文方法胜出种子数：  0—3    |    4    |    5—7    |    8",
             ha="center", fontproperties=CHINESE_FONT, fontsize=7.3)
    export(fig, "C_胜出稳定性构成")


def main():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Microsoft YaHei", "DejaVu Sans"],
        "font.size": 7.2,
        "axes.labelsize": 7.4,
        "xtick.labelsize": 6.6,
        "ytick.labelsize": 6.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": .8,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    wins, coverage = prepare()
    option_a(wins)
    option_b(coverage)
    option_c(wins)


if __name__ == "__main__":
    main()
