from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
audit=json.loads((QA/'audit.json').read_text(encoding='utf-8'))
path=Path(audit['output'])
assert sha256(path.read_bytes()).hexdigest()==audit['output_sha256']
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+ns['w']+'}'
with ZipFile(path) as z:
    infos=z.infolist();members={i.filename:z.read(i.filename) for i in infos}
old=E.fromstring(members['word/document.xml'])
root=E.fromstring(members['word/document.xml'])
body=root.find('w:body',ns)

def keep(p,kind):
    pp=p.find('w:pPr',ns)
    if pp is None:
        pp=E.Element(W+'pPr');p.insert(0,pp)
    prop=pp.find('w:'+kind,ns)
    if prop is None:
        prop=E.Element(W+kind)
        # Paragraph property order: style, keepNext, keepLines, remaining props.
        pos=1 if len(pp) and pp[0].tag==W+'pStyle' else 0
        if kind=='keepLines' and pp.find('w:keepNext',ns) is not None:pos+=1
        pp.insert(pos,prop)
    prop.set(W+'val','1')

# Keep the short three-row data table on one page, without changing its
# grid, values, font, row heights or spacing.
table=root.find('.//w:tbl',ns)
for row in table.findall('w:tr',ns)[:-1]:
    for p in row.findall('.//w:p',ns):keep(p,'keepNext')

# Keep the original English title, author and abstract together. The
# English words and all paragraph styles remain exactly as supplied.
title=next(p for p in body if ''.join(p.xpath('.//w:t/text()',namespaces=ns))=='Multivariate network traffic forecasting with adaptive multiscale weighting')
start=list(body).index(title)
block=list(body)[start:]
block=[p for p in block if p.tag==W+'p']
assert len(block)==6
for p in block[:-1]:keep(p,'keepNext')
for p in block:keep(p,'keepLines')

def without_keep(x):
    x=deepcopy(x)
    for p in x.xpath('.//w:p',namespaces=ns):
        for q in p.xpath('./w:pPr/w:keepNext | ./w:pPr/w:keepLines',namespaces=ns):q.getparent().remove(q)
        pp=p.find('w:pPr',ns)
        if pp is not None and not len(pp) and not pp.attrib:p.remove(pp)
    return E.tostring(x,method='c14n')

assert without_keep(old)==without_keep(root)
assert old.xpath('.//w:t/text() | .//m:t/text()',namespaces=ns)==root.xpath('.//w:t/text() | .//m:t/text()',namespaces=ns)
with ZipFile(path,'w') as z:
    for info in infos:
        z.writestr(info,E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='word/document.xml' else members[info.filename])
audit['output_sha256']=sha256(path.read_bytes()).hexdigest()
audit['pagination_only_adjustments']=['表1整表同页','英文题名、作者信息及摘要保持同页']
audit['tables_unchanged']='All values and formatting preserved except paragraph keepNext in table 1'
audit['all_other_source_nodes_unchanged']='All words, drawings, native math and formatting preserved except documented keepNext/keepLines pagination properties'
(QA/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
note=path.parent/'修改与核对说明.md'
txt=note.read_text(encoding='utf-8')
txt=txt.replace('原稿、表格、图片、原有公式、版式及其他段落保持不变。','原稿、表格数值、图片、原有公式及其他段落文字保持不变。字号、字体、页边距与样式沿用V3；仅设置局部分页约束，使表1整表同页、英文题名和摘要不被拆开。')
note.write_text(txt,encoding='utf-8')
print(json.dumps({'output':str(path),'output_sha256':audit['output_sha256'],'only_pagination_properties_changed':True},ensure_ascii=False))
