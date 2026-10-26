from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import os
import sys

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
audit = json.loads((QA/'audit.json').read_text(encoding='utf-8'))
stats = json.loads((QA/'word_statistics.json').read_text(encoding='utf-8-sig'))
for name in ('source','output'):
    assert sha256(Path(audit[name]).read_bytes()).hexdigest()==audit[name+'_sha256']
skill = Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1022.11436\skills\documents')
spec=importlib.util.spec_from_file_location('screenshot_docx_renderer',skill/'render_docx.py')
renderer=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=renderer
spec.loader.exec_module(renderer)
poppler=Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
os.environ['PATH']=str(next(poppler.rglob('pdftoppm.exe')).parent)+os.pathsep+os.environ['PATH']
pdf=Path(stats['pdf'])
renderer.convert_to_pdf=lambda *args,**kwargs:(str(pdf),'Native Word read-only PDF export')
pages=sorted(pdf.parent.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
if not pages:
    pages=renderer.rasterize(audit['output'],str(pdf.parent),150,False,False)
assert len(pages)==stats['pages']
info=[]
texts=[]
with pdfplumber.open(pdf) as doc:
    for n,p in enumerate(doc.pages,1):
        text=p.extract_text() or ''
        texts.append(text)
        outside=[c for c in p.chars if c['text'].strip() and (c['x0'] < -1 or c['top'] < -1 or c['x1'] > p.width+1 or c['bottom'] > p.height+1)]
        assert not outside,(n,outside[:1])
        assert '�' not in text and '□' not in text,n
        info.append({'page':n,'first':text[:70],'last':text[-100:],'images':len(p.images)})
text='\n'.join(texts)
(QA/'rendered_text.txt').write_text(text,encoding='utf-8')
compact=''.join(text.split())
for token in ['25.77%','43.74%','12.66%','29.09%','99.23%','106.26%',
              '8.01%','8.91%','17.47%','20.84%','0.841±0.088','0.536±0.028','23.16%','11.16%',
              '131','57587','(16)','AUE','Window-wise']:
    assert token in compact,token
for token in ['补充材料','CPU','GPU','显卡']:
    assert token not in compact,token
report={**stats,'source_and_output_hashes_match':True,'outside_page_text':0,'missing_glyph_boxes':0,'visual_review_pending':True,'page_details':info}
(QA/'render_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
