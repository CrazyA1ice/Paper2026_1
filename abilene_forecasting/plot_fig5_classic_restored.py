"""Recreate the earlier Figure 5 style from stored per-window router weights."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "paper_figures" / "fig5_classic_restored"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

COLORS = ("#4F81BD", "#6A9F58", "#D9782D")
SEEDS = range(42, 50)
JITTER = np.array([-.052, .024, -.030, .061, -.012, .043, -.063, .009])
CHINESE_FONT = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")


def load_weights(dataset):
    runs = []
    for seed in SEEDS:
        source = ROOT / "results" / dataset / f"dlinear_scale_seed{seed}" / "router_weights.csv"
        weights = pd.read_csv(source, header=None).to_numpy(float)
        assert weights.ndim == 2 and weights.shape[1] == 3
        assert np.all(np.isfinite(weights))
        assert np.allclose(weights.sum(axis=1), 1, atol=1e-5)
        runs.append(weights)
    return runs


def main():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Microsoft YaHei", "DejaVu Sans"],
        "font.size": 7.2,
        "axes.labelsize": 7.4,
        "axes.titlesize": 9.0,
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
    fig, axes = plt.subplots(1, 2, figsize=(7.00, 3.29), sharey=True)
    for index, (ax, dataset, title) in enumerate(zip(
        axes, ("abilene", "geant"), ("Abilene", "GÉANT")
    )):
        runs = load_weights(dataset)
        pooled = np.vstack(runs)
        violins = ax.violinplot([pooled[:, i] for i in range(3)],
                                positions=[1, 2, 3], widths=.68,
                                showmeans=False, showmedians=True,
                                showextrema=False)
        for body, color in zip(violins["bodies"], COLORS):
            body.set_facecolor(color)
            body.set_edgecolor(color)
            body.set_alpha(.26)
            body.set_linewidth(.9)
        violins["cmedians"].set_color("#222222")
        violins["cmedians"].set_linewidth(.9)

        for scale_index, color in enumerate(COLORS):
            seed_means = np.array([run[:, scale_index].mean() for run in runs])
            ax.scatter(scale_index + 1 + JITTER, seed_means, s=24,
                       facecolor=color, edgecolor="white", linewidth=.55, zorder=4)
            ax.errorbar(scale_index + 1, seed_means.mean(),
                        yerr=seed_means.std(ddof=1), fmt="D", ms=4.3,
                        color="#222222", mfc="#222222", mec="#222222",
                        capsize=2.5, lw=.9, zorder=5)

        ax.axhline(1/3, color="#666666", lw=.8, ls="--", dashes=(4, 3))
        ax.set_xticks([1, 2, 3], ["α₁", "α₂", "α₄"], fontfamily="DejaVu Sans")
        ax.set_xlabel("尺度权重", fontproperties=CHINESE_FONT)
        ax.set_title(title, fontweight="bold", fontfamily="Times New Roman")
        ax.set_ylim(0, .82)
        ax.grid(axis="y", color="#dddddd", ls="--", lw=.45, alpha=.55)
        ax.text(-.12, 1.04, "ab"[index], transform=ax.transAxes,
                fontsize=9.5, fontweight="bold", fontfamily="Times New Roman",
                ha="left", va="bottom")
    axes[0].set_ylabel("样本级路由权重", fontproperties=CHINESE_FONT)
    fig.subplots_adjust(left=.09, right=.99, bottom=.18, top=.88, wspace=.14)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "fig5_router_weights_classic"
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
