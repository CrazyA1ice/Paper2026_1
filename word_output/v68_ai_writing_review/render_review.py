from pathlib import Path
import sys
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
import pymupdf

audit = json.loads((QA / 'structural_audit.json').read_text(encoding='utf-8'))
assert hashlib.sha256((QA / 'render_input_com.docx').read_bytes()).hexdigest() == audit['output_sha256']
pdf = pymupdf.open(QA / '2026.10.04v68.pdf')
old_pdf = pymupdf.open(ROOT / 'word_output/v67_aigc_review/2026.10.04v67.pdf')
texts = []
for index, page in enumerate(pdf):
    texts.append(page.get_text())
    page.get_pixmap(matrix=pymupdf.Matrix(150/72, 150/72), alpha=False).save(QA / f'page-{index+1:02d}.png')
figures = {}
for number, caption in enumerate(('自适应多尺度预测框架', '相对LightTS的误差降低率与参数规模',
                                  '相对两类基线的多指标改进分布', '分组预测校准与典型窗口轨迹',
                                  '尺度权重分布与种子均值'), 1):
    pages = [i+1 for i, text in enumerate(texts) if f'图{number}{caption}' in re.sub(r'\s+', '', text)]
    assert len(pages) == 1, (number, pages)
    figures[number] = pages[0]
record = {'page_count_before': len(old_pdf), 'page_count_after': len(pdf), 'figure_pages': figures,
          'render_input_hash_matches_final': True,
          'renderer': 'Microsoft Word task copy, exported without saving'}
tables = {}
for number, caption in enumerate(('数据集与预测任务设置', '三随机种子外部基线比较', '八随机种子核心消融结果'), 1):
    pages = [i+1 for i, text in enumerate(texts) if f'表{number}{caption}' in re.sub(r'\s+', '', text)]
    assert len(pages) == 1, (number, pages)
    tables[number] = pages[0]
record['table_pages'] = tables
(QA / 'render_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'rendered_text.txt').write_text('\n\n'.join(texts), encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
