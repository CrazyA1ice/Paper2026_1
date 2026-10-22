# Figure 2 update contract

Question: how do normalized prediction errors and parameter counts compare with LightTS in the two hourly 24-hour tasks?
Design: retain the accepted three-panel quantitative grid, physical dimensions, labels, typography and palette. Panel a shows relative MSE reduction, panel b the complementary absolute-error metric, and panel c architecture size relative to LightTS. This is a data refresh, not a new layout.
Data: all 48 model/dataset/seed records, seeds 42–49; no exclusions. Four sets of eight matched relative reductions. Compute each reduction before taking its mean and sample SD (ddof=1). Error bars denote seed variability, not confidence intervals or significance.
Mapping: dataset -> x category; metric -> error panel; paired relative reduction -> height and sample SD; parameter count ratio -> deterministic third panel without error bars.
Guard: baseline errors must be finite and positive; all seeds and identical test targets must be present; labels and uncertainty extents must fit the axes.
Journal authority: retain 138 mm by 54.61 mm, Songti/Times text, embedded image container geometry and 600 dpi. Generic Nature sans-serif and column-width defaults do not override this manuscript.
Reuse level: structural adaptation of the existing paired-effect figure; statistics and n change from three to eight; all original source assets remain untouched.
Backend: established Python/matplotlib workflow. Export editable SVG/PDF and PNG/TIFF. Run alignment, source preflight, actual PDF glyph and collision audits, and visual review.
