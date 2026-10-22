from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from collections import Counter
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'review_scratch/figureqa_dependencies'))
import fitz
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
for version,name in [(74,'2026.10.07v74.docx'),(68,'2026.10.04v68.docx')]:
    with ZipFile(ROOT/'word_output'/name) as z: root=E.fromstring(z.read('word/document.xml'))
    records=[]
    for i,p in enumerate(root.findall('w:body/w:p',NS)):
        plain=''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))
        bits=[]; math=0
        for child in p:
            if child.tag.startswith('{'+NS['m']+'}'):
                bits.append(f'⟦M{math}⟧');math+=1
            else: bits.extend(child.xpath('.//w:t/text()',namespaces=NS))
        records.append({'index':i,'text':plain,'protected_text':''.join(bits),'math':math,'images':len(p.xpath('.//w:drawing',namespaces=NS))})
    (QA/f'v{version}_paragraphs.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    (QA/f'v{version}_paragraphs.txt').write_text('\n\n'.join(f"P{x['index']:03d} {x['protected_text']}" for x in records),encoding='utf-8')
for version,name in [(74,'检测报告_2026.10.07v74_.pdf'),(68,'检测报告_2026.10.04v68_.pdf')]:
    pdf=fitz.open(Path('C:/Users/Quant/Downloads')/name)
    pages=[]; colors=Counter()
    for i,p in enumerate(pdf):
        spans=[]
        for b in p.get_text('dict')['blocks']:
            for line in b.get('lines',[]):
                for s in line['spans']:
                    spans.append({'text':s['text'],'color':s['color'],'bbox':s['bbox']})
                    colors[s['color']]+=len(s['text'])
        pages.append({'page':i+1,'text':p.get_text(),'spans':spans})
        if i==0: p.get_pixmap(dpi=110).save(QA/f'report_v{version}_front.png')
    (QA/f'report_v{version}_pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
    (QA/f'report_v{version}.txt').write_text('\n\n'.join(f"PAGE {p['page']}\n{p['text']}" for p in pages),encoding='utf-8')
    print(json.dumps({'version':version,'pages':len(pdf),'colors':colors.most_common(12),'first_page':pages[0]['text']},ensure_ascii=False))
