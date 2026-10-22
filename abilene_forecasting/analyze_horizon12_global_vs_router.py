"""Summarize the paired H=12 global-weight versus adaptive-router experiment."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import t


ROOT = Path(__file__).resolve().parent
DATASETS = ("abilene", "geant")
SEEDS = range(42, 50)
MODELS = ("dlinear_scale_global", "dlinear_scale")


def load_run(results: Path, dataset: str, model: str, seed: int):
    run_dir = results / dataset / f"{model}_seed{seed}"
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    expected = {
        "dataset": dataset,
        "model": model,
        "seed": seed,
        "input_len": 96,
        "pred_len": 12,
        "batch_size": 16,
        "epochs_max": 30,
        "patience": 6,
        "learning_rate": 0.001,
        "cut_ratio": 0.5,
    }
    for key, value in expected.items():
        if metrics.get(key) != value:
            raise ValueError(f"{run_dir}: {key} is {metrics.get(key)!r}, expected {value!r}")
    with np.load(run_dir / "predictions.npz") as arrays:
        prediction, truth = arrays["prediction"], arrays["truth"]
    if prediction.shape != truth.shape or prediction.shape[1] != 12:
        raise ValueError(f"{run_dir}: unexpected prediction shape {prediction.shape}")
    return metrics, truth


def confidence_interval(values: np.ndarray):
    mean = float(values.mean())
    half_width = float(t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return mean, mean - half_width, mean + half_width


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results", type=Path,
        default=ROOT / "results" / "horizon12_global_vs_router",
    )
    args = parser.parse_args()
    results = args.results.resolve()

    paired = []
    for dataset in DATASETS:
        for seed in SEEDS:
            global_metrics, global_truth = load_run(results, dataset, MODELS[0], seed)
            router_metrics, router_truth = load_run(results, dataset, MODELS[1], seed)
            if global_truth.shape != router_truth.shape or not np.allclose(global_truth, router_truth):
                raise ValueError(f"{dataset} seed={seed}: test targets differ between models")
            row = {"dataset": dataset, "seed": seed, "input_len": 96, "pred_len": 12}
            for metric in ("mse", "mae", "rmse"):
                global_value = global_metrics["test_normalized"][metric]
                router_value = router_metrics["test_normalized"][metric]
                row[f"global_{metric}"] = global_value
                row[f"router_{metric}"] = router_value
                row[f"{metric}_difference"] = global_value - router_value
                row[f"{metric}_reduction_pct"] = 100 * (global_value - router_value) / global_value
            paired.append(row)

    summary = []
    for dataset in DATASETS:
        rows = [row for row in paired if row["dataset"] == dataset]
        for metric in ("mse", "mae", "rmse"):
            difference = np.asarray([row[f"{metric}_difference"] for row in rows])
            reduction = np.asarray([row[f"{metric}_reduction_pct"] for row in rows])
            mean_difference, diff_low, diff_high = confidence_interval(difference)
            mean_reduction, pct_low, pct_high = confidence_interval(reduction)
            summary.append({
                "dataset": dataset,
                "metric": metric,
                "n_seeds": len(rows),
                "global_mean": float(np.mean([row[f"global_{metric}"] for row in rows])),
                "router_mean": float(np.mean([row[f"router_{metric}"] for row in rows])),
                "mean_difference": mean_difference,
                "difference_ci95_low": diff_low,
                "difference_ci95_high": diff_high,
                "mean_seedwise_reduction_pct": mean_reduction,
                "reduction_ci95_low": pct_low,
                "reduction_ci95_high": pct_high,
                "router_wins": int((difference > 0).sum()),
            })

    analysis = results / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    write_csv(analysis / "paired_seed_results.csv", paired)
    write_csv(analysis / "paired_summary.csv", summary)
    print(f"Validated {len(paired) * 2} H=12 runs. Results: {analysis}")
    for row in summary:
        if row["metric"] == "mse":
            print(f"{row['dataset']}: mean seed-wise MSE reduction "
                  f"{row['mean_seedwise_reduction_pct']:.2f}% "
                  f"(95% CI {row['reduction_ci95_low']:.2f}% to "
                  f"{row['reduction_ci95_high']:.2f}%), wins {row['router_wins']}/8")


if __name__ == "__main__":
    main()
