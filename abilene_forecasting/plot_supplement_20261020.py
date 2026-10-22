"""Plot every completed history condition; uncertainty is across training seeds."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/supplement_20261020"
QA = ROOT.parent / "review_scratch/supplement_20261020"
sys.path.insert(0, str(Path(r"C:\Users\Quant\.codex\skills\nature-figure\scripts")))
from audit_panel_alignment import require_matplotlib_panel_alignment


def main():
    data = pd.read_csv(OUT / "learning_curve_summary.csv")
    assert len(data) == 24
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 8.5,
        "axes.labelsize": 8.5, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "axes.linewidth": .65,
        "xtick.major.width": .65, "ytick.major.width": .65,
    })
    fig, axes = plt.subplots(1, 2, figsize=(7.08661417, 3.07086614))  # 180 x 78 mm
    fig.subplots_adjust(left=.085, right=.985, bottom=.19, top=.79, wspace=.30)
    styles = [
        ("dlinear", "DLinear", "#60646C", "o", "-"),
        ("dlinear_scale_global", "Global weights", "#C47B33", "s", "--"),
        ("dlinear_scale", "Proposed routing", "#147D87", "^", "-"),
    ]
    for axis, dataset, label, title in zip(
        axes, ["abilene", "geant"], ["a", "b"],
        ["Abilene (144 OD variables)", "GÉANT (524 OD variables)"]
    ):
        for model, legend, color, marker, linestyle in styles:
            rows = data[(data.dataset == dataset) & (data.model == model)].sort_values("train_percent")
            assert rows.train_percent.tolist() == [25, 50, 75, 100]
            axis.errorbar(rows.train_percent, rows.mse_mean, yerr=rows.mse_sd,
                          label=legend, color=color, marker=marker, linestyle=linestyle,
                          linewidth=1.15, markersize=4, capsize=2, capthick=.8,
                          elinewidth=.8, markeredgewidth=.7)
        axis.set(xlim=(20, 105), ylim=(0, None), xticks=[25, 50, 75, 100],
                 xlabel="Retained training history (%)", ylabel="Reference-space test MSE")
        axis.set_title(title, pad=10)
        axis.text(-.14, 1.065, label, transform=axis.transAxes,
                  fontsize=10, fontweight="bold", va="bottom")
        axis.grid(axis="y", color="#D9DDE0", linewidth=.45, zorder=0)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(direction="out", length=3)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.52, 1.0),
               ncol=3, frameon=False, handlelength=2.2, columnspacing=2.0)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig, json_out=QA / "figure6_alignment.json",
        overlay_svg=QA / "figure6_alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
    fig.savefig(OUT / "figure6_training_history.pdf", dpi=600,
                facecolor="white", metadata={"Creator": "Matplotlib"})
    fig.savefig(OUT / "figure6_training_history.svg", dpi=600, facecolor="white")
    fig.savefig(OUT / "figure6_training_history.png", dpi=600, facecolor="white")
    plt.close(fig)
    print("Figure 6 exported from all 24 summary rows")


if __name__ == "__main__":
    main()
