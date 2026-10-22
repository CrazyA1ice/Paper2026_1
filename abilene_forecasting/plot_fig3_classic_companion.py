"""Figure 3 companion to the restored classic router-weight Figure 5."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper_figures" / "source_data_v24" / "fig5_relative_improvement_8seeds.csv"
OUT = ROOT.parent / "paper_figures" / "fig3_classic_companion"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CHINESE_FONT = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
COLORS = {"DLinear": "#4F81BD", "固定等权": "#D9782D"}
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
METRICS = ("MSE", "MAE", "RMSE")
YROWS = (6, 5, 4, 2.5, 1.5, .5)
JITTER = np.array([-.15, -.11, -.07, -.02, .025, .07, .115, .16])


def ci95(values):
    return stats.t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))


def main():
    data = pd.read_csv(SOURCE)
    assert len(data) == 96 and not data.isna().any().any()
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
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.45), sharex=True, sharey=True)
    for panel, (ax, (dataset, title)) in enumerate(zip(axes, DATASETS)):
        ax.axvline(0, color="#666666", lw=.8, ls="--", dashes=(4, 3), zorder=0)
        for x in (-5, 5, 10, 15):
            ax.axvline(x, color="#dddddd", lw=.45, ls="--", alpha=.55, zorder=0)
        ax.axhline(3.55, color="#c8c8c8", lw=.7, zorder=0)
        ax.text(-14.5, 6.73, "DLinear", color=COLORS["DLinear"],
                fontsize=7.4, fontweight="bold")
        ax.text(-14.5, 3.04, "固定等权", color=COLORS["固定等权"],
                fontproperties=CHINESE_FONT, fontsize=7.4)
        for baseline_index, baseline in enumerate(COLORS):
            color = COLORS[baseline]
            for metric_index, metric in enumerate(METRICS):
                y = YROWS[baseline_index * 3 + metric_index]
                part = data[(data.dataset == dataset) & (data.baseline == baseline)
                            & (data.metric == metric)].sort_values("seed")
                assert part.seed.tolist() == list(range(42, 50))
                values = part.relative_improvement_pct.to_numpy()
                body = ax.violinplot(values, positions=[y], orientation="horizontal",
                                     widths=.56, showmeans=False, showmedians=False,
                                     showextrema=False, bw_method=.4)["bodies"][0]
                vertices = body.get_paths()[0].vertices
                vertices[:, 1] = np.maximum(vertices[:, 1], y)
                body.set_facecolor(color)
                body.set_edgecolor(color)
                body.set_alpha(.22)
                body.set_linewidth(.75)
                ax.scatter(values, y + JITTER - .17, s=18, color=color,
                           edgecolor="white", linewidth=.55, zorder=3)
                ax.errorbar(values.mean(), y+.08, xerr=ci95(values), fmt="D",
                            markersize=3.6, color="#222222", markerfacecolor="#222222",
                            capsize=2.3, capthick=.9, elinewidth=.9, zorder=4)
        ax.set_xlim(-15, 17)
        ax.set_ylim(-.05, 7.15)
        ax.set_xticks([-15, -10, -5, 0, 5, 10, 15])
        ax.set_yticks(YROWS, ["MSE", "MAE", "RMSE"] * 2)
        ax.set_xlabel("相对改进率（%）", fontproperties=CHINESE_FONT)
        ax.set_title(title, fontfamily="Times New Roman", fontweight="bold", fontsize=9)
        ax.text(-.12, 1.04, "ab"[panel], transform=ax.transAxes,
                fontsize=9.5, fontfamily="Times New Roman", fontweight="bold",
                ha="left", va="bottom")
    fig.subplots_adjust(left=.09, right=.99, bottom=.17, top=.88, wspace=.14)
    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "fig3_relative_improvement_classic"
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
