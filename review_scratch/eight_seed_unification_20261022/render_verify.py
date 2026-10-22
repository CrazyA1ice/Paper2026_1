from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import importlib.util
import json
import os
import re
import sys

import pdfplumber
from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
audit = json.loads((QA / 'audit.json').read_text(encoding='utf-8'))
stats = json.loads((QA / 'word_statistics.json').read_text(encoding='utf-8-sig'))
for path, digest in [('source', 'source_sha256'), ('output', 'output_sha256')]:
    assert sha256(Path(audit[path]).read_bytes()).hexdigest() == audit[digest]
skill = Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1020.11127\skills\documents')
spec = importlib.util.spec_from_file_location('content_docx_renderer', skill / 'render_docx.py')
renderer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = renderer
spec.loader.exec_module(renderer)
poppler = Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
os.environ['PATH'] = str(next(poppler.rglob('pdftoppm.exe')).parent) + os.pathsep + os.environ['PATH']
pdf = Path(stats['pdf'])
# Native Word is the conversion backend on this Windows host. Reuse the
# packaged rasterizer, passing its previously exported read-only PDF.
renderer.convert_to_pdf = lambda *args, **kwargs: (str(pdf), 'Native Word read-only export')
pages = renderer.rasterize(audit['output'], str(pdf.parent), 150, False, False)
assert len(pages) == stats['pages']
page_info = []
text_pages = []
with pdfplumber.open(pdf) as doc:
    for n, page in enumerate(doc.pages, 1):
        text = page.extract_text() or ''
        text_pages.append(text)
        outside = [c for c in page.chars if c['text'].strip() and
                   (c['x0'] < -1 or c['top'] < -1 or c['x1'] > page.width + 1 or c['bottom'] > page.height + 1)]
        assert not outside, (n, outside[:1])
        assert '�' not in text and '□' not in text, n
        page_info.append({'page': n, 'first': text[:100], 'last': text[-140:], 'images': len(page.images)})
text = '\n'.join(text_pages)
(QA / 'rendered_text.txt').write_text(text, encoding='utf-8')
compact = re.sub(r'\s+', '', text)
for token in ['2.77%', '2.35%', '25.77%', '43.74%', '23.16%', '11.16%',
              '8339', '57587', '1446/307/307', '12345678900', 'TimesNet公开基准', '10⁻⁸']:
    assert token in compact, token
assert stats['text_boxes'] == 4 and stats['sections'] == 3
for i in range(1, 5):
    assert '图' + str(i) in compact
for token in ['补充材料', 'CPU', 'GPU', '显卡', '八种子', '逐种子']:
    assert token not in compact, token
with ZipFile(audit['output']) as z:
    root = E.fromstring(z.read('word/document.xml'))
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
assert len(root.xpath('.//w:tbl', namespaces=ns)) == 3
assert len(root.xpath('.//m:oMath', namespaces=ns)) == 16
report = {**stats, 'output_sha256': audit['output_sha256'], 'outside_page_text': 0,
          'source_and_output_hashes_match': True, 'native_math': 16, 'tables': 3,
          'visual_review_pending': True, 'page_details': page_info}
(QA / 'render_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
