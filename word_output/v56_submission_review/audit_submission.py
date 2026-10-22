from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}

def read(name):
    with ZipFile(ROOT / 'word_output' / name) as archive:
        return etree.fromstring(archive.read('word/document.xml'))

def text(p):
    return ''.join(p.xpath('.//w:t/text()', namespaces=NS))

old = read('2026.10.02v55.docx')
new = read('2026.10.03v56.docx')
pars = new.xpath('./w:body/w:p', namespaces=NS)
values = [text(p) for p in pars]
old_tables = [t.xpath('.//w:t/text()', namespaces=NS) for t in old.xpath('//w:tbl', namespaces=NS)]
new_tables = [t.xpath('.//w:t/text()', namespaces=NS) for t in new.xpath('//w:tbl', namespaces=NS)]
old_math = [t.xpath('.//m:t/text()', namespaces=NS) for t in old.xpath('//m:oMath', namespaces=NS)]
new_math = [t.xpath('.//m:t/text()', namespaces=NS) for t in new.xpath('//m:oMath', namespaces=NS)]
equations = [int(re.fullmatch(r'\s*\((\d+)\)\s*', v).group(1)) for v in values if re.fullmatch(r'\s*\((\d+)\)\s*', v)]
body = '\n'.join(v for v in values if not re.match(r'^\[\d+\]', v))
first_citations = list(dict.fromkeys(int(n) for n in re.findall(r'\[(\d+)\]', body)))
appearance = {}
for number in range(1, 6):
    caption = next(i for i, v in enumerate(values) if re.match(fr'^图{number}\s', v))
    assert pars[caption-1].xpath('.//wp:inline', namespaces=NS)
    appearance[f'figure{number}'] = any(f'图{number}' in v for v in values[:caption-1])
for number in range(1, 4):
    caption = next(i for i, v in enumerate(values) if re.match(fr'^表{number}\s', v))
    assert pars[caption].getnext().tag.endswith('}tbl')
    appearance[f'table{number}'] = any(f'表{number}' in v for v in values[:caption])

report = {
    'tables': len(new_tables), 'figures': len(new.xpath('//wp:inline', namespaces=NS)),
    'native_math_objects': len(new_math), 'numbered_equations': equations,
    'table_values_unchanged': old_tables == new_tables,
    'math_text_unchanged': old_math == new_math,
    'citations_first_appearance': first_citations,
    'captions_and_first_mentions': appearance,
    'single_spacing': all(s.get('{%s}line' % NS['w']) == '240' for s in new.xpath('//w:spacing', namespaces=NS)),
    'manuscript_sha256': hashlib.sha256((ROOT/'word_output/2026.10.03v56.docx').read_bytes()).hexdigest(),
}
assert report['table_values_unchanged'] and report['math_text_unchanged']
assert equations == list(range(1,17))
assert first_citations == list(range(1,12))
assert all(appearance.values()) and report['single_spacing']
(HERE/'protected_content_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
