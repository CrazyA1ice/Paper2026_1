from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json, hashlib, difflib
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1')
out=root/'review_scratch/v74_manual_audit_20261008'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def parse(path):
 with ZipFile(path) as z:
  doc=E.fromstring(z.read('word/document.xml')); ps=[]; tables=[]; blocks=[]
  for child in doc.find('w:body',ns):
   if child.tag==f"{{{ns['w']}}}p":
    i=len(ps); text=''.join(child.xpath('.//w:t/text() | .//m:t/text()',namespaces=ns))
    p={'index':i,'text':text,'math':len(child.xpath('.//m:oMath',namespaces=ns)),'drawing':len(child.xpath('.//w:drawing',namespaces=ns)),'style':child.xpath('./w:pPr/w:pStyle/@w:val',namespaces=ns),'runs':[{'text':''.join(r.xpath('.//w:t/text()',namespaces=ns)),'properties':E.tostring(r.find('w:rPr',ns),encoding='unicode') if r.find('w:rPr',ns) is not None else None} for r in child.findall('w:r',ns)],'ppr':E.tostring(child.find('w:pPr',ns),encoding='unicode') if child.find('w:pPr',ns) is not None else None}; ps.append(p); blocks.append({'p':i})
   elif child.tag==f"{{{ns['w']}}}tbl":
    rows=[[''.join(c.xpath('.//w:t/text() | .//m:t/text()',namespaces=ns)) for c in r.findall('w:tc',ns)] for r in child.findall('w:tr',ns)]; tables.append(rows); blocks.append({'table':len(tables)})
  media=[{'name':n,'size':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if n.startswith('word/media/')]
  footnotes={n:''.join(E.fromstring(z.read(n)).xpath('.//w:t/text()',namespaces=ns)) for n in z.namelist() if n in ['word/footnotes.xml','word/endnotes.xml']}
  stats={'paragraphs':len(ps),'tables':len(tables),'math':len(doc.xpath('.//m:oMath',namespaces=ns)),'images':len(doc.xpath('.//w:drawing',namespaces=ns)),'sections':[E.tostring(s,encoding='unicode') for s in doc.xpath('.//w:sectPr',namespaces=ns)],'tracked_insertions':len(doc.xpath('.//w:ins',namespaces=ns)),'tracked_deletions':len(doc.xpath('.//w:del',namespaces=ns))}
  return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'paragraphs':ps,'tables':tables,'blocks':blocks,'media':media,'footnotes':footnotes,'stats':stats}
new=parse(root/'word_output/2026.10.07v74.docx'); old=parse(root/'word_output/2026.10.07v73.docx')
for label,data in [('v74',new),('v73',old)]:
 (out/f'{label}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 text=[]
 for block in data['blocks']:
  if 'p' in block: text.append(f"[P{block['p']}] {data['paragraphs'][block['p']]['text']}")
  else:
   text.append(f"[TABLE {block['table']}]"); text+=[' | '.join(row) for row in data['tables'][block['table']-1]]
 (out/f'{label}.txt').write_text('\n\n'.join(text),encoding='utf-8')
changes=[]
if len(new['paragraphs'])==len(old['paragraphs']):
 for a,b in zip(old['paragraphs'],new['paragraphs']):
  if a['text']!=b['text']: changes.append({'p':a['index'],'old':a['text'],'new':b['text']})
(out/'v73_v74_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source':new['path'],'sha256':new['sha256'],'stats':new['stats'],'changes':len(changes),'footnotes':new['footnotes']},ensure_ascii=False))
