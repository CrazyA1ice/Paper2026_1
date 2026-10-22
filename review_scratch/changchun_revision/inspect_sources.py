from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re
from lxml import etree
from pypdf import PdfReader
from pdf2image import convert_from_path

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
SRC = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
DOC = ROOT / 'word_output/补充实验_20261020/基于自适应多尺度加权的多变量网络流量预测方法_补充实验净稿.docx'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
native = Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
poppler = str(next(native.rglob('pdftoppm.exe')).parent)
records = []
for i, path in enumerate(sorted(SRC.glob('*.pdf')), 1):
    reader = PdfReader(path)
    texts = [p.extract_text(extraction_mode='layout') for p in reader.pages]
    (QA/f'sample_{i}.txt').write_text('\n\n'.join(f'PAGE {j+1}\n{s}' for j,s in enumerate(texts)), encoding='utf8')
    selected = sorted(set([1,2,len(reader.pages)]))
    for page in selected:
        im = convert_from_path(str(path), dpi=120, first_page=page, last_page=page, poppler_path=poppler)[0]
        im.save(QA/f'sample_{i}_page_{page}.png')
    records.append({'id':i,'file':str(path),'pages':len(reader.pages),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'selected':selected})
    print('SAMPLE', i, path.name, len(reader.pages), 'pages')
    print(texts[0][:6500])
    print('HEADINGS', re.findall(r'(?m)^\s*[0-9０-９]+(?:[.．][0-9０-９]+)?\s+[^\n]{2,55}', '\n'.join(texts)))
with ZipFile(DOC) as z:
    xml = etree.fromstring(z.read('word/document.xml'))
    items=[]
    for i, e in enumerate(xml.find('w:body',NS)):
        text=''.join(e.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))
        item={'index':i,'type':etree.QName(e).localname,'text':text,
              'equations':len(e.xpath('.//m:oMath',namespaces=NS)), 'drawings':len(e.xpath('.//w:drawing',namespaces=NS))}
        if item['type']=='tbl':
            item['rows']=[[''.join(c.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS)) for c in r.findall('w:tc',NS)] for r in e.findall('w:tr',NS)]
        items.append(item)
    media=QA/'source_media'; media.mkdir(exist_ok=True)
    for n in z.namelist():
        if n.startswith('word/media/'):
            (media/Path(n).name).write_bytes(z.read(n))
    (QA/'source_blocks.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf8')
(QA/'sample_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print('SOURCE_BLOCKS',len(items))
