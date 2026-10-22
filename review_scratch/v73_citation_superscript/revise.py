from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import copy
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
SOURCE = ROOT / 'word_output/2026.10.07v72.docx'
TARGET = ROOT / 'word_output/2026.10.07v73.docx'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W = '{' + NS['w'] + '}'
CITATION = re.compile(r'\[(?:[1-9]\d*)(?:[,，、\-–][1-9]\d*)*\]')

source_bytes = SOURCE.read_bytes()
source_hash = hashlib.sha256(source_bytes).hexdigest()
with ZipFile(SOURCE) as z:
    original = z.read('word/document.xml')
    tree = E.fromstring(original)
    ps = tree.findall('w:body/w:p', NS)
    reference_index = next(i for i,p in enumerate(ps)
                           if ''.join(p.xpath('.//w:t/text()', namespaces=NS)).strip() == '参考文献')
    changes = []
    replacements = []
    raw = original.decode('utf-8')
    run_spans = list(re.finditer(r'<w:r(?:\s[^>]*)?>.*?</w:r>', raw, re.S))
    raw_runs = [x.group() for x in run_spans]
    parsed_runs = tree.findall('.//w:r', NS)
    assert len(parsed_runs) == len(raw_runs)
    raw_by_run = dict(zip(parsed_runs, raw_runs))
    for i,p in enumerate(ps[:reference_index]):
        paragraph = ''.join(p.xpath('.//w:t/text()', namespaces=NS))
        for r in p.findall('w:r', NS):
            texts = r.findall('w:t', NS)
            rt = ''.join(t.text or '' for t in texts)
            matches = list(CITATION.finditer(rt))
            if not matches:
                continue
            assert len(texts) == 1 and all(c.tag in {W+'rPr', W+'t'} for c in r)
            props = r.find('w:rPr', NS)
            assert props is not None and props.find('w:vertAlign', NS) is None
            old_run = raw_by_run[r]
            pieces = []
            last = 0
            for m in matches:
                if m.start() > last:
                    pieces.append((rt[last:m.start()], False))
                pieces.append((m.group(), True))
                changes.append({'paragraph_index': i, 'citation': m.group(),
                                'context': paragraph[max(0,paragraph.index(rt)+m.start()-25):
                                                     paragraph.index(rt)+m.end()+25]})
                last = m.end()
            if last < len(rt):
                pieces.append((rt[last:], False))
            new_runs = []
            for text, superscript in pieces:
                run = re.sub(r'(<w:t(?:\s[^>]*)?>).*?(</w:t>)',
                             lambda m: m.group(1)+text+m.group(2), old_run, count=1, flags=re.S)
                if superscript:
                    run = run.replace('</w:rPr>', '<w:vertAlign w:val="superscript"/></w:rPr>', 1)
                new_runs.append(run)
            replacements.append((old_run, ''.join(new_runs)))
    assert len(changes) == 13
    for old,new in replacements:
        assert raw.count(old) >= 1
        raw = raw.replace(old,new,1)
    modified = raw.encode('utf-8')
    assert SOURCE.read_bytes() == source_bytes
    assert not TARGET.exists(), 'Output already exists'
    with ZipFile(TARGET,'w') as out:
        for info in z.infolist():
            out.writestr(info, modified if info.filename=='word/document.xml' else z.read(info.filename))

# Only the targeted run replacements may differ in the document XML.
restored = raw
for old,new in reversed(replacements):
    assert restored.count(new) >= 1
    restored = restored.replace(new,old,1)
assert restored.encode('utf-8') == original
with ZipFile(SOURCE) as old, ZipFile(TARGET) as new:
    assert old.namelist() == new.namelist()
    assert all(old.read(n) == new.read(n) for n in old.namelist() if n!='word/document.xml')
    a = E.fromstring(new.read('word/document.xml'))
    assert tree.xpath('//w:t/text()|//m:t/text()',namespaces=NS) != []
    assert ''.join(tree.xpath('//w:t/text()|//m:t/text()',namespaces=NS)) == ''.join(a.xpath('//w:t/text()|//m:t/text()',namespaces=NS))
    for q in ['//m:oMath','//w:tbl','//w:drawing','//w:pPr','//w:sectPr']:
        assert [E.tostring(x) for x in tree.xpath(q,namespaces=NS)] == [E.tostring(x) for x in a.xpath(q,namespaces=NS)], q
    new_ps = a.findall('w:body/w:p',NS)
    assert all(E.tostring(x)==E.tostring(y) for x,y in zip(ps[reference_index:],new_ps[reference_index:]))
    count = 0
    for p in new_ps[:reference_index]:
        for r in p.findall('w:r',NS):
            t = ''.join(r.xpath('./w:t/text()',namespaces=NS))
            if CITATION.search(t):
                assert CITATION.fullmatch(t)
                assert r.find('w:rPr/w:vertAlign',NS).get(W+'val') == 'superscript'
                count += 1
    assert count == 13

audit = {'source':str(SOURCE),'target':str(TARGET),'source_sha256':source_hash,
         'target_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
         'citation_occurrences':len(changes),'distinct_references':11,
         'changed_paragraphs':sorted({c['paragraph_index'] for c in changes}),
         'changes':changes,'text_unchanged':True,'non_document_package_parts_unchanged':True,
         'tables_equations_images_paragraph_and_section_formats_unchanged':True,
         'reference_list_unchanged':True,'source_unchanged':True}
(QA/'preservation_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in {'changes','source','target'}},ensure_ascii=False))
