from pathlib import Path
import hashlib,json,re
import pdfplumber

QA=Path(__file__).resolve().parent
manifest=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
stats=json.loads((QA/'word_statistics.json').read_text(encoding='utf-8-sig'))
pages=[];bad=[];alltext=[]
with pdfplumber.open(QA/'render/review.pdf') as pdf:
    for n,p in enumerate(pdf.pages,1):
        text=p.extract_text(layout=False) or ''
        alltext.append(text)
        chars=[c for c in p.chars if c['text'].strip()]
        out=[{'text':c['text'],'box':[c['x0'],c['top'],c['x1'],c['bottom']]} for c in chars if c['x0']<-1 or c['top']<-1 or c['x1']>p.width+1 or c['bottom']>p.height+1]
        bad.extend([{'page':n,**item} for item in out])
        pages.append({'page':n,'characters':len(chars),'first':text[:180],'last':text[-200:],'out_of_page':len(out)})
assert len(pages)==stats['pages']
assert not bad,bad
text='\n'.join(alltext)
assert not re.search(r'(?<![A-Za-z])nan(?![A-Za-z])',text,re.I)
assert '编辑部填写' not in text
assert '作者简介' in text
assert '第一作者简介' not in text
for s in ['2.77%','2.35%','29.80%','46.89%','44.93%','31.77%','47.80%','29.69%','3.28','131.35']:
    assert s in text,s
for n in range(1,17):
    assert '('+str(n)+')' in text.replace('（','(').replace('）',')'),n
for n in range(1,12):assert '['+str(n)+']' in text,n
for n in range(1,5):assert re.search(r'表\s*'+str(n),text),n
for n in [1,2]:assert re.search(r'图\s*'+str(n),text),n
(QA/'rendered_text.txt').write_text(text,encoding='utf8')
result={'pages':len(pages),'word_count':stats['words'],'out_of_page_text':bad,'page_details':pages,
        'all_main_percentage_claims_rendered':True,'all_equation_numbers_rendered':True,
        'author_biography_retained':True,'editorial_placeholder_removed':True,
        'output_sha256':hashlib.sha256(Path(manifest['output']).read_bytes()).hexdigest()}
(QA/'rendered_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'pages':len(pages),'word_count':stats['words'],'out_of_page_text':len(bad),'all_percentage_claims_present':True,'equations_numbered':16}))
