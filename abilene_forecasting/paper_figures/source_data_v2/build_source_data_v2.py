from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUT = Path(__file__).resolve().parent
CORE = RESULTS / "core_v2_summary.csv"

CORE_MODELS = ["dlinear", "dlinear_scale_static", "dlinear_scale"]
EXTERNAL_MODELS = ["dlinear", "lightts", "dlinear_scale"]
CORE_SEEDS = list(range(42, 50))
EXTERNAL_SEEDS = [42, 43, 44]

LABELS = {
    "dlinear": "DLinear",
    "dlinear_scale_static": "FixedEqualMultiscale",
    "dlinear_scale": "AdaptiveMultiscale",
    "lightts": "LightTS",
}

def require_seed_coverage(df, dataset, model, seeds):
    got = sorted(df.loc[(df.dataset == dataset) & (df.model == model), "seed"].tolist())
    missing = sorted(set(seeds) - set(got))
    if missing:
        raise RuntimeError(f"{dataset}/{model} missing seeds: {missing}")

def summarize(df):
    return (
        df.groupby(["dataset", "model"], as_index=False)
        .agg(
            mse_mean=("mse", "mean"),
            mse_std=("mse", "std"),
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
            rmse_mean=("rmse", "mean"),
            rmse_std=("rmse", "std"),
            parameters=("parameters", "first"),
            n_seeds=("seed", "count"),
        )
    )

def main():
    df = pd.read_csv(CORE)

    for dataset in ["abilene", "geant"]:
        for model in CORE_MODELS:
            require_seed_coverage(df, dataset, model, CORE_SEEDS)
        for model in EXTERNAL_MODELS:
            require_seed_coverage(df, dataset, model, EXTERNAL_SEEDS)

    table1 = pd.DataFrame([
        {
            "dataset": "abilene",
            "source": "CESNET TS-Zoo",
            "aggregation": "1_hour",
            "feature": "matrix_avg_realOD",
            "timepoints": 4656,
            "raw_channels": 144,
            "active_channels": 144,
            "train_rows": 2793,
            "val_rows": 931,
            "test_rows": 932,
            "train_windows": 2674,
            "val_windows": 812,
            "test_windows": 813,
            "input_len": 96,
            "pred_len": 24,
        },
        {
            "dataset": "geant",
            "source": "CESNET TS-Zoo",
            "aggregation": "1_hour",
            "feature": "matrix_avg_bandwidth_kbps",
            "timepoints": 2849,
            "raw_channels": 529,
            "active_channels": 524,
            "train_rows": 1709,
            "val_rows": 570,
            "test_rows": 570,
            "train_windows": 1590,
            "val_windows": 451,
            "test_windows": 451,
            "input_len": 96,
            "pred_len": 24,
        },
    ])
    table1.to_csv(OUT / "table1_datasets.csv", index=False)

    common = df[df.seed.isin(EXTERNAL_SEEDS) & df.model.isin(EXTERNAL_MODELS)].copy()
    t2 = summarize(common)
    t2["model_label"] = t2.model.map(LABELS)
    t2["seed_start"] = 42
    t2["seed_end"] = 44
    order = {"dlinear": 0, "lightts": 1, "dlinear_scale": 2}
    t2["_order"] = t2.model.map(order)
    t2 = t2.sort_values(["dataset", "_order"]).drop(columns="_order")
    t2 = t2[
        ["dataset", "model", "model_label", "seed_start", "seed_end", "n_seeds",
         "parameters", "mse_mean", "mse_std", "mae_mean", "mae_std",
         "rmse_mean", "rmse_std"]
    ]
    t2.to_csv(OUT / "table2_external_baseline_3seeds.csv", index=False)

    core = df[df.seed.isin(CORE_SEEDS) & df.model.isin(CORE_MODELS)].copy()
    t3 = summarize(core)
    t3["model_label"] = t3.model.map(LABELS)
    for col in [
        "mse_improve_vs_dlinear_pct", "mae_improve_vs_dlinear_pct",
        "mse_improve_vs_fixed_pct", "mae_improve_vs_fixed_pct",
    ]:
        t3[col] = pd.NA

    for dataset in ["abilene", "geant"]:
        d = t3[t3.dataset == dataset].set_index("model")
        idx = t3.index[(t3.dataset == dataset) & (t3.model == "dlinear_scale")][0]
        t3.loc[idx, "mse_improve_vs_dlinear_pct"] = (
            (d.loc["dlinear", "mse_mean"] - d.loc["dlinear_scale", "mse_mean"])
            / d.loc["dlinear", "mse_mean"] * 100
        )
        t3.loc[idx, "mae_improve_vs_dlinear_pct"] = (
            (d.loc["dlinear", "mae_mean"] - d.loc["dlinear_scale", "mae_mean"])
            / d.loc["dlinear", "mae_mean"] * 100
        )
        t3.loc[idx, "mse_improve_vs_fixed_pct"] = (
            (d.loc["dlinear_scale_static", "mse_mean"] - d.loc["dlinear_scale", "mse_mean"])
            / d.loc["dlinear_scale_static", "mse_mean"] * 100
        )
        t3.loc[idx, "mae_improve_vs_fixed_pct"] = (
            (d.loc["dlinear_scale_static", "mae_mean"] - d.loc["dlinear_scale", "mae_mean"])
            / d.loc["dlinear_scale_static", "mae_mean"] * 100
        )

    order = {"dlinear": 0, "dlinear_scale_static": 1, "dlinear_scale": 2}
    t3["_order"] = t3.model.map(order)
    t3 = t3.sort_values(["dataset", "_order"]).drop(columns="_order")
    t3 = t3[
        ["dataset", "model", "model_label", "n_seeds", "parameters",
         "mse_mean", "mse_std", "mae_mean", "mae_std", "rmse_mean", "rmse_std",
         "mse_improve_vs_dlinear_pct", "mae_improve_vs_dlinear_pct",
         "mse_improve_vs_fixed_pct", "mae_improve_vs_fixed_pct"]
    ]
    t3.to_csv(OUT / "table3_core_8seeds.csv", index=False)

    rows = []
    for dataset in ["abilene", "geant"]:
        for seed in CORE_SEEDS:
            fixed = df[(df.dataset == dataset) & (df.seed == seed) & (df.model == "dlinear_scale_static")].iloc[0]
            adaptive = df[(df.dataset == dataset) & (df.seed == seed) & (df.model == "dlinear_scale")].iloc[0]
            rows.append({
                "dataset": dataset,
                "seed": seed,
                "fixed_mse": fixed.mse,
                "adaptive_mse": adaptive.mse,
                "mse_delta_adaptive_minus_fixed": adaptive.mse - fixed.mse,
                "mse_improve_pct": (fixed.mse - adaptive.mse) / fixed.mse * 100,
                "fixed_mae": fixed.mae,
                "adaptive_mae": adaptive.mae,
                "mae_delta_adaptive_minus_fixed": adaptive.mae - fixed.mae,
                "mae_improve_pct": (fixed.mae - adaptive.mae) / fixed.mae * 100,
                "fixed_rmse": fixed.rmse,
                "adaptive_rmse": adaptive.rmse,
            })
    pd.DataFrame(rows).to_csv(OUT / "fig2_weight_pairing_8seeds.csv", index=False)

if __name__ == "__main__":
    main()
