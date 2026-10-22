"""Compact OD-channel win-count matrix for two internal baselines."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "paper_figures/fig4_channel_coverage_preview/fig4_channel_coverage_source.csv"
OUT = ROOT.parent / "paper_figures/fig4_joint_coverage_preview"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


BLUE = "#4F81BD"
ORANGE = "#D9782D"
CHINESE_FONT = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene", 144), ("geant", "GÉANT", 524))


def main():
    data = pd.read_csv(SOURCE)
    assert len(data) == 10688 and data.seed.nunique() == 8
    counts = data.groupby(["dataset", "channel", "baseline"]).router_better.sum().unstack()
    assert set(counts.columns) == {"DLinear", "固定等权"}

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
        "xtick.direction": "in",
        "ytick.direction": "in",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    palette = LinearSegmentedColormap.from_list("count_blue", ["#F9FBFC", "#B5CBE1", BLUE, "#285D93"])
    norm = Normalize(vmin=0, vmax=30)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.85))
    fig.subplots_adjust(left=.095, right=.99, bottom=.145, top=.875, wspace=.14)
    table_rows = []

    for panel, (ax, (dataset, title, n_channels)) in enumerate(zip(axes, DATASETS)):
        sub = counts.loc[dataset]
        assert len(sub) == n_channels
        matrix = np.zeros((9, 9), dtype=int)
        for channel, record in sub.iterrows():
            x, y = int(record["DLinear"]), int(record["固定等权"])
            assert 0 <= x <= 8 and 0 <= y <= 8
            matrix[y, x] += 1
        assert matrix.sum() == n_channels
        percent = matrix / n_channels * 100
        ax.imshow(percent, origin="lower", cmap=palette, norm=norm,
                  extent=(-.5, 8.5, -.5, 8.5), interpolation="nearest")
        ax.add_patch(Rectangle((4.5, 4.5), 4, 4, fill=False,
                               edgecolor=ORANGE, linewidth=1.2, zorder=3))
        ax.axvline(4.5, color=ORANGE, lw=.6, ls=(0, (2, 3)), alpha=.7)
        ax.axhline(4.5, color=ORANGE, lw=.6, ls=(0, (2, 3)), alpha=.7)
        ax.set_xticks(range(9))
        ax.set_yticks(range(9))
        ax.set_xlim(-.5, 8.5)
        ax.set_ylim(-.5, 8.5)
        ax.set_xticks(np.arange(-.5, 9, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 9, 1), minor=True)
        ax.grid(which="minor", color="white", lw=.75)
        ax.tick_params(which="minor", bottom=False, left=False)
        ax.set_xlabel("优于DLinear的随机种子数", color=BLUE, fontproperties=CHINESE_FONT)
        if panel == 0:
            ax.set_ylabel("优于固定等权的随机种子数", color=ORANGE,
                          fontproperties=CHINESE_FONT)
        both = int(matrix[5:, 5:].sum())
        ax.set_title(f"{'ab'[panel]}  {title}", loc="left", pad=10,
                     fontfamily="Times New Roman", fontweight="bold", fontsize=9)
        ax.text(.99, 1.045, f"双基线≥5/8：{both}/{n_channels}",
                transform=ax.transAxes, ha="right", va="bottom",
                fontproperties=CHINESE_FONT, fontsize=7, color="#333333")
        for y in range(9):
            for x in range(9):
                value = int(matrix[y, x])
                table_rows.append((dataset, x, y, value, value / n_channels * 100))
                if value:
                    ax.text(x, y, str(value), ha="center", va="center",
                            fontsize=6.8, color="white" if percent[y, x] > 12 else "#283E50",
                            weight="bold" if value >= 10 else "normal")

    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(table_rows, columns=["dataset", "wins_vs_dlinear", "wins_vs_equal",
                                       "channel_count", "channel_pct"]).to_csv(
        OUT / "fig4_joint_coverage_matrix.csv", index=False)
    stem = OUT / "fig4_joint_coverage_preview"
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


if __name__ == "__main__":
    main()
