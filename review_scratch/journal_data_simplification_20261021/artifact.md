# Statistical presentation revision contract

## Source design and evidence

Main source: C:/Users/Quant/Desktop/Paper2026_1/paper_template/长春工程学院学报(自然科学版)/长预测核验与修订_20261021/自适应多尺度加权的多变量网络流量预测_扩展预测修订版.docx
SHA256 76b2b907abd388a49503c7ad21e8a4b009848b033e65d59e5660f2033168c744.
Supplement source: same directory, 长预测时长扩展实验_完整结果与核验.docx, SHA256 57177770317afe921c081a98e4b51fd18158c9e9795d318b0909e0068a095a46.
Main reference was rendered and every one of its 9 pages inspected in the preceding revision; supplement 4 pages also inspected. Section/style evidence and complete inventory are in ../long_horizon_followup_20261021/package_inventory.json and render_verification.json.

Keep existing A4 geometry, single column, margins 2.2 cm top/bottom and 2.4 cm left/right; source body Songti/Times New Roman 10.5 pt, 1.1 line spacing; heading hierarchy, black 16 pt Title, 9 pt captions, original author biography and references. Preserve the eleven references and every retained editable Office Math equation exactly.

## Scope and minimum evidence chain

The problem is redundant reporting and dispersed evaluation cohorts, not excessive inferential testing. Main has no P values, confidence intervals or significance tests. Repeated training and sample SD remain. Four window statistics are algorithm inputs and remain.

1. Necessary processing: log1p, train-only active channels and standardization, chronological split, within-split windows. Clarify existing zero treatment for missing/non-finite or negative raw inputs; do not alter data.
2. Overall comparison: main Table2, matched three seeds, all original rows/values. Show results once. Retain parameter ratio in one sentence.
3. Fusion controls: main Table3, matched eight seeds, all original rows/values. This supports the weighting design; weight distribution is supplementary descriptive evidence.
4. High demand: original Figure4 retained as new Figure2, all models/seeds/metrics, threshold from training only.
5. Weekly task: original Figure5 retained as new Figure3, all five models/eight seeds, bounded GÉANT H168 claim. Complete horizon results remain in supplementary S1–S4.
6. Runtime: batch size, hardware, H24 and means/SD in main; warm-ups/repetition mechanics moved to supplementary.

## Editable and preserved parts

Main word/document.xml: change experiment paragraphs/headings, remove redundant RMSE paragraph/equation16, move Figure2 and Figure3 plus their prose, move periodic Table4 plus its prose to supplement, renumber retained Figures4/5 to2/3. Combine metric definitions with experimental settings. Compress repeated numerical recitations. Methods only get the missing cleaning-policy sentence and a shorter repeated parameter paragraph. Abstract and references unchanged.
Main all other existing package parts preserve, including images, footnotes, styles, numbering, headers/footers, core properties; unused original media may remain. New main drawings=3, tables=3, Office Math=16 (15 numbered plus parameter formula).
Supplement: append source-derived paragraphs/drawings/table as S5–S8 after the full four-page result record. Preserve existing S1–S4 body, all five tables and all contrary horizon results. Added assets: old Figure2→FigureS1; old Figure3→FigureS2; old Table4→TableS6. Remap image relationships correctly. Appendix caption numbers are explicit, not inferred.
Separate author-facing comparison note records source page evidence, eight comparison dimensions, retain/move/remove decisions and before/after counts. It is not part of the manuscript.

## Terminology and statistics location

MSE=均方误差, MAE=平均绝对误差, SD=样本标准差. 主稿“重复次数” refers to training runs, not overlapping time points. Short model labels in figures retain their canonical mapping: 全局权重=全局可学习权重; 恒定路由=恒定输入路由.
Main primary statistics: means ± sample SD, matched-seed average percentage reductions; no new tests. RMSE and per-seed heatmap are retained only in supplementary. No favorable seed is selected or result recomputed.

## Gates

- Verify all source hashes, two processed matrices and sample primary pages.
- Retained tables byte-identical and figure media identical. Main retained math byte-identical except explicitly removed redundant equation16. References, chronological evaluation and all training data preserved.
- Supplement retains original four-page body evidence and all 40 error summaries/64 paired comparisons, plus relocated material.
- Native Word read-only export, canonical renderer, inspect every final page, no clipping or broken display numbering.
- Record experiment-subsection character delta and compact claim-repetition audit.
