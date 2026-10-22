"""Compare learned global scale weights with the existing adaptive router."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results" / "global_weight_ablation" / "analysis"
SCALES = (1, 2, 4)
SEEDS = range(42, 50)


def run_dir(dataset: str, model: str, seed: int) -> Path:
    if model == "dlinear_scale_global":
        return ROOT / "results" / "global_weight_ablation" / dataset / f"{model}_seed{seed}"
    return ROOT / "results" / dataset / f"{model}_seed{seed}"


def load_run(dataset: str, model: str, seed: int):
    path = run_dir(dataset, model, seed)
    metrics = json.loads((path / "metrics.json").read_text(encoding="utf-8"))
    with np.load(path / "predictions.npz") as data:
        prediction, truth = data["prediction"], data["truth"]
    weights = np.loadtxt(path / "router_weights.csv", delimiter=",")
    return metrics, prediction, truth, weights


def volatility(values: np.ndarray, input_len: int = 96, pred_len: int = 24) -> np.ndarray:
    count = len(values) - input_len - pred_len + 1
    return np.asarray([
        np.abs(np.diff(values[i:i + input_len], axis=0)).mean()
        for i in range(count)
    ])


def mean_ci(values: np.ndarray) -> tuple[float, float, float]:
    mean = float(values.mean())
    half_width = float(t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return mean, mean - half_width, mean + half_width


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    paired, within, bins, by_bin, summaries = [], [], [], [], []
    for dataset in ("abilene", "geant"):
        with np.load(ROOT / "data" / "processed" / f"{dataset}_1hour.npz") as data:
            training, test = data["train"], data["test"]
        thresholds = np.quantile(volatility(training), [1 / 3, 2 / 3])
        test_volatility = volatility(test)
        group = np.searchsorted(thresholds, test_volatility, side="right")
        for bin_id, name in enumerate(("low", "medium", "high")):
            bins.append({"dataset": dataset, "bin": name, "train_threshold_low": float(thresholds[0]),
                         "train_threshold_high": float(thresholds[1]), "test_windows": int((group == bin_id).sum())})

        for seed in SEEDS:
            gm, gp, gt, gw = load_run(dataset, "dlinear_scale_global", seed)
            am, ap, at, aw = load_run(dataset, "dlinear_scale", seed)
            if not np.allclose(gt, at) or len(gp) != len(test_volatility):
                raise ValueError(f"Prediction targets or window counts differ: {dataset} seed {seed}")
            if not np.allclose(gw, gw[0], atol=1e-7) or not np.allclose(gw.sum(axis=1), 1, atol=1e-6):
                raise ValueError(f"Global weights are not fixed and normalized: {dataset} seed {seed}")
            global_mse = gm["test_normalized"]["mse"]
            adaptive_mse = am["test_normalized"]["mse"]
            paired.append({"dataset": dataset, "seed": seed, "global_mse": global_mse,
                           "adaptive_mse": adaptive_mse, "mse_difference": global_mse - adaptive_mse,
                           "adaptive_reduction_pct": 100 * (global_mse - adaptive_mse) / global_mse,
                           "global_mae": gm["test_normalized"]["mae"],
                           "adaptive_mae": am["test_normalized"]["mae"]})
            for col, scale in enumerate(SCALES):
                within.append({"dataset": dataset, "seed": seed, "scale": scale,
                               "adaptive_mean": float(aw[:, col].mean()),
                               "adaptive_within_seed_sd": float(aw[:, col].std(ddof=0)),
                               "global_weight": float(gw[0, col])})
            global_window_mse = ((gp - gt) ** 2).mean(axis=(1, 2))
            adaptive_window_mse = ((ap - at) ** 2).mean(axis=(1, 2))
            for bin_id, name in enumerate(("low", "medium", "high")):
                selected = group == bin_id
                if not selected.any():
                    continue
                global_bin_mse = float(global_window_mse[selected].mean())
                adaptive_bin_mse = float(adaptive_window_mse[selected].mean())
                by_bin.append({"dataset": dataset, "seed": seed, "bin": name,
                               "test_windows": int(selected.sum()), "global_mse": global_bin_mse,
                               "adaptive_mse": adaptive_bin_mse,
                               "mse_difference": global_bin_mse - adaptive_bin_mse,
                               "adaptive_reduction_pct": 100 * (global_bin_mse - adaptive_bin_mse) / global_bin_mse,
                               **{f"adaptive_weight_{scale}": float(aw[selected, col].mean())
                                  for col, scale in enumerate(SCALES)}})

        dataset_pairs = pd.DataFrame(paired).query("dataset == @dataset")
        for metric in ("mse_difference", "adaptive_reduction_pct"):
            values = dataset_pairs[metric].to_numpy()
            mean, low, high = mean_ci(values)
            summaries.append({"dataset": dataset, "measure": metric, "n_seeds": len(values),
                              "mean": mean, "ci95_low": low, "ci95_high": high,
                              "adaptive_wins": int((dataset_pairs.mse_difference > 0).sum())})

    variance = []
    for (dataset, scale), group in pd.DataFrame(within).groupby(["dataset", "scale"]):
        within_variance = float(np.mean(group.adaptive_within_seed_sd.to_numpy() ** 2))
        between_variance = float(group.adaptive_mean.var(ddof=0))
        variance.append({"dataset": dataset, "scale": scale,
                         "within_seed_variance": within_variance,
                         "between_seed_variance": between_variance,
                         "between_seed_share": between_variance / (within_variance + between_variance)})
    bin_summary = []
    for (dataset, name), group in pd.DataFrame(by_bin).groupby(["dataset", "bin"], sort=False):
        values = group.adaptive_reduction_pct.to_numpy()
        mean, low, high = mean_ci(values)
        bin_summary.append({"dataset": dataset, "bin": name, "n_seeds": len(values),
                            "test_windows": int(group.test_windows.iloc[0]),
                            "global_mse_mean": float(group.global_mse.mean()),
                            "adaptive_mse_mean": float(group.adaptive_mse.mean()),
                            "reduction_pct_mean": mean, "ci95_low": low, "ci95_high": high,
                            "adaptive_wins": int((group.mse_difference > 0).sum()),
                            **{f"adaptive_weight_{scale}_mean": float(group[f"adaptive_weight_{scale}"].mean())
                               for scale in SCALES}})
    for name, rows in (("paired_seed_results", paired), ("within_seed_weights", within),
                       ("volatility_bin_counts", bins), ("volatility_seed_results", by_bin),
                       ("paired_summary", summaries), ("weight_variance_decomposition", variance),
                       ("volatility_summary", bin_summary)):
        pd.DataFrame(rows).to_csv(OUTPUT / f"{name}.csv", index=False)
    print(pd.DataFrame(summaries).to_string(index=False))
    print(pd.DataFrame(bin_summary).to_string(index=False))


if __name__ == "__main__":
    main()
