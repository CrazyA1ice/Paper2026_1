"""Measure the test-time contribution of assigning router weights to windows."""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import torch
from scipy.stats import t
from torch.utils.data import DataLoader

from src.data import SlidingWindowDataset
from src.models import build_model


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "router_window_assignment_audit"
SEEDS = range(42, 50)
PERMUTATIONS = 100


def run(dataset, seed, values, training, device):
    folder = ROOT / "results" / dataset / f"dlinear_scale_seed{seed}"
    model = build_model("dlinear_scale", 96, 24).to(device)
    model.load_state_dict(torch.load(folder / "best_model.pt", map_location=device,
                                     weights_only=True))
    model.eval()
    loader = DataLoader(SlidingWindowDataset(values, 96, 24), batch_size=16)
    gram, actual_weights, predictions = [], [], []
    with torch.no_grad():
        for history, future in loader:
            history, future = history.to(device), future.to(device)
            experts = torch.stack([
                expert(model._downsample(history, scale))
                for scale, expert in zip(model.scales, model.experts)
            ], dim=1)
            weights = model.router(history)
            residual = experts - future[:, None]
            q = torch.einsum("bshc,bthc->bst", residual, residual)
            q /= future.shape[1] * future.shape[2]
            gram.append(q.cpu().numpy().astype(np.float64))
            actual_weights.append(weights.cpu().numpy().astype(np.float64))
            predictions.append((experts * weights[:, :, None, None]).sum(1).cpu().numpy())
    q = np.concatenate(gram)
    w = np.concatenate(actual_weights)
    prediction = np.concatenate(predictions)
    with np.load(folder / "predictions.npz") as saved:
        assert np.allclose(prediction, saved["prediction"], atol=2e-5)
        assert np.array_equal(saved["truth"], np.stack([
            values[i + 96:i + 120] for i in range(len(values) - 119)
        ]))
    saved_weights = np.loadtxt(folder / "router_weights.csv", delimiter=",")
    assert np.allclose(w, saved_weights, atol=1e-6)
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    train_loader = DataLoader(SlidingWindowDataset(training, 96, 24), batch_size=16)
    train_weights = []
    with torch.no_grad():
        for history, _ in train_loader:
            train_weights.append(model.router(history.to(device)).cpu().numpy())
    train_mean = np.concatenate(train_weights).mean(axis=0).astype(np.float64)

    def mse(weights):
        return float(np.einsum("bi,bij,bj->", weights, q, weights) / len(weights))

    adaptive = mse(w)
    assert abs(adaptive - metrics["test_normalized"]["mse"]) < 2e-5
    fixed = mse(np.broadcast_to(w.mean(axis=0), w.shape))
    fixed_train = mse(np.broadcast_to(train_mean, w.shape))
    rng = np.random.default_rng(1000 + seed)
    shuffled = np.array([mse(w[rng.permutation(len(w))])
                         for _ in range(PERMUTATIONS)])
    return dict(dataset=dataset, seed=seed, test_windows=len(w),
                adaptive_mse=adaptive, fixed_test_mean_mse=fixed,
                fixed_train_mean_mse=fixed_train,
                shuffled_mse_mean=float(shuffled.mean()),
                shuffled_mse_sd=float(shuffled.std(ddof=1)),
                fixed_minus_adaptive_pct=100 * (fixed-adaptive) / fixed,
                train_fixed_minus_adaptive_pct=100 * (fixed_train-adaptive) / fixed_train,
                shuffled_minus_adaptive_pct=100 * (shuffled.mean()-adaptive) / shuffled.mean(),
                **{f"weight_{s}_mean":float(w[:,i].mean()) for i,s in enumerate(model.scales)},
                **{f"weight_{s}_within_sd":float(w[:,i].std()) for i,s in enumerate(model.scales)})


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = []
    for dataset in ("abilene", "geant"):
        with np.load(ROOT / "data" / "processed" / f"{dataset}_1hour.npz") as data:
            values, training = data["test"], data["train"]
        for seed in SEEDS:
            row = run(dataset, seed, values, training, device)
            rows.append(row)
            print(dataset, seed, f"adaptive={row['adaptive_mse']:.6f}",
                  f"fixed={row['fixed_test_mean_mse']:.6f}",
                  f"train_fixed={row['fixed_train_mean_mse']:.6f}",
                  f"shuffle={row['shuffled_mse_mean']:.6f}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "paired_seed_results.csv", index=False)
    summaries = []
    for dataset, group in pd.DataFrame(rows).groupby("dataset"):
        for measure in ("fixed_minus_adaptive_pct", "train_fixed_minus_adaptive_pct",
                        "shuffled_minus_adaptive_pct"):
            values = group[measure].to_numpy()
            half = t.ppf(.975, len(values)-1) * values.std(ddof=1) / np.sqrt(len(values))
            summaries.append(dict(dataset=dataset, measure=measure,
                                  mean=float(values.mean()), ci95_low=float(values.mean()-half),
                                  ci95_high=float(values.mean()+half),
                                  positive_seeds=int((values > 0).sum())))
    pd.DataFrame(summaries).to_csv(OUT / "summary.csv", index=False)
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__ == "__main__":
    main()
