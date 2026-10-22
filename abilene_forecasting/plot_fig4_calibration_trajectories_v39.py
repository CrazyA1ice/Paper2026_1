"""Figure 4 with the constant-input router control and softer truth curves."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from plot_forecast_truth_previews import load_runs, choose_truth_only, MODELS as ORIGINAL_MODELS


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "paper_figures/forecast_truth_previews/calibration_source_8seeds.csv"
OUT = ROOT / "paper_figures/fig4_calibration_trajectories_v39"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CN = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
INK = "#203747"
TRUTH = "#586773"
IDEAL = "#8998A2"
CONSTANT = ("恒定输入路由", "dlinear_scale_constant_router", "#806A9B")
MODELS = ORIGINAL_MODELS[:2] + (CONSTANT,) + ORIGINAL_MODELS[2:]


def line_style(label):
    if label == "本文方法":
        return "-"
    if label == CONSTANT[0]:
        return (0, (4, 1.5, 1, 1.5))
    return (0, (3, 2))


def constant_prediction(dataset, seed, truth):
    path = (ROOT / "abilene_forecasting/results/constant_router_ablation" /
            dataset / f"{CONSTANT[1]}_seed{seed}" / "predictions.npz")
    with np.load(path) as data:
        assert np.array_equal(data["truth"], truth)
        return data["prediction"].copy()


def add_constant_calibration(source):
    rows = []
    for dataset, _ in DATASETS:
        for seed in range(42, 50):
            _, truth = load_runs(dataset, seed)
            prediction = constant_prediction(dataset, seed, truth)
            y = truth.ravel()
            edges = np.unique(np.quantile(y, np.linspace(0, 1, 41)))
            index = np.searchsorted(edges[1:-1], y, side="right")
            counts = np.bincount(index, minlength=len(edges)-1)
            true_mean = np.bincount(index, weights=y, minlength=len(counts)) / counts
            original = source[(source.dataset == dataset) &
                              (source.seed == seed) &
                              (source.model == "本文方法")].sort_values("bin")
            assert np.array_equal(counts, original.n_elements.to_numpy())
            assert np.allclose(true_mean, original.true_mean.to_numpy(), atol=1e-7)
            pred = prediction.ravel()
            predicted_mean = np.bincount(index, weights=pred, minlength=len(counts)) / counts
            mse = np.bincount(index, weights=(pred-y)**2, minlength=len(counts)) / counts
            mae = np.bincount(index, weights=np.abs(pred-y), minlength=len(counts)) / counts
            for bin_index, (n, x, value, squared, absolute) in enumerate(
                zip(counts, true_mean, predicted_mean, mse, mae)
            ):
                rows.append((dataset, seed, CONSTANT[0], bin_index, n, x,
                             value, squared, absolute))
    combined = pd.concat([source, pd.DataFrame(rows, columns=source.columns)],
                         ignore_index=True)
    combined.to_csv(OUT / "calibration_source_8seeds_v39.csv", index=False)
    return combined


def main():
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.linewidth": .8,
    })
    source = add_constant_calibration(pd.read_csv(SOURCE))
    assert source.seed.nunique() == 8
    fig = plt.figure(figsize=(7.15, 5.15))
    grid = fig.add_gridspec(3, 2, height_ratios=[1.55, 1, 1],
                            left=.105, right=.985, bottom=.16, top=.95,
                            wspace=.18, hspace=.58)
    axes = np.array([[fig.add_subplot(grid[row, col]) for col in range(2)]
                     for row in range(3)])

    for col, (dataset, name) in enumerate(DATASETS):
        ax = axes[0, col]
        part = source[source.dataset == dataset]
        x_min, x_max = part.true_mean.min(), part.true_mean.max()
        ax.plot([x_min, x_max], [x_min, x_max], color=IDEAL,
                ls=(0, (3, 2)), lw=.95, zorder=1)
        for label, _, color in MODELS:
            group = part[part.model == label].groupby("bin", sort=True)
            x = group.true_mean.mean().to_numpy()
            mid = group.predicted_mean.mean().to_numpy()
            sd = group.predicted_mean.std().to_numpy()
            ax.fill_between(x, mid-sd, mid+sd, color=color, alpha=.11, lw=0)
            ax.plot(x, mid, color=color, lw=1.45 if label == "本文方法" else 1.15,
                    ls=line_style(label), zorder=3)
        ax.set_title(f"{'ab'[col]}  {name}  ·  全测试点校准", loc="left",
                     fontproperties=CN, fontsize=8.5, color=INK, pad=5)
        ax.set_xlabel("真实值（标准化）", fontproperties=CN, fontsize=7.5)
        if col == 0:
            ax.set_ylabel("预测均值（标准化）", fontproperties=CN, fontsize=7.5)
        ax.grid(color="#E7EAEC", lw=.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=INK, labelsize=6.6, length=2)

        runs, truth = load_runs(dataset, seed=42)
        runs[CONSTANT[0]] = (constant_prediction(dataset, 42, truth), truth)
        channel, windows, _ = choose_truth_only(truth)
        for row, (window, level) in enumerate(zip(windows, ("典型波动", "较高波动")), start=1):
            ax = axes[row, col]
            y = truth[window, :, channel]
            ax.plot(np.arange(1, 25), y, color=TRUTH, lw=1.25, zorder=5)
            for label, _, color in MODELS:
                ax.plot(np.arange(1, 25), runs[label][0][window, :, channel],
                        color=color, lw=1.35 if label == "本文方法" else 1.0,
                        ls=line_style(label),
                        alpha=.97, zorder=3)
            ax.set_title(f"{'cdef'[(row-1)*2+col]}  {level}  ·  OD {channel+1}  ·  窗口 {window+1}",
                         loc="left", fontproperties=CN, fontsize=7.7, color=INK, pad=4)
            ax.set_xlim(1, 24)
            ax.set_xticks([1, 6, 12, 18, 24])
            if row == 2:
                ax.set_xlabel("预测步", fontproperties=CN, fontsize=7.5)
            if col == 0:
                ax.set_ylabel("标准化流量", fontproperties=CN, fontsize=7.5)
            ax.grid(axis="y", color="#E7EAEC", lw=.5)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(colors=INK, labelsize=6.6, length=2)

    legend = [Line2D([0], [0], color=TRUTH, lw=1.25, label="真实值"),
              Line2D([0], [0], color=IDEAL, lw=.95, ls=(0, (3, 2)), label="理想线")]
    legend += [Line2D([0], [0], color=color, lw=1.45,
                      ls=line_style(label), label=label)
               for label, _, color in MODELS]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(.5, .02),
               ncol=6, frameon=False, prop=CN, fontsize=7.1,
               handlelength=1.6, columnspacing=.75)
    stem = OUT / "fig4_calibration_plus_constant_router"
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.png", dpi=450, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(stem)


if __name__ == "__main__":
    main()
