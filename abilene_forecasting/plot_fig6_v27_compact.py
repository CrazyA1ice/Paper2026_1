"""Compact v27-style Figure 6 from real seed and test-window statistics."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "global_weight_ablation" / "analysis" / "within_seed_weights.csv"
OUT = ROOT.parent / "paper_figures" / "fig6_router_seedwise_realdata_compact"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


COLORS = ("#4E82B5", "#77A876", "#E3A16A")
OFFSETS = np.array([-0.17, -0.12, -0.07, -0.02, 0.02, 0.07, 0.12, 0.17])


def main():
    data = pd.read_csv(SOURCE)
    assert len(data) == 48 and not data.isna().any().any()
    chinese_font = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#AAB4BC",
        "text.color": "#253344",
        "axes.labelcolor": "#253344",
        "xtick.color": "#5D6B79",
        "ytick.color": "#5D6B79",
    })
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9), sharex=True, sharey=True)
    for ax, (dataset, title) in zip(axes, [("abilene", "Abilene"), ("geant", "GÉANT")]):
        ax.axhline(1 / 3, color="#829098", lw=0.8, ls=(0, (4, 3)), zorder=0)
        for i, scale in enumerate((1, 2, 4)):
            part = data[(data.dataset == dataset) & (data.scale == scale)].sort_values("seed")
            assert part.seed.tolist() == list(range(42, 50))
            means = part.adaptive_mean.to_numpy()
            within_sd = part.adaptive_within_seed_sd.to_numpy()
            violin = ax.violinplot(means, positions=[i + 1], widths=0.72,
                                   showmeans=False, showmedians=False,
                                   showextrema=False, bw_method=0.35)["bodies"][0]
            violin.set_facecolor(COLORS[i])
            violin.set_edgecolor(COLORS[i])
            violin.set_alpha(0.19)
            violin.set_linewidth(0.85)
            for x, mean, sd in zip(i + 1 + OFFSETS, means, within_sd):
                ax.plot([x, x], [max(0, mean - sd), min(1, mean + sd)],
                        color=COLORS[i], lw=0.75, alpha=0.8, zorder=2)
            ax.scatter(i + 1 + OFFSETS, means, s=14, color=COLORS[i],
                       edgecolor="white", linewidth=0.6, zorder=3)
            center = means.mean()
            half = stats.t.ppf(0.975, 7) * means.std(ddof=1) / np.sqrt(8)
            ax.errorbar(i + 1 + 0.28, center, yerr=half, fmt="D", markersize=3.2,
                        markerfacecolor="white", color="#27323D",
                        capsize=2, capthick=0.85, elinewidth=0.85, zorder=4)
        ax.set(xlim=(0.5, 3.5), ylim=(0, 0.83), xticks=[1, 2, 3],
               xticklabels=["α₁", "α₂", "α₄"], yticks=np.arange(0, 0.81, 0.2))
        ax.set_title(title, loc="left", fontsize=8.7, fontweight="bold", pad=7)
        ax.set_xlabel("尺度权重", fontproperties=chinese_font, fontsize=8)
        ax.grid(axis="y", color="#E7EBEE", lw=0.6)
        ax.tick_params(length=0, pad=3)
    axes[0].set_ylabel("逐种子平均权重", fontproperties=chinese_font, fontsize=8)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.86, bottom=0.18, wspace=0.13)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_matplotlib_panel_alignment(
        fig, json_out=f"{OUT}.alignment.json", overlay_svg=f"{OUT}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{OUT}.pdf")
    fig.savefig(f"{OUT}.svg")
    fig.savefig(f"{OUT}.png", dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
