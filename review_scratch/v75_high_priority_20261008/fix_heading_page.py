from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,hashlib
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v75_high_priority_20261008';p=root/'word_output/2026.10.08v75.docx';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'};q=lambda n:'{'+ns['w']+'}'+n
with ZipFile(p) as z:infos=z.infolist();parts={a.filename:z.read(a.filename) for a in infos}
d=E.fromstring(parts['word/document.xml']);paras=d.find('w:body',ns).findall('w:p',ns);heading=paras[61];assert ''.join(heading.xpath('.//w:t/text()',namespaces=ns))=='2 实验与结果分析'
pr=heading.find('w:pPr',ns);assert pr is not None
keep=pr.find('w:keepNext',ns)
if keep is None:keep=E.Element(q('keepNext'));pr.insert(0,keep)
keep.set(q('val'),'1');parts['word/document.xml']=E.tostring(d,encoding='UTF-8',xml_declaration=True,standalone=True)
temp=out/'v75_layout_fixed.docx'
with ZipFile(temp,'w') as z:
 for a in infos:z.writestr(a,parts[a.filename])
p.write_bytes(temp.read_bytes())
a=json.loads((out/'edit_validation.json').read_text(encoding='utf8'));a['output_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();a['formatting_preserved']='Fonts, paragraph spacing, image size and all other formatting preserved; added keep-with-next only to chapter 2 heading';a['layout_fix']={'paragraph_index':61,'heading':'2 实验与结果分析','change':'keep-with-next','reason':'Prevent heading isolation created by text-length changes'};(out/'edit_validation.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
print('Applied one heading pagination fix')
