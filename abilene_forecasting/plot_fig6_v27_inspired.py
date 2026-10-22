"""Render the v27-style router figure from the eight real training seeds."""

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
OUT = ROOT.parent / "paper_figures" / "fig6_router_seedwise_realdata"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


COLORS = ("#4E82B5", "#77A876", "#E3A16A")
SCALES = (1, 2, 4)
OFFSETS = np.array([-0.16, -0.11, -0.065, -0.02, 0.02, 0.065, 0.11, 0.16])


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
    fig, axes = plt.subplots(
        2, 2, figsize=(6.8, 3.4), sharex="col", sharey="row",
        gridspec_kw={"height_ratios": [3.0, 0.85]},
    )
    for col, (dataset, name) in enumerate([("abilene", "Abilene"), ("geant", "GÉANT")]):
        upper, lower = axes[:, col]
        upper.axhline(1 / 3, color="#7E8C95", lw=0.8, ls=(0, (4, 3)), zorder=0)
        upper.set_title(f"({chr(97 + col)})  {name}", loc="left", fontsize=8.7, fontweight="bold", pad=9)
        for i, scale in enumerate(SCALES):
            part = data[(data.dataset == dataset) & (data.scale == scale)].sort_values("seed")
            assert part.seed.tolist() == list(range(42, 50))
            values = part.adaptive_mean.to_numpy()
            spreads = part.adaptive_within_seed_sd.to_numpy()
            body = upper.violinplot(values, positions=[i + 1], widths=0.72,
                                    showmeans=False, showmedians=False,
                                    showextrema=False, bw_method=0.35)["bodies"][0]
            body.set_facecolor(COLORS[i])
            body.set_edgecolor(COLORS[i])
            body.set_alpha(0.20)
            body.set_linewidth(0.9)
            upper.scatter(i + 1 + OFFSETS, values, s=13, color=COLORS[i],
                          edgecolor="white", linewidth=0.55, zorder=3)
            center = values.mean()
            half = stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
            upper.errorbar(i + 1 + 0.28, center, yerr=half, fmt="D", markersize=3.3,
                           color="#27323D", markerfacecolor="white", capsize=2,
                           elinewidth=0.95, capthick=0.95, zorder=4)
            lower.scatter(i + 1 + OFFSETS, spreads, s=12, color=COLORS[i],
                          edgecolor="white", linewidth=0.45, zorder=3)
            lower.plot([i + 0.77, i + 1.23], [np.median(spreads)] * 2,
                       color="#27323D", lw=1.0, zorder=2)
        upper.set(ylim=(0, 0.8), xlim=(0.52, 3.48), yticks=np.arange(0, 0.81, 0.2))
        lower.set(ylim=(0, 0.155), yticks=[0, 0.05, 0.10, 0.15],
                  xticks=[1, 2, 3], xticklabels=["α₁", "α₂", "α₄"])
        for ax in (upper, lower):
            ax.grid(axis="y", color="#E7EBEE", lw=0.6)
            ax.tick_params(length=0, pad=3)
        lower.set_xlabel("尺度权重", fontproperties=chinese_font, fontsize=8)
    axes[0, 0].set_ylabel("逐种子平均权重", fontproperties=chinese_font, fontsize=8)
    axes[1, 0].set_ylabel("种子内标准差", fontproperties=chinese_font, fontsize=8)
    fig.subplots_adjust(left=0.10, right=0.985, top=0.92, bottom=0.12, wspace=0.14, hspace=0.22)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_matplotlib_panel_alignment(
        fig,
        json_out=f"{OUT}.alignment.json",
        overlay_svg=f"{OUT}.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(f"{OUT}.pdf")
    fig.savefig(f"{OUT}.svg")
    fig.savefig(f"{OUT}.png", dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
