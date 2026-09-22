from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper_figures" / "real_preview"
OUT.mkdir(parents=True, exist_ok=True)

INPUT_LEN = 96
PRED_LEN = 24
SEEDS = list(range(42, 50))
GROUP_LABELS = ["低", "中低", "中", "中高", "高"]
SCALE_LABELS = ["尺度1", "尺度2", "尺度4"]
COLORS = ["#0B63B6", "#80BDF2", "#8FD17F"]


def setup_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            prop = font_manager.FontProperties(fname=p)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
            return p
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return None


def q5(values: np.ndarray) -> np.ndarray:
    s = pd.Series(values)
    try:
        return pd.qcut(s, 5, labels=False, duplicates="raise").to_numpy(dtype=int)
    except ValueError:
        # deterministic percentile-rank fallback if exact ties occur at boundaries
        ranks = s.rank(method="average", pct=True).to_numpy()
        return np.minimum((ranks * 5).astype(int), 4)


def window_features(test: np.ndarray):
    n = len(test) - INPUT_LEN - PRED_LEN + 1
    t = np.arange(INPUT_LEN, dtype=np.float64)
    tc = t - t.mean()
    denom = float(np.sum(tc * tc))
    variability = np.empty(n, dtype=np.float64)
    trend = np.empty(n, dtype=np.float64)

    for i in range(n):
        h = test[i:i + INPUT_LEN].astype(np.float64, copy=False)
        # Mean temporal standard deviation across OD channels.
        variability[i] = np.std(h, axis=0, ddof=0).mean()
        # Mean absolute least-squares slope across OD channels.
        centered = h - h.mean(axis=0, keepdims=True)
        slopes = (tc[:, None] * centered).sum(axis=0) / denom
        trend[i] = np.abs(slopes).mean()

    return variability, trend


def load_router_mean(dataset: str, n_windows: int):
    mats = []
    for seed in SEEDS:
        p = ROOT / "results" / dataset / f"dlinear_scale_seed{seed}" / "router_weights.csv"
        arr = np.loadtxt(p, delimiter=",")
        if arr.shape != (n_windows, 3):
            raise ValueError(f"Unexpected router shape for {p}: {arr.shape}, expected {(n_windows, 3)}")
        if not np.allclose(arr.sum(axis=1), 1.0, atol=1e-5):
            raise ValueError(f"Router weights do not sum to 1: {p}")
        mats.append(arr)
    stacked = np.stack(mats, axis=0)
    return stacked.mean(axis=0), stacked


def run_model(dataset: str, model: str, output_root: Path):
    run_dir = output_root / dataset / f"{model}_seed42"
    pred_file = run_dir / "predictions.npz"
    if not pred_file.exists():
        cmd = [
            sys.executable, str(ROOT / "train.py"),
            "--dataset", dataset,
            "--model", model,
            "--seed", "42",
            "--input-len", str(INPUT_LEN),
            "--pred-len", str(PRED_LEN),
            "--output-root", str(output_root),
        ]
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = "42"
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)

    p = np.load(pred_file)
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    return p["prediction"], p["truth"], metrics


def committed_metrics(dataset: str, model: str):
    p = ROOT / "results" / dataset / f"{model}_seed42" / "metrics.json"
    return json.loads(p.read_text(encoding="utf-8"))


def mean_heatmap(delta: np.ndarray, var_group: np.ndarray, trend_group: np.ndarray):
    mat = np.full((5, 5), np.nan, dtype=np.float64)
    counts = np.zeros((5, 5), dtype=int)
    # Row index 0 in the plotted matrix will be "高", so reverse trend group.
    for tg in range(5):
        for vg in range(5):
            mask = (trend_group == tg) & (var_group == vg)
            counts[4 - tg, vg] = int(mask.sum())
            if mask.any():
                mat[4 - tg, vg] = float(delta[mask].mean())
    return mat, counts


def main():
    font_path = setup_font()
    retrain_root = OUT / "_retrain_results"
    datasets = ["abilene", "geant"]
    display = {"abilene": "Abilene", "geant": "GÉANT"}
    packed = {}
    audit = {
        "data_policy": "All plotted values are computed from repository files or deterministic seed-42 reruns using repository code/data.",
        "input_len": INPUT_LEN,
        "pred_len": PRED_LEN,
        "router_seeds": SEEDS,
        "variability_definition": "mean across channels of temporal std over each 96-step normalized input window",
        "trend_definition": "mean across channels of absolute least-squares temporal slope over each 96-step normalized input window",
        "grouping": "within each dataset, variability and trend strength are independently split into quintiles",
        "delta_mse_definition": "per-window MSE(static equal-weight multiscale) - MSE(adaptive multiscale), normalized scale; positive means adaptive is better",
        "font_path": font_path,
        "datasets": {},
    }

    summary_rows = []

    for dataset in datasets:
        arrays = np.load(ROOT / "data" / "processed" / f"{dataset}_1hour.npz")
        test = arrays["test"]
        variability, trend = window_features(test)
        n_windows = len(variability)
        var_group = q5(variability)
        trend_group = q5(trend)

        router_mean, router_all = load_router_mean(dataset, n_windows)
        group_weights = np.vstack([
            router_mean[var_group == g].mean(axis=0)
            for g in range(5)
        ])

        # Re-run seed 42 from the committed processed data to recover per-window predictions.
        pred_ad, truth_ad, metric_ad = run_model(dataset, "dlinear_scale", retrain_root)
        pred_st, truth_st, metric_st = run_model(dataset, "dlinear_scale_static", retrain_root)
        if not np.allclose(truth_ad, truth_st, atol=1e-7):
            raise ValueError(f"Truth mismatch between models for {dataset}")
        if len(pred_ad) != n_windows or len(pred_st) != n_windows:
            raise ValueError(f"Prediction/window count mismatch for {dataset}")

        mse_ad_win = np.mean((pred_ad - truth_ad) ** 2, axis=(1, 2))
        mse_st_win = np.mean((pred_st - truth_st) ** 2, axis=(1, 2))
        delta = mse_st_win - mse_ad_win
        heat, counts = mean_heatmap(delta, var_group, trend_group)

        c_ad = committed_metrics(dataset, "dlinear_scale")
        c_st = committed_metrics(dataset, "dlinear_scale_static")
        committed_ad = float(c_ad["test_normalized"]["mse"])
        committed_st = float(c_st["test_normalized"]["mse"])
        rerun_ad = float(metric_ad["test_normalized"]["mse"])
        rerun_st = float(metric_st["test_normalized"]["mse"])

        packed[dataset] = {
            "group_weights": group_weights,
            "heat": heat,
            "counts": counts,
            "delta": delta,
            "var_group": var_group,
            "trend_group": trend_group,
        }

        audit["datasets"][dataset] = {
            "test_rows": int(len(test)),
            "test_windows": int(n_windows),
            "router_shape_all_seeds": list(router_all.shape),
            "committed_seed42_mse": {
                "adaptive": committed_ad,
                "static": committed_st,
            },
            "rerun_seed42_mse": {
                "adaptive": rerun_ad,
                "static": rerun_st,
            },
            "absolute_rerun_difference": {
                "adaptive": abs(rerun_ad - committed_ad),
                "static": abs(rerun_st - committed_st),
            },
            "overall_window_delta_mse_mean_rerun": float(delta.mean()),
            "positive_delta_window_fraction_rerun": float((delta > 0).mean()),
            "variability_quintile_counts": [int((var_group == g).sum()) for g in range(5)],
            "trend_quintile_counts": [int((trend_group == g).sum()) for g in range(5)],
            "heatmap_counts_top_high_to_bottom_low": counts.tolist(),
        }

        for g, name in enumerate(GROUP_LABELS):
            summary_rows.append({
                "dataset": display[dataset],
                "panel": "scale_weight",
                "variability_group": name,
                "scale1": group_weights[g, 0],
                "scale2": group_weights[g, 1],
                "scale4": group_weights[g, 2],
            })
        row_names = ["高", "中高", "中", "中低", "低"]
        for r, tname in enumerate(row_names):
            for c, vname in enumerate(GROUP_LABELS):
                summary_rows.append({
                    "dataset": display[dataset],
                    "panel": "delta_mse_heatmap",
                    "trend_group": tname,
                    "variability_group": vname,
                    "delta_mse": heat[r, c],
                    "n_windows": counts[r, c],
                })

    # Figure
    fig, axes = plt.subplots(2, 2, figsize=(8.1, 6.25))
    fig.subplots_adjust(left=0.095, right=0.965, bottom=0.105, top=0.955, wspace=0.30, hspace=0.42)

    for col, dataset in enumerate(datasets):
        ax = axes[0, col]
        gw = packed[dataset]["group_weights"]
        x = np.arange(5)
        ax.bar(x, gw[:, 0], width=0.72, color=COLORS[0], label="尺度1", edgecolor="none")
        ax.bar(x, gw[:, 1], width=0.72, bottom=gw[:, 0], color=COLORS[1], label="尺度2", edgecolor="none")
        ax.bar(x, gw[:, 2], width=0.72, bottom=gw[:, 0] + gw[:, 1], color=COLORS[2], label="尺度4", edgecolor="none")
        ax.set_ylim(0, 1.0)
        ax.set_xticks(x, GROUP_LABELS)
        ax.set_xlabel("输入波动性分组")
        ax.set_ylabel("平均尺度权重")
        ax.set_title(f"({chr(97 + col)}) {display[dataset]}", loc="left", fontsize=11.5, fontweight="bold")
        ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
        ax.set_axisbelow(True)
        # Display legend in the same visual order as the user's chosen draft.
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc="upper right", frameon=True, fontsize=8.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # Use a common color range derived from actual values, always including zero.
    all_heat = np.concatenate([packed[d]["heat"][np.isfinite(packed[d]["heat"])] for d in datasets])
    vmin = min(0.0, float(np.min(all_heat)))
    vmax = max(0.0, float(np.max(all_heat)))
    if abs(vmax - vmin) < 1e-10:
        vmax = vmin + 1e-6

    for col, dataset in enumerate(datasets):
        ax = axes[1, col]
        heat = packed[dataset]["heat"]
        im = ax.imshow(heat, cmap="YlOrRd", vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_xticks(np.arange(5), GROUP_LABELS)
        ax.set_yticks(np.arange(5), ["高", "中高", "中", "中低", "低"])
        ax.set_xlabel("输入波动性分组")
        ax.set_ylabel("趋势强度分组")
        ax.set_title(f"({chr(99 + col)}) {display[dataset]}", loc="left", fontsize=11.5, fontweight="bold")
        for r in range(5):
            for c in range(5):
                val = heat[r, c]
                if np.isfinite(val):
                    ax.text(c, r, f"{val:.4f}", ha="center", va="center", fontsize=7.4, color="black")
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.035)
        cb.set_label("均方误差差值 ΔMSE", fontsize=8.5)
        cb.ax.tick_params(labelsize=7.5)

    out_png = OUT / "real_multiscale_mechanism_figure.png"
    fig.savefig(out_png, dpi=360, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    pd.DataFrame(summary_rows).to_csv(OUT / "real_multiscale_mechanism_source.csv", index=False, encoding="utf-8-sig")
    (OUT / "real_multiscale_mechanism_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    print(f"FIGURE={out_png}")


if __name__ == "__main__":
    main()
