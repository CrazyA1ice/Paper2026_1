$ErrorActionPreference = "Stop"

$pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$trainScript = Join-Path $PSScriptRoot "train.py"
$outputRoot = Join-Path $PSScriptRoot "results\constant_router_ablation"
$model = "dlinear_scale_constant_router"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python environment not found: $pythonExe"
}
foreach ($dataset in @("abilene", "geant")) {
    $dataPath = Join-Path $PSScriptRoot "data\processed\${dataset}_1hour.npz"
    if (-not (Test-Path -LiteralPath $dataPath)) {
        throw "Processed dataset not found: $dataPath"
    }
}

Push-Location $PSScriptRoot
try {
    foreach ($dataset in @("abilene", "geant")) {
        foreach ($seed in 42..49) {
            $runDir = Join-Path $outputRoot "$dataset\${model}_seed$seed"
            $metricsPath = Join-Path $runDir "metrics.json"
            $predictionPath = Join-Path $runDir "predictions.npz"
            $weightsPath = Join-Path $runDir "router_weights.csv"
            $checkpointPath = Join-Path $runDir "best_model.pt"

            if (Test-Path -LiteralPath $metricsPath) {
                $record = Get-Content -LiteralPath $metricsPath -Raw | ConvertFrom-Json
                if ($record.dataset -ne $dataset -or $record.model -ne $model -or
                    $record.seed -ne $seed -or $record.input_len -ne 96 -or
                    $record.pred_len -ne 24 -or $record.batch_size -ne 16 -or
                    $record.epochs_max -ne 30 -or $record.patience -ne 6 -or
                    $record.learning_rate -ne 0.001 -or $record.cut_ratio -ne 0.5 -or
                    $record.parameters -ne 8339) {
                    throw "Existing result has a different experiment configuration: $metricsPath"
                }
                if ((Test-Path -LiteralPath $predictionPath) -and
                    (Test-Path -LiteralPath $weightsPath) -and
                    (Test-Path -LiteralPath $checkpointPath)) {
                    Write-Host "Skip completed run: $dataset seed=$seed"
                    continue
                }
            }

            Write-Host "Train: $dataset $model seed=$seed H=24"
            & $pythonExe $trainScript --dataset $dataset --model $model --seed $seed `
                --input-len 96 --pred-len 24 --batch-size 16 --epochs 30 `
                --patience 6 --learning-rate 0.001 --cut-ratio 0.5 --output-root $outputRoot
            if ($LASTEXITCODE -ne 0) {
                throw "Training failed: $dataset seed=$seed"
            }
            if (-not ((Test-Path -LiteralPath $metricsPath) -and
                (Test-Path -LiteralPath $predictionPath) -and
                (Test-Path -LiteralPath $weightsPath) -and
                (Test-Path -LiteralPath $checkpointPath))) {
                throw "Training output is incomplete: $runDir"
            }
        }
    }
}
finally {
    Pop-Location
}

Write-Host "All 16 constant-router runs completed: $outputRoot"
