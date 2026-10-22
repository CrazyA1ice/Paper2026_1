from pathlib import Path

QA = Path(__file__).resolve().parent
PREVIOUS = QA.parent / 'v63_aigc_review'

apply_source = (PREVIOUS / 'apply_revision.py').read_text(encoding='utf-8')
apply_source = apply_source.replace("SOURCE = ROOT / 'word_output/2026.10.03v62.docx'", "SOURCE = ROOT / 'word_output/2026.10.03v63.docx'")
apply_source = apply_source.replace("OUTPUT = ROOT / 'word_output/2026.10.03v63.docx'", "OUTPUT = ROOT / 'word_output/2026.10.03v64.docx'")
apply_source = apply_source.replace('7403a693cd9221f4a26b3e9702af893e1c0f0e50c270d669b9e73b13141ecfae', 'd77c1fbcc3e35d3ab744c99cfcfc38af104702f97c7e6d5cbf672e515eea368d')
(QA / 'apply_revision.py').write_text(apply_source, encoding='utf-8')

render_source = (PREVIOUS / 'render_review.py').read_text(encoding='utf-8')
render_source = render_source.replace("pdf = pymupdf.open(QA / '2026.10.03v63.pdf')", "pdf = pymupdf.open(QA / '2026.10.03v64.pdf')")
render_source = render_source.replace("old_pdf = pymupdf.open(ROOT / 'word_output/v62_figure1_review/2026.10.03v62.pdf')", "old_pdf = pymupdf.open(ROOT / 'word_output/v63_aigc_review/2026.10.03v63.pdf')")
(QA / 'render_review.py').write_text(render_source, encoding='utf-8')

export_source = (PREVIOUS / 'export_word.ps1').read_text(encoding='utf-8')
export_source = export_source.replace('v63_aigc_review', 'v64_aigc_review').replace('2026.10.03v63', '2026.10.03v64')
(QA / 'export_word.ps1').write_text(export_source, encoding='utf-8')
print('Prepared task-local editing and verification scripts; no DOCX written.')
