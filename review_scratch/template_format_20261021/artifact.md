# Journal template formatting contract

## Authority and scope

The retained authority is the user-supplied 论文模板.doc, read-only converted by native Word to 论文模板.docx in this task folder. Its five rendered pages were individually inspected. reference_manifest.json and template_evidence.json record the original and converted SHA256 values. The accompanying two-page 投稿须知 was also read. The red written rules take precedence over inconsistent demonstration fonts: use 14 pt title, not the displayed 22 pt demonstration title. Figure width uses the stricter shared requirement under 14 cm (13.8 cm). Do not copy any demonstration author, date, fund, reference, figure, or instructional text into the manuscript.

Content authority is the latest independently readable manuscript, SHA256 5419c896a038614c048d0c6d8545b085846498e76f454acec9bdb8c2cc3017f8 (verify actual manifest before authoring; the exact authoritative value is its manifest). Preserve every reported empirical result, all three tables, the fifteen numbered formulas and unnumbered parameter formula. No additional experiments, result filtering, hardware details, or supplement references. The sole submitted artifact remains the main manuscript.

## Page and package system

Build a working package copy of the retained converted template. Preserve template-owned opaque parts. Replace only mapped body slots, define explicit journal role styles, and add the manuscript figures as new relationship-backed media. Retain the template's three single-column sections: front matter, Chinese main text and references, English end matter. All sections A4 11906×16838 twips; margins top935/right746/bottom779/left1080; header851/footer331; gutter0. Template columns are one column, with spaces720/425/720. Template header and footer are empty. Keep this geometry; do not import the former manuscript's page geometry or footer biography.

## Slot map and role rules

1. Front title: <=20 Chinese characters, Songti14 pt bold centered. Title named style, black, no border.
2. Receipt date: Songti10.5 pt. Leave the value blank because submission has not occurred; do not invent a receipt date. Article number and DOI are also editorial slots and stay blank.
3. Fund slot: remove, because the user explicitly reports no funded project.
4. Author biography: Songti10.5 pt. User-authorized facts: 柯亚文,1998,male,Han,Chizhou Anhui,assistant lecturer,postgraduate education,master's degree,computer software,email as original, telephone12345678900. Do not infer other personal information.
5. Chinese author and secondary-level affiliation: Songti10.5 pt centered; retain verified institution and postal code.
6. Chinese abstract: one paragraph, third person, <=200 characters, purpose/method/quantitative results/conclusion; define DLinear at first use. Bold Songti10.5 pt label, regular10.5 pt body. No citations or figures. English content must match exactly in claims and scope.
7. Keywords: five existing full terms, Songti10.5 pt; retain order in English; bold label.
8. Classification and document code: retain TP393 and A, bold10.5 pt labels, regular values. Article number and DOI blank for editorial completion.
9. Introduction starts0. Main headings12 pt Songti bold; secondary headings10.5 pt Songti bold; left flush; number followed by one ideographic space. No tertiary headings needed; if present10.5 pt regular. Body10.5 pt Songti, Times New Roman for non-Chinese, justified, exact18 pt line spacing, two-character first indent. Define nonstandard terms on first use; use consistent terminology.
10. Every display formula native editable OMML, centered, number right flush, sequential1–15. Preserve mathematical content. Add punctuation to the unnumbered parameter equation. Existing variable definitions remain in order. Semantic vector/matrix styles stay bold italic; functions and descriptive subscripts upright.
11. Four figures retain their scientific questions, all models/seeds/endpoints, and claims. Re-export typography as nominal7.5 pt (六号), Songti Chinese and Times New Roman non-Chinese, >=300dpi (600dpi used),13.8 cm width. Each figure has a preceding introduction. Number1–4; comparable panels named(a),(b),(c). Numeric ticks point inward and stop on an explicitly labelled endpoint. Remove unnecessary grids. Group each picture and its Chinese9 pt bold caption in one borderless text box; do not add supplementary legends or duplicate prose.
12. Three tables: preserve every value; three-line format; captions Chinese9 pt bold above table; cell labels/numbers7.5 pt; numeric units in headers where applicable. Keep each table with its introduction and repeat header if a split becomes unavoidable.
13. References: blank line before; heading10.5 pt bold; items10.5 pt Songti/TNR. In-text citations superscript and numbered by first mention. Surname uppercase; full Chinese given names capitalized normally; first3authors+等/et al. For the sole preprint, cite the formally published TimesNet benchmark for the limited claim that LightTS is a multilayer-perceptron baseline used in public benchmarks and use its published implementation; do not attribute LightTS invention to TimesNet authors. TimeMixer is a formally published ICLR2024 conference paper. Other reference facts unchanged.
14. English block after references, preceded by blank line. Sentence-case English title14 pt bold TNR, first author KE Yawen10.5 pt, full affiliation10.5 pt, blank line before Abstract; Abstract/Key words labels10.5 pt bold and body10.5 pt regular. Semicolon-separated keyword order identical to Chinese.

## Figure evidence and checks

Established Python backend reused exclusively. Figure1 is a style adaptation of the existing original schematic source; retain all labels, curves and connections, adjust nominal fonts and physical height. Figures2–4 are style-only re-exports of the same quantitative grids. Figure2 uses all12 matched percentage reductions from seeds42–44; deterministic parameter ratios have no error bars. Figure3 uses80 dataset/model/seed rows and sample SD; Figure4 uses40 GÉANT H168 model/seed rows, same307windows, sample SD. Zero axes, no significance tests. Run alignment at1.5pt, PDF font and collision audits, source preflight, final-size visual inspection. Template standards override generic Nature design defaults.

## Final gates

Check the original DOC and prior main hashes unchanged; compare table strings and mathematical text to the prior main; verify four text boxes/four images/three tables/16math objects/15numbered equations; all inline citation first-mention order and superscripts. Search all visible XML parts for red instructional residue, source-example content, hardware and supplement references. Verify template section geometry and preserved package parts. Native Word render, packaged renderer rasterization, inspect every final page, and repair defects. Keep QA files internal; deliver final main DOCX and local requirement ledger only if requested.

## Final acceptance

PASS. Seven final native-Word-rendered pages individually inspected in the final fidelity-diff folder. All41 red-instruction paragraphs mapped; none unmapped. Four borderless figure boxes, three tables,16native editable math objects,15equation numbers,11references and13superscript citation occurrences. Main numeric results and mathematical content preserved; parameter equation punctuation added. Explicit Times New Roman numeral/operator upright styling and scalar/matrix notation verified visually. Original template geometry and preserve-only package parts intact. Generic Nature font/width preflight defaults are superseded by independently verified journal-specific Songti/Times and138mm width requirements; all four rendered figure collision and font-floor audits pass. Original template and previous main are unchanged. Editorial receipt date, article number and DOI intentionally blank. User-supplied author metadata inserted; no fund invented.
