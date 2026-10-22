from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
import io, json
q=Path(__file__).resolve().parent
m=json.loads((q/'manifest.json').read_text(encoding='utf8'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
w=ns['w']
for k in ['clean','marked']:
    path=Path(m[k]);out=io.BytesIO()
    with ZipFile(path) as zin,ZipFile(out,'w',ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            raw=zin.read(info.filename)
            if info.filename=='word/document.xml':
                root=etree.fromstring(raw)
                p=next(p for p in root.findall('w:body/w:p',ns) if ''.join(p.xpath('.//w:t/text()',namespaces=ns))=='参考文献')
                pp=p.find('w:pPr',ns)
                if pp is None:pp=etree.Element('{'+w+'}pPr');p.insert(0,pp)
                if pp.find('w:keepNext',ns) is None:etree.SubElement(pp,'{'+w+'}keepNext')
                raw=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
            zout.writestr(info,raw)
    path.write_bytes(out.getvalue())
print('Reference heading kept with first reference')
