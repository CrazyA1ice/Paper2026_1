# GÉANT dataset source

- Dataset: GÉANT backbone OD traffic matrix
- Aggregation used by this project: 1 hour
- TS-Zoo subset: matrix
- Feature: `matrix_avg_bandwidth_kbps`
- Source bucket: `https://liberouter.org/datazoo/download?bucket=geant`
- Source file: `GEANT-matrix-backbone_network-1_hour.h5`
- Raw H5 bytes downloaded by GitHub Actions: 34656272
- Processed NPZ bytes: 4804440
- Preparation entry point: `abilene_forecasting/prepare_geant.py`
- Processing: chronological 60/20/20 split, `log1p`, train-only per-channel standardization
- Raw matrix shape: `(2849, 529)`
- Active OD channels after removing constant channels: `524`
- Split rows: train `1709`, validation `570`, test `570`

The raw TS-Zoo file is committed at
`abilene_forecasting/data/raw/tszoo/databases/GEANT/GEANT-matrix-backbone_network-1_hour.h5`.

The processed file used by training is committed at
`abilene_forecasting/data/processed/geant_1hour.npz`.
