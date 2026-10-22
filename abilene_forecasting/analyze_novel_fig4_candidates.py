"""Audit unused H=24 prediction slices for potential Figure 4 concepts."""

from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent / "results"
MODELS = {"DLinear": "dlinear", "FixedEqual": "dlinear_scale_static",
          "Proposed": "dlinear_scale"}
rows = []
spectral_rows = []
joint_rows = []
for dataset in ("abilene", "geant"):
    for seed in range(42, 50):
        arrays = {}
        for name, directory in MODELS.items():
            with np.load(ROOT / dataset / f"{directory}_seed{seed}" / "predictions.npz") as z:
                arrays[name] = (z["prediction"], z["truth"])
        truth = arrays["Proposed"][1]
        assert all(np.array_equal(truth, pair[1]) for pair in arrays.values())
        losses = {name: (prediction - truth) ** 2
                  for name, (prediction, _) in arrays.items()}
        window_losses = {name: loss.mean(axis=(1, 2)) for name, loss in losses.items()}
        win_dlinear = window_losses["Proposed"] < window_losses["DLinear"]
        win_equal = window_losses["Proposed"] < window_losses["FixedEqual"]
        joint_rows.append(dict(dataset=dataset, seed=seed,
                               both=100*np.mean(win_dlinear & win_equal),
                               dlinear_only=100*np.mean(win_dlinear & ~win_equal),
                               equal_only=100*np.mean(~win_dlinear & win_equal),
                               neither=100*np.mean(~win_dlinear & ~win_equal)))
        volatility = np.abs(np.diff(truth, axis=1)).mean(axis=(1, 2))
        # Bins depend on the observed targets, identically for every model.
        vol_bin = np.digitize(volatility, np.quantile(volatility, [.25, .5, .75]))
        channel_q90 = np.quantile(truth, .9, axis=(0, 1))
        high_target = truth >= channel_q90[None, None, :]
        for baseline in ("DLinear", "FixedEqual"):
            left, right = window_losses[baseline], window_losses["Proposed"]
            rows.append(dict(dataset=dataset, seed=seed, baseline=baseline,
                             slice="all_windows", n=len(left),
                             baseline_mse=left.mean(), proposed_mse=right.mean(),
                             improvement=100*(left.mean()-right.mean())/left.mean(),
                             window_win_pct=100*np.mean(right < left),
                             p90_ratio=np.quantile(right, .9)/np.quantile(left, .9)))
            for group in range(4):
                mask = vol_bin == group
                lb, rb = left[mask], right[mask]
                rows.append(dict(dataset=dataset, seed=seed, baseline=baseline,
                                 slice=f"target_vol_Q{group+1}", n=mask.sum(),
                                 baseline_mse=lb.mean(), proposed_mse=rb.mean(),
                                 improvement=100*(lb.mean()-rb.mean())/lb.mean(),
                                 window_win_pct=100*np.mean(rb < lb),
                                 p90_ratio=np.quantile(rb, .9)/np.quantile(lb, .9)))
            for label, mask in (("target_top10pct", high_target),
                                ("target_other90pct", ~high_target)):
                lb, rb = losses[baseline][mask].mean(), losses["Proposed"][mask].mean()
                rows.append(dict(dataset=dataset, seed=seed, baseline=baseline,
                                 slice=label, n=mask.sum(), baseline_mse=lb,
                                 proposed_mse=rb, improvement=100*(lb-rb)/lb))
            # Parseval-consistent temporal error-energy decomposition over H=24.
            spectra = {}
            for name in (baseline, "Proposed"):
                error = arrays[name][0] - truth
                ft = np.fft.rfft(error, axis=1)
                energy = np.abs(ft) ** 2
                energy[:, 1:-1] *= 2
                spectra[name] = energy.mean(axis=(0, 2))
            for label, bins in (("low_k0_2", slice(0, 3)),
                                ("mid_k3_6", slice(3, 7)),
                                ("high_k7_12", slice(7, 13))):
                lb = spectra[baseline][bins].sum()
                rb = spectra["Proposed"][bins].sum()
                spectral_rows.append(dict(dataset=dataset, seed=seed, baseline=baseline,
                                          band=label, baseline_energy=lb,
                                          proposed_energy=rb,
                                          improvement=100*(lb-rb)/lb))

out = pd.DataFrame(rows)
dest = Path(__file__).resolve().parent.parent / "paper_figures" / "fig4_novel_audit"
dest.mkdir(exist_ok=True)
out.to_csv(dest / "candidate_metrics.csv", index=False)
summary = out.groupby(["dataset", "baseline", "slice"]).agg(
    n=("n", "mean"), improvement_mean=("improvement", "mean"),
    improvement_min=("improvement", "min"),
    improvement_max=("improvement", "max"),
    positive_seeds=("improvement", lambda x: int((x > 0).sum())),
    window_win_pct=("window_win_pct", "mean"), p90_ratio=("p90_ratio", "mean"),
).reset_index()
summary.to_csv(dest / "candidate_summary.csv", index=False)
print(summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
spectral = pd.DataFrame(spectral_rows)
spectral.to_csv(dest / "spectral_metrics.csv", index=False)
spectral_summary = spectral.groupby(["dataset", "baseline", "band"]).agg(
    mean=("improvement", "mean"), minimum=("improvement", "min"),
    maximum=("improvement", "max"),
    positive_seeds=("improvement", lambda x: int((x > 0).sum())),
).reset_index()
spectral_summary.to_csv(dest / "spectral_summary.csv", index=False)
print("\nTEMPORAL ERROR SPECTRUM")
print(spectral_summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
joint = pd.DataFrame(joint_rows)
joint.to_csv(dest / "window_joint_outcomes.csv", index=False)
print("\nWINDOW JOINT OUTCOMES")
print(joint.groupby("dataset").agg(["mean", "min", "max"]).to_string(float_format=lambda x: f"{x:.2f}"))
