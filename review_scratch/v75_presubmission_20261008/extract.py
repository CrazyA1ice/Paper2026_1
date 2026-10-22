from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image
import json,hashlib,re
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v75_presubmission_20261008';out.mkdir(exist_ok=True)
source=root/'word_output/2026.10.08v75.docx';old=root/'review_scratch/v75_high_priority_20261008/render_v75_last_readonly.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def txt(e):return ''.join(n.text or '' for n in e.iter() if n.tag in ['{'+ns['w']+'}t','{'+ns['m']+'}t'])
with ZipFile(source) as z,ZipFile(old) as oz:
 x=E.fromstring(z.read('word/document.xml'));ox=E.fromstring(oz.read('word/document.xml'));body=x.find('w:body',ns);ps=body.findall('w:p',ns);ops=ox.find('w:body',ns).findall('w:p',ns)
 lines=[];pi=0;ti=0
 for n in body:
  if n.tag.endswith('}p'):lines.append(f'[P{pi}] '+txt(n));pi+=1
  elif n.tag.endswith('}tbl'):
   ti+=1;lines.append(f'[TABLE {ti}]');lines+=[' | '.join(txt(c) for c in row.findall('w:tc',ns)) for row in n.findall('w:tr',ns)]
 changes=[{'index':i,'before':txt(p),'after':txt(q)} for i,(p,q) in enumerate(zip(ops,ps)) if txt(p)!=txt(q)]
 math=[E.tostring(n) for n in x.xpath('//m:oMath',namespaces=ns)];omath=[E.tostring(n) for n in ox.xpath('//m:oMath',namespaces=ns)]
 table=[E.tostring(n) for n in x.xpath('//w:tbl',namespaces=ns)];otable=[E.tostring(n) for n in ox.xpath('//w:tbl',namespaces=ns)]
 media=[n for n in z.namelist() if n.startswith('word/media/')];same_media=all(n in oz.namelist() and z.read(n)==oz.read(n) for n in media)
 citations=[]
 for i,p in enumerate(ps):
  for r in p.findall('w:r',ns):
   t=txt(r)
   if re.search(r'\[\d+(?:[-,，]\d+)*\]',t):citations.append({'paragraph':i,'text':t,'vertical':r.xpath('w:rPr/w:vertAlign/@w:val',namespaces=ns)})
 issues={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'old_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'paragraph_count':len(ps),'old_paragraph_count':len(ops),'changes':changes,'math_exactly_same':math==omath,'math_count':len(math),'tables_exactly_same':table==otable,'media_exactly_same':same_media,'citation_runs':citations,'tracked_insertions':len(x.xpath('//w:ins',namespaces=ns)),'tracked_deletions':len(x.xpath('//w:del',namespaces=ns)),'comment_references':len(x.xpath('//w:commentReference',namespaces=ns)),'comments_part':'word/comments.xml' in z.namelist(),'unusual_strings':[t for p in ps for t in re.findall(r'TODO|待补充|待填写|ChatGPT|AIGC|占位',txt(p))],'changed_package_parts':[n for n in z.namelist() if n not in oz.namelist() or z.read(n)!=oz.read(n)]}
 (out/'audit_extract.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf8');(out/'manuscript.txt').write_text('\n\n'.join(lines),encoding='utf8');(out/'changes.txt').write_text('\n\n'.join(f"[P{c['index']}]\nBEFORE: {c['before']}\nAFTER: {c['after']}" for c in changes),encoding='utf8')
print('Extracted manuscript and comparison')
