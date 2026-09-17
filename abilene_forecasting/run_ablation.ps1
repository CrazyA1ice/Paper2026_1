$ErrorActionPreference = "Stop"

$models = @("dlinear", "fits", "dlinear_freq", "dlinear_scale", "proposed")
$seeds = @(42, 43, 44)

foreach ($model in $models) {
    foreach ($seed in $seeds) {
        python train.py --model $model --seed $seed --input-len 96 --pred-len 24 --batch-size 16 --epochs 30
    }
}

python summarize.py

