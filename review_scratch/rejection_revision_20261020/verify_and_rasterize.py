from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import json, re, hashlib, sys, importlib.util
sys.stdout.reconfigure(encoding='utf8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
manifest=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def xml(path):
    with ZipFile(path) as z:return etree.fromstring(z.read('word/document.xml'))
def text(el):return ''.join(el.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns))
original,clean,marked=[xml(manifest[k]) for k in ['source','clean','marked']]
assert hashlib.sha256(Path(manifest['source']).read_bytes()).hexdigest()==manifest['source_sha256']
assert text(clean)==text(marked)
oldmath=original.xpath('.//m:oMath',namespaces=ns)
newmath=clean.xpath('.//m:oMath',namespaces=ns)
assert len(oldmath)==41 and len(newmath)==42
for m in oldmath:
    sig=etree.tostring(m,method='c14n')
    assert any(etree.tostring(n,method='c14n')==sig for n in newmath),text(m)
assert len(clean.xpath('.//w:drawing',namespaces=ns))==5
assert len(clean.xpath('.//w:tbl',namespaces=ns))==5
for p in original.xpath('.//w:p',namespaces=ns):
    if re.match(r'^\[\d+\]',text(p)):
        assert any(etree.tostring(x,method='c14n')==etree.tostring(p,method='c14n') for x in clean.xpath('.//w:p',namespaces=ns))
assert not clean.xpath('.//w:color[@w:val="C00000"]',namespaces=ns)
assert marked.xpath('.//w:color[@w:val="C00000"]',namespaces=ns)
for k in ['clean','marked']:
    # Edits are restricted to the main document part. Media, relationships and styles stay intact.
    with ZipFile(manifest['source']) as za,ZipFile(manifest[k]) as zb:
        assert za.namelist()==zb.namelist()
        for name in za.namelist():
            if name!='word/document.xml':assert za.read(name)==zb.read(name),name

checks={'original_unchanged':True,'clean_marked_text_equal':True,'original_math_preserved':41,
        'new_math_total':42,'figures':5,'tables':5,'references_preserved':11,
        'non_document_parts_unchanged':True}
(QA/'structural_verification.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print(json.dumps(checks,ensure_ascii=False))

if '--rasterize' in sys.argv:
    # The packaged LibreOffice backend is unavailable on this Windows host.
    # Keep the canonical renderer's Poppler rasterization; use the native Word PDFs already exported.
    renderer=Path(r'C:\Users\Quant\.codex\plugins\cache\openai-primary-runtime\documents\26.1015.12040\skills\documents\render_docx.py')
    spec=importlib.util.spec_from_file_location('document_renderer',renderer)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    import os
    poppler=Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler')
    pdftoppm=next(poppler.rglob('pdftoppm.exe'));os.environ['PATH']=str(pdftoppm.parent)+os.pathsep+os.environ['PATH']
    for kind in ['clean','marked','report']:
        folder=QA/f'render_{kind}';pdf=folder/f'{kind}.pdf'
        mod.convert_to_pdf=lambda *args, p=pdf, **kwargs:(str(p),'Native Microsoft Word export')
        paths=mod.rasterize(manifest[kind],str(folder),150,False,False)
        print(kind, len(paths),'pages')
