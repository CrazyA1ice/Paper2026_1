from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
import json,hashlib
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');s=root/'review_scratch/v75_high_priority_20261008';f=root/'word_output/2026.10.08v75.docx';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(f) as z: info=z.infolist();data={i.filename:z.read(i.filename) for i in info}
x=E.fromstring(data['word/document.xml']);ps=x.find('w:body',ns).findall('w:p',ns);added=[]
for i,p in enumerate(ps):
 t=''.join(p.xpath('.//w:t/text()',namespaces=ns))
 if t.startswith('2.2 总体预测性能') or t.startswith('趋势项') and t.endswith('预测长度H：'):
  pr=p.find('w:pPr',ns)
  if pr is None:pr=E.Element('{'+ns['w']+'}pPr');p.insert(0,pr)
  keep=pr.find('w:keepNext',ns)
  if keep is None:keep=E.Element('{'+ns['w']+'}keepNext');pr.insert(0,keep)
  keep.set('{'+ns['w']+'}val','1');added.append({'paragraph_index':i,'text':t,'change':'keep-with-next'})
assert len(added)==2,added
data['word/document.xml']=E.tostring(x,encoding='UTF-8',xml_declaration=True,standalone=True);temp=s/'layout_last.docx'
with ZipFile(temp,'w',ZIP_DEFLATED) as z:
 for i in info:z.writestr(i,data[i.filename])
f.write_bytes(temp.read_bytes());v=json.loads((s/'edit_validation.json').read_text(encoding='utf8'));v['additional_layout_fixes']=added;v['output_sha256']=hashlib.sha256(f.read_bytes()).hexdigest();(s/'edit_validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(added)
