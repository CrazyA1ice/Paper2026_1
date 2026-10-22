"""Plot channel coverage and forecast-step effects for the H=24 comparison."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "abilene_forecasting/results/global_weight_ablation/analysis"
OUT = ROOT / "paper_figures/fig4_channel_horizon_v35"
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment


def main():
    channels = pd.read_csv(DATA / "channel_paired_errors.csv")
    leads = pd.read_csv(DATA / "horizon_paired_errors.csv")
    assert channels.groupby("dataset").size().to_dict() == {"abilene": 1152, "geant": 4192}
    assert leads.groupby("dataset").size().to_dict() == {"abilene": 192, "geant": 192}

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#88949D",
        "xtick.color": "#384654",
        "ytick.color": "#384654",
        "text.color": "#172C3C",
        "axes.labelcolor": "#172C3C",
    })
    teal = "#287F88"
    coral = "#C47C68"
    neutral = "#AAB6BC"
    dark = "#19394B"
    fig, axes = plt.subplots(2, 2, figsize=(6.45, 3.82))
    fig.subplots_adjust(left=0.095, right=0.985, bottom=0.115, top=0.87,
                        wspace=0.24, hspace=0.58)

    for col, (dataset, title, n_channels) in enumerate([
        ("abilene", "a  Abilene", 144),
        ("geant", "b  GÉANT", 524),
    ]):
        channel_data = channels[channels.dataset == dataset]
        lead_data = leads[leads.dataset == dataset]
        counts = channel_data.assign(win=channel_data.difference > 0).groupby("channel").win.sum()
        frequencies = counts.value_counts().reindex(range(9), fill_value=0).to_numpy()
        assert frequencies.sum() == n_channels
        majority = int((counts >= 5).sum())

        top = axes[0, col]
        x = np.arange(9)
        colors = [coral if i < 4 else neutral if i == 4 else teal for i in x]
        top.bar(x, frequencies / n_channels * 100, color=colors, width=0.72)
        top.axvline(4.5, color="#B4BDC3", lw=0.7, ls=(0, (3, 2)))
        top.set_xticks(x)
        top.set_ylim(0, 34)
        top.set_yticks([0, 10, 20, 30])
        top.set_title(title, loc="left", weight="bold", fontsize=9, pad=6)
        top.text(0.98, 1.06, f"{majority}/{n_channels} 通道 ≥5/8 种子改善",
                 transform=top.transAxes, ha="right", va="bottom", fontsize=6.7, color=teal)
        top.set_xlabel("MSE较低的随机种子数（共8个）", labelpad=3)
        top.grid(axis="y", color="#E4E9EB", lw=0.6)
        top.set_axisbelow(True)
        if col == 0:
            top.set_ylabel("OD通道占比（%）")

        bottom = axes[1, col]
        pivot = lead_data.pivot(index="horizon", columns="seed", values="reduction_pct")
        assert list(pivot.index) == list(range(1, 25))
        for seed in pivot.columns:
            bottom.plot(pivot.index, pivot[seed], color="#AFBBC0", alpha=0.60,
                        lw=0.65, zorder=1)
        mean = pivot.mean(axis=1)
        bottom.plot(pivot.index, mean, color=dark, lw=1.9, zorder=3)
        bottom.axhline(0, color=coral, lw=0.9, ls=(0, (4, 2)), zorder=2)
        bottom.set_xlim(1, 24)
        bottom.set_xticks([1, 6, 12, 18, 24])
        bottom.set_ylim((-52, 62) if dataset == "abilene" else (-32, 25))
        bottom.set_xlabel("预测步位置", labelpad=3)
        bottom.grid(axis="y", color="#E4E9EB", lw=0.6)
        bottom.set_axisbelow(True)
        if col == 0:
            bottom.set_ylabel("相对全局权重模型的MSE降低率（%）")
        bottom.text(0.02, 0.96, "深线：8种子均值 · 浅线：各随机种子",
                    transform=bottom.transAxes, ha="left", va="top", fontsize=6,
                    color="#526471")

    require_matplotlib_panel_alignment(
        fig, json_out=str(OUT) + ".alignment.json",
        overlay_svg=str(OUT) + ".alignment.svg", strict=True,
        tolerance_pt=1.5, gutter_tolerance_pt=1.5,
    )
    fig.savefig(str(OUT) + ".png", dpi=450)
    fig.savefig(str(OUT) + ".pdf")
    fig.savefig(str(OUT) + ".svg")
    fig.savefig(str(OUT) + ".tiff", dpi=600)
    plt.close(fig)
    print(OUT)


if __name__ == "__main__":
    main()
