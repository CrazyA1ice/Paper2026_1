from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,re,hashlib,copy
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1'); scratch=root/'review_scratch/v75_high_priority_20261008'
src=root/'word_output/2026.10.07v74.docx'; dst=root/'word_output/2026.10.08v75.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def sem(z):return None if z is None else (z.tag,sorted(z.attrib.items()),z.text,[(sem(c),c.tail) for c in z])
with ZipFile(src) as a,ZipFile(dst) as b:
 assert a.namelist()==b.namelist()
 changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]; assert changed==['word/document.xml']
 x=E.fromstring(a.read('word/document.xml')); y=E.fromstring(b.read('word/document.xml'))
 for path in ['//m:oMath','//w:tbl','//w:rPr','//w:sectPr']:
  assert [sem(z) for z in x.xpath(path,namespaces=ns)]==[sem(z) for z in y.xpath(path,namespaces=ns)],path
 xp=x.find('w:body',ns).findall('w:p',ns); yp=y.find('w:body',ns).findall('w:p',ns)
 def txt(z):return ''.join(z.xpath('.//w:t/text()',namespaces=ns))
 text_changed=[];format_changed=[]
 for i,(p,q) in enumerate(zip(xp,yp)):
  if txt(p)!=txt(q):text_changed.append(i)
  assert re.findall(r'\d+(?:\.\d+)?',txt(p))==re.findall(r'\d+(?:\.\d+)?',txt(q))
  if sem(p.find('w:pPr',ns))!=sem(q.find('w:pPr',ns)):format_changed.append(i)
 assert text_changed==[15,17,49,60,68,105],text_changed
 assert format_changed==[41,61,75],format_changed
 for i in format_changed:
  p=copy.deepcopy(yp[i]);pr=p.find('w:pPr',ns);keep=p.find('w:pPr/w:keepNext',ns);original_keep=xp[i].find('w:pPr/w:keepNext',ns)
  if original_keep is None:pr.remove(keep)
  else:keep.attrib.clear();keep.attrib.update(original_keep.attrib)
  if xp[i].find('w:pPr',ns) is None:assert len(pr)==0 and len(pr.attrib)==0
  else:assert sem(pr)==sem(xp[i].find('w:pPr',ns)),i
 assert hashlib.sha256(src.read_bytes()).hexdigest()=='a6a4ab0e3d57004a9815dfe73a8886e1dac8a28050f9fa1cb6fc9035bd9589c1'
 result={'passed':True,'changed_text_paragraphs':text_changed,'only_paragraph_format_change':{'paragraphs':[41,61,75],'change':'keep-with-next'},'protected_math_objects':len(x.xpath('//m:oMath',namespaces=ns)),'tables':len(x.xpath('//w:tbl',namespaces=ns)),'other_package_parts_unchanged':True,'all_numeric_sequences_preserved':True,'original_unchanged':True,'final_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()}
 (scratch/'final_preservation_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print('Final preservation verification passed')
render=(scratch/'render_pdf_review.py').read_text(encoding='utf8').replace("pdf=fitz.open(out/'v75_direct_export.pdf')","out=out/'final_render';out.mkdir(exist_ok=True);pdf=fitz.open(out.parent/'v75_last_direct.pdf')")
(scratch/'render_final.py').write_text(render,encoding='utf8')


