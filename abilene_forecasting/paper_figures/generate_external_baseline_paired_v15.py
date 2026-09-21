from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.lines import Line2D
from matplotlib.transforms import ScaledTranslation

ROOT = Path(__file__).resolve().parents[1]
FIGDIR = Path(__file__).resolve().parent
OUT_COLOR = FIGDIR / "exports" / "color"
OUT_GRAY = FIGDIR / "exports" / "grayscale"
SOURCE_DIR = FIGDIR / "source_data_v15"
for p in (OUT_COLOR, OUT_GRAY, SOURCE_DIR):
    p.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": [
        "Noto Serif CJK SC", "Noto Serif CJK JP", "SimSun",
        "Times New Roman", "Liberation Serif", "DejaVu Serif",
    ],
    "font.size": 7.0,
    "axes.labelsize": 7.2,
    "axes.titlesize": 8.2,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.1,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "axes.unicode_minus": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

DLINEAR = "#6B5B95"
LIGHTTS = "#E87522"
PROPOSED = "#0072B2"
SEED_EDGE = "#FFFFFF"
GRID = "#D9D9D9"
MEAN_LW = 1.55
SEED_LW = 0.8
MARKERS = {42: "s", 43: "o", 44: "^"}


def add_panel_label(ax: plt.Axes, label: str) -> None:
    offset = ScaledTranslation(-9 / 72, 4 / 72, ax.figure.dpi_scale_trans)
    ax.text(
        0, 1, label,
        transform=ax.transAxes + offset,
        fontsize=8.5,
        fontweight="bold",
        fontfamily="Times New Roman",
        ha="left", va="bottom",
        color="#111111",
    )


def load_data() -> pd.DataFrame:
    rows = []
    for dataset in ("abilene", "geant"):
        for model, model_label in (
            ("dlinear", "DLinear"),
            ("lightts", "LightTS"),
            ("dlinear_scale", "本文方法"),
        ):
            for seed in (42, 43, 44):
                path = ROOT / "results" / dataset / f"{model}_seed{seed}" / "metrics.json"
                obj = json.loads(path.read_text(encoding="utf-8"))
                for metric in ("mse", "mae"):
                    rows.append({
                        "dataset": dataset,
                        "dataset_label": "Abilene" if dataset == "abilene" else "GÉANT",
                        "model": model,
                        "model_label": model_label,
                        "seed": seed,
                        "metric": metric.upper(),
                        "value": float(obj["test_normalized"][metric]),
                    })
    df = pd.DataFrame(rows)
    df.to_csv(SOURCE_DIR / "fig2_external_baseline_paired_seed42_44.csv", index=False)
    return df


def values(df: pd.DataFrame, dataset: str, metric: str, model: str) -> np.ndarray:
    sub = df[
        (df.dataset == dataset) & (df.metric == metric) & (df.model == model)
    ].sort_values("seed")
    return sub.value.to_numpy(float)


def draw_pair_group(ax, x0, x1, baseline_vals, proposed_vals, baseline_color):
    seeds = [42, 43, 44]
    # Per-seed paired lines.
    for seed, y0, y1 in zip(seeds, baseline_vals, proposed_vals):
        ax.plot(
            [x0, x1], [y0, y1],
            color=baseline_color,
            lw=SEED_LW,
            ls=":",
            alpha=0.80,
            zorder=1,
        )
        ax.scatter(
            [x0], [y0],
            marker=MARKERS[seed], s=31,
            facecolor=baseline_color, edgecolor=SEED_EDGE,
            linewidth=0.55, zorder=3,
        )
        ax.scatter(
            [x1], [y1],
            marker=MARKERS[seed], s=31,
            facecolor=PROPOSED, edgecolor=SEED_EDGE,
            linewidth=0.55, zorder=3,
        )
        # Small seed labels only at the baseline side to avoid clutter.
        ax.annotate(
            str(seed), (x0, y0),
            xytext=(-8, 0), textcoords="offset points",
            ha="right", va="center", fontsize=5.5,
            color=baseline_color,
        )

    # Mean comparison.
    m0, m1 = baseline_vals.mean(), proposed_vals.mean()
    ax.plot([x0, x1], [m0, m1], color=baseline_color, lw=MEAN_LW, zorder=2)
    ax.scatter([x0], [m0], s=48, marker="o", facecolor=baseline_color,
               edgecolor="white", linewidth=0.65, zorder=4)
    ax.scatter([x1], [m1], s=48, marker="o", facecolor=PROPOSED,
               edgecolor="white", linewidth=0.65, zorder=4)


def draw_panel(ax, df, dataset, metric, title, panel):
    dlinear = values(df, dataset, metric, "dlinear")
    lightts = values(df, dataset, metric, "lightts")
    proposed = values(df, dataset, metric, "dlinear_scale")

    draw_pair_group(ax, 0, 1, dlinear, proposed, DLINEAR)
    draw_pair_group(ax, 2, 3, lightts, proposed, LIGHTTS)

    ax.set_xticks([0, 1, 2, 3], ["DLinear", "本文方法", "LightTS", "本文方法"])
    ax.set_ylabel(metric)
    ax.set_title(title, fontweight="bold", pad=5)
    ax.grid(axis="y", color=GRID, ls="--", lw=0.45, alpha=0.72)
    ax.set_axisbelow(True)
    ax.tick_params(direction="in", length=3.0, width=0.7)
    add_panel_label(ax, panel)

    # Give a little horizontal room for seed labels and separation between pairs.
    ax.set_xlim(-0.48, 3.48)

    # Dataset-specific, data-driven y limits with modest padding.
    all_vals = np.concatenate([dlinear, lightts, proposed])
    lo, hi = float(all_vals.min()), float(all_vals.max())
    span = max(hi - lo, 1e-6)
    ax.set_ylim(max(0.0, lo - 0.14 * span), hi + 0.16 * span)


def main() -> None:
    df = load_data()
    fig, axes = plt.subplots(2, 2, figsize=(7.09, 5.05))

    draw_panel(axes[0, 0], df, "abilene", "MSE", "Abilene-MSE", "a")
    draw_panel(axes[0, 1], df, "abilene", "MAE", "Abilene-MAE", "b")
    draw_panel(axes[1, 0], df, "geant", "MSE", "GÉANT-MSE", "c")
    draw_panel(axes[1, 1], df, "geant", "MAE", "GÉANT-MAE", "d")

    legend = [
        Line2D([0], [0], marker="o", color=DLINEAR, lw=MEAN_LW,
               markerfacecolor=DLINEAR, markeredgecolor="white",
               label="DLinear（均值）"),
        Line2D([0], [0], marker="o", color=LIGHTTS, lw=MEAN_LW,
               markerfacecolor=LIGHTTS, markeredgecolor="white",
               label="LightTS（均值）"),
        Line2D([0], [0], marker="o", color=PROPOSED, lw=MEAN_LW,
               markerfacecolor=PROPOSED, markeredgecolor="white",
               label="本文方法（均值）"),
        Line2D([0], [0], marker="s", color="#888888", lw=0,
               markerfacecolor="#888888", markeredgecolor="white",
               label="seed 42"),
        Line2D([0], [0], marker="o", color="#888888", lw=0,
               markerfacecolor="#888888", markeredgecolor="white",
               label="seed 43"),
        Line2D([0], [0], marker="^", color="#888888", lw=0,
               markerfacecolor="#888888", markeredgecolor="white",
               label="seed 44"),
    ]
    fig.legend(
        handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.012),
        ncol=6, columnspacing=1.35, handletextpad=0.45, frameon=False,
    )
    fig.subplots_adjust(
        left=0.09, right=0.985, bottom=0.13, top=0.96,
        wspace=0.22, hspace=0.29,
    )

    stem = "fig2_external_baseline_paired_v15"
    png = OUT_COLOR / f"{stem}_color.png"
    jpg = OUT_COLOR / f"{stem}_color.jpg"
    pdf = OUT_COLOR / f"{stem}_color.pdf"
    svg = OUT_COLOR / f"{stem}_color.svg"
    fig.savefig(png, dpi=600, bbox_inches="tight")
    fig.savefig(jpg, dpi=600, bbox_inches="tight",
                pil_kwargs={"quality": 95, "subsampling": 0})
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)

    rgb = Image.open(png).convert("RGB")
    gray = rgb.convert("L")
    gray.save(OUT_GRAY / f"{stem}_grayscale.png", dpi=(600, 600))
    gray.save(OUT_GRAY / f"{stem}_grayscale.jpg",
              quality=95, subsampling=0, dpi=(600, 600))
    gray.save(OUT_GRAY / f"{stem}_grayscale.tiff",
              compression="tiff_lzw", dpi=(600, 600))

    # Numerical audit output.
    for dataset in ("abilene", "geant"):
        for metric in ("MSE", "MAE"):
            p = values(df, dataset, metric, "dlinear_scale")
            for baseline in ("dlinear", "lightts"):
                b = values(df, dataset, metric, baseline)
                reduction = (b - p) / b * 100.0
                aggregate = (b.mean() - p.mean()) / b.mean() * 100.0
                print(
                    dataset, metric, baseline,
                    "baseline=", np.round(b, 6).tolist(),
                    "proposed=", np.round(p, 6).tolist(),
                    "seed_reduction=", np.round(reduction, 2).tolist(),
                    "wins=", int((p < b).sum()), "/3",
                    "aggregate_reduction=", round(float(aggregate), 2),
                )


if __name__ == "__main__":
    main()
