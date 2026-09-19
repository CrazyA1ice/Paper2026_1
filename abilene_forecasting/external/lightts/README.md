# Vendored LightTS

This directory contains the LightTS model file used as an external lightweight
baseline.

- Upstream: `thuml/Time-Series-Library`
- Pinned commit: `4e938a1767106324dd753b2a44832bf870a0252e`
- Upstream model blob SHA: `a2051e44d864ec4ec5e72e59660b98c30c93a902`
- Upstream path: `models/LightTS.py`
- License: MIT (see `LICENSE`)

The upstream model logic is vendored unchanged. Project-specific configuration
and the single-input forecasting interface live in
`src/lightts_adapter.py`.
