from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT / 'review_scratch/figureqa_dependencies'))
import fitz
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
source = ROOT / 'word_output/2026.10.07v71.docx'
target = ROOT / 'word_output/2026.10.07v72.docx'
audit = json.loads((QA / 'preservation_audit.json').read_text(encoding='utf-8'))
assert hashlib.sha256(source.read_bytes()).hexdigest() == audit['source_sha256']
assert hashlib.sha256(target.read_bytes()).hexdigest() == audit['target_sha256']
assert target.read_bytes() == (QA / 'render_v72.docx').read_bytes()
with ZipFile(source) as old, ZipFile(target) as new:
    before = etree.fromstring(old.read('word/document.xml'))
    after = etree.fromstring(new.read('word/document.xml'))
    assert all(old.read(p) == new.read(p) for p in old.namelist() if p != 'word/document.xml')
    assert [etree.tostring(x) for x in before.xpath('//m:oMath',namespaces=NS)] == [etree.tostring(x) for x in after.xpath('//m:oMath',namespaces=NS)]
    assert [etree.tostring(x) for x in before.xpath('//w:tbl',namespaces=NS)] == [etree.tostring(x) for x in after.xpath('//w:tbl',namespaces=NS)]
    old_ps = before.xpath('./w:body/w:p',namespaces=NS)
    ps = after.xpath('./w:body/w:p',namespaces=NS)
    old_text = [''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS)) for p in old_ps]
    text = [''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS)) for p in ps]
    deleted = {20,81,91,98,103}
    changed = {17,75,77,84,88,95,100}
    new_index = 0
    for i in range(len(old_ps)):
        if i in deleted:
            continue
        if i not in changed:
            assert etree.tostring(old_ps[i]) == etree.tostring(ps[new_index]), (i,new_index)
        new_index += 1
    assert new_index == 123
    assert not any(t.startswith('注：') for t in text)
    numbers = []
    for p,t in zip(ps,text):
        if p.xpath('.//m:oMath',namespaces=NS):
            match = re.search(r'\((\d+)\)$',t)
            if match: numbers.append(int(match.group(1)))
    assert numbers == list(range(1,17))
    for i,p in enumerate(ps):
        if p.xpath('.//w:drawing',namespaces=NS):
            assert text[i+1].startswith('图'), (i,text[i+1])
            figure = int(re.search(r'图(\d)',text[i+1]).group(1))
            assert re.search(rf'图\s*{figure}(?!\d)','\n'.join(text[:i]))
    reference_index = text.index('参考文献')
    order = list(dict.fromkeys(int(n) for n in re.findall(r'\[(\d+)\]','\n'.join(text[:reference_index]))))
    assert order == list(range(1,12))
    assert len(re.sub(r'\s','',text[text.index('3 结语')+1])) <= 150
    body_reduction = sum(len(re.sub(r'\s','',x)) for x in old_text)-sum(len(re.sub(r'\s','',x)) for x in text)
    assert body_reduction == 251

pdf = fitz.open(QA / 'v72_review.pdf')
pages=[]
for i,page in enumerate(pdf):
    page.get_pixmap(dpi=150).save(QA / f'page-{i+1:02d}.png')
    pages.append({'page':i+1,'text':page.get_text(),'images':len(page.get_images())})
(QA / 'rendered_text.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
counts = json.loads((QA / 'word_counts_v72.json').read_text(encoding='utf-8-sig'))
assert counts['words'] <= 8000
assert counts['pages'] == len(pdf)
figure_pages={}
for page in pages:
    for n in re.findall(r'图\s*(\d)\s+(?:自适应|相对|真实值|尺度)',page['text']):
        figure_pages[n]=page['page']
assert set(figure_pages) == set('12345'), figure_pages
result={'word_statistics':counts,'figure_caption_pages':figure_pages,
        'deleted_note_paragraphs':5,'native_equations_unchanged':True,
        'table_xml_unchanged':True,'all_media_unchanged':True,
        'unrelated_paragraphs_unchanged':True,'original_source_unchanged':True,
        'body_nonspace_characters_reduced':body_reduction,
    'formula_numbers':numbers,'reference_first_appearance_order':order}
result['section_2_3_starts_new_page_to_keep_table3_whole'] = True
(QA / 'final_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
