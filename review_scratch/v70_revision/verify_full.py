from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from PIL import Image
from io import BytesIO
import hashlib
import json
import re
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
source = ROOT / 'word_output/2026.10.04v69.docx'
target = ROOT / 'word_output/2026.10.07v70.docx'
with ZipFile(source) as old, ZipFile(target) as new:
    before = etree.fromstring(old.read('word/document.xml'))
    after = etree.fromstring(new.read('word/document.xml'))
    paragraphs = after.xpath('./w:body/w:p', namespaces=NS)
    text = [''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=NS)) for p in paragraphs]
    manuscript = '\n'.join(text)
    excluded = ['末时状态', '最近状态', '平均变化强度', '两层感知器', '预测步长', '校准',
                '常权重', '早停耐心值', '运维侧', '运行观测', '容量复核', '权重偏好',
                '核心消融', '外部基线', '理应占据', '稍弱', '曲边连接', 'KESHAVARZ', 'AMIN-NEJAD']
    remaining = [(term, [i for i, p in enumerate(text) if term in p]) for term in excluded if term in manuscript]
    assert not remaining, json.dumps(remaining, ensure_ascii=True)
    assert [etree.tostring(x) for x in before.xpath('//m:oMath', namespaces=NS)] == [etree.tostring(x) for x in after.xpath('//m:oMath', namespaces=NS)]
    assert [etree.tostring(x) for x in before.xpath('//w:tbl', namespaces=NS)] == [etree.tostring(x) for x in after.xpath('//w:tbl', namespaces=NS)]
    for number in [2, 3, 5]:
        assert old.read(f'word/media/image{number}.png') == new.read(f'word/media/image{number}.png')
    first = np.asarray(Image.open(BytesIO(old.read('word/media/image4.png'))).convert('RGBA'))
    final = np.asarray(Image.open(BytesIO(new.read('word/media/image4.png'))).convert('RGBA'))
    assert first.shape == final.shape
    assert np.array_equal(first[120:], final[120:])
    reference_order = list(dict.fromkeys(int(n) for n in re.findall(r'\[(\d+)\]', '\n'.join(text[:116]))))
    assert reference_order == list(range(1, 12))
    assert len(re.sub(r'\s', '', text[115])) <= 150
    result = {'excluded_ambiguous_terms_absent': excluded, 'native_math_objects_identical': 41,
              'tables_identical': 3, 'figures_2_3_5_identical': True,
              'figure4_pixels_below_titles_identical': True, 'reference_first_appearance_order': reference_order,
              'chinese_abstract_nonspace_characters': len(re.sub(r'\s', '', text[3][3:])),
              'conclusion_nonspace_characters': len(re.sub(r'\s', '', text[115])),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'target_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (QA / 'final_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
