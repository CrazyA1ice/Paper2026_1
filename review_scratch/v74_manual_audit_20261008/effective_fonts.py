from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v74_manual_audit_20261008';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};lines=[]
for ver in ['73','74']:
 with ZipFile(root/f'word_output/2026.10.07v{ver}.docx') as z:
  d=E.fromstring(z.read('word/document.xml'));s=E.fromstring(z.read('word/styles.xml'));sm={a.get('{'+ns['w']+'}styleId'):a for a in s.findall('w:style',ns)};default_sid=next(k for k,a in sm.items() if a.get('{'+ns['w']+'}type')=='paragraph' and a.get('{'+ns['w']+'}default')=='1')
  def props(e):return {} if e is None else {E.QName(n).localname:{E.QName(k).localname:v for k,v in n.attrib.items()} for n in e}
  def merge(*items):
   v={}
   for item in items:
    for k,attrs in item.items():v[k]={**v.get(k,{}),**attrs}
   return v
  def sty(k):
   a=sm.get(k)
   if a is None:return {}
   b=a.find('w:basedOn',ns)
   return merge(sty(b.get('{'+ns['w']+'}val')) if b is not None else {},props(a.find('w:rPr',ns)))
  default=props(s.find('w:docDefaults/w:rPrDefault/w:rPr',ns));pars=d.find('w:body',ns).findall('w:p',ns)
  for i in [1,3,4,9,10,11,12,22,49,68,105,110,112]:
   p=pars[i];ps=p.find('w:pPr/w:pStyle',ns);pid=ps.get('{'+ns['w']+'}val') if ps is not None else default_sid;items=[]
   for r in p.findall('w:r',ns):
    text=''.join(r.xpath('.//w:t/text()',namespaces=ns))
    if not text:continue
    rs=r.find('w:rPr/w:rStyle',ns);rid=rs.get('{'+ns['w']+'}val') if rs is not None else None;v=merge(default,sty(pid),sty(rid),props(r.find('w:rPr',ns)))
    items.append({'text':text[:23],'sz':v.get('sz'),'fonts':v.get('rFonts'),'character_style':rid})
   lines.append('V'+ver+' P'+str(i)+' '+json.dumps(items[:4],ensure_ascii=False))
(out/'effective_fonts.txt').write_text('\n'.join(lines),encoding='utf8');print('Complete')
