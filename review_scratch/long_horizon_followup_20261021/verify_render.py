from pathlib import Path
from zipfile import ZipFile
import hashlib, importlib.util, json, os, re, sys
import pdfplumber
from docx import Document
from lxml import etree

sys.stdout.reconfigure(encoding='utf8')
QA=Path(__file__).resolve().parent
manifest=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
stats=json.loads((QA/'word_statistics.json').read_text(encoding='utf-8-sig'))
assert hashlib.sha256(Path(manifest['base']).read_bytes()).hexdigest()==manifest['base_sha256']
SKILL=Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1020.11127\skills\documents')
spec=importlib.util.spec_from_file_location('long_prediction_renderer',SKILL/'render_docx.py')
renderer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=renderer;spec.loader.exec_module(renderer)
native=Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
os.environ['PATH']=str(next(native.rglob('pdftoppm.exe')).parent)+os.pathsep+os.environ['PATH']
records=[]
for info in stats:
    kind=info['kind'];docx=Path(manifest[kind]);pdf=Path(info['pdf']);render=pdf.parent
    assert hashlib.sha256(docx.read_bytes()).hexdigest()==manifest[kind+'_sha256']
    renderer.convert_to_pdf=lambda *args,**kwargs:(str(pdf),'Native Microsoft Word readonly export')
    pages=renderer.rasterize(str(docx),str(render),150,False,False)
    assert len(pages)==info['pages']
    texts=[];details=[]
    with pdfplumber.open(pdf) as document:
        for i,page in enumerate(document.pages,1):
            txt=page.extract_text() or '';texts.append(txt)
            bad=[c for c in page.chars if c['text'].strip() and (c['x0']<-1 or c['top']<-1 or c['x1']>page.width+1 or c['bottom']>page.height+1)]
            assert not bad,(kind,i)
            details.append({'page':i,'first':txt[:130],'last':txt[-170:],'characters':len(txt)})
    extracted='\n'.join(texts)
    (QA/f'{kind}_rendered_text.txt').write_text(extracted,encoding='utf8')
    if kind=='main':
        for value in ['23.16%','11.16%','26.02%','12.34%','57587','8339','0.841','0.536','补充材料']:
            assert value in extracted,value
        for n in range(1,6):assert re.search(r'图\s*'+str(n),extracted)
        assert '作者简介' in extracted
        assert info['words']<=7500
    else:
        for value in ['0.326210','0.840610','-12.79','-5.57','320','669','307']:
            assert value in extracted,value
        for n in range(1,6):assert re.search(r'表\s*S'+str(n),extracted)
        assert '作者简介' not in extracted
    records.append({**info,'page_details':details,'out_of_page_text':0,'visual_review_pending':True})
(QA/'render_verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([{k:v for k,v in r.items() if k!='page_details'} for r in records],ensure_ascii=False))
