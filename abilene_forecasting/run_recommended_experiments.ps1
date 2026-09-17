$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$train = Join-Path $PSScriptRoot "train.py"
$summarize = Join-Path $PSScriptRoot "summarize.py"
$data = Join-Path $PSScriptRoot "data\processed\abilene_1hour.npz"
$seeds = @(42, 43, 44)

# Experiment A: frequency-retention sensitivity (2 models x 3 ratios x 3 seeds).
foreach ($ratio in @(0.25, 0.50, 0.75)) {
    $ratioTag = $ratio.ToString("0.00", [Globalization.CultureInfo]::InvariantCulture).Replace(".", "")
    $outputRoot = Join-Path $PSScriptRoot "results\frequency_sensitivity\cut_$ratioTag"
    foreach ($model in @("dlinear_freq", "proposed")) {
        foreach ($seed in $seeds) {
            & $python $train --model $model --seed $seed --data $data --input-len 96 --pred-len 24 --batch-size 16 --epochs 30 --patience 6 --cut-ratio $ratio --output-root $outputRoot
            if ($LASTEXITCODE -ne 0) { throw "Training failed: $model, seed=$seed, cut_ratio=$ratio" }
        }
    }
    & $python $summarize --results $outputRoot --output (Join-Path $outputRoot "runs.csv")
    if ($LASTEXITCODE -ne 0) { throw "Summary failed: cut_ratio=$ratio" }
}

# Experiment B: fixed equal weights versus sample-adaptive weights
# (4 models x 3 seeds). The frequency-enabled variants use cut_ratio=0.50.
$outputRoot = Join-Path $PSScriptRoot "results\weight_ablation"
foreach ($model in @("dlinear_scale_static", "dlinear_scale", "proposed_static", "proposed")) {
    foreach ($seed in $seeds) {
        & $python $train --model $model --seed $seed --data $data --input-len 96 --pred-len 24 --batch-size 16 --epochs 30 --patience 6 --cut-ratio 0.50 --output-root $outputRoot
        if ($LASTEXITCODE -ne 0) { throw "Training failed: $model, seed=$seed" }
    }
}
& $python $summarize --results $outputRoot --output (Join-Path $outputRoot "runs.csv")
if ($LASTEXITCODE -ne 0) { throw "Weight-ablation summary failed" }
