"""Preview truth-volatility strata and Parseval-consistent error bands (H=24)."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "paper_figures/fig4_novel_audit"
OUT = ROOT / "paper_figures/conditional_error_previews"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CN = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
BASELINES = (("DLinear", "DLinear", "#4F81BD"),
             ("FixedEqual", "固定等权", "#D9782D"))
INK = "#203747"
TEAL = "#23838C"


def polish(ax, *, ylabel, title):
    ax.set_title(title, loc="left", fontproperties=CN, fontsize=9.2,
                 color=INK, pad=8)
    ax.set_ylabel(ylabel, fontproperties=CN, fontsize=7.8)
    ax.axhline(0, color=INK, lw=.9, zorder=1)
    ax.grid(axis="y", color="#E7EAEC", lw=.55, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=INK, labelsize=7, length=2)


def export(fig, stem):
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json",
        overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.png", dpi=450, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def plot_volatility():
    source = pd.read_csv(SOURCE / "candidate_metrics.csv")
    source = source[source.slice.str.startswith("target_vol_Q")].copy()
    assert len(source) == 2 * 8 * 2 * 4
    source["quartile"] = source.slice.str[-1].astype(int)
    assert set(source.seed) == set(range(42, 50))
    source.to_csv(OUT / "volatility_strata_source_8seeds.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.45))
    fig.subplots_adjust(left=.105, right=.985, top=.85, bottom=.22, wspace=.19)
    for ax, (dataset, name), letter in zip(axes, DATASETS, "ab"):
        part = source[source.dataset == dataset]
        for baseline, display, color in BASELINES:
            block = part[part.baseline == baseline]
            x = np.arange(1, 5) + (-.105 if baseline == "DLinear" else .105)
            for q, xpos in zip(range(1, 5), x):
                y = block[block.quartile == q].sort_values("seed").improvement.to_numpy()
                ax.scatter(np.full(len(y), xpos), y, color=color, s=10,
                           alpha=.35, zorder=3, edgecolors="none")
            center = block.groupby("quartile").improvement.mean().reindex(range(1, 5)).to_numpy()
            ax.plot(x, center, color=color, lw=1.3, marker="D", ms=4,
                    mec="white", mew=.55, zorder=5, label=display)
        ax.set_xlim(.65, 4.35)
        ax.set_xticks(range(1, 5), ["低 Q1", "Q2", "Q3", "高 Q4"], fontproperties=CN)
        ax.set_xlabel("真实流量波动四分位", fontproperties=CN, fontsize=7.8)
        polish(ax, ylabel="MSE 降低率（%）" if ax is axes[0] else "",
               title=f"{letter}  {name}")
    fig.text(.985, .955, "细点：各随机种子  ·  菱形：8种子均值",
             ha="right", va="top", fontproperties=CN, fontsize=7,
             color="#607684")
    handles = [Line2D([0], [0], color=color, marker="D", lw=1.3,
                      ms=4, label=f"相对{display}")
               for _, display, color in BASELINES]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(.5, .035), prop=CN, fontsize=7.5)
    stem = OUT / "A_真实波动分层预测误差"
    export(fig, stem)
    return stem


def plot_spectral():
    source = pd.read_csv(SOURCE / "spectral_metrics.csv")
    assert len(source) == 2 * 8 * 2 * 3
    assert set(source.seed) == set(range(42, 50))
    total = source.groupby(["dataset", "seed", "baseline"]).baseline_energy.transform("sum")
    source["contribution_pp"] = 100 * (source.baseline_energy - source.proposed_energy) / total
    all_rows = source.groupby(["dataset", "seed", "baseline"], as_index=False).agg(
        contribution_pp=("contribution_pp", "sum"))
    all_rows["band"] = "total"
    source = pd.concat([source, all_rows], ignore_index=True)
    source.to_csv(OUT / "spectral_contribution_source_8seeds.csv", index=False)
    order = ["low_k0_2", "mid_k3_6", "high_k7_12", "total"]
    labels = ["偏置与慢变\n(DC, 12–24 h)", "中频\n(4–8 h)",
              "高频\n(2–3.4 h)", "总计"]

    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.45))
    fig.subplots_adjust(left=.105, right=.985, top=.85, bottom=.22, wspace=.19)
    for ax, (dataset, name), letter in zip(axes, DATASETS, "ab"):
        part = source[source.dataset == dataset]
        for baseline, display, color in BASELINES:
            block = part[part.baseline == baseline]
            x = np.arange(4) + (-.18 if baseline == "DLinear" else .18)
            mean = block.groupby("band").contribution_pp.mean().reindex(order).to_numpy()
            sd = block.groupby("band").contribution_pp.std().reindex(order).to_numpy()
            ax.bar(x, mean, width=.30, color=color, alpha=.82, zorder=3,
                   label=f"相对{display}")
            ax.errorbar(x, mean, yerr=sd, fmt="none", ecolor=INK,
                        elinewidth=.7, capsize=2, zorder=5)
        ax.set_xticks(range(4), labels, fontproperties=CN, fontsize=6.7)
        ax.axvline(2.5, color="#BBC7CC", lw=.8, ls=(0, (2, 2)))
        polish(ax, ylabel="对总 MSE 降低率的贡献（百分点）" if ax is axes[0] else "",
               title=f"{letter}  {name}")
    fig.text(.985, .955, "柱：8种子均值  ·  误差线：±1 SD",
             ha="right", va="top", fontproperties=CN, fontsize=7,
             color="#607684")
    handles = [Line2D([0], [0], color=color, lw=5, label=f"相对{display}")
               for _, display, color in BASELINES]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(.5, .035), prop=CN, fontsize=7.5)
    stem = OUT / "B_预测误差时间频段分解"
    export(fig, stem)
    return stem


if __name__ == "__main__":
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.linewidth": .8,
    })
    print(plot_volatility())
    print(plot_spectral())
