"""Audit Word PDFs after the required visual render; does not replace inspection."""
from pathlib import Path
import json, re, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'figureqa_dependencies'))
import fitz

QA=Path(__file__).resolve().parent
manifest=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
def normalized(s):return re.sub(r'\s|\u00ad','',s)

pdfs={kind:fitz.open(QA/f'render_{kind}'/f'{kind}.pdf') for kind in ['clean','marked','report']}
assert len(pdfs['clean'])==len(pdfs['marked'])
texts={kind:normalized(''.join(p.get_text() for p in pdf)) for kind,pdf in pdfs.items()}
assert texts['clean']==texts['marked']
for phrase in ['2.6周期基线与稳定性补充实验','表6共同测试起点上的周期基线比较',
               '图6不同训练历史长度下的测试MSE','表7三个连续测试时段的MSE',
               '2.7泛化能力与研究局限','47.80%','29.69%','144']:
    if phrase=='144':
        assert phrase in texts['report']
    else:
        assert phrase in texts['clean'],phrase
bounds=[]
for kind,pdf in pdfs.items():
    for i,page in enumerate(pdf,1):
        assert page.get_text().strip(),(kind,i,'empty page')
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                        bounds.append(dict(kind=kind,page=i,text=span['text'],bbox=span['bbox']))
assert not bounds,bounds
report=dict(pages={k:len(v) for k,v in pdfs.items()},clean_marked_pdf_text_equal=True,
            supplement_titles_and_results_present=True,out_of_page_text_spans=bounds)
(QA/'rendered_text_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
