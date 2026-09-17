from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--output", default="results/ablation_summary.csv")
    args = parser.parse_args()

    rows = []
    for path in Path(args.results).glob("*/metrics.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "model": record["model"],
                "seed": record["seed"],
                "parameters": record["parameters"],
                "mse": record["test_normalized"]["mse"],
                "mae": record["test_normalized"]["mae"],
                "rmse": record["test_normalized"]["rmse"],
                "raw_rmse": record["test_original_units"]["rmse"],
                "seconds": record["elapsed_seconds"],
            }
        )
    if not rows:
        raise SystemExit("No metrics.json files found")
    frame = pd.DataFrame(rows).sort_values(["model", "seed"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    summary = frame.groupby("model").agg(
        mse_mean=("mse", "mean"), mse_std=("mse", "std"),
        mae_mean=("mae", "mean"), mae_std=("mae", "std"),
        raw_rmse_mean=("raw_rmse", "mean"), seconds_mean=("seconds", "mean"),
    )
    summary.to_csv(output.with_name("ablation_mean_std.csv"))
    print(summary)


if __name__ == "__main__":
    main()

