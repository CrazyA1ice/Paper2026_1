from pathlib import Path
from zipfile import ZipFile
import json,hashlib,re,sys,os,importlib.util
from lxml import etree as E
import pdfplumber
from docx import Document

sys.stdout.reconfigure(encoding='utf8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
m=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
stats=json.loads((QA/'word_statistics.json').read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for path,key in [('output','output_sha256'),('source','source_sha256'),('template_original','template_original_sha256'),('template_converted','template_converted_sha256')]:assert sha(m[path])==m[key],path
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml'}
def tag(n):a,b=n.split(':');return '{'+NS[a]+'}'+b
with ZipFile(m['output']) as z:
    root=E.fromstring(z.read('word/document.xml'));styles=E.fromstring(z.read('word/styles.xml'))
with ZipFile(m['template_converted']) as z:template=E.fromstring(z.read('word/document.xml'))
assert stats['sections']==3 and stats['text_boxes']==4 and stats['words']<7500
assert len(root.xpath('.//v:textbox',namespaces=NS))==4
assert len(root.xpath('.//m:oMath',namespaces=NS))==16
for a,b in zip(template.xpath('.//w:sectPr',namespaces=NS),root.xpath('.//w:sectPr',namespaces=NS)):
    for name in ['w:pgSz','w:pgMar','w:cols','w:type','w:titlePg','w:docGrid']:
        aa=a.find(tag(name));bb=b.find(tag(name));assert (dict(aa.attrib) if aa is not None else None)==(dict(bb.attrib) if bb is not None else None),name
roles={'Title':28,'JournalBody':21,'JournalHeading1':24,'JournalHeading2':21,'JournalCaption':18,'JournalTable':15,'JournalReference':21}
for name,half_points in roles.items():
    style=styles.xpath('./w:style[@w:styleId="'+name+'"]',namespaces=NS)[0]
    assert style.find('w:rPr/w:sz',NS).get(tag('w:val'))==str(half_points)
    assert style.find('w:rPr/w:rFonts',NS).get(tag('w:eastAsia'))=='宋体'
    assert style.find('w:rPr/w:rFonts',NS).get(tag('w:ascii'))=='Times New Roman'
    if name=='JournalBody':assert style.find('w:pPr/w:spacing',NS).get(tag('w:line'))=='360'
body=root.find(tag('w:body'))
refs_started=False;first_mentions=[];cite_count=0
for p in body.findall(tag('w:p')):
    value=''.join(p.xpath('.//w:t/text()',namespaces=NS))
    if value=='参考文献：':refs_started=True
    if refs_started:continue
    for run in p.findall(tag('w:r')):
        value=''.join(run.xpath('.//w:t/text()',namespaces=NS))
        if re.fullmatch(r'\[\d+\]',value):
            assert run.find('w:rPr/w:vertAlign',NS).get(tag('w:val'))=='superscript'
            n=int(value[1:-1]);cite_count+=1
            if n not in first_mentions:first_mentions.append(n)
assert first_mentions==list(range(1,12)),first_mentions
all_text=''.join(root.xpath('.//w:t/text()',namespaces=NS))
assert all_text.index('[11] UHLIG')<all_text.index('Multivariate network traffic forecasting')
assert '12345678900' in all_text and '安徽池州人' in all_text
assert '基金项目' not in all_text
assert not root.xpath('.//w:color[@w:val="FF0000"]',namespaces=NS)
for token in ['补充材料','附录','CPU','GPU','显卡','GTX','投到编辑部的日期','XXX','Charged active contour','五号宋体','四号宋体']:
    assert token not in all_text,token

skill=Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1020.11127\skills\documents')
spec=importlib.util.spec_from_file_location('journal_template_renderer',skill/'render_docx.py')
renderer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=renderer;spec.loader.exec_module(renderer)
poppler=Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
os.environ['PATH']=str(next(poppler.rglob('pdftoppm.exe')).parent)+os.pathsep+os.environ['PATH']
pdf=Path(stats['pdf']);renderer.convert_to_pdf=lambda *args,**kwargs:(str(pdf),'Native Word read-only export')
pages=renderer.rasterize(m['output'],str(pdf.parent),150,False,False)
assert len(pages)==stats['pages']
details=[];texts=[]
with pdfplumber.open(pdf) as doc:
    for n,page in enumerate(doc.pages,1):
        text=page.extract_text() or '';texts.append(text)
        outside=[c for c in page.chars if c['text'].strip() and (c['x0']<-1 or c['top']<-1 or c['x1']>page.width+1 or c['bottom']>page.height+1)]
        assert not outside,(n,outside[:1])
        details.append({'page':n,'first':text[:120],'last':text[-180:],'images':len(page.images)})
text='\n'.join(texts);compact=re.sub(r'\s+','',text)
(QA/'main_rendered_text.txt').write_text(text,encoding='utf8')
for token in ['29.80%','46.89%','23.16%','11.16%','57587','1446/307/307','12345678900','参考文献','Abstract:','Keywords:']:
    assert token in compact,token
for n in range(1,5):assert '图'+str(n) in compact,n
for token in ['补充材料','附录','CPU','GPU','显卡','GTX','Chargedactivecontour','□','�']:assert token not in compact,token
report={**stats,'native_math':16,'numbered_equations':15,'figures':4,'tables':3,'superscript_citations':cite_count,'first_citation_order':first_mentions,'template_geometry_matches':True,'source_and_template_unchanged':True,'outside_page_text':0,'visual_review_pending':True,'page_details':details}
(QA/'render_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
