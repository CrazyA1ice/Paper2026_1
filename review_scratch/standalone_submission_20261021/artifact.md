# Standalone main manuscript contract

## Design authority

Reference C:/Users/Quant/Desktop/Paper2026_1/paper_template/长春工程学院学报(自然科学版)/数据处理精简修订_20261021/自适应多尺度加权的多变量网络流量预测_数据分析精简版.docx.
SHA256 3a79dfd13db4bac005b8ffff1e12845f6e7846d84e2acaad7a6520db2f061086. Seven pages rendered and individually inspected in prior revision. Current complete text inspected again.
Keep A4 single-column, 2.2 cm top/bottom and 2.4 cm side margins, source named styles, Songti and Times New Roman 10.5 pt body, black centered Title, 9 pt captions, all sixteen native Office Math objects and eleven references. Source file remains unchanged. Journal format template remains unused.

## User authority and scope

Only the main manuscript will be submitted. No supporting claim or definition may depend on an unsubmitted appendix, supplementary file or archive. Remove every such pointer, every hardware name/CPU/GPU reference and the entire hardware-dependent runtime subsection. Retain useful method and experimental information directly.
The submitted evidence scope is Abilene H24, GÉANT H24 and GÉANT H168, all with L96. No claim of all-horizon superiority, monotonic advantage or deployment latency. The complete previously computed horizon grid remains in its existing archive; do not cite it as submitted evidence or describe four-horizon experiments without reporting them. Every model/seed/endpoint inside a reported condition remains included.

## Evidence chain and placement

- Figure1 method framework and all algorithm formulas: preserve.
- Table1: make all submitted task sizes self-contained. Add GÉANT H168 (training1446, validation307, test307) with the same1709/570/570 time split. Retain Abilene H24 and GÉANT H24 exact counts. Add the horizon column by replacing redundant total count column; total time points are given in prose.
- Table2: preserve all three-model H24 errors and three seeds, including DLinear. It provides absolute error values.
- New Figure2: relative MSE/MAE reductions versus LightTS plus parameter ratio. Source all paired seeds42–44, 2 networks. This gives a joint error/model-size view beyond the table. No RMSE or per-seed heatmap.
- Table3: preserve all five-model H24 results across eight seeds. Retain short control definitions and bounded interpretation. No need to restore weight-distribution plot.
- Original Figure2 high-demand→Figure3; original Figure3 GÉANT weekly→Figure4. Preserve media exactly and update all captions/cross-references.
- Seasonal-copy analysis and weight distribution stay absent. Main no longer promises a periodic-baseline section in its Introduction.
- H168 section specifies independent training, fixed input/normalization, all five models/eight seeds, 307 windows/524 variables; all hyperparameters are in main setup. Parameter count57587 in main.
- Conclusion includes the strong LightTS comparison and weekly result without generalization beyond the displayed conditions. Bilingual abstracts remain aligned with the actual H24/H168 tasks.

## Figure2 contract

Question: At H24, how much does the proposed method reduce error and model size relative to LightTS in each network?
Claim: lower mean paired MSE and MAE and a small fraction of LightTS parameters, for the two displayed networks and three paired seeds.
Archetype quantitative grid, three equal-width aligned panels. (a) squared-error reduction; (b) absolute-error reduction; (c) deterministic parameter ratio. All panels jointly substantiate precision plus model-size tradeoff. Reference always LightTS; DLinear remains in absolute-value Table2.
Backend established Python only. Width138 mm, minimum7.5 pt text, Songti/Times New Roman, restrained blue, direct dataset labels. Panels a/b: mean across all three paired seeds with sample SD; panel c: P_proposed/P_LightTS ×100%, no stochastic error bar. Dashed100% reference.
All bars zero-based, no stars or significance statements. Source data contain every seed and both error metrics, model counts constant across seeds. Recompute percentages from original metrics, cross-check prior CSV, preserve source hashes. Editable PDF/SVG,600dpiPNG/TIFF, mandatory1.5pt alignment, source preflight, font and collision audits, visual review.

## Fidelity and acceptance

Editable main package parts: document.xml, document.xml.rels and new figure media only. Original sixteen math objects, eleven references, retained old figure blobs, Table2/Table3 numeric contents, author block, section geometry, styles and other parts preserve.
Final main: four figures, three tables, five experimental subsections. Zero supplement/appendix/archive pointers, zero CPU/GPU/hardware names, zero unsupported runtime/realtime statements.
Verify reported values against originals, native Word read-only PDF export, canonical DOCX rasterization, inspect every final page. Deliver one main DOCX; source plots/data are local archive assets only.

## Final acceptance

PASS: eight Word-rendered pages individually inspected. Four figures, three tables, sixteen native math objects and eleven references verified. New three-panel figure checked against all original records. Extra copied Table1 rule removed; final three-line table visually verified. No hardware or unsubmitted-material references. Source manuscript and original figure media preserved. Final native Word export is read-only; target hash unchanged.
