from pathlib import Path
import json, re, unicodedata
import pdfplumber
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'source_inventory.json').read_text(encoding='utf-8'))
ps=data['manuscript']['paragraphs']
counts={}
for name,a,b in [('引言',10,14),('方法',15,54),('实验',55,89),('结语',90,92),('中文摘要含标签',5,5)]:
    selected=[p for p in ps if a<=p['index']<=b]
    # 原始段落文本剔除附加的公式提取标记，单独呈现叙述文字计数。
    ss=[p['text'].split(' [公式文本:')[0] for p in selected if p['style'] not in ['JournalEquation','JournalFigure']]
    counts[name]={'nonspace_chars':len(re.sub(r'\s+','',''.join(ss))),
                  'cjk_chars':len(re.findall(r'[\u4e00-\u9fff]',''.join(ss)))}
body=sum(counts[k]['nonspace_chars'] for k in ['引言','方法','实验','结语'])
for k in ['引言','方法','实验','结语']: counts[k]['body_percent']=round(counts[k]['nonspace_chars']/body*100,1)
counts['正文叙述合计不含公式表内图内文字']=body
print(json.dumps(counts,ensure_ascii=False,indent=2))
(ROOT/'structure_counts.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2),encoding='utf-8')

for item in data['samples']:
    parts=[]
    with pdfplumber.open(ROOT.parent/item['filename']) as pdf:
        for n,p in enumerate(pdf.pages,1):
            w,h=p.width,p.height
            if n==1:
                boxes=[('first_full',(0,0,w,h))]
            else:
                boxes=[('left',(0,0,w/2,h)),('right',(w/2,0,w,h))]
            for label,box in boxes:
                txt=unicodedata.normalize('NFKC',p.crop(box).extract_text(x_tolerance=2,y_tolerance=3) or '')
                parts.append(f'===== PDF页{n} {label} =====\n'+txt)
    (ROOT/(item['slug']+'_columns.txt')).write_text('\n\n'.join(parts),encoding='utf-8')
    print(item['slug'], 'dimensions',item['pages'][0]['width'],item['pages'][0]['height'])
for f in sorted(ROOT.glob('image*')):
    if f.suffix.lower() not in ['.png','.jpeg','.jpg']: continue
    im=Image.open(f).convert('RGB'); print(f.name,im.size)
    im.thumbnail((1300,1500)); im.save(ROOT/(f.stem+'_preview.png'))
