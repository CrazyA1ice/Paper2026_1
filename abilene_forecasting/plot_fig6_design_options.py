"""Three publication-size design previews for the router-weight figure."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "global_weight_ablation" / "analysis" / "within_seed_weights.csv"
OUTPUT = ROOT.parent / "paper_figures" / "fig6_options"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


INK = "#253344"
MUTED = "#637383"
GRID = "#E3E9ED"
COLORS = {1: "#246B96", 2: "#C2854A", 4: "#43867C"}
NAMES = {"abilene": "Abilene", "geant": "GÉANT"}
SCALES = (1, 2, 4)
SEEDS = np.arange(42, 50)


def prepare():
    data = pd.read_csv(SOURCE)
    assert len(data) == 48
    assert not data.isna().any().any()
    for dataset in NAMES:
        sub = data[data.dataset == dataset]
        assert set(sub.seed) == set(SEEDS)
        assert set(sub.scale) == set(SCALES)
        assert len(sub) == 24
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#AAB6BF",
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
    })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    return data


def save(fig, name):
    path = OUTPUT / name
    require_matplotlib_panel_alignment(
        fig,
        json_out=f"{path}.alignment.json",
        overlay_svg=f"{path}.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(f"{path}.pdf")
    fig.savefig(f"{path}.svg")
    fig.savefig(f"{path}.png", dpi=500)
    plt.close(fig)


def rows(data, dataset, scale):
    return data[(data.dataset == dataset) & (data.scale == scale)].sort_values("seed")


def option_a(data):
    """Horizontal interval ledger: precise comparison within each seed."""
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.6), sharex=True, sharey=True)
    offsets = {1: -0.20, 2: 0, 4: 0.20}
    for ax, dataset in zip(axes, NAMES):
        ax.axvspan(0.325, 0.342, color="#F0F2F3", zorder=0)
        ax.axvline(1 / 3, color="#A0AAB0", lw=0.7, zorder=0)
        for i in range(8):
            if i % 2 == 0:
                ax.axhspan(i - 0.48, i + 0.48, color="#F7F9FA", zorder=-1)
        for scale in SCALES:
            part = rows(data, dataset, scale)
            y = np.arange(8) + offsets[scale]
            mean = part.adaptive_mean.to_numpy()
            sd = part.adaptive_within_seed_sd.to_numpy()
            lo = np.minimum(sd, mean)
            hi = np.minimum(sd, 1 - mean)
            ax.errorbar(mean, y, xerr=np.vstack([lo, hi]), fmt="o", ms=3.4,
                        capsize=1.4, capthick=0.65, elinewidth=0.8,
                        color=COLORS[scale], label=f"Scale {scale}", zorder=3)
        ax.set(xlim=(0, 0.8), ylim=(-0.5, 7.5), yticks=range(8),
               yticklabels=SEEDS, xlabel="Adaptive weight")
        ax.invert_yaxis()
        ax.set_title(NAMES[dataset], loc="left", fontsize=9, fontweight="bold", pad=10)
        ax.tick_params(axis="both", length=0)
        ax.grid(axis="x", color=GRID, lw=0.5)
    axes[0].set_ylabel("Random seed")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.52, 0.995),
               ncol=3, frameon=False, handletextpad=0.4, columnspacing=1.6)
    fig.text(0.5, 0.035, "Point = seed mean    |    whisker = within-seed SD    |    pale line = equal weight (1/3)",
             ha="center", fontsize=6.3, color=MUTED)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.17, top=0.86, wspace=0.12)
    save(fig, "option_A_interval_ledger")


def option_b(data):
    """Two-layer heatmap: separate the mean and the within-seed variation."""
    fig, axes = plt.subplots(2, 2, figsize=(6.8, 3.9), sharex=True)
    mean_cmap = LinearSegmentedColormap.from_list(
        "weight", ["#E8F2F4", "#9CBCC9", "#346E91", "#203D5B"])
    sd_cmap = LinearSegmentedColormap.from_list(
        "variation", ["#F0F5F4", "#A3C9C1", "#4A907F", "#27685E"])
    for col, dataset in enumerate(NAMES):
        sub = data[data.dataset == dataset]
        mean = sub.pivot(index="scale", columns="seed", values="adaptive_mean").loc[list(SCALES), SEEDS].to_numpy()
        sd = sub.pivot(index="scale", columns="seed", values="adaptive_within_seed_sd").loc[list(SCALES), SEEDS].to_numpy()
        for row, (matrix, cmap, vmax) in enumerate([(mean, mean_cmap, 0.75), (sd, sd_cmap, 0.15)]):
            ax = axes[row, col]
            ax.imshow(matrix, cmap=cmap, vmin=0, vmax=vmax, aspect="auto", interpolation="none")
            ax.set_yticks(range(3), ["Scale 1", "Scale 2", "Scale 4"])
            ax.set_xticks(range(8), SEEDS)
            ax.tick_params(length=0, pad=3)
            ax.set_xticks(np.arange(-0.5, 8, 1), minor=True)
            ax.set_yticks(np.arange(-0.5, 3, 1), minor=True)
            ax.grid(which="minor", color="white", linewidth=1.5)
            ax.tick_params(which="minor", bottom=False, left=False)
            for spine in ax.spines.values():
                spine.set_visible(False)
            if row == 0:
                ax.set_title(NAMES[dataset], loc="left", fontsize=9, fontweight="bold", pad=10)
                for i in range(3):
                    for j in range(8):
                        value = mean[i, j]
                        ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                                fontsize=6.5, color="white" if value > 0.48 else INK)
            else:
                ax.set_xlabel("Random seed")
        if col == 0:
            axes[0, col].set_ylabel("Mean adaptive weight", fontsize=7)
            axes[1, col].set_ylabel("Within-seed SD", fontsize=7)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.11, top=0.88, wspace=0.17, hspace=0.42)
    gradient = np.linspace(0, 1, 256)[None, :]
    for bottom, cmap, end in [(0.92, mean_cmap, "0.75"), (0.505, sd_cmap, "0.15")]:
        bar = fig.add_axes([0.78, bottom, 0.15, 0.014])
        bar.imshow(gradient, cmap=cmap, aspect="auto", interpolation="none")
        bar.set_yticks([])
        bar.set_xticks([0, 255], ["0", end], fontsize=6.5)
        bar.tick_params(axis="x", length=0, pad=2)
        for spine in bar.spines.values():
            spine.set_visible(False)
    save(fig, "option_B_two_layer_heatmap")


def option_c(data):
    """Scale facets: the cleanest direct reading of weight variability."""
    fig, axes = plt.subplots(3, 2, figsize=(6.8, 4.35), sharex=True, sharey=True)
    for row, scale in enumerate(SCALES):
        for col, dataset in enumerate(NAMES):
            ax = axes[row, col]
            part = rows(data, dataset, scale)
            mean = part.adaptive_mean.to_numpy()
            sd = part.adaptive_within_seed_sd.to_numpy()
            lo = np.minimum(sd, mean)
            hi = np.minimum(sd, 1 - mean)
            ax.axhline(1 / 3, color="#9DAAB1", lw=0.75, ls=(0, (3, 3)), zorder=0)
            ax.errorbar(SEEDS, mean, yerr=np.vstack([lo, hi]), fmt="o", ms=4,
                        capsize=1.8, capthick=0.7, elinewidth=0.9,
                        color=COLORS[scale], zorder=3)
            ax.set(xlim=(41.5, 49.5), ylim=(0, 0.8), xticks=SEEDS)
            ax.grid(axis="y", color=GRID, lw=0.55)
            ax.tick_params(length=0, pad=3)
            if row == 0:
                ax.set_title(NAMES[dataset], loc="left", fontsize=9, fontweight="bold", pad=8)
            if col == 0:
                ax.set_ylabel(f"Scale {scale}\nweight", color=COLORS[scale])
            if row == 2:
                ax.set_xlabel("Random seed")
    fig.text(0.5, 0.02, "Dots = seed means; whiskers = within-seed SD; dashed line = 1/3",
             ha="center", fontsize=6.3, color=MUTED)
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.13, top=0.92, wspace=0.13, hspace=0.34)
    save(fig, "option_C_scale_facets")


if __name__ == "__main__":
    table = prepare()
    option_a(table)
    option_b(table)
    option_c(table)
