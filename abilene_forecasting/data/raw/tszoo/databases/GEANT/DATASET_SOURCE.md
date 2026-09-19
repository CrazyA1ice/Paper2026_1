# GÉANT dataset source

- Dataset: GÉANT backbone OD traffic matrix
- Aggregation used by this project: 1 hour
- TS-Zoo subset: matrix
- Feature: 
- Source bucket: 
- Source file: 
- Raw H5 bytes downloaded by GitHub Actions: 34656272
- Processed NPZ bytes: 4804440
- Preparation entry point: 
- Processing: chronological 60/20/20 split, , train-only per-channel standardization

The processed file used by training is committed at
.

GitHub rejects individual regular Git objects above 100 MiB. The raw H5 is
committed only when it is below a conservative 95 MiB threshold.
