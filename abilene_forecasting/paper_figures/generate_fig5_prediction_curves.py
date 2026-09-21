from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.transforms import ScaledTranslation


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "exports" / "fig5_prediction_curves"
SOURCE = Path(__file__).resolve().parent / "source_data_v2"
NATURE_SCRIPTS = Path(r"C:\Users\Quant\.codex\skills\nature-figure\scripts")
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(NATURE_SCRIPTS))

from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

font_manager.fontManager.addfont(r"C:\Windows\Fonts\simsun.ttc")

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [
            "SimSun",
            "Arial",
            "Noto Serif CJK SC",
            "Noto Serif CJK JP",
            "DejaVu Serif",
        ],
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 8,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "axes.unicode_minus": False,
        "legend.frameon": False,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)

TRUTH_COLOR = "#222222"
DLINEAR_COLOR = "#7A5195"
PROPOSED_COLOR = "#0072B2"


def inverse_transform(values: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    log_values = values * std.reshape(1, 1, -1) + mean.reshape(1, 1, -1)
    return np.maximum(np.expm1(log_values), 0.0)


def choose_representative_case(
    truth: np.ndarray, dlinear: np.ndarray, proposed: np.ndarray
) -> tuple[int, int]:
    """Choose a median-error case, never a best-case or relative-gain case."""
    del dlinear
    window_error = np.abs(proposed - truth).mean(axis=(1, 2))
    window_idx = int(np.argmin(np.abs(window_error - np.median(window_error))))

    channel_sd = truth[window_idx].std(axis=0)
    eligible = np.flatnonzero(channel_sd > 1e-8)
    if eligible.size == 0:
        raise ValueError("No nonconstant channel is available in the selected window")
    channel_idx = int(
        eligible[np.argmin(np.abs(channel_sd[eligible] - np.median(channel_sd[eligible])))]
    )
    return window_idx, channel_idx


def load_case(dataset: str) -> tuple[pd.DataFrame, dict[str, object]]:
    dlinear_path = ROOT / "results" / dataset / "dlinear_seed42" / "predictions.npz"
    proposed_path = ROOT / "results" / dataset / "dlinear_scale_seed42" / "predictions.npz"
    processed_path = ROOT / "data" / "processed" / f"{dataset}_1hour.npz"

    with np.load(dlinear_path) as data:
        dlinear_pred = data["prediction"].copy()
        dlinear_truth = data["truth"].copy()
    with np.load(proposed_path) as data:
        proposed_pred = data["prediction"].copy()
        proposed_truth = data["truth"].copy()
    with np.load(processed_path) as data:
        mean = data["mean"].copy()
        std = data["std"].copy()
        active_indices = data["active_indices"].copy()

    if not np.allclose(dlinear_truth, proposed_truth, atol=1e-7):
        raise ValueError(f"{dataset}: model files do not share identical targets")

    window_idx, channel_idx = choose_representative_case(
        proposed_truth, dlinear_pred, proposed_pred
    )
    truth = inverse_transform(proposed_truth, mean, std)
    dlinear = inverse_transform(dlinear_pred, mean, std)
    proposed = inverse_transform(proposed_pred, mean, std)
    horizon = np.arange(1, truth.shape[1] + 1)

    frame = pd.DataFrame(
        {
            "dataset": dataset,
            "forecast_hour": horizon,
            "truth": proposed_truth[window_idx, :, channel_idx],
            "dlinear_seed42": dlinear_pred[window_idx, :, channel_idx],
            "adaptive_multiscale_seed42": proposed_pred[window_idx, :, channel_idx],
            "truth_original_scale": truth[window_idx, :, channel_idx],
            "dlinear_original_scale": dlinear[window_idx, :, channel_idx],
            "adaptive_multiscale_original_scale": proposed[window_idx, :, channel_idx],
        }
    )
    metadata = {
        "dataset": dataset,
        "seed": 42,
        "window_index_zero_based": window_idx,
        "active_channel_index_zero_based": channel_idx,
        "original_channel_index_zero_based": int(active_indices[channel_idx]),
        "selection_rule": (
            "在标准化测试集上，选择本文方法绝对误差最接近全部测试窗口中位数的窗口；"
            "再从该窗口的非恒定OD通道中，选择24步真实值标准差最接近通道中位数的通道。"
            "该规则用于展示典型而非最佳预测，不按本文方法相对DLinear的误差优势筛选。"
        ),
        "dlinear_case_mae_standardized": float(
            np.mean(np.abs(frame["dlinear_seed42"] - frame["truth"]))
        ),
        "adaptive_case_mae_standardized": float(
            np.mean(np.abs(frame["adaptive_multiscale_seed42"] - frame["truth"]))
        ),
    }
    return frame, metadata


def add_panel_label(ax: plt.Axes, label: str) -> None:
    offset = ScaledTranslation(-10 / 72, 4 / 72, ax.figure.dpi_scale_trans)
    ax.text(
        0,
        1,
        label,
        transform=ax.transAxes + offset,
        fontsize=8,
        fontweight="bold",
        fontfamily="Times New Roman",
        ha="left",
        va="bottom",
        color="#111111",
    )


def main() -> None:
    cases = [load_case("abilene"), load_case("geant")]
    source = pd.concat([item[0] for item in cases], ignore_index=True)
    metadata = [item[1] for item in cases]
    source.to_csv(SOURCE / "fig5_representative_forecasts.csv", index=False)
    (SOURCE / "fig5_representative_forecasts_selection.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.09, 2.62), sharex=True)
    for ax, (frame, info), title, panel in zip(
        axes, cases, ["Abilene", "GÉANT"], ["a", "b"]
    ):
        x = frame["forecast_hour"].to_numpy()
        ax.plot(x, frame["truth"], color=TRUTH_COLOR, lw=1.55, label="真实值", zorder=4)
        ax.plot(
            x,
            frame["dlinear_seed42"],
            color=DLINEAR_COLOR,
            lw=1.15,
            ls="--",
            marker="o",
            ms=2.8,
            markevery=3,
            mfc="white",
            mec=DLINEAR_COLOR,
            mew=0.65,
            label="DLinear",
            zorder=2,
        )
        ax.plot(
            x,
            frame["adaptive_multiscale_seed42"],
            color=PROPOSED_COLOR,
            lw=1.35,
            marker="s",
            ms=2.6,
            markevery=3,
            mfc=PROPOSED_COLOR,
            mec="white",
            mew=0.4,
            label="本文方法",
            zorder=3,
        )
        ax.set_title(title, fontweight="bold", pad=5)
        ax.set_xlabel("预测时长（h）")
        ax.set_ylabel("标准化流量")
        ax.set_xlim(1, 24)
        ax.set_xticks([1, 6, 12, 18, 24])
        ax.grid(axis="y", color="#D9D9D9", ls="--", lw=0.55, alpha=0.75)
        ax.set_axisbelow(True)
        add_panel_label(ax, panel)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=3,
        handlelength=2.6,
        columnspacing=1.8,
    )
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.22, top=0.78, wspace=0.28)
    fig.canvas.draw()

    stem = OUT / "fig5_representative_forecasts"
    require_matplotlib_panel_alignment(
        fig,
        json_out=str(stem) + ".alignment.json",
        overlay_svg=str(stem) + ".alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=True,
        strict=True,
    )
    fig.savefig(str(stem) + ".svg", bbox_inches="tight")
    fig.savefig(str(stem) + ".pdf", bbox_inches="tight")
    fig.savefig(str(stem) + ".png", dpi=600, bbox_inches="tight")
    fig.savefig(
        str(stem) + ".tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)

    for item in metadata:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
