"""Extract paired prediction errors by forecast horizon and OD channel."""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/global_weight_ablation/analysis"
horizon_rows, channel_rows = [], []
for dataset in ("abilene", "geant"):
    for seed in range(42, 50):
        paths = {
            "global": ROOT / f"results/global_weight_ablation/{dataset}/dlinear_scale_global_seed{seed}/predictions.npz",
            "adaptive": ROOT / f"results/{dataset}/dlinear_scale_seed{seed}/predictions.npz",
        }
        errors = {}
        targets = None
        for model, path in paths.items():
            with np.load(path) as data:
                prediction, truth = data["prediction"], data["truth"]
                if targets is not None:
                    assert np.allclose(truth, targets)
                targets = truth
                errors[model] = (prediction - truth) ** 2
        g, a = errors["global"], errors["adaptive"]
        assert g.shape == a.shape and g.shape[1] == 24
        gh, ah = g.mean(axis=(0, 2)), a.mean(axis=(0, 2))
        for h, (gv, av) in enumerate(zip(gh, ah), 1):
            horizon_rows.append({"dataset": dataset, "seed": seed, "horizon": h,
                                 "global_mse": float(gv), "adaptive_mse": float(av),
                                 "difference": float(gv - av),
                                 "reduction_pct": float(100 * (gv - av) / gv)})
        gc, ac = g.mean(axis=(0, 1)), a.mean(axis=(0, 1))
        for c, (gv, av) in enumerate(zip(gc, ac)):
            channel_rows.append({"dataset": dataset, "seed": seed, "channel": c,
                                 "global_mse": float(gv), "adaptive_mse": float(av),
                                 "difference": float(gv - av),
                                 "reduction_pct": float(100 * (gv - av) / gv) if gv > 0 else np.nan})
pd.DataFrame(horizon_rows).to_csv(OUT / "horizon_paired_errors.csv", index=False)
pd.DataFrame(channel_rows).to_csv(OUT / "channel_paired_errors.csv", index=False)
h = pd.DataFrame(horizon_rows)
c = pd.DataFrame(channel_rows)
print("HORIZON")
print(h.groupby("dataset").agg(
    n_horizons=("horizon", "nunique"),
    positive_seed_horizons=("difference", lambda x: float((x > 0).mean())),
    min_mean_horizon_gain=("difference", lambda x: float(x.groupby(h.loc[x.index, "horizon"]).mean().min())),
).to_string())
print("CHANNEL")
print(c.groupby("dataset").agg(
    n_channels=("channel", "nunique"),
    positive_seed_channels=("difference", lambda x: float((x > 0).mean())),
).to_string())
