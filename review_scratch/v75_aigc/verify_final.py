from pathlib import Path
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'review_scratch/figureqa_dependencies'))
import fitz
audit=json.loads((QA/'preservation_audit.json').read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/'word_output/2026.10.07v74.docx').read_bytes()).hexdigest()==audit['source_sha256']
assert hashlib.sha256((ROOT/'word_output/2026.10.07v75.docx').read_bytes()).hexdigest()==audit['target_sha256']
assert (QA/'render_v75_final.docx').read_bytes()==(ROOT/'word_output/2026.10.07v75.docx').read_bytes()
pdf=fitz.open(QA/'v75_final_review.pdf')
counts=json.loads((QA/'word_counts_final.json').read_text(encoding='utf-8-sig'))
assert len(pdf)==counts['pages']
assert counts['words']<=8000
pages=[]
citations=[]
for i,page in enumerate(pdf):
    page.get_pixmap(dpi=150).save(QA/f'page-{i+1:02d}.png')
    pages.append({'page':i+1,'text':page.get_text(),'images':len(page.get_images())})
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for s in line['spans']:
                if re.fullmatch(r'\[\d+\]',s['text']) and s['size']<8:
                    citations.append({'page':i+1,'text':s['text'],'size':s['size']})
assert len(citations)==13,citations
audit['word_statistics']=counts
audit['rendered_citations']=citations
audit['figure_pages']=[p['page'] for p in pages if p['images']>0]
(QA/'final_verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'rendered_text.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'word_statistics':counts,'rendered_citations':citations,'figure_pages':audit['figure_pages']},ensure_ascii=False))
