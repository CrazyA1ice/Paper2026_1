from pathlib import Path
import json, subprocess, unicodedata
from zipfile import ZipFile
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
POPPLER = Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
PY = r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
PREFLIGHT = r'C:\Users\Quant\.codex\plugins\cache\ars-codex\ars-codex\0.1.28\skills\academic-research-suite\ars\scripts\pdf_read_preflight.py'
data=json.loads((ROOT/'source_inventory.json').read_text(encoding='utf-8'))
for item in data['samples']:
    slug=item['slug']
    r=subprocess.run([PY,PREFLIGHT,str(BASE/item['filename'])],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (ROOT/f'{slug}_preflight_stdout.txt').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
    subprocess.run([str(POPPLER),'-r','90','-png',str(BASE/item['filename']),str(ROOT/slug)],check=True,capture_output=True)
    files=sorted(ROOT.glob(f'{slug}-*.png'))
    thumbs=[]
    for f in files:
        im=Image.open(f).convert('RGB')
        im.thumbnail((700,1020))
        canvas=Image.new('RGB',(720,1050),'#dddddd')
        canvas.paste(im,((720-im.width)//2,22))
        ImageDraw.Draw(canvas).text((12,5),f.name,fill='black')
        thumbs.append(canvas)
    sheet=Image.new('RGB',(720*len(thumbs),1050),'white')
    for i,im in enumerate(thumbs): sheet.paste(im,(i*720,0))
    sheet.save(ROOT/f'{slug}_overview.jpg')
    normalized=unicodedata.normalize('NFKC',(ROOT/f'{slug}.txt').read_text(encoding='utf-8'))
    (ROOT/f'{slug}_normalized.txt').write_text(normalized,encoding='utf-8')
    print(slug,'rendered',len(files),'preflight_exit',r.returncode)
path=BASE/data['manuscript']['filename']
with ZipFile(path) as z:
    for name in data['manuscript']['media']:
        (ROOT/Path(name).name).write_bytes(z.read(name))
