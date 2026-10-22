from pathlib import Path
from zipfile import ZipFile
from lxml import etree

QA = Path(__file__).resolve().parent
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W, 'm': M}

def paragraph(p):
    pieces = []
    for child in p:
        if child.tag in (f'{{{M}}}oMath', f'{{{M}}}oMathPara'):
            pieces.append('`' + ''.join(child.xpath('.//m:t/text()', namespaces=NS)) + '`')
        else:
            pieces.append(''.join(child.xpath('.//w:t/text()', namespaces=NS)))
    value = ''.join(pieces)
    style = p.find('w:pPr/w:pStyle', NS)
    if style is not None and style.get(f'{{{W}}}val', '').lower().startswith('heading'):
        value = '## ' + value
    return value

for version, label in [('v67', 'before'), ('v68', 'after')]:
    with ZipFile(QA.parent / f'2026.10.04{version}.docx') as z:
        root = etree.fromstring(z.read('word/document.xml'))
    blocks = []
    paragraph_index = 0
    heading_indices = {11, 18, 24, 35, 46, 58, 63, 65, 77, 85, 95, 107, 115, 117}
    for child in root.find('w:body', NS):
        if child.tag == f'{{{W}}}p':
            value = paragraph(child)
            if paragraph_index in heading_indices and not value.startswith('#'):
                value = '## ' + value
            blocks.append(value)
            paragraph_index += 1
        elif child.tag == f'{{{W}}}tbl':
            rows = []
            for row in child.findall('w:tr', NS):
                cells = [' / '.join(paragraph(p) for p in cell.findall('.//w:p', NS))
                         for cell in row.findall('w:tc', NS)]
                rows.append('| ' + ' | '.join(cells) + ' |')
            blocks.append('\n'.join(rows))
    (QA / f'preservation_{label}.md').write_text('\n\n'.join(blocks), encoding='utf-8')
assert (QA / 'scan_before.txt').read_text(encoding='utf-8') == (QA / 'editorial_before.txt').read_text(encoding='utf-8')
assert (QA / 'scan_after.txt').read_text(encoding='utf-8') == (QA / 'editorial_draft.txt').read_text(encoding='utf-8')
print('Verification text extracted from both actual DOCX files; draft matches saved document.')
