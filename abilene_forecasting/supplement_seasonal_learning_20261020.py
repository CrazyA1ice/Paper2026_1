"""Fixed supplementary protocol: seasonal references, training-history curves, time blocks."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from src.data import SlidingWindowDataset, load_npz
from src.models import build_model
from train import evaluate, set_seed, split_model_output

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/supplement_20261020"
DATASETS = ("abilene", "geant")
MODELS = ("dlinear", "dlinear_scale_global", "dlinear_scale")
FRACTIONS = (25, 50, 75, 100)
SEEDS = tuple(range(42, 50))
L, H, BATCH, EPOCHS, PATIENCE, LR = 96, 24, 16, 30, 6, 0.001


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived_run(dataset: str, model: str, seed: int) -> Path:
    base = ROOT / "results"
    if model == "dlinear_scale_global":
        base /= "global_weight_ablation"
    return base / dataset / f"{model}_seed{seed}"


def fractional_arrays(arrays, percent):
    """Fit each suffix's normalizer, preserving the common OD universe and test periods."""
    if percent == 100:
        return arrays, dict(train_start=0, train_rows=len(arrays["train"]),
                            mean=arrays["mean"], std=arrays["std"], constant_channels=0)
    n = len(arrays["train"]) * percent // 100
    start = len(arrays["train"]) - n
    ref_mean, ref_std = arrays["mean"].astype(np.float64), arrays["std"].astype(np.float64)
    logged_train = arrays["train"][start:].astype(np.float64) * ref_std + ref_mean
    mean, std = logged_train.mean(axis=0), logged_train.std(axis=0)
    constant = std < 1e-8
    std[constant] = 1.0
    transformed = {}
    for split in ("train", "val", "test"):
        x = arrays[split][start:] if split == "train" else arrays[split]
        logged = x.astype(np.float64) * ref_std + ref_mean
        transformed[split] = ((logged - mean) / std).astype(np.float32)
    return transformed, dict(train_start=start, train_rows=n, mean=mean, std=std,
                             constant_channels=int(constant.sum()))


def time_blocks(test_rows):
    # Partition target timestamps. No forecast target is allowed to cross a boundary.
    edges = np.linspace(L, test_rows, 4, dtype=int)
    origins = np.arange(L, test_rows-H+1)
    return [dict(block=f"T{i+1}", start=int(edges[i]), end=int(edges[i+1]),
                 mask=(origins >= edges[i]) & (origins+H <= edges[i+1])) for i in range(3)]


def score(prediction, truth):
    error = prediction.astype(np.float64) - truth.astype(np.float64)
    mse = float(np.mean(error*error))
    return dict(mse=mse, mae=float(np.mean(np.abs(error))), rmse=math.sqrt(mse))


def protocol():
    p = dict(version="supplement-20261020-v1", datasets=DATASETS, models=MODELS,
             training_percentages=FRACTIONS, seeds=SEEDS, input_len=L, pred_len=H,
             batch_size=BATCH, epochs_max=EPOCHS, patience=PATIENCE, learning_rate=LR,
             data_design="nested most-recent training suffixes; validation/test dates fixed",
             scaling="fit suffix-only normalizers; report all errors in original full-training reference coordinates",
             channels="original task's OD universe held fixed across history fractions",
             temporal_design="three equal chronological target-time blocks in original holdout; fixed trained model, no retraining per block",
             seasonal_design="lag-24 and lag-168 references on common origins >=168 inside test; learned models use 96-hour history, weekly reference uses 168 hours",
             statistical_unit="eight paired training seeds; time blocks descriptive; no iid-window hypothesis tests",
             limitations=["post-rejection supplementary analysis, not preregistered",
                          "training-history size changes both amount and age coverage",
                          "fixed epochs/early stopping do not equate optimizer update counts",
                          "time blocks are from the same two networks and are not independent networks"],
             source_files={ds:sha256(ROOT/f"data/processed/{ds}_1hour.npz") for ds in DATASETS},
             model_source_sha256=sha256(ROOT/"src/models.py"),
             training_source_sha256=sha256(ROOT/"train.py"))
    OUT.mkdir(exist_ok=True)
    path=OUT/"protocol.json"
    if path.exists():
        assert json.loads(path.read_text(encoding="utf8")) == json.loads(json.dumps(p)), "Existing protocol differs"
    else:
        path.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf8")
    return p


def seasonal_references(dataset, arrays):
    test=arrays["test"]
    origins=np.arange(168,len(test)-H+1)
    targets=origins[:,None]+np.arange(H)[None,:]
    truth=test[targets]
    rows=[]
    for lag in (24,168):
        prediction=test[targets-lag]
        assert np.all(targets-lag < origins[:,None])
        rows.append(dict(dataset=dataset, model=f"seasonal_{lag}", history_hours=lag,
                         windows=len(origins), **score(prediction,truth)))
    folder=OUT/dataset;folder.mkdir(exist_ok=True)
    (folder/"seasonal.json").write_text(json.dumps(rows,indent=2),encoding="utf8")
    return rows


def run_one(dataset, model_name, percent, seed, arrays, device):
    folder=OUT/dataset/f"history_{percent:03d}"/f"{model_name}_seed{seed}"
    completed=folder/"metrics.json"
    if completed.exists():
        r=json.loads(completed.read_text(encoding="utf8"))
        assert (r["dataset"],r["model"],r["train_percent"],r["seed"]) == (dataset,model_name,percent,seed)
        return r, True
    folder.mkdir(parents=True,exist_ok=True)
    transformed,meta=fractional_arrays(arrays,percent)
    sets={s:SlidingWindowDataset(transformed[s],L,H) for s in ("train","val","test")}
    set_seed(seed)
    loaders={s:DataLoader(sets[s],batch_size=BATCH,shuffle=s=="train",num_workers=0,
                         pin_memory=s=="train" and device.type=="cuda") for s in sets}
    model=build_model(model_name,L,H,n_channels=arrays["train"].shape[1],device=device).to(device)
    criterion=nn.MSELoss()
    history=[]
    started=time.perf_counter()
    checkpoint=folder/"best_model.pt"
    if percent==100:
        archive=archived_run(dataset,model_name,seed)
        old=json.loads((archive/"metrics.json").read_text(encoding="utf8"))
        assert (old["input_len"],old["pred_len"],old["batch_size"],old["epochs_max"],old["patience"],old["learning_rate"]) == (L,H,BATCH,EPOCHS,PATIENCE,LR)
        checkpoint=archive/"best_model.pt"
        source="archived_full_training_checkpoint"
    else:
        optimizer=torch.optim.Adam(model.parameters(),lr=LR)
        best_val=float("inf");stale=0
        for epoch in range(1,EPOCHS+1):
            model.train();total=0.0
            for x,y in loaders["train"]:
                x,y=x.to(device),y.to(device)
                optimizer.zero_grad(set_to_none=True)
                prediction,_=split_model_output(model(x))
                loss=criterion(prediction,y);loss.backward();optimizer.step()
                total+=loss.item()*len(x)
            val,_,_,_=evaluate(model,loaders["val"],criterion,device)
            history.append(dict(epoch=epoch,train_mse=total/len(sets["train"]),val_mse=val))
            if val < best_val-1e-7:
                best_val=val;stale=0;torch.save(model.state_dict(),checkpoint)
            else:
                stale+=1
                if stale>=PATIENCE:break
        source="new_training"
    model.load_state_dict(torch.load(checkpoint,map_location=device,weights_only=True))
    _,prediction,_,_=evaluate(model,loaders["test"],criterion,device)
    if percent!=100:
        prediction=((prediction.astype(np.float64)*meta["std"]+meta["mean"]-arrays["mean"])/arrays["std"]).astype(np.float32)
    reference_set=SlidingWindowDataset(arrays["test"],L,H)
    truth=np.stack([reference_set[i][1].numpy() for i in range(len(reference_set))])
    if percent==100:
        stored=np.load(archived_run(dataset,model_name,seed)/"predictions.npz")
        assert np.array_equal(truth,stored["truth"])
        assert np.allclose(prediction,stored["prediction"],atol=2e-5,rtol=2e-5), "Checkpoint predictions differ from archive"
    err=prediction.astype(np.float64)-truth.astype(np.float64)
    window_mse=np.mean(err**2,axis=(1,2));window_mae=np.mean(np.abs(err),axis=(1,2))
    blocks=[]
    for b in time_blocks(len(arrays["test"])):
        blocks.append(dict(block=b["block"],target_start=b["start"],target_end_exclusive=b["end"],
                           windows=int(b["mask"].sum()),**score(prediction[b["mask"]],truth[b["mask"]])))
    common=slice(168-L,None)
    result=dict(dataset=dataset,model=model_name,train_percent=percent,seed=seed,
                train_start=meta["train_start"],train_rows=meta["train_rows"],train_windows=len(sets["train"]),
                val_rows=len(arrays["val"]),test_rows=len(arrays["test"]),
                n_channels=arrays["test"].shape[1],constant_channels_in_suffix=meta["constant_channels"],
                config=dict(input_len=L,pred_len=H,batch_size=BATCH,epochs_max=EPOCHS,patience=PATIENCE,learning_rate=LR),
                source=source,checkpoint=str(checkpoint.relative_to(ROOT)),checkpoint_sha256=sha256(checkpoint),
                device=str(device),elapsed_seconds=time.perf_counter()-started,epochs_executed=len(history),
                test_reference=score(prediction,truth),temporal_blocks=blocks,
                seasonal_common=score(prediction[common],truth[common]),seasonal_common_windows=len(truth[common]))
    np.savez_compressed(folder/"window_errors.npz",mse=window_mse,mae=window_mae)
    np.savez_compressed(folder/"normalizer.npz",mean=meta["mean"],std=meta["std"])
    (folder/"training_history.json").write_text(json.dumps(history,indent=2),encoding="utf8")
    completed.write_text(json.dumps(result,indent=2),encoding="utf8")
    return result,False


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--smoke",action="store_true",help="Run the first complete training condition, not a shortened-epoch test")
    args=parser.parse_args()
    protocol()
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}, threads={torch.get_num_threads()}",flush=True)
    datasets={d:load_npz(ROOT/f"data/processed/{d}_1hour.npz") for d in DATASETS}
    for d,a in datasets.items():
        print(json.dumps(seasonal_references(d,a)),flush=True)
    tasks=[(d,m,p,s) for d in DATASETS for p in FRACTIONS for m in MODELS for s in SEEDS]
    if args.smoke:tasks=tasks[:1]
    all_started=time.perf_counter()
    for i,(d,m,p,s) in enumerate(tasks,1):
        r,skipped=run_one(d,m,p,s,datasets[d],device)
        progress=dict(done=i,total=len(tasks),dataset=d,model=m,percent=p,seed=s,skipped=skipped,
                      mse=r["test_reference"]["mse"],seconds=r["elapsed_seconds"],source=r["source"],
                      run_elapsed_seconds=time.perf_counter()-all_started)
        (OUT/"progress.json").write_text(json.dumps(progress,indent=2),encoding="utf8")
        print(json.dumps(progress),flush=True)
    print("SUPPLEMENT_COMPLETE",flush=True)


if __name__=="__main__":main()
