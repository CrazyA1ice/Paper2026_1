from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from src.data import SlidingWindowDataset, inverse_traffic_transform, load_npz
from src.models import build_model


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def unpack_prediction(output):
    return output[0] if isinstance(output, tuple) else output


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    predictions, truths, router_weights = [], [], []
    for history, future in loader:
        history, future = history.to(device), future.to(device)
        output = model(history)
        prediction = unpack_prediction(output)
        total_loss += criterion(prediction, future).item() * len(history)
        predictions.append(prediction.cpu().numpy())
        truths.append(future.cpu().numpy())
        if isinstance(output, tuple):
            router_weights.append(output[1].cpu().numpy())
    weights = np.concatenate(router_weights) if router_weights else None
    return (
        total_loss / len(loader.dataset),
        np.concatenate(predictions),
        np.concatenate(truths),
        weights,
    )


def metrics(prediction: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    error = prediction - truth
    return {
        "mse": float(np.mean(error**2)),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=[
            "dlinear", "fits", "dlinear_freq", "dlinear_scale",
            "dlinear_scale_static", "proposed", "proposed_static",
        ],
        default="dlinear",
    )
    parser.add_argument("--data", default="data/processed/abilene_1hour.npz")
    parser.add_argument("--input-len", type=int, default=96)
    parser.add_argument("--pred-len", type=int, default=24)
    parser.add_argument("--cut-ratio", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=6)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-root", default="results")
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    arrays = load_npz(args.data)
    datasets = {
        split: SlidingWindowDataset(arrays[split], args.input_len, args.pred_len)
        for split in ("train", "val", "test")
    }
    loaders = {
        "train": DataLoader(
            datasets["train"], batch_size=args.batch_size, shuffle=True,
            num_workers=0, pin_memory=device.type == "cuda",
        ),
        "val": DataLoader(datasets["val"], batch_size=args.batch_size, num_workers=0),
        "test": DataLoader(datasets["test"], batch_size=args.batch_size, num_workers=0),
    }

    model = build_model(args.model, args.input_len, args.pred_len, args.cut_ratio).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    criterion = nn.MSELoss()
    run_dir = Path(args.output_root) / f"{args.model}_seed{args.seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = run_dir / "best_model.pt"

    best_val = float("inf")
    stale_epochs = 0
    started = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        for history, future in loaders["train"]:
            history, future = history.to(device), future.to(device)
            optimizer.zero_grad(set_to_none=True)
            prediction = unpack_prediction(model(history))
            loss = criterion(prediction, future)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(history)

        val_loss, _, _, _ = evaluate(model, loaders["val"], criterion, device)
        train_loss /= len(datasets["train"])
        print(f"epoch={epoch:03d} train_mse={train_loss:.6f} val_mse={val_loss:.6f}")
        if val_loss < best_val - 1e-7:
            best_val = val_loss
            stale_epochs = 0
            torch.save(model.state_dict(), checkpoint)
        else:
            stale_epochs += 1
            if stale_epochs >= args.patience:
                print(f"Early stopping at epoch {epoch}")
                break

    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    _, prediction, truth, weights = evaluate(model, loaders["test"], criterion, device)
    normalized_metrics = metrics(prediction, truth)
    raw_prediction = inverse_traffic_transform(prediction, arrays["mean"], arrays["std"])
    raw_truth = inverse_traffic_transform(truth, arrays["mean"], arrays["std"])
    raw_metrics = metrics(raw_prediction, raw_truth)
    elapsed = time.perf_counter() - started

    result = {
        "model": args.model,
        "seed": args.seed,
        "device": str(device),
        "input_len": args.input_len,
        "pred_len": args.pred_len,
        "cut_ratio": args.cut_ratio,
        "parameters": sum(p.numel() for p in model.parameters()),
        "best_val_mse_normalized": best_val,
        "test_normalized": normalized_metrics,
        "test_original_units": raw_metrics,
        "elapsed_seconds": elapsed,
    }
    (run_dir / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    np.savez_compressed(run_dir / "predictions.npz", prediction=prediction, truth=truth)
    if weights is not None:
        np.savetxt(run_dir / "router_weights.csv", weights, delimiter=",")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
