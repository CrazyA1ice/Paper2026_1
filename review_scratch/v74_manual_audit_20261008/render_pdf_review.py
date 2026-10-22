from pathlib import Path
import sys,json
from PIL import Image,ImageOps,ImageDraw
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v74_manual_audit_20261008';sys.path.insert(0,str(root/'review_scratch/figureqa_dependencies'));import fitz
pdf=fitz.open(out/'v74_direct_export.pdf');texts=[];thumbs=[];records=[]
for i,p in enumerate(pdf):
 t=p.get_text();texts.append(f'PAGE {i+1}\n'+t);pix=p.get_pixmap(matrix=fitz.Matrix(1.25,1.25));pix.save(out/f'page-{i+1:02d}.png');im=Image.open(out/f'page-{i+1:02d}.png').convert('RGB');im.thumbnail((595,842));canvas=Image.new('RGB',(615,882),'#e3e3e3');canvas.paste(im,((615-im.width)//2,30));ImageDraw.Draw(canvas).text((12,7),str(i+1),fill='black');thumbs.append(canvas);records.append({'page':i+1,'chars':len(t),'text_start':t[:150],'text_end':t[-150:],'image_count':len(p.get_images()),'captions':[line for line in t.splitlines() if line.startswith(('图1','图2','图3','图4','图5','表1','表2','表3'))]})
for k in range(0,len(thumbs),6):
 group=thumbs[k:k+6];montage=Image.new('RGB',(615*3,882*((len(group)+2)//3)),'white')
 for j,im in enumerate(group):montage.paste(im,((j%3)*615,(j//3)*882))
 montage.save(out/f'montage-{k//6+1}.png')
(out/'pdf_text.txt').write_text('\n\n'.join(texts),encoding='utf8');(out/'pdf_pages.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'pages':len(pdf),'records':records},ensure_ascii=False))
