from pathlib import Path
import sys
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
import fitz

record = json.loads((QA / 'change_record.json').read_text(encoding='utf-8'))
assert hashlib.sha256((QA / 'render_input.docx').read_bytes()).hexdigest() == record['target_sha256']
pdf = fitz.open(QA / '2026.10.03v62.pdf')
texts = []
for index, page in enumerate(pdf):
    texts.append(page.get_text())
    page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72), alpha=False).save(QA / f'page-{index+1:02d}.png')
figures = {}
for number, caption in enumerate(('自适应多尺度预测框架', '相对LightTS的误差降低率与参数规模',
                                  '相对两类基线的多指标改进分布', '分组预测校准与典型窗口轨迹',
                                  '尺度权重分布与种子均值'), 1):
    pages = [i+1 for i, text in enumerate(texts) if f'图{number}{caption}' in re.sub(r'\s+', '', text)]
    assert len(pages) == 1, (number, pages)
    figures[number] = pages[0]
assert figures[1] == 2
old_pdf = fitz.open(ROOT / 'word_output/v61_step5_review/2026.10.03v61.pdf')
def text_only(document):
    return re.sub(r'\s+', '', ''.join(page.get_text() for page in document))
text_match = text_only(pdf) == text_only(old_pdf)
record.update(page_count=len(pdf), figure_pages=figures, rendered_text_matches_v61=text_match,
              renderer='Microsoft Word on an identical temporary copy; no save to manuscript',
              render_input_hash_matches_final=True)
(QA / 'render_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
