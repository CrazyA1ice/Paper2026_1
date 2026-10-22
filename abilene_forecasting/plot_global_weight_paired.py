"""Plot paired MSE changes against learned global scale weights."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results/global_weight_ablation/analysis/paired_seed_results.csv"
OUT = ROOT.parent / "paper_figures/fig3_global_vs_adaptive_paired"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


def main():
    data = pd.read_csv(SOURCE)
    assert len(data) == 16 and not data.isna().any().any()
    font = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7.4, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#AAB4BC", "text.color": "#253344",
        "axes.labelcolor": "#253344", "xtick.color": "#5D6B79",
        "ytick.color": "#5D6B79",
    })
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0), sharex=True, sharey=True)
    for ax, (name, title) in zip(axes, [("abilene", "Abilene"), ("geant", "GÉANT")]):
        part = data[data.dataset == name].sort_values("seed")
        assert part.seed.tolist() == list(range(42, 50))
        values = part.adaptive_reduction_pct.to_numpy()
        calculated = 100 * (part.global_mse - part.adaptive_mse) / part.global_mse
        assert np.allclose(values, calculated, atol=1e-9)
        y = np.arange(8)
        for yi, value in zip(y, values):
            color = "#387C82" if value >= 0 else "#BD765F"
            ax.plot([0, value], [yi, yi], lw=1.35, color=color, alpha=0.75, zorder=2)
            ax.scatter([value], [yi], s=26, color=color, edgecolor="white",
                       linewidth=0.7, zorder=3)
        mean = values.mean()
        half = stats.t.ppf(0.975, 7) * values.std(ddof=1) / np.sqrt(8)
        ax.errorbar(mean, 8.45, xerr=half, fmt="D", markersize=4.3,
                    markerfacecolor="white", markeredgecolor="#253344",
                    color="#253344", capsize=2.8, capthick=1.1,
                    elinewidth=1.1, zorder=4)
        ax.axvline(0, color="#77858F", lw=0.85, ls=(0, (3, 3)), zorder=1)
        ax.axhline(7.8, color="#D7DEE2", lw=0.7)
        ax.set_title(f"{title}  ({int((values > 0).sum())}/8)", loc="left",
                     fontsize=9, fontweight="bold", pad=6)
        ax.set_xlim(-16, 16)
        ax.set_xticks([-15, -10, -5, 0, 5, 10, 15])
        ax.set_ylim(9.05, -0.65)
        ax.set_yticks(list(y) + [8.45], [str(s) for s in part.seed] + ["均值"],
                      fontproperties=font)
        ax.grid(axis="x", color="#EDF0F2", lw=0.6)
        ax.tick_params(length=0, pad=3)
        ax.set_xlabel("相对全局权重模型的 MSE 降低率 (%)", fontproperties=font, fontsize=7.8)
    axes[0].set_ylabel("随机种子", fontproperties=font, fontsize=8)
    fig.subplots_adjust(left=0.095, right=0.985, top=0.87, bottom=0.16, wspace=0.12)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_matplotlib_panel_alignment(
        fig, json_out=f"{OUT}.alignment.json", overlay_svg=f"{OUT}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{OUT}.pdf")
    fig.savefig(f"{OUT}.svg")
    fig.savefig(f"{OUT}.png", dpi=600)
    fig.savefig(f"{OUT}.tiff", dpi=600)
    plt.close(fig)
    print(f"{OUT}.png")


if __name__ == "__main__":
    main()
