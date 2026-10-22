"""Three H=24, paired-window Figure 4 previews from saved predictions."""

from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = HERE.parent / "paper_figures" / "fig4_window_previews"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

CN = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
DATASETS = (("abilene", "Abilene"), ("geant", "GÉANT"))
BASELINES = (("DLinear", "dlinear"), ("固定等权", "dlinear_scale_static"))
MODEL = "dlinear_scale"
BLUE = "#4F81BD"
ORANGE = "#D9782D"
TEAL = "#2A8793"
TERRA = "#C77762"
INK = "#203747"


def source_data():
    csv_path = OUT / "window_level_source.csv"
    blocks = []
    for dataset, _ in DATASETS:
        for seed in range(42, 50):
            runs = {}
            for label, directory in (*BASELINES, ("本文方法", MODEL)):
                path = RESULTS / dataset / f"{directory}_seed{seed}" / "predictions.npz"
                with np.load(path) as arrays:
                    prediction = arrays["prediction"]
                    truth = arrays["truth"]
                runs[label] = (prediction, truth)
            truth = runs["本文方法"][1]
            assert all(np.array_equal(truth, pair[1]) for pair in runs.values())
            proposed = ((runs["本文方法"][0] - truth) ** 2).mean(axis=(1, 2))
            for baseline, _ in BASELINES:
                base = ((runs[baseline][0] - truth) ** 2).mean(axis=(1, 2))
                if np.any(base <= 0) or np.any(proposed <= 0):
                    raise ValueError("Window MSE must be positive before taking the ratio")
                score = np.log2(base / proposed)
                blocks.append(pd.DataFrame({
                    "dataset": dataset, "seed": seed, "baseline": baseline,
                    "window": np.arange(1, len(base) + 1), "baseline_mse": base,
                    "proposed_mse": proposed, "log2_mse_ratio": score,
                    "proposed_better": proposed < base,
                }))
    frame = pd.concat(blocks, ignore_index=True)
    frame.to_csv(csv_path, index=False)
    return frame


def panel_array(frame, dataset, baseline, field):
    part = frame[(frame.dataset == dataset) & (frame.baseline == baseline)]
    rows = []
    for seed in range(42, 50):
        row = part[part.seed == seed].sort_values("window")[field].to_numpy()
        rows.append(row)
    values = np.stack(rows)
    assert np.isfinite(values).all()
    return values


def export(fig, name):
    stem = OUT / name
    require_matplotlib_panel_alignment(
        fig, json_out=f"{stem}.alignment.json", overlay_svg=f"{stem}.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    fig.savefig(f"{stem}.png", dpi=450, bbox_inches="tight")
    fig.savefig(f"{stem}.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)
    print(stem)


def style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#73808A")
    ax.spines["bottom"].set_color("#73808A")
    ax.tick_params(colors=INK, labelsize=7, length=2)


def option_a(frame):
    cmap = LinearSegmentedColormap.from_list("paired_error", [TERRA, "#F7F7F5", TEAL])
    fig, axes = plt.subplots(2, 2, figsize=(7.15, 4.55))
    fig.subplots_adjust(left=.09, right=.985, bottom=.28, top=.91,
                        wspace=.12, hspace=.43)
    im = None
    for row, (baseline, _) in enumerate(BASELINES):
        for col, (dataset, name) in enumerate(DATASETS):
            ax = axes[row, col]
            values = panel_array(frame, dataset, baseline, "log2_mse_ratio")
            n = values.shape[1]
            im = ax.imshow(values, aspect="auto", interpolation="nearest",
                           cmap=cmap, norm=TwoSlopeNorm(vmin=-1.5, vcenter=0, vmax=1.5),
                           origin="upper", extent=(.5, n+.5, 49.5, 41.5), rasterized=True)
            ax.set_xlim(.5, n+.5)
            ax.set_yticks(range(42, 50))
            if col == 0:
                ax.set_ylabel("随机种子", fontproperties=CN, fontsize=8)
            else:
                ax.set_yticklabels([])
            ax.set_xticks(np.linspace(1, n, 5).round(),
                          [str(int(x)) for x in np.linspace(1, n, 5).round()])
            if row == 1:
                ax.set_xlabel("测试窗口序号", fontproperties=CN, fontsize=8)
            win_pct = 100 * (values > 0).mean()
            ax.set_title(name, loc="left", fontfamily="Times New Roman",
                         fontsize=9, fontweight="bold", color=INK, pad=5)
            ax.text(.53, 1.06, baseline, transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=8, color=BLUE if row == 0 else ORANGE,
                    fontproperties=CN if row == 1 else None)
            ax.text(.99, 1.06, f"胜出 {win_pct:.1f}%", transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=8, color=TEAL,
                    fontproperties=CN)
            style_axes(ax)
    cax = fig.add_axes((.22, .085, .56, .025))
    cb = fig.colorbar(im, cax=cax, orientation="horizontal",
                      ticks=[-1, -.5, 0, .5, 1], extend="both")
    cb.ax.tick_params(labelsize=7, length=2)
    cb.ax.set_title("log2(对照MSE / 本文MSE)  ·  正值表示本文方法更优",
                    fontproperties=CN, fontsize=8, pad=8)
    export(fig, "A_逐窗口误差时间图")


def option_b(frame):
    colors = [TEAL, BLUE, ORANGE, TERRA]
    labels = ["均胜出", "仅胜DLinear", "仅胜固定等权", "均未胜出"]
    cmap = mpl.colors.ListedColormap(colors)
    fig, axes = plt.subplots(2, 1, figsize=(7.15, 3.20))
    fig.subplots_adjust(left=.10, right=.985, bottom=.26, top=.88, hspace=.42)
    for ax, (dataset, name) in zip(axes, DATASETS):
        d = panel_array(frame, dataset, "DLinear", "proposed_better").astype(bool)
        e = panel_array(frame, dataset, "固定等权", "proposed_better").astype(bool)
        state = np.where(d & e, 0, np.where(d, 1, np.where(e, 2, 3)))
        n = state.shape[1]
        ax.imshow(state, aspect="auto", interpolation="nearest", cmap=cmap,
                  norm=BoundaryNorm(np.arange(-.5, 4.5, 1), 4), origin="upper",
                  extent=(.5, n+.5, 49.5, 41.5), rasterized=True)
        ax.set_yticks(range(42, 50))
        ax.set_ylabel("随机种子", fontproperties=CN, fontsize=8)
        ax.set_xticks(np.linspace(1, n, 5).round(),
                      [str(int(x)) for x in np.linspace(1, n, 5).round()])
        ax.set_xlim(.5, n+.5)
        ax.set_title(name, loc="left", fontfamily="Times New Roman",
                     fontweight="bold", fontsize=10, color=INK, pad=4)
        ax.text(.99, 1.035, f"{(state == 0).mean()*100:.1f}% 均胜出",
                transform=ax.transAxes, ha="right", va="bottom",
                fontproperties=CN, fontsize=8, color=TEAL)
        style_axes(ax)
    axes[1].set_xlabel("测试窗口序号", fontproperties=CN, fontsize=8)
    patches = [Patch(facecolor=c, label=l) for c, l in zip(colors, labels)]
    fig.legend(handles=patches, loc="lower center", bbox_to_anchor=(.5, .06),
               ncol=4, frameon=False, prop=CN, fontsize=8,
               columnspacing=1.7, handlelength=1.25)
    export(fig, "B_双对照窗口状态图")


def option_c(frame):
    # Within-seed quantiles preserve seed replication without treating windows as iid.
    q = np.linspace(0, 1, 101)
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.35))
    fig.subplots_adjust(left=.11, right=.985, bottom=.19, top=.87, wspace=.10)
    for ax, (dataset, name) in zip(axes, DATASETS):
        for baseline, color in (("DLinear", BLUE), ("固定等权", ORANGE)):
            values = panel_array(frame, dataset, baseline, "log2_mse_ratio")
            curves = np.quantile(values, q, axis=1).T
            lo, med, hi = np.quantile(curves, [.25, .5, .75], axis=0)
            ax.fill_between(q * 100, lo, hi, color=color, alpha=.17, linewidth=0)
            ax.plot(q * 100, med, color=color, lw=1.8,
                    label=baseline, solid_capstyle="round")
        ax.axhline(0, color="#73808A", lw=.8, ls=(0, (3, 2)), zorder=0)
        ax.set_xlim(0, 100)
        ax.set_ylim((-3.5, 4.0) if dataset == "abilene" else (-.4, .8))
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks([-3, -1, 0, 1, 3] if dataset == "abilene" else [-.4, 0, .4, .8])
        ax.set_title(name, loc="left", fontfamily="Times New Roman",
                     fontweight="bold", fontsize=10, color=INK, pad=6)
        ax.set_xlabel("窗口误差比的百分位（%）", fontproperties=CN, fontsize=8)
        ax.grid(axis="y", color="#E7EAEC", lw=.6)
        style_axes(ax)
    axes[0].set_ylabel("log2(对照MSE / 本文MSE)", fontproperties=CN, fontsize=8)
    axes[1].legend(loc="upper left", frameon=False, prop=CN, fontsize=8)
    fig.text(.5, .025, "实线：8种子中位数    ·    浅色带：种子间四分位范围    ·    零线上方为本文方法更优",
             ha="center", fontproperties=CN, fontsize=7.5)
    export(fig, "C_窗口收益分布曲线")


def main():
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 8, "pdf.fonttype": 42, "svg.fonttype": "none",
                         "axes.linewidth": .8, "savefig.facecolor": "white"})
    frame = source_data()
    assert frame.groupby(["dataset", "baseline", "seed"]).size().to_dict() == {
        (ds, base, seed): n for ds, n in (("abilene", 813), ("geant", 451))
        for base, _ in BASELINES for seed in range(42, 50)
    }
    option_a(frame)
    option_b(frame)
    option_c(frame)


if __name__ == "__main__":
    main()
