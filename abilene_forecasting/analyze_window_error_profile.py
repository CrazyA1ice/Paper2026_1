"""Explore window-level error characteristics of learned-global and adaptive routing."""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/global_weight_ablation/analysis/window_error_profile.csv"
rows = []
window_rows = []
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
                prediction = data["prediction"]
                truth = data["truth"]
                if targets is not None:
                    assert np.allclose(truth, targets)
                targets = truth
                errors[model] = ((prediction - truth) ** 2).mean(axis=(1, 2))
        g, a = errors["global"], errors["adaptive"]
        assert len(g) == len(a)
        window_rows.extend(
            {"dataset": dataset, "seed": seed, "window": i,
             "global_window_mse": float(gv), "adaptive_window_mse": float(av),
             "mse_difference": float(gv - av)}
            for i, (gv, av) in enumerate(zip(g, a))
        )
        for measure, selector in (
            ("mean", lambda x: x.mean()),
            ("median", lambda x: np.median(x)),
            ("q75", lambda x: np.quantile(x, .75)),
            ("q90", lambda x: np.quantile(x, .90)),
            ("q95", lambda x: np.quantile(x, .95)),
            ("top10_mean", lambda x: np.sort(x)[-int(np.ceil(.1 * len(x))):].mean()),
        ):
            gv, av = float(selector(g)), float(selector(a))
            rows.append({"dataset": dataset, "seed": seed, "n_windows": len(g),
                         "measure": measure, "global": gv, "adaptive": av,
                         "reduction_pct": 100 * (gv - av) / gv,
                         "window_win_fraction": float((a < g).mean())})
pd.DataFrame(rows).to_csv(OUT, index=False)
pd.DataFrame(window_rows).to_csv(OUT.with_name("window_error_differences.csv"), index=False)
summary = pd.DataFrame(rows).groupby(["dataset", "measure"]).agg(
    mean_reduction=("reduction_pct", "mean"),
    min_reduction=("reduction_pct", "min"),
    wins=("reduction_pct", lambda x: int((x > 0).sum())),
    mean_window_win_fraction=("window_win_fraction", "mean"),
).reset_index()
print(summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
