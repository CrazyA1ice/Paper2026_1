# Figure and table revision contract

Authority: retain latest Results manuscript and all journal typography, 138 mm figure width, editable equations, references and other content. Python/matplotlib is the established and exclusive plotting backend. Use 7.5 pt Songti/Times at actual print size, editable SVG/PDF and 600 dpi PNG/TIFF. No new experiments or significance tests. Use all eight matched seeds 42–49 in each displayed group. Error bars are sample SD, never confidence intervals.

Figure 2 question: how large are the error reductions against both baseline architectures, with what LightTS parameter ratio? Two panels stratify the dataset; within each panel four rows show paired MSE/MAE gains against DLinear and LightTS, all seed points and means ± SD. Parameter ratios are deterministic footer labels; exact counts go to table 2. No joint cross-dataset raw-error comparison and no claim of Pareto domination over DLinear (4656 parameters versus 8339).

Figure 3 question: how does high-demand target error differ between methods? Two dataset panels show all five models, both MAE and AUE, individual seeds and means ± SD. A point plot permits a labelled local numeric axis without encoding a misleading nonzero bar length. DLinear means are references. Proposed markers have restrained colour and shape emphasis. Percentage annotations use paired mean reductions and do not imply significance.

Figure 4 question: how large and consistent is the weekly improvement? A 2×2 grid uses columns for absolute errors and matched relative reductions; rows for MSE and MAE. All 40 absolute records and 64 paired reductions are shown. No density estimates for n=8, no smoothed clouds, no 100% significant annotation. Absolute errors have smaller-is-better direction, relative reductions larger-is-better. Final height may increase locally to retain 7.5 pt readability; page fonts/margins remain unchanged.

Table 2: keep all MSE/MAE values unchanged, retain bold best values, add architecture parameter counts. Table 3: retain bold best values and original columns; do not add a sparse new column with metric-dependent strongest-comparator denominators. Existing prose reports the intended paired comparisons.

QA: run data profiling, multi-panel physical alignment gate, source preflight, exported PDF glyph audit, collision audit and visual review of each panel and grayscale. Inspect every final Word page. Preserve source file byte-for-byte.
