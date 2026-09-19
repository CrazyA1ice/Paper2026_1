# Vendored Pathformer baseline

This directory vendors the minimum source files required to run Pathformer as an
external baseline inside the unified experiment pipeline.

- Upstream: `decisionintelligence/pathformer`
- Pinned commit: `ea85d82932215e171357da47b3bc82d502344758`
- Local changes: import paths were converted to package-relative imports so the
  upstream model can be loaded from `abilene_forecasting`.
- Model logic is otherwise kept aligned with the pinned upstream files.
- The adapter uses the upstream multivariate traffic defaults where applicable:
  `d_model=16`, `d_ff=128`, 3 AMS layers, top-k=2, RevIN enabled and the
  traffic patch-size configuration.

When updating this baseline, update the pinned commit in both this file and
`src/pathformer_adapter.py`, then rerun the smoke tests on Abilene and GÉANT.
