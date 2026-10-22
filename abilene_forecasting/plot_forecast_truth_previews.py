"""Truth-led examples and all-point calibration from H=24 saved predictions."""

from pathlib import Path
import json
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = HERE.parent / "paper_figures" / "forecast_truth_previews"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CN = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
MODELS = (("DLinear", "dlinear", "#4F81BD"),
          ("固定等权", "dlinear_scale_static", "#D9782D"),
          ("本文方法", "dlinear_scale", "#23838C"))
INK = "#203747"


def load_runs(dataset, seed=42):
    runs = {}
    for label, directory, _ in MODELS:
        with np.load(RESULTS / dataset / f"{directory}_seed{seed}" / "predictions.npz") as z:
            runs[label] = (z["prediction"], z["truth"])
    truth = runs["本文方法"][1]
    assert all(np.array_equal(pair[1], truth) for pair in runs.values())
    return runs, truth


def choose_truth_only(truth):
    # A moderately dynamic OD channel, then typical and high-variation windows.
    channel_sd = truth.std(axis=(0, 1))
    eligible = np.flatnonzero(channel_sd > 0)
    target = np.quantile(channel_sd[eligible], .75)
    channel = int(eligible[np.argmin(np.abs(channel_sd[eligible] - target))])
    variation = np.abs(np.diff(truth[:, :, channel], axis=1)).mean(axis=1)
    windows = [int(np.argmin(np.abs(variation - np.quantile(variation, q))))
               for q in (.5, .9)]
    return channel, windows, variation


def export(fig, stem):
    path = OUT / stem
    require_matplotlib_panel_alignment(fig, json_out=f"{path}.alignment.json",
                                       overlay_svg=f"{path}.alignment.svg",
                                       tolerance_pt=1.5, gutter_tolerance_pt=1.5,
                                       strict=True)
    fig.savefig(f"{path}.png", dpi=450, bbox_inches="tight")
    fig.savefig(f"{path}.pdf", bbox_inches="tight")
    fig.savefig(f"{path}.svg", bbox_inches="tight")
    fig.savefig(f"{path}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(path)


def trajectories():
    fig, axes = plt.subplots(2, 2, figsize=(7.15, 4.25))
    fig.subplots_adjust(left=.11, right=.985, bottom=.17, top=.88,
                        wspace=.17, hspace=.40)
    selection = []
    for col, (dataset, name) in enumerate(DATASETS):
        runs, truth = load_runs(dataset)
        channel, windows, variation = choose_truth_only(truth)
        for row, (window, quantile) in enumerate(zip(windows, (50, 90))):
            ax = axes[row, col]
            y = truth[window, :, channel]
            ax.plot(range(1, 25), y, color=INK, lw=2.15, label="真实值", zorder=5)
            values = {}
            for label, _, color in MODELS:
                pred = runs[label][0][window, :, channel]
                values[label] = float(np.mean((pred - y) ** 2))
                ax.plot(range(1, 25), pred, color=color, lw=1.25,
                        ls="-" if label == "本文方法" else (0, (3, 2)),
                        label=label, alpha=.96)
            ax.set_xlim(1, 24)
            ax.set_xticks([1, 6, 12, 18, 24])
            ax.grid(axis="y", color="#E8ECEE", lw=.6)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(colors=INK, labelsize=7)
            ax.set_title(f"{name}  ·  OD {channel+1}  ·  窗口 {window+1}",
                         loc="left", fontproperties=CN, fontsize=8.8, color=INK, pad=5)
            if col == 0:
                ax.set_ylabel("标准化流量", fontproperties=CN, fontsize=8)
            if row == 1:
                ax.set_xlabel("预测步", fontproperties=CN, fontsize=8)
            selection.append(dict(dataset=dataset, seed=42, channel_zero_based=channel,
                                  window_zero_based=window, truth_volatility_quantile=quantile,
                                  truth_volatility=float(variation[window]),
                                  mse=values))
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .02),
               ncol=4, frameon=False, prop=CN, fontsize=8,
               handlelength=2.4, columnspacing=1.5)
    (OUT / "trajectory_selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(selection, ensure_ascii=False, indent=2))
    export(fig, "A_真实与预测轨迹")


def calibration():
    rows = []
    for dataset, _ in DATASETS:
        for seed in range(42, 50):
            runs, truth = load_runs(dataset, seed)
            y = truth.ravel()
            # All test elements enter a common quantile-bin partition.
            edges = np.unique(np.quantile(y, np.linspace(0, 1, 41)))
            index = np.searchsorted(edges[1:-1], y, side="right")
            counts = np.bincount(index, minlength=len(edges)-1)
            assert counts.sum() == len(y) and np.all(counts > 0)
            true_mean = np.bincount(index, weights=y, minlength=len(counts)) / counts
            for label, _, _ in MODELS:
                pred = runs[label][0].ravel()
                predicted_mean = np.bincount(index, weights=pred,
                                             minlength=len(counts)) / counts
                squared_error = np.bincount(index, weights=(pred-y)**2,
                                            minlength=len(counts)) / counts
                absolute_error = np.bincount(index, weights=np.abs(pred-y),
                                             minlength=len(counts)) / counts
                for bin_index, (n, x, pred_y, mse, mae) in enumerate(
                    zip(counts, true_mean, predicted_mean, squared_error, absolute_error)
                ):
                    rows.append((dataset, seed, label, bin_index, n, x, pred_y, mse, mae))
    source = pd.DataFrame(rows, columns=["dataset", "seed", "model", "bin",
                                         "n_elements", "true_mean", "predicted_mean",
                                         "mse", "mae"])
    source.to_csv(OUT / "calibration_source_8seeds.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.40))
    fig.subplots_adjust(left=.10, right=.985, bottom=.22, top=.88, wspace=.15)
    for ax, (dataset, name) in zip(axes, DATASETS):
        subset = source[source.dataset == dataset]
        xmin, xmax = subset.true_mean.min(), subset.true_mean.max()
        ax.plot([xmin, xmax], [xmin, xmax], color=INK, lw=1.2,
                ls=(0, (3, 2)), label="理想预测")
        for label, _, color in MODELS:
            part = subset[subset.model == label]
            grouped = part.groupby("bin", sort=True)
            x = grouped.true_mean.mean().to_numpy()
            center = grouped.predicted_mean.mean().to_numpy()
            spread = grouped.predicted_mean.std().to_numpy()
            ax.fill_between(x, center-spread, center+spread,
                            color=color, alpha=.13, linewidth=0)
            ax.plot(x, center, color=color, lw=1.5, label=label)
        ax.set_title(name, loc="left", fontfamily="Times New Roman",
                     fontweight="bold", fontsize=10, color=INK)
        ax.set_xlabel("真实值（标准化）", fontproperties=CN, fontsize=8)
        ax.grid(color="#E8ECEE", lw=.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=INK, labelsize=7)
    axes[0].set_ylabel("预测均值（标准化）", fontproperties=CN, fontsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .025),
               ncol=4, frameon=False, prop=CN, fontsize=7.5,
               handlelength=2.2, columnspacing=1.4)
    export(fig, "B_全测试点预测校准_8种子")


if __name__ == "__main__":
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 8, "pdf.fonttype": 42, "svg.fonttype": "none",
                         "axes.linewidth": .8})
    trajectories()
    calibration()
