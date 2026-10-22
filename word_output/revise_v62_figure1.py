"""Replace Figure 1 only, retaining its location and width in v61."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json
import posixpath
import hashlib

from lxml import etree
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'word_output/2026.10.03v61.docx'
TARGET = ROOT / 'word_output/2026.10.03v62.docx'
FIGURE = ROOT / 'paper_figures/fig1_selected_v62/fig1.png'
QA = ROOT / 'word_output/v62_figure1_review'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

with ZipFile(SOURCE) as original:
    old_xml = original.read('word/document.xml')
    root = etree.fromstring(old_xml)
    drawing = root.xpath('.//w:drawing', namespaces=NS)[0]
    rid = drawing.find('.//a:blip', NS).get('{' + NS['r'] + '}embed')
    rels = etree.fromstring(original.read('word/_rels/document.xml.rels'))
    image_target = next(rel.get('Target') for rel in rels if rel.get('Id') == rid)
    image_part = posixpath.normpath(posixpath.join('word', image_target))
    with Image.open(FIGURE) as image:
        pixels = image.size
        if image_part.lower().endswith(('.jpg', '.jpeg')):
            converted = BytesIO()
            image.convert('RGB').save(converted, format='JPEG', quality=97, dpi=(600, 600))
            image_bytes = converted.getvalue()
        else:
            assert image_part.lower().endswith('.png'), image_part
            image_bytes = FIGURE.read_bytes()
    extent = drawing.find('.//wp:extent', NS)
    cx = int(extent.get('cx'))
    old_cy = int(extent.get('cy'))
    cy = round(cx * pixels[1] / pixels[0])
    extent.set('cy', str(cy))
    drawing.find('.//a:xfrm/a:ext', NS).set('cy', str(cy))
    new_xml = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
    with ZipFile(TARGET, 'w') as output:
        for item in original.infolist():
            payload = new_xml if item.filename == 'word/document.xml' else image_bytes if item.filename == image_part else original.read(item.filename)
            output.writestr(item, payload)

# Only the Figure 1 raster and its two height attributes may differ.
with ZipFile(SOURCE) as before, ZipFile(TARGET) as after:
    assert before.namelist() == after.namelist()
    changed = [name for name in before.namelist() if before.read(name) != after.read(name)]
    assert set(changed) == {'word/document.xml', image_part}, changed
    restored = etree.fromstring(after.read('word/document.xml'))
    first = restored.xpath('.//w:drawing', namespaces=NS)[0]
    first.find('.//wp:extent', NS).set('cy', str(old_cy))
    first.find('.//a:xfrm/a:ext', NS).set('cy', str(old_cy))
    assert etree.tostring(restored, method='c14n') == etree.tostring(etree.fromstring(old_xml), method='c14n')

QA.mkdir(exist_ok=True)
record = {'source': str(SOURCE), 'target': str(TARGET), 'figure': str(FIGURE),
          'width_mm': cx/36000, 'height_mm': cy/36000, 'old_height_mm': old_cy/36000,
          'changed_zip_parts': changed, 'body_tables_equations_other_figures_unchanged': True,
          'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'target_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest()}
(QA / 'change_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
