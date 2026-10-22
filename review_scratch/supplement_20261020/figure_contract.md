# Training history figure contract

Purpose: test whether adding older training history improves held-out forecasting and whether the routing model benefits consistently. The conclusion is to be determined from all completed runs, including negative results.

Evidence: two fixed original chronological validation/test splits, three models, four nested training suffixes, eight common training seeds. Errors are expressed in the original full-training normalization coordinates. Error bars are sample SD across training seeds, not uncertainty across independent networks. Increasing a suffix changes both observation amount and age coverage. Epoch ceilings and early stopping are fixed; optimizer update counts are not matched.

Archetype: two aligned quantitative panels. Panel a establishes the history response in Abilene; panel b tests whether that response repeats in the second backbone dataset. Each panel shows every history fraction and every model. Neither panel establishes cross-network transfer.

Encoding: x is retained training history percent; y is held-out reference-space MSE, starting at zero. DLinear gray circles; global weights orange squares; proposed routing teal triangles. Means and SD are computed from all eight seeds. No selected best seed, smoothing, or omitted fraction.

Contract: Python/Matplotlib, 180 mm wide, vector PDF/SVG plus 600 dpi PNG. Existing manuscript has no newly selected journal template. Preserve source-data CSV, plotting source, alignment manifest, PDF text audit and collision audit. Insert figure as Figure 6 in the revised Word manuscript. Review all glyphs, error bars, panels, labels and full page layout before delivery.
