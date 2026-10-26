from pathlib import Path
from zipfile import ZipFile
import json
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
root = Path(__file__).resolve().parents[2]
source = root/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV8_指定项目修订稿.docx'
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(source) as z:
    doc = E.fromstring(z.read('word/document.xml'))
    body = doc.find('w:body', ns)
    lines = []
    for i,p in enumerate(body):
        text = ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=ns))
        lines.append(f'{i}: {text}')
    (Path(__file__).parent/'source_paragraphs.txt').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))
    math = doc.xpath('//m:oMath',namespaces=ns)
    for i in [0,8,15,23]:
        print('MATH',i,E.tostring(math[i],encoding='unicode')[:3500])
