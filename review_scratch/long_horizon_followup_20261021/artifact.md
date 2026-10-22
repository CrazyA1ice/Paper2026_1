# Revision contract

Reference: retained latest grouped-bar manuscript, SHA256 eb2f06a71158bb9162efb38a8bad3943d4ad357ebe7e163c3aa8abfd5fe0ef1f.
Reference visual evidence: eight pages already inspected in the preceding revision; current paragraph, table, section and style inventory inspected again.

## Preserve

- Main manuscript title, author, affiliation, eleven references, seventeen native Office Math objects, four existing figures and table numeric values.
- A4 portrait, margins top/bottom 2.20 cm and left/right 2.40 cm; single column.
- Body Songti with Times New Roman, 10.5 pt, 1.1 line spacing, 21 pt first-line indent. Title black centered 16 pt. Existing heading ladder and 9 pt centered figure captions.
- Original document remains unchanged. No journal template file is used.

## Editable slots

- Compress bilingual abstracts to add the scoped GÉANT H168 result; Chinese abstract maximum 200 characters excluding label.
- Generalize method notation to H and qualify parameter/timing claims by H24.
- Add one H168 subsection with a new figure, all five models, both requested metrics and all eight seeds. Point to the complete supplemental grid.
- Rename daily/weekly naïve forecasts as 日周期复制 and 周周期复制 with their meaning retained.
- Add a bounded weekly result to the conclusion.
- Supplement uses a copy of the reference package with its body replaced by a standalone experiment report, retaining page geometry and typographic styles. Intentional deviations: no author biography, no original figures/equations/references; five pages of protocol and complete numerical tables, repeated headers, no split rows.

## Figure contract

Question: Do the five requested models differ in squared and absolute forecast errors for GÉANT H168 with L96?
Claim: the proposed method has lower mean MSE and MAE than all four listed controls in this specific task.
Archetype: quantitative grid, two aligned panels. MSE emphasizes large errors; MAE supplies the requested absolute-error endpoint. No duplicate third metric or gap annotation.
Backend: established Python matplotlib only. 138 mm wide, white background, neutral controls and blue proposed bars, zero baselines, direct category labels.
Statistics: eight paired training seeds 42–49; bar means and sample SD. 307 common forecast origins; every target hour and retained OD variable included. No significance claim.
Selection: user requested positive conditions in main and all other conditions in supplement after seeing the full grid. Thus this is a post-results focused display, not evidence of universal or monotonically increasing superiority. Main explicitly points to all 2 × 4 × 5 conditions; no model/seed/metric removed within the displayed condition.
Exports: editable SVG/PDF and 600 dpi PNG/TIFF, 7.5 pt minimum text, source 40 seed records and five summaries. Alignment tolerance 1.5 pt, static preflight, PDF font floor and collision audits, final-size visual inspection.

## Acceptance

- Independently recompute all 40 means/SD and 64 paired reductions from 320 rows.
- Verify sources, configurations and prediction hashes; check raw weekly scores against saved metrics.
- Main: 5 figures, 4 tables, 17 unmodified Office Math objects, 11 unchanged references; old media and table numbers preserved.
- Supplement: all 40 mean/SD groups, all 64 paired comparisons and both networks; negative effects retained.
- Export both through native Word read-only, run canonical DOCX rasterizer, inspect every page and fix layout defects.
