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
SOURCE_DIR = FIGDIR / "source_data_v13"
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
    "legend.fontsize": 6.2,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "axes.unicode_minus": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

BLUE = "#4F81BD"
ORANGE = "#D9782D"
DARK = "#222222"
MID = "#A0A5AA"
GRID = "#D7DADF"


def add_panel_label(ax: plt.Axes, label: str) -> None:
    offset = ScaledTranslation(-10 / 72, 3 / 72, ax.figure.dpi_scale_trans)
    ax.text(
        0, 1, label,
        transform=ax.transAxes + offset,
        fontsize=8.5, fontweight="bold",
        fontfamily="Times New Roman",
        ha="left", va="bottom", color=DARK,
    )


def load_results() -> pd.DataFrame:
    rows = []
    for dataset in ("abilene", "geant"):
        per_model = {}
        for model in ("dlinear", "lightts", "dlinear_scale"):
            vals = {}
            for seed in (42, 43, 44):
                p = ROOT / "results" / dataset / f"{model}_seed{seed}" / "metrics.json"
                obj = json.loads(p.read_text(encoding="utf-8"))
                vals[seed] = obj["test_normalized"]
            per_model[model] = vals

        for metric in ("mse", "mae"):
            proposed_values = np.array(
                [per_model["dlinear_scale"][s][metric] for s in (42, 43, 44)],
                dtype=float,
            )
            for baseline, baseline_label in (("dlinear", "DLinear"), ("lightts", "LightTS")):
                baseline_values = np.array(
                    [per_model[baseline][s][metric] for s in (42, 43, 44)],
                    dtype=float,
                )
                aggregate_reduction = (
                    (baseline_values.mean() - proposed_values.mean())
                    / baseline_values.mean() * 100.0
                )
                for idx, seed in enumerate((42, 43, 44)):
                    reduction = (
                        (baseline_values[idx] - proposed_values[idx])
                        / baseline_values[idx] * 100.0
                    )
                    rows.append({
                        "dataset": dataset,
                        "dataset_label": "Abilene" if dataset == "abilene" else "GÉANT",
                        "metric": metric.upper(),
                        "baseline": baseline,
                        "baseline_label": baseline_label,
                        "seed": seed,
                        "baseline_error": baseline_values[idx],
                        "adaptive_error": proposed_values[idx],
                        "reduction_pct": reduction,
                        "aggregate_reduction_from_3seed_means_pct": aggregate_reduction,
                        "adaptive_better": bool(reduction > 0),
                    })
    frame = pd.DataFrame(rows)
    frame.to_csv(
        SOURCE_DIR / "fig2_external_baseline_reduction_3seeds.csv",
        index=False,
    )
    return frame


def draw() -> None:
    data = load_results()
    order = [
        ("abilene", "dlinear", "Abilene / DLinear"),
        ("abilene", "lightts", "Abilene / LightTS"),
        ("geant", "dlinear", "GÉANT / DLinear"),
        ("geant", "lightts", "GÉANT / LightTS"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.08), sharey=True)
    for panel_idx, (ax, metric, title) in enumerate(
        zip(axes, ("MSE", "MAE"), ("MSE", "MAE"))
    ):
        for y, (dataset, baseline, label) in enumerate(order):
            sub = data[
                (data.dataset == dataset)
                & (data.baseline == baseline)
                & (data.metric == metric)
            ].sort_values("seed")
            vals = sub.reduction_pct.to_numpy(dtype=float)
            aggregate = float(
                sub.aggregate_reduction_from_3seed_means_pct.iloc[0]
            )
            color = BLUE if dataset == "abilene" else ORANGE

            # Min-max connector shows the full seed-to-seed range.
            ax.hlines(y, vals.min(), vals.max(), color=MID, lw=0.8, zorder=1)
            ax.scatter(
                vals, np.full_like(vals, y, dtype=float),
                s=27, marker="o",
                facecolor=color, edgecolor="white", linewidth=0.55,
                alpha=0.92, zorder=3,
            )
            ax.scatter(
                [aggregate], [y], s=42, marker="D",
                facecolor=DARK, edgecolor="white", linewidth=0.6,
                zorder=4,
            )

        ax.axvline(0.0, color="#666666", lw=0.8, ls="--", dashes=(4, 3), zorder=0)
        ax.grid(axis="x", color=GRID, ls="--", lw=0.45, alpha=0.75)
        ax.set_axisbelow(True)
        ax.set_xlabel("相对误差降低率/%")
        ax.set_title(title, fontweight="bold", pad=6, fontfamily="Times New Roman")
        ax.set_yticks(range(len(order)), [x[2] for x in order])
        ax.invert_yaxis()
        ax.tick_params(direction="in", length=3.0, width=0.7)
        add_panel_label(ax, chr(ord("a") + panel_idx))

    axes[0].set_xlim(-10, 55)
    axes[1].set_xlim(-10, 40)

    legend = [
        Line2D([0], [0], marker="o", color="none", label="单个随机种子",
               markerfacecolor="#7A7A7A", markeredgecolor="white", markersize=5.2),
        Line2D([0], [0], marker="D", color="none", label="3种子均值降幅",
               markerfacecolor=DARK, markeredgecolor="white", markersize=5.2),
    ]
    fig.legend(
        handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.995),
        ncol=2, columnspacing=1.8, handletextpad=0.55,
    )
    fig.subplots_adjust(left=0.205, right=0.985, bottom=0.18, top=0.83, wspace=0.22)

    stem = "fig2_external_baseline_reduction"
    png = OUT_COLOR / f"{stem}_color.png"
    jpg = OUT_COLOR / f"{stem}_color.jpg"
    pdf = OUT_COLOR / f"{stem}_color.pdf"
    svg = OUT_COLOR / f"{stem}_color.svg"
    fig.savefig(png, dpi=600, bbox_inches="tight")
    fig.savefig(jpg, dpi=600, bbox_inches="tight", pil_kwargs={"quality": 95, "subsampling": 0})
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)

    rgb = Image.open(png).convert("RGB")
    gray = rgb.convert("L")
    gray.save(OUT_GRAY / f"{stem}_grayscale.png", dpi=(600, 600))
    gray.save(
        OUT_GRAY / f"{stem}_grayscale.jpg",
        quality=95, subsampling=0, dpi=(600, 600),
    )
    gray.save(
        OUT_GRAY / f"{stem}_grayscale.tiff",
        compression="tiff_lzw", dpi=(600, 600),
    )

    # Console audit: every claim entering the manuscript comes from these rows.
    for metric in ("MSE", "MAE"):
        print("==", metric, "==")
        for dataset, baseline, label in order:
            sub = data[
                (data.dataset == dataset)
                & (data.baseline == baseline)
                & (data.metric == metric)
            ]
            vals = sub.reduction_pct.to_numpy(dtype=float)
            aggregate = sub.aggregate_reduction_from_3seed_means_pct.iloc[0]
            print(
                label,
                "seed_reductions=", np.round(vals, 2).tolist(),
                "wins=", int((vals > 0).sum()), "/3",
                "aggregate=", round(float(aggregate), 2),
            )


if __name__ == "__main__":
    draw()
