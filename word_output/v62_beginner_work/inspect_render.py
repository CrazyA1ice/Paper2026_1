import sys,json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,r'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\figureqa_dependencies')
import fitz
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parent/'render';d=fitz.open(p/'guide.pdf')
texts=[];issues=[]
for i,page in enumerate(d):
 text=page.get_text();texts.append(text)
 if '\ufffd' in text:issues.append([i+1,'replacement character'])
 page.get_pixmap(matrix=fitz.Matrix(120/72,120/72),alpha=False).save(p/f'page-{i+1:02}.png')
 for b in page.get_text('dict')['blocks']:
  if 'lines' not in b:continue
  for l in b['lines']:
   for s in l['spans']:
    x0,y0,x1,y1=s['bbox']
    if x0<45 or x1>569 or y0<28 or y1>770:issues.append([i+1,s['text'][:40],s['bbox']])
 print(i+1,len(text),text[:65].replace('\n',' '))
for start in range(0,len(d),6):
 canvas=Image.new('RGB',(1200,((min(6,len(d)-start)+1)//2)*800),'#dddddd');draw=ImageDraw.Draw(canvas)
 for j in range(min(6,len(d)-start)):
  im=Image.open(p/f'page-{start+j+1:02}.png');im.thumbnail((580,755));x=(j%2)*600;y=(j//2)*800;canvas.paste(im,(x+10,y+28));draw.text((x+12,y+8),f'PAGE {start+j+1}',fill='black')
 canvas.save(p/f'sheet-{start//6+1:02}.png')
(p/'rendered_text.txt').write_text('\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(texts)),encoding='utf-8')
(p/'render_audit.json').write_text(json.dumps({'page_count':len(d),'issues':issues},ensure_ascii=False,indent=2),encoding='utf-8')
print('pages',len(d),'issues',len(issues),issues[:12])
