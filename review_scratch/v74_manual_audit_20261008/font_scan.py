from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from collections import Counter
import json,re
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v74_manual_audit_20261008';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
lines=[]
for version in ['73','74']:
 with ZipFile(root/f'word_output/2026.10.07v{version}.docx') as z:
  d=E.fromstring(z.read('word/document.xml'));s=E.fromstring(z.read('word/styles.xml'));style={a.get('{'+ns['w']+'}styleId'):a for a in s.findall('w:style',ns)}
  normal=next(a for a in s.findall('w:style',ns) if a.get('{'+ns['w']+'}type')=='paragraph' and a.get('{'+ns['w']+'}default')=='1');lines.append('V'+version+' NORMAL '+E.tostring(normal,encoding='unicode')[-3500:]);lines.append('V'+version+' DEFAULT '+E.tostring(s.find('w:docDefaults',ns),encoding='unicode')[-2000:])
  sizes=Counter();wrong=[]
  for i,p in enumerate(d.find('w:body',ns).findall('w:p',ns)):
   if not(11<=i<=110) or p.xpath('.//w:drawing|.//m:oMath',namespaces={**ns,'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}):continue
   text=''.join(p.xpath('.//w:t/text()',namespaces=ns))
   if re.match(r'^(图|表|\d+\s|\d+\.\d+\s)',text) or not text:continue
   c=Counter()
   for r in p.findall('w:r',ns):
    rt=''.join(r.xpath('.//w:t/text()',namespaces=ns));sz=r.xpath('./w:rPr/w:sz/@w:val',namespaces=ns)
    val=sz[0] if sz else 'inherited';c[val]+=len(rt);sizes[val]+=len(rt)
   if c.get('22',0)>0:wrong.append({'p':i,'start':text[:28],'sizes':dict(c)})
  lines.append('V'+version+' BODY_SIZE_COUNTS '+json.dumps(sizes));lines.append('V'+version+' BODY_11pt_PARAGRAPHS '+json.dumps(wrong,ensure_ascii=False))
  theme=E.fromstring(z.read('word/theme/theme1.xml'));lines.append('V'+version+' THEME '+E.tostring(theme.find('.//a:fontScheme',ns),encoding='unicode')[:5500])
(out/'font_scan.txt').write_text('\n'.join(lines),encoding='utf8');print('Complete')

