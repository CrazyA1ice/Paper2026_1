"""Aggregate the complete fixed supplementary experiment without selecting seeds."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

from supplement_seasonal_learning_20261020 import ROOT, OUT, DATASETS, MODELS, FRACTIONS, SEEDS, sha256

T7 = 2.3646242515927844


def paired(frame, baseline, proposed="dlinear_scale"):
    pivot=frame.pivot(index="seed",columns="model",values="mse")
    assert list(pivot.index)==list(SEEDS)
    x=(pivot[baseline]-pivot[proposed])/pivot[baseline]*100
    half=T7*x.std(ddof=1)/np.sqrt(len(x))
    return dict(mean_seedwise_reduction_pct=x.mean(),reduction_sd=x.std(ddof=1),
                reduction_ci95_low=x.mean()-half,reduction_ci95_high=x.mean()+half,
                wins=int((x>0).sum()),n_seeds=len(x))


def main():
    learning=[];temporal=[];seasonal=[];normalizers=[]
    for ds in DATASETS:
        seasonal.extend(json.loads((OUT/ds/"seasonal.json").read_text(encoding="utf8")))
        for percent in FRACTIONS:
            for model in MODELS:
                for seed in SEEDS:
                    folder=OUT/ds/f"history_{percent:03d}"/f"{model}_seed{seed}"
                    r=json.loads((folder/"metrics.json").read_text(encoding="utf8"))
                    assert sha256(ROOT/r["checkpoint"])==r["checkpoint_sha256"]
                    row=dict(dataset=ds,train_percent=percent,model=model,seed=seed,
                             train_rows=r["train_rows"],train_windows=r["train_windows"],
                             source=r["source"],epochs_executed=r["epochs_executed"],
                             elapsed_seconds=r["elapsed_seconds"],**r["test_reference"])
                    assert np.all(np.isfinite([row[m] for m in ["mse","mae","rmse"]]))
                    learning.append(row)
                    errors=np.load(folder/"window_errors.npz")
                    assert np.isclose(errors["mse"].mean(),row["mse"],rtol=1e-10)
                    assert np.isclose(errors["mae"].mean(),row["mae"],rtol=1e-10)
                    origins=np.arange(96,96+len(errors["mse"]))
                    for block in r["temporal_blocks"]:
                        mask=(origins>=block["target_start"]) & (origins+24<=block["target_end_exclusive"])
                        assert int(mask.sum())==block["windows"]
                        assert np.isclose(errors["mse"][mask].mean(),block["mse"],rtol=1e-10)
                        assert np.isclose(errors["mae"][mask].mean(),block["mae"],rtol=1e-10)
                    assert np.isclose(errors["mse"][72:].mean(),r["seasonal_common"]["mse"],rtol=1e-10)
                    if model==MODELS[0] and seed==SEEDS[0]:
                        normalizers.append(dict(dataset=ds,train_percent=percent,
                                                constant_channels=r["constant_channels_in_suffix"]))
                    if percent==100:
                        seasonal.append(dict(dataset=ds,model=model,seed=seed,history_hours=96,
                                             windows=r["seasonal_common_windows"],**r["seasonal_common"]))
                        for b in r["temporal_blocks"]:
                            temporal.append(dict(dataset=ds,model=model,seed=seed,**b))
    learn=pd.DataFrame(learning);temp=pd.DataFrame(temporal);season=pd.DataFrame(seasonal)
    assert len(learn)==192 and (learn["source"]=="new_training").sum()==144
    assert (learn.groupby(["dataset","train_percent","model"]).size()==8).all()
    learn.to_csv(OUT/"learning_curve_by_seed.csv",index=False)
    temp.to_csv(OUT/"temporal_by_seed.csv",index=False)
    season.to_csv(OUT/"seasonal_by_seed.csv",index=False)
    def summary(frame,groups):
        return frame.groupby(groups,as_index=False).agg(
            mse_mean=("mse","mean"),mse_sd=("mse","std"),
            mae_mean=("mae","mean"),mae_sd=("mae","std"),
            rmse_mean=("rmse","mean"),rmse_sd=("rmse","std"))
    ls=summary(learn,["dataset","train_percent","train_rows","train_windows","model"])
    ts=summary(temp,["dataset","block","target_start","target_end_exclusive","windows","model"])
    ss=summary(season,["dataset","model","history_hours","windows"])
    ls.to_csv(OUT/"learning_curve_summary.csv",index=False)
    ts.to_csv(OUT/"temporal_summary.csv",index=False)
    ss.to_csv(OUT/"seasonal_summary.csv",index=False)
    effects=[]
    for (ds,p),group in learn.groupby(["dataset","train_percent"]):
        for base in ["dlinear","dlinear_scale_global"]:
            effects.append(dict(dataset=ds,train_percent=p,baseline=base,**paired(group,base)))
    le=pd.DataFrame(effects);le.to_csv(OUT/"learning_curve_paired_effects.csv",index=False)
    effects=[]
    for (ds,b),group in temp.groupby(["dataset","block"]):
        for base in ["dlinear","dlinear_scale_global"]:
            effects.append(dict(dataset=ds,block=b,baseline=base,**paired(group,base)))
    te=pd.DataFrame(effects);te.to_csv(OUT/"temporal_paired_effects.csv",index=False)
    effects=[]
    for ds,group in season.groupby("dataset"):
        proposed=group[group["model"]=="dlinear_scale"].sort_values("seed")
        assert len(proposed)==8
        for base in ["seasonal_24","seasonal_168"]:
            b=group[group["model"]==base].iloc[0]["mse"]
            x=(b-proposed["mse"])/b*100
            half=T7*x.std(ddof=1)/np.sqrt(8)
            effects.append(dict(dataset=ds,baseline=base,mean_seedwise_reduction_pct=x.mean(),
                                reduction_ci95_low=x.mean()-half,reduction_ci95_high=x.mean()+half,
                                wins=int((x>0).sum()),n_seeds=8))
    se=pd.DataFrame(effects);se.to_csv(OUT/"seasonal_paired_effects.csv",index=False)
    complete=dict(learning_conditions=192,new_trainings=144,archived_checkpoints=48,
                  seeds=list(SEEDS),normalizers=normalizers,
                  seasonal=ss.to_dict(orient="records"),seasonal_effects=se.to_dict(orient="records"),
                  learning=ls.to_dict(orient="records"),learning_effects=le.to_dict(orient="records"),
                  temporal=ts.to_dict(orient="records"),temporal_effects=te.to_dict(orient="records"))
    (OUT/"complete_analysis.json").write_text(json.dumps(complete,ensure_ascii=False,indent=2),encoding="utf8")
    print(ss.to_string(index=False))
    print(le.to_string(index=False))
    print(te.to_string(index=False))
    print("All 192 conditions verified; summaries saved")


if __name__=="__main__":main()
