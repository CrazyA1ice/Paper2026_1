# Two additional manuscript figures

The established Python backend is retained. The existing two figures remain unchanged.

Figure 3 exactly reuses the two-dataset, eight-seed scale-weight distribution image from the verified manuscript. All original pixels are retained. Its role is descriptive: show the allocation among scales 1, 2 and 4, including variation across windows and training seeds. It does not establish that larger window-level variation causes better predictions. The raw router weights for all eight seeds and both networks are checked and exported. Mean weights are compared with the previous verified interpretation.

Figure 4 is a new plot of existing high-demand evaluation results. A high-demand target exceeds its own OD variable's training-only 90th percentile. The two primary metrics are MAE and the mean of max(truth - prediction, 0) over all such forecast targets. Each point is the mean across seeds 42–49, and each horizontal error bar is the sample standard deviation across these eight training seeds. Both datasets, all five models and all eight seeds are retained. No individual windows, variables or seeds are chosen by prediction performance. The second panel evaluates the same metrics on the other measured network; neither panel implies transfer learning or deployment benefit.

The layout is a two-panel quantitative comparison with shared model order and zero-based horizontal axes. Metrics use distinct colors and markers. The new plot is 138 mm wide with at least 7.5 pt text, native text in PDF/SVG and a 600 dpi PNG. Model names follow the manuscript. Alignment, PDF text size and collision checks precede final Word render inspection. No new model training or prediction data are generated.

The main manuscript remains limited to the fixed split, complete training histories and 96 h to 24 h task. All supplemental observations remain available in the prior record. Main-text additions are limited to the new captions, their necessary definitions and concise result interpretation.
