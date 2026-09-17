from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parent


def load_runs(directory: Path, label: str) -> pd.DataFrame:
    rows = []
    for path in directory.glob("*/metrics.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "experiment": label,
                "model": record["model"],
                "seed": record["seed"],
                "cut_ratio": record["cut_ratio"],
                "mse": record["test_normalized"]["mse"],
                "mae": record["test_normalized"]["mae"],
                "rmse": record["test_normalized"]["rmse"],
                "parameters": record["parameters"],
                "seconds": record["elapsed_seconds"],
            }
        )
    return pd.DataFrame(rows)


def paired_comparison(frame: pd.DataFrame, better: str, reference: str) -> dict:
    indexed = frame.pivot(index="seed", columns="model", values="mse")
    better_values = indexed[better].to_numpy()
    reference_values = indexed[reference].to_numpy()
    differences = reference_values - better_values
    test = stats.ttest_rel(reference_values, better_values)
    sem = stats.sem(differences)
    interval = stats.t.interval(0.95, len(differences) - 1, loc=differences.mean(), scale=sem)
    return {
        "comparison": f"{better} vs {reference}",
        "n_paired_seeds": len(differences),
        "better_mse_mean": better_values.mean(),
        "reference_mse_mean": reference_values.mean(),
        "relative_mse_reduction_percent": 100 * differences.mean() / reference_values.mean(),
        "mean_paired_difference": differences.mean(),
        "ci95_low": interval[0],
        "ci95_high": interval[1],
        "paired_t": test.statistic,
        "p_value_uncorrected": test.pvalue,
        "cohen_dz": differences.mean() / differences.std(ddof=1),
    }


def main() -> None:
    frequency_frames = []
    for ratio_tag in ("025", "050", "075"):
        directory = ROOT / "results" / "frequency_sensitivity" / f"cut_{ratio_tag}"
        frequency_frames.append(load_runs(directory, f"frequency_cut_{ratio_tag}"))
    frequency = pd.concat(frequency_frames, ignore_index=True)
    weights = load_runs(ROOT / "results" / "weight_ablation", "weight_ablation")
    final_static = load_runs(
        ROOT / "results" / "final_cut075_weight_ablation", "final_cut075_weight_ablation"
    )
    final_adaptive = frequency[
        (frequency["model"] == "proposed") & (frequency["cut_ratio"] == 0.75)
    ].copy()
    final_adaptive["model"] = "proposed_adaptive"
    final_weights = pd.concat([final_static, final_adaptive], ignore_index=True)

    if len(frequency) != 18 or len(weights) != 12:
        raise SystemExit(
            f"Expected 18 frequency and 12 weight runs, got {len(frequency)} and {len(weights)}"
        )
    if not (frequency.groupby(["model", "cut_ratio"])["seed"].nunique() == 3).all():
        raise SystemExit("Frequency experiment has an incomplete seed group")
    if not (weights.groupby("model")["seed"].nunique() == 3).all():
        raise SystemExit("Weight experiment has an incomplete seed group")
    if len(final_weights) != 6 or not (
        final_weights.groupby("model")["seed"].nunique() == 3
    ).all():
        raise SystemExit("Final cut_ratio=0.75 comparison has an incomplete seed group")

    frequency_summary = frequency.groupby(["model", "cut_ratio"], as_index=False).agg(
        mse_mean=("mse", "mean"), mse_std=("mse", "std"),
        mae_mean=("mae", "mean"), mae_std=("mae", "std"),
        seconds_mean=("seconds", "mean"),
    )
    weight_summary = weights.groupby("model", as_index=False).agg(
        mse_mean=("mse", "mean"), mse_std=("mse", "std"),
        mae_mean=("mae", "mean"), mae_std=("mae", "std"),
        seconds_mean=("seconds", "mean"),
    )
    comparisons = pd.DataFrame(
        [
            paired_comparison(weights, "dlinear_scale", "dlinear_scale_static"),
            paired_comparison(weights, "proposed", "proposed_static"),
        ]
    )
    # Two prespecified weight comparisons: Holm adjustment.
    order = comparisons["p_value_uncorrected"].sort_values().index
    adjusted = np.empty(len(comparisons))
    running = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, comparisons.loc[index, "p_value_uncorrected"] * (len(comparisons) - rank))
        running = max(running, value)
        adjusted[index] = running
    comparisons["p_value_holm"] = adjusted
    final_comparison = pd.DataFrame(
        [paired_comparison(final_weights, "proposed_adaptive", "proposed_static")]
    )

    output = ROOT / "results" / "recommended_analysis"
    output.mkdir(parents=True, exist_ok=True)
    frequency.to_csv(output / "frequency_all_runs.csv", index=False)
    frequency_summary.to_csv(output / "frequency_mean_std.csv", index=False)
    weights.to_csv(output / "weight_all_runs.csv", index=False)
    weight_summary.to_csv(output / "weight_mean_std.csv", index=False)
    comparisons.to_csv(output / "paired_tests.csv", index=False)
    final_weights.to_csv(output / "final_cut075_all_runs.csv", index=False)
    final_comparison.to_csv(output / "final_cut075_paired_test.csv", index=False)

    print("Frequency sensitivity")
    print(frequency_summary.to_string(index=False))
    print("\nWeight ablation")
    print(weight_summary.to_string(index=False))
    print("\nPaired tests")
    print(comparisons.to_string(index=False))
    print("\nFinal cut_ratio=0.75 paired test")
    print(final_comparison.to_string(index=False))


if __name__ == "__main__":
    main()
