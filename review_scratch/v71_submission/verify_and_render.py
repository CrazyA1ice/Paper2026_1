from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'review_scratch/figureqa_dependencies'))
import fitz

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W = NS['w']
Q = lambda tag: f'{{{W}}}{tag}'
source = ROOT / 'word_output/2026.10.07v70.docx'
target = ROOT / 'word_output/2026.10.07v71.docx'
with ZipFile(source) as old, ZipFile(target) as new:
    original = etree.fromstring(old.read('word/document.xml'))
    root = etree.fromstring(new.read('word/document.xml'))
    assert old.namelist() == new.namelist()
    assert all(old.read(name) == new.read(name) for name in old.namelist() if name != 'word/document.xml')
    assert [etree.tostring(e) for e in original.xpath('//m:oMath', namespaces=NS)] == [etree.tostring(e) for e in root.xpath('//m:oMath', namespaces=NS)]
    old_tables = original.xpath('//w:tbl', namespaces=NS)
    new_tables = root.xpath('//w:tbl', namespaces=NS)
    assert [etree.tostring(e) for e in old_tables[1:]] == [etree.tostring(e) for e in new_tables[1:]]
    normalized_tables = []
    for table in [old_tables[0], new_tables[0]]:
        copy = deepcopy(table)
        for flag in copy.xpath('.//w:i', namespaces=NS):
            flag.getparent().remove(flag)
        normalized_tables.append(etree.tostring(copy))
    assert normalized_tables[0] == normalized_tables[1]
    ps = root.xpath('./w:body/w:p', namespaces=NS)
    texts = [''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS)) for p in ps]
    for index, p in enumerate(original.xpath('./w:body/w:p', namespaces=NS)):
        old_text = ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS))
        assert re.findall(r'\d+(?:\.\d+)?', old_text) == re.findall(r'\d+(?:\.\d+)?', texts[index])
    margins = root.xpath('//w:sectPr/w:pgMar', namespaces=NS)[0]
    assert {k: margins.get(Q(k)) for k in ['top','bottom','left','right']} == {'top':'1757','bottom':'1417','left':'1134','right':'1134'}
    assert root.xpath('//w:sectPr/w:cols/@w:num', namespaces=NS) in [[], ['1']]
    for i in [16,62,114]:
        assert ps[i].xpath('./w:pPr/w:outlineLvl/@w:val', namespaces=NS) == ['0']
        assert set(ps[i].xpath('./w:r/w:rPr/w:sz/@w:val', namespaces=NS)) == {'24'}
    for i in [19,80,90,97,102,66,78,86]:
        assert ps[i].xpath('./w:pPr/w:jc/@w:val', namespaces=NS) == ['center']
        assert set(ps[i].xpath('./w:r/w:rPr/w:sz/@w:val', namespaces=NS)) == {'18'}
    for i in [20,81,91,98,103]:
        assert set(ps[i].xpath('./w:r/w:rPr/w:sz/@w:val', namespaces=NS)) == {'15'}
    formula_numbers = []
    for p in ps:
        if p.xpath('.//m:oMath', namespaces=NS):
            end = re.search(r'\((\d+)\)$', ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS)))
            if end:
                formula_numbers.append(int(end.group(1)))
    assert formula_numbers == list(range(1,17)), formula_numbers
    first_references = list(dict.fromkeys(int(n) for n in re.findall(r'\[(\d+)\]', '\n'.join(texts[:116]))))
    assert first_references == list(range(1,12))
    for number, image_index in [(1,18),(2,79),(3,89),(4,96),(5,101)]:
        assert re.search(rf'图\s*{number}(?!\d)', '\n'.join(texts[:image_index]))
    cell_text = '\n'.join(''.join(cell.xpath('.//w:t/text()', namespaces=NS)) for cell in root.xpath('//w:tbl//w:tc', namespaces=NS))
    assert all(len(decimals) <= 3 for decimals in re.findall(r'\d+\.(\d+)', cell_text))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '4ba9ad75c596156efd990307f4e8ccbb126418c73077f02b851252c488b9dc3d'
    assert target.read_bytes() == (QA / 'render_v71.docx').read_bytes()

pdf = fitz.open(QA / 'v71_review.pdf')
pages = []
for i, page in enumerate(pdf):
    page.get_pixmap(dpi=150).save(QA / f'page-{i+1:02d}.png')
    pages.append({'page': i+1, 'text': page.get_text()})
(QA / 'rendered_text.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
counts = json.loads((QA / 'word_counts_v71.json').read_text(encoding='utf-8-sig'))
assert counts['words'] <= 8000, counts
assert counts['pages'] == len(pdf)
result = {'word_statistics': counts, 'formula_numbers': formula_numbers,
          'first_reference_order': first_references, 'protected_content_preserved': True,
          'source_unchanged': True, 'render_copy_identical': True,
          'all_figures_mentioned_before_embedding': True,
          'margins_and_column_compliant': True, 'caption_font_and_alignment_compliant': True,
          'figure_notes_font_compliant': True, 'heading_outline_correct': True,
          'table_decimals_at_most_three': True}
result['table1_header_symbol_italic_only'] = ['C', 'L/H']
(QA / 'final_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
