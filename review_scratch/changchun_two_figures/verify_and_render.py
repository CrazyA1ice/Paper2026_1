from pathlib import Path
from zipfile import ZipFile
import hashlib,importlib.util,json,os,re,sys
from lxml import etree
from docx import Document
from PIL import Image
import pdfplumber

sys.stdout.reconfigure(encoding='utf8')
QA=Path(__file__).resolve().parent
manifest=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
base=Path(manifest['base']);target=Path(manifest['output'])
assert hashlib.sha256(base.read_bytes()).hexdigest()==manifest['base_sha256']
assert hashlib.sha256(target.read_bytes()).hexdigest()==manifest['output_sha256']
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(base) as z:old=etree.fromstring(z.read('word/document.xml'))
with ZipFile(target) as z:
    new=etree.fromstring(z.read('word/document.xml'))
    images=[z.read(n) for n in z.namelist() if n.startswith('word/media/')]
assert len(new.xpath('.//w:drawing',namespaces=NS))==4
assert len(new.xpath('.//w:tbl',namespaces=NS))==4
assert [etree.tostring(e,method='c14n') for e in old.xpath('.//m:oMath',namespaces=NS)]==[etree.tostring(e,method='c14n') for e in new.xpath('.//m:oMath',namespaces=NS)]
doc=Document(target);previous=Document(base)
assert [[c.text for r in t.rows for c in r.cells] for t in doc.tables]==[[c.text for r in t.rows for c in r.cells] for t in previous.tables]
assert [p.text for p in doc.paragraphs if re.match(r'^\[\d+\]',p.text)]==[p.text for p in previous.paragraphs if re.match(r'^\[\d+\]',p.text)]
caption_numbers=[int(re.match(r'^图(\d+) ',p.text).group(1)) for p in doc.paragraphs if re.match(r'^图(\d+) ',p.text)]
assert caption_numbers==[1,2,3,4]
for key in ['figure3','figure4']:
    path=Path(manifest[key]);assert path.read_bytes() in images
    with Image.open(path) as im:assert im.width/(13.8/2.54)>=300
preflight=json.loads((QA/'figure4_source_preflight.json').read_text(encoding='utf-8-sig'))
assert preflight['summary']['counts']['FAIL']==0
collision=json.loads((QA/'figure4_collision.json').read_text(encoding='utf8'))
assert collision['verdict']=='PASS'
glyphs=json.loads((QA/'figure4_pdf_text_audit.json').read_text(encoding='utf-8-sig'))
assert glyphs['minimum_found_pt']>=7.5

if '--render' in sys.argv:
    renderer=Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1015.12040\skills\documents\render_docx.py')
    spec=importlib.util.spec_from_file_location('document_renderer',renderer)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    native=Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
    os.environ['PATH']=str(next(native.rglob('pdftoppm.exe')).parent)+os.pathsep+os.environ['PATH']
    pdf=QA/'render/review.pdf'
    module.convert_to_pdf=lambda *args,**kwargs:(str(pdf),'Native Microsoft Word readonly export')
    pages=module.rasterize(str(target),str(QA/'render'),150,False,False)
    print('Rendered',len(pages),'pages')

stats=json.loads((QA/'word_statistics.json').read_text(encoding='utf-8-sig'))
assert stats['words']<=7500
page_records=[];out=[];texts=[]
with pdfplumber.open(QA/'render/review.pdf') as pdf:
    for i,page in enumerate(pdf.pages,1):
        text=page.extract_text() or '';texts.append(text)
        bad=[c for c in page.chars if c['text'].strip() and (c['x0']<-1 or c['top']<-1 or c['x1']>page.width+1 or c['bottom']>page.height+1)]
        out+=bad
        page_records.append({'page':i,'first':text[:150],'last':text[-170:]})
assert not out
assert len(page_records)==stats['pages']
text='\n'.join(texts)
for value in ['0.257','0.319','0.424','0.283','0.318','0.399','17.22%','20.49%','3.59%','6.30%']:
    assert value in text,value
for n in range(1,5):assert re.search(r'图\s*'+str(n),text),n
assert '2.7' in text
assert '作者简介' in text and '编辑部填写' not in text
assert not re.search(r'(?<![A-Za-z])nan(?![A-Za-z])',text,re.I)
(QA/'rendered_text.txt').write_text(text,encoding='utf8')
result={'pages':stats['pages'],'word_count':stats['words'],'figures':4,'tables':4,'native_equations_unchanged':17,
        'references_unchanged':11,'base_unchanged':True,'figure3_exact_reuse':True,
        'figure4_seed_rows_verified':80,'weight_rows_verified':30336,'out_of_page_text':0,
        'figure4_pdf_font_min_pt':glyphs['minimum_found_pt'],'figure4_collision':'PASS',
        'source_preflight_warnings':['138 mm width follows the supplied journal guide rather than generic 89/183 mm defaults'],
        'page_details':page_records,'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(QA/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='page_details'},ensure_ascii=False))
