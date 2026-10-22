from pathlib import Path
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'review_scratch/figureqa_dependencies'))
import fitz

audit = json.loads((QA/'preservation_audit.json').read_text(encoding='utf-8'))
for version,key in [('72','source_sha256'),('73','target_sha256')]:
    original = ROOT/f'word_output/2026.10.07v{version}.docx'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == audit[key]
    assert original.read_bytes() == (QA/f'render_v{version}.docx').read_bytes()
counts = json.loads((QA/'word_counts.json').read_text(encoding='utf-8-sig'))
before = fitz.open(QA/'v72_review.pdf')
after = fitz.open(QA/'v73_review.pdf')
baseline_sizes = {}
for page in before:
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for s in line['spans']:
                for n in re.findall(r'\[\d+\]',s['text']):
                    baseline_sizes[n] = max(baseline_sizes.get(n,0),s['size'])
assert len(before)==len(after)==counts[0]['pages']==counts[1]['pages']
assert counts[0]['characters']==counts[1]['characters']
assert counts[0]['words']==counts[1]['words']
pages=[]
citations=[]
for i,page in enumerate(after):
    page.get_pixmap(dpi=150).save(QA/f'page-{i+1:02d}.png')
    pages.append({'page':i+1,'text':page.get_text(),'images':len(page.get_images())})
    if i < len(after)-1:
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                spans=line['spans']
                for j,s in enumerate(spans):
                    if re.fullmatch(r'\[\d+\]',s['text']):
                        # Word automatically reduces native superscript glyph size.
                        # Baseline raising is additionally checked in the page images.
                        assert s['size'] < baseline_sizes[s['text']]*0.8, (i+1,s)
                        citations.append({'page':i+1,'text':s['text'],'size':s['size'],
                                          'bbox':s['bbox'],'flags':s['flags']})
assert len(citations)==13, citations
audit['word_statistics_before_after']=counts
audit['visual_superscript_count']=len(citations)
audit['citation_render_positions']=citations
(QA/'final_verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'rendered_text.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'citation_render_positions':citations},ensure_ascii=False))
