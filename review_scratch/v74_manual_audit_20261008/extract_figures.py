from pathlib import Path
from zipfile import ZipFile
import json, hashlib, sys
from PIL import Image
from lxml import etree as E
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1'); out=root/'review_scratch/v74_manual_audit_20261008'; ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
with ZipFile(root/'word_output/2026.10.07v74.docx') as z:
 doc=E.fromstring(z.read('word/document.xml')); rels=E.fromstring(z.read('word/_rels/document.xml.rels')); relmap={r.get('Id'):r.get('Target') for r in rels}; figs=[]
 for i,d in enumerate(doc.xpath('.//w:drawing',namespaces=ns),1):
  rid=d.xpath('.//a:blip/@r:embed',namespaces=ns)[0]; name='word/'+relmap[rid]; b=z.read(name); dest=out/f'figure-{i}{Path(name).suffix}'; dest.write_bytes(b); im=Image.open(dest); ext=d.xpath('./wp:inline/wp:extent|./wp:anchor/wp:extent',namespaces=ns)[0]; info={'figure':i,'path':str(dest),'pixels':im.size,'width_cm':int(ext.get('cx'))/360000,'height_cm':int(ext.get('cy'))/360000,'sha256':hashlib.sha256(b).hexdigest()}; figs.append(info)
 (out/'figures.json').write_text(json.dumps(figs,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(figs,ensure_ascii=False))
 styles=E.fromstring(z.read('word/styles.xml')); props=[]
 for i,p in enumerate(doc.find('w:body',ns).findall('w:p',ns)):
  if i in [0,1,2,3,6,9,16,19,22,33,44,56,65,77,84,88,94,98,109,110,111,112]:props.append({'p':i,'ppr':E.tostring(p.find('w:pPr',ns),encoding='unicode') if p.find('w:pPr',ns) is not None else None,'rpr':[E.tostring(r.find('w:rPr',ns),encoding='unicode') if r.find('w:rPr',ns) is not None else None for r in p.findall('w:r',ns)][:3]})
 for n in ['word/footer1.xml','word/footer2.xml','word/header1.xml']:
  if n in z.namelist():print(n, ''.join(E.fromstring(z.read(n)).xpath('.//w:t/text()',namespaces=ns)))
 (out/'format_properties.json').write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding='utf-8')
 print('font/layout extraction complete')
