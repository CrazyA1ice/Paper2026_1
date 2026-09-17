$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$train = Join-Path $PSScriptRoot "train.py"
$summarize = Join-Path $PSScriptRoot "summarize.py"
$data = Join-Path $PSScriptRoot "data\processed\abilene_1hour.npz"
$outputRoot = Join-Path $PSScriptRoot "results\final_cut075_weight_ablation"

foreach ($seed in @(42, 43, 44)) {
    & $python $train --model proposed_static --seed $seed --data $data --input-len 96 --pred-len 24 --batch-size 16 --epochs 30 --patience 6 --learning-rate 0.001 --cut-ratio 0.75 --output-root $outputRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Training failed: proposed_static, seed=$seed, cut_ratio=0.75"
    }
}

& $python $summarize --results $outputRoot --output (Join-Path $outputRoot "runs.csv")
if ($LASTEXITCODE -ne 0) {
    throw "Summary failed: proposed_static, cut_ratio=0.75"
}
