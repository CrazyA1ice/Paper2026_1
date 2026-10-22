"""All-test absolute-error quantiles across the eight H=24 seeds."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = HERE.parent / "paper_figures" / "forecast_truth_previews"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CN = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
MODELS = (("DLinear", "dlinear", "#4F81BD"),
          ("固定等权", "dlinear_scale_static", "#D9782D"),
          ("本文方法", "dlinear_scale", "#23838C"))
PERCENTILES = [50, 75, 90, 95, 99]


def compute():
    rows = []
    for dataset, _ in DATASETS:
        for seed in range(42, 50):
            truth_ref = None
            for label, directory, _ in MODELS:
                path = RESULTS / dataset / f"{directory}_seed{seed}" / "predictions.npz"
                with np.load(path) as z:
                    truth = z["truth"]
                    if truth_ref is None:
                        truth_ref = truth
                    else:
                        assert np.array_equal(truth_ref, truth)
                    error = np.abs(z["prediction"] - truth).ravel()
                values = np.percentile(error, PERCENTILES)
                for percentile, value in zip(PERCENTILES, values):
                    rows.append((dataset, seed, label, percentile, value))
    source = pd.DataFrame(rows, columns=["dataset", "seed", "model",
                                         "percentile", "absolute_error"])
    source.to_csv(OUT / "absolute_error_quantiles_8seeds.csv", index=False)
    return source


def plot(source):
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.35))
    fig.subplots_adjust(left=.11, right=.985, bottom=.22, top=.88, wspace=.15)
    for ax, (dataset, name) in zip(axes, DATASETS):
        for label, _, color in MODELS:
            subset = source[(source.dataset == dataset) & (source.model == label)]
            grouped = subset.groupby("percentile").absolute_error
            center = grouped.mean().reindex(PERCENTILES).to_numpy()
            spread = grouped.std().reindex(PERCENTILES).to_numpy()
            x = np.arange(len(PERCENTILES))
            ax.fill_between(x, center-spread, center+spread,
                            color=color, alpha=.13, linewidth=0)
            ax.plot(x, center, color=color, lw=1.75, marker="o", ms=3.8,
                    label=label, zorder=3)
        ax.set_title(name, loc="left", fontfamily="Times New Roman",
                     fontweight="bold", fontsize=10, color="#203747")
        ax.set_xticks(range(len(PERCENTILES)), [f"P{q}" for q in PERCENTILES])
        ax.set_xlabel("绝对误差百分位", fontproperties=CN, fontsize=8)
        ax.grid(axis="y", color="#E7EAEC", lw=.6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors="#203747", labelsize=7)
        ax.set_ylim(bottom=0)
    axes[0].set_ylabel("绝对误差（标准化）", fontproperties=CN, fontsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .025),
               ncol=3, frameon=False, prop=CN, fontsize=7.6, handlelength=2.2)
    stem = OUT / "C_全测试点绝对误差分位"
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(f"{stem}.png", dpi=450, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(stem)


if __name__ == "__main__":
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 8, "pdf.fonttype": 42, "svg.fonttype": "none",
                         "axes.linewidth": .8})
    data = compute()
    print(data.groupby(["dataset", "model", "percentile"]).absolute_error.mean().unstack().round(4))
    plot(data)
