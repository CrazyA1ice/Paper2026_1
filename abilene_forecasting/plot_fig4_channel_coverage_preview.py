"""Preview OD-channel coverage against DLinear and equal fusion at H=24."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "paper_figures" / "fig4_channel_coverage_preview"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


BLUE = "#4F81BD"
ORANGE = "#D9782D"
COLORS = {"DLinear": BLUE, "固定等权": ORANGE}
FOLDERS = {"DLinear": "dlinear_seed", "固定等权": "dlinear_scale_static_seed"}
LEGEND = {"DLinear": "本文方法优于DLinear", "固定等权": "本文方法优于固定等权"}
DATASETS = (("abilene", "Abilene", 144), ("geant", "GÉANT", 524))
CHINESE_FONT = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")


def collect():
    rows = []
    for dataset, _, n_channels in DATASETS:
        for seed in range(42, 50):
            router_file = ROOT / "results" / dataset / f"dlinear_scale_seed{seed}" / "predictions.npz"
            with np.load(router_file) as saved:
                router_pred = saved["prediction"]
                truth = saved["truth"]
            assert router_pred.shape == truth.shape and router_pred.shape[1:] == (24, n_channels)
            router_mse = ((router_pred - truth) ** 2).mean(axis=(0, 1))
            for baseline, folder in FOLDERS.items():
                filename = ROOT / "results" / dataset / f"{folder}{seed}" / "predictions.npz"
                with np.load(filename) as saved:
                    assert np.allclose(saved["truth"], truth)
                    baseline_mse = ((saved["prediction"] - truth) ** 2).mean(axis=(0, 1))
                assert len(baseline_mse) == n_channels
                for channel in range(n_channels):
                    rows.append((dataset, seed, baseline, channel,
                                 float(baseline_mse[channel]), float(router_mse[channel]),
                                 int(router_mse[channel] < baseline_mse[channel])))
    data = pd.DataFrame(rows, columns=["dataset", "seed", "baseline", "channel",
                                        "baseline_mse", "router_mse", "router_better"])
    assert len(data) == 2 * 8 * (144 + 524)
    return data


def draw(data):
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
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 3.78))
    fig.subplots_adjust(left=.09, right=.99, bottom=.14, top=.84,
                        wspace=.16, hspace=.55)
    fig.legend(
        handles=[plt.Line2D([0], [0], marker="s", linestyle="none", color=color,
                            markerfacecolor=color, markersize=5, label=LEGEND[name])
                 for name, color in COLORS.items()],
        loc="upper center", bbox_to_anchor=(.5, .985), ncol=2, frameon=False,
        prop=CHINESE_FONT, fontsize=7,
    )

    for col, (dataset, title, n_channels) in enumerate(DATASETS):
        sub = data[data.dataset == dataset]
        upper = axes[0, col]
        lower = axes[1, col]
        upper.axvspan(4.5, 8.5, facecolor="#F4F7F9", zorder=0)
        upper.axvline(4.5, color="#9D9D9D", lw=.65, ls="--", dashes=(3, 3), zorder=1)
        lower.axvspan(50, 100, facecolor="#F4F7F9", zorder=0)
        lower.axvline(50, color="#9D9D9D", lw=.65, ls="--", dashes=(3, 3), zorder=1)

        counts = {}
        for index, baseline in enumerate(COLORS):
            part = sub[sub.baseline == baseline]
            wins = part.groupby("channel").router_better.sum()
            assert len(wins) == n_channels and part.seed.nunique() == 8
            counts[baseline] = int((wins >= 5).sum())
            k = np.arange(9)
            coverage = np.array([(wins >= threshold).mean() * 100 for threshold in k])
            upper.step(k, coverage, where="mid", color=COLORS[baseline],
                       lw=1.45, zorder=2)
            upper.scatter(k, coverage, s=17, color=COLORS[baseline], zorder=3)

            by_seed = part.groupby("seed").router_better.mean().mul(100).sort_index()
            y = np.arange(8) + (-.14 if index == 0 else .14)
            lower.scatter(by_seed.to_numpy(), y, s=25, marker="o", color=COLORS[baseline],
                          edgecolor="white", linewidth=.5, zorder=3)
            for yi, value in zip(y, by_seed):
                lower.plot([50, value], [yi, yi], color=COLORS[baseline], lw=.7,
                           alpha=.70, zorder=2)

        upper.set_title(f"{'ab'[col]}  {title}", loc="left", pad=8,
                        fontfamily="Times New Roman", fontweight="bold", fontsize=9)
        upper.text(.98, 1.06,
                   f"≥5种子: {counts['DLinear']}/{n_channels} · {counts['固定等权']}/{n_channels}",
                   transform=upper.transAxes, ha="right", va="bottom", fontsize=6.4,
                   fontproperties=CHINESE_FONT)
        upper.set_xlim(-.6, 8.6)
        upper.set_ylim(0, 105)
        upper.set_yticks([0, 25, 50, 75, 100])
        upper.set_xticks(range(9))
        upper.set_xlabel("本文方法MSE更低的随机种子数", fontproperties=CHINESE_FONT)
        upper.grid(axis="y", color="#dddddd", lw=.5, ls="--", alpha=.7, zorder=0)
        if col == 0:
            upper.set_ylabel("满足条件的OD通道占比（%）", fontproperties=CHINESE_FONT)

        lower.set_xlim(0, 103)
        lower.set_xticks([0, 25, 50, 75, 100])
        lower.set_yticks(range(8), [str(seed) for seed in range(42, 50)])
        lower.invert_yaxis()
        lower.set_xlabel("每个种子中本文方法MSE更低的通道占比（%）", fontproperties=CHINESE_FONT)
        lower.grid(axis="x", color="#dddddd", lw=.5, ls="--", alpha=.7, zorder=0)
        if col == 0:
            lower.set_ylabel("随机种子", fontproperties=CHINESE_FONT)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "fig4_channel_coverage_preview"
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)
    return stem


def main():
    data = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT / "fig4_channel_coverage_source.csv", index=False)
    print(draw(data))


if __name__ == "__main__":
    main()
