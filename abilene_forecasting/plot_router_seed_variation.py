"""Plot the router's within-seed test-window variation for the manuscript."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "results" / "global_weight_ablation" / "analysis" / "within_seed_weights.csv"
OUT = ROOT.parent / "paper_figures" / "router_seed_variation_v28"
FIGURE_SCRIPTS = Path(r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
sys.path.insert(0, str(FIGURE_SCRIPTS))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


def main() -> None:
    data = pd.read_csv(DATA)
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "font.size": 7,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    colors = {1: "#285C92", 2: "#C17D35", 4: "#39816F"}
    offsets = {1: -0.18, 2: 0.0, 4: 0.18}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    for ax, (dataset, title) in zip(axes, [("abilene", "Abilene"), ("geant", "GÉANT")]):
        subset = data[data.dataset == dataset]
        for scale in [1, 2, 4]:
            rows = subset[subset.scale == scale].sort_values("seed")
            x = rows.seed.to_numpy() + offsets[scale]
            ax.errorbar(
                x,
                rows.adaptive_mean,
                yerr=rows.adaptive_within_seed_sd,
                fmt="o",
                ms=3.4,
                capsize=1.5,
                capthick=0.65,
                elinewidth=0.65,
                color=colors[scale],
                label=f"Scale {scale}",
            )
        ax.axhline(1 / 3, color="#777777", lw=0.8, ls="--", zorder=0)
        ax.set(xlim=(41.55, 49.45), ylim=(0, 0.8), xticks=range(42, 50), xlabel="Random seed")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.grid(axis="y", color="#E4E4E4", linewidth=0.5)
    axes[0].set_ylabel("Adaptive router weight")
    axes[1].legend(loc="upper right", ncol=3, fontsize=6.2, handlelength=1.2, columnspacing=0.7)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.18, top=0.88, wspace=0.16)
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
