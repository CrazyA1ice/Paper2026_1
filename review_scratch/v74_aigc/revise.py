from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from xml.sax.saxutils import escape
from difflib import SequenceMatcher
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import re
import sys
from replacements import EDITS, TERMS

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
SOURCE=ROOT/'word_output/2026.10.07v73.docx'
TARGET=ROOT/'word_output/2026.10.07v74.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}'
source_bytes=SOURCE.read_bytes()
source_hash=hashlib.sha256(source_bytes).hexdigest()
with ZipFile(SOURCE) as z:
    source_xml=z.read('word/document.xml')
tree=E.fromstring(source_xml)
ps=tree.findall('w:body/w:p',NS)

def fulltext(p):
    return ''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))

def tokens(p):
    result=[]
    math_index=0
    for child in p:
        if child.tag==W+'r':
            ts=child.findall('w:t',NS)
            if not ts:
                continue
            assert len(ts)==1
            text=ts[0].text or ''
            pr=child.find('w:rPr',NS)
            styled=pr is not None and any(pr.find('w:'+x,NS) is not None for x in ['vertAlign','i','b'])
            literal=(len(text.strip())<=50 and re.fullmatch(r'[A-Za-z0-9\s.∶%±×/()=~～\-+√]+',text) is not None)
            fixed=styled or literal or text in TERMS
            result.append({'text':text,'fixed':fixed,'node':ts[0]})
        elif child.tag.startswith('{'+NS['m']+'}'):
            result.append({'text':f'⟦M{math_index}⟧','fixed':True,'node':None})
            math_index+=1
        else:
            assert not child.xpath('.//w:t',namespaces=NS), E.QName(child).localname
    return result

def distribute(nodes,new):
    if not nodes:
        assert not new, ('No existing plain text run for insertion',new)
        return
    old=''.join(n.text or '' for n in nodes)
    if old==new:
        return
    owners=[]
    for j,n in enumerate(nodes):
        owners.extend([j]*len(n.text or ''))
    contents=['']*len(nodes)
    for op,a,b,c,d in SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        if op=='equal':
            for k in range(a,b):
                contents[owners[k]]+=old[k]
        elif op in ('replace','insert'):
            owner=owners[a] if a<len(owners) else (owners[-1] if owners else 0)
            contents[owner]+=new[c:d]
    assert ''.join(contents)==new
    for n,t in zip(nodes,contents):
        n.text=t

def apply_new(p,new):
    ts=tokens(p)
    cursor=0
    pending=[]
    for t in ts:
        if not t['fixed']:
            pending.append(t['node'])
            continue
        start=new.find(t['text'],cursor)
        assert start>=0, ('Protected anchor missing',t['text'],new)
        distribute(pending,new[cursor:start])
        pending=[]
        cursor=start+len(t['text'])
    distribute(pending,new[cursor:])
    assert ''.join(t['text'] for t in tokens(p))==new

changes=[]
for i,edits in EDITS.items():
    old=''.join(t['text'] for t in tokens(ps[i]))
    new=old
    for source,target in edits:
        assert new.count(source)==1, (i,source,new.count(source))
        new=new.replace(source,target,1)
    assert new!=old
    assert re.findall(r'\d+(?:\.\d+)?',old)==re.findall(r'\d+(?:\.\d+)?',new), (i,'numeric sequence')
    assert re.findall(r'\[\d+\]',old)==re.findall(r'\[\d+\]',new), (i,'citations')
    for term in TERMS:
        if term.casefold() in old.casefold():
            assert term.casefold() in new.casefold(), (i,'term removed',term)
    apply_new(ps[i],new)
    changes.append({'index':i,'before':old,'after':new,'operations':edits,
                    'old_length':len(re.sub(r'\s','',old)),
                    'new_length':len(re.sub(r'\s','',new)),
                    'character_change_ratio':1-SequenceMatcher(None,old,new,autojunk=False).ratio()})

# Surgical XML patch: only character data within existing w:t nodes may change.
baseline=E.fromstring(source_xml)
old_nodes=baseline.findall('.//w:t',NS)
new_nodes=tree.findall('.//w:t',NS)
raw=source_xml.decode('utf-8')
spans=list(re.finditer(r'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)',raw,re.S))
assert len(spans)==len(old_nodes)==len(new_nodes)
modifications=[]
for span,a,b in zip(spans,old_nodes,new_nodes):
    if (a.text or '')!=(b.text or ''):
        modifications.append((span.start(2),span.end(2),escape(b.text or '')))
for start,end,text in reversed(modifications):
    raw=raw[:start]+text+raw[end:]
modified_xml=raw.encode('utf-8')
after=E.fromstring(modified_xml)
assert ''.join(after.xpath('//w:t/text()|//m:t/text()',namespaces=NS))==''.join(tree.xpath('//w:t/text()|//m:t/text()',namespaces=NS))

# Removing text content makes the two XML trees byte-identical: all formatting,
# native equations, drawings, table structures, paragraph and section properties
# and reference markers therefore remain untouched.
def without_text(root):
    r=copy.deepcopy(root)
    for n in r.findall('.//w:t',NS):
        n.text=''
    return E.tostring(r)
assert without_text(baseline)==without_text(after)
for query in ['//m:oMath','//w:tbl','//w:drawing','//w:pPr','//w:rPr','//w:sectPr']:
    assert [E.tostring(n) for n in baseline.xpath(query,namespaces=NS)]==[E.tostring(n) for n in after.xpath(query,namespaces=NS)], query
bp=baseline.findall('w:body/w:p',NS)
ap=after.findall('w:body/w:p',NS)
assert len(bp)==len(ap)==123
assert all(E.tostring(a)==E.tostring(b) for i,(a,b) in enumerate(zip(bp,ap)) if i not in EDITS)
citations=after.xpath('//w:r[w:rPr/w:vertAlign[@w:val="superscript"]]/w:t/text()',namespaces=NS)
assert [x for x in citations if re.fullmatch(r'\[\d+\]',x)]==['[1]','[2]','[3]','[4]','[5]','[6]','[7]','[8]','[6]','[9]','[10]','[11]','[6]']
assert len(re.sub(r'\s','',fulltext(ap[110])))<=150, fulltext(ap[110])
assert SOURCE.read_bytes()==source_bytes
if TARGET.exists():
    previous=json.loads((QA/'preservation_audit.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==previous['target_sha256'], 'Output was changed externally'
with ZipFile(SOURCE) as source, ZipFile(TARGET,'w') as output:
    for info in source.infolist():
        output.writestr(info,modified_xml if info.filename=='word/document.xml' else source.read(info.filename))
with ZipFile(SOURCE) as old,ZipFile(TARGET) as new:
    assert old.namelist()==new.namelist()
    assert all(old.read(n)==new.read(n) for n in old.namelist() if n!='word/document.xml')

def eligible(i,p):
    return i in (3,9) or (11<=i<=110 and not p.xpath('.//w:drawing',namespaces=NS)
                         and not re.match(r'^(?:\d[.\d]*\s|图\d|表\d)',fulltext(p))
                         and len(fulltext(p))>=30
                         and not re.search(r'\(\d+\)$',fulltext(p)))
prose_indices=[i for i,p in enumerate(bp) if eligible(i,p)]
before_prose='\n\n'.join(fulltext(bp[i]) for i in prose_indices)
after_prose='\n\n'.join(fulltext(ap[i]) for i in prose_indices)
(QA/'before_prose.txt').write_text(before_prose,encoding='utf-8')
(QA/'after_prose.txt').write_text(after_prose,encoding='utf-8')
(QA/'v74.txt').write_text('\n\n'.join(f'P{i:03d} {fulltext(p)}' for i,p in enumerate(ap)),encoding='utf-8')
spec=importlib.util.spec_from_file_location('aigc_scan',Path('C:/Users/Quant/.codex/skills/aigc-reduce/scripts/aigc_scan.py'))
scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)
scans={'before':scanner.scan(before_prose),'after':scanner.scan(after_prose)}
(QA/'local_scan_comparison.json').write_text(json.dumps(scans,ensure_ascii=False,indent=2),encoding='utf-8')

audit={'source_sha256':source_hash,'target_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
       'edited_paragraphs':len(changes),'replacement_operations':sum(len(c['operations']) for c in changes),
       'eligible_prose_paragraphs':len(prose_indices),
       'edited_paragraph_coverage':len(changes)/len(prose_indices),
       'nonspace_text_before':sum(len(re.sub(r'\s','',fulltext(p))) for p in bp),
       'nonspace_text_after':sum(len(re.sub(r'\s','',fulltext(p))) for p in ap),
       'changed_text_nodes':len(modifications),'all_nontext_xml_unchanged':True,
       'all_package_parts_except_document_xml_unchanged':True,
       'all_numbers_per_paragraph_in_original_order':True,'superscript_citations_preserved':13,
       'native_math_objects_unchanged':len(after.xpath('//m:oMath',namespaces=NS)),
       'tables_unchanged':len(after.xpath('//w:tbl',namespaces=NS)),
       'images_unchanged':len(after.xpath('//w:drawing',namespaces=NS)),
       'source_unchanged':True,'changes':changes,
       'prose_character_change_ratio':1-SequenceMatcher(None,before_prose,after_prose,autojunk=False).ratio()}
(QA/'preservation_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='changes'},ensure_ascii=False))
