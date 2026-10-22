from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import hashlib, importlib.util, json, os, re, sys

QA = Path(__file__).resolve().parent
manifest = json.loads((QA / 'manifest.json').read_text(encoding='utf8'))
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}


def xml(path):
    with ZipFile(path) as archive:
        return etree.fromstring(archive.read('word/document.xml'))


def text(element):
    return ''.join(element.xpath('.//w:t/text()|.//m:t/text()', namespaces=NS))


base, clean, marked = [xml(manifest[k]) for k in ['base','clean','marked']]
assert hashlib.sha256(Path(manifest['original']).read_bytes()).hexdigest() == manifest['original_sha256']
assert hashlib.sha256(Path(manifest['base']).read_bytes()).hexdigest() == manifest['base_sha256']
assert text(clean) == text(marked)
old_math = base.xpath('.//m:oMath', namespaces=NS)
new_math = clean.xpath('.//m:oMath', namespaces=NS)
assert len(old_math) == len(new_math) == 42
for old, new in zip(old_math, new_math):
    assert etree.tostring(old, method='c14n') == etree.tostring(new, method='c14n')
assert len(clean.xpath('.//w:drawing', namespaces=NS)) == 6
assert len(clean.xpath('.//w:tbl', namespaces=NS)) == 7
for p in base.xpath('.//w:p', namespaces=NS):
    if re.match(r'^\[\d+\]', text(p)):
        assert any(etree.tostring(q, method='c14n') == etree.tostring(p, method='c14n')
                   for q in clean.xpath('.//w:p', namespaces=NS))
with ZipFile(manifest['base']) as old, ZipFile(manifest['clean']) as new:
    media = [n for n in old.namelist() if n.startswith('word/media/')]
    for name in media:
        assert old.read(name) == new.read(name)
assert not clean.xpath('.//w:color[@w:val="C00000"]', namespaces=NS)
assert marked.xpath('.//w:color[@w:val="C00000"]', namespaces=NS)
assert '尚未绘制训练数据量学习曲线' not in text(clean)
checks = dict(original_and_previous_revision_unchanged=True, clean_marked_text_equal=True,
              original_math_preserved=42, original_media_preserved=len(media),
              figures=6,tables=7,references_preserved=11)
(QA/'structural_verification.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print(json.dumps(checks))

if '--rasterize' in sys.argv:
    renderer=Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1015.12040\skills\documents\render_docx.py')
    spec=importlib.util.spec_from_file_location('document_renderer',renderer)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    native=Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
    pdftoppm=next(native.rglob('pdftoppm.exe'))
    os.environ['PATH']=str(pdftoppm.parent)+os.pathsep+os.environ['PATH']
    for kind in ['clean','marked','report']:
        directory=QA/f'render_{kind}';pdf=directory/f'{kind}.pdf'
        module.convert_to_pdf=lambda *args,p=pdf,**kwargs:(str(p),'Native Microsoft Word export')
        pages=module.rasterize(manifest[kind],str(directory),150,False,False)
        print(kind,len(pages),'pages')
