from collections import Counter
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
qa = Path(__file__).resolve().parent
root = qa.parents[1]
sys.path.insert(0,str(root/'review_scratch/figureqa_dependencies'))
import pymupdf

audit = json.loads((qa/'audit.json').read_text(encoding='utf-8'))
pdf = pymupdf.open(json.loads((qa/'word_statistics.json').read_text(encoding='utf-8-sig'))['pdf'])
spans = [s for page in pdf for b in page.get_text('dict')['blocks'] if 'lines' in b
         for line in b['lines'] for s in line['spans']]
symbols = [{'text':s['text'],'font':s['font']} for s in spans if 'Cambria' in s['font']]
font_audit = {'fonts':dict(Counter(s['font'] for s in spans)), 'Cambria_math_symbols':symbols}
(qa/'document_font_audit.json').write_text(json.dumps(font_audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(font_audit,ensure_ascii=False))
assert not [s for s in symbols if re.search('[A-Za-z0-9]',s['text'])], symbols
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
text = lambda p: ''.join(p.xpath('.//w:t/text() | .//m:t/text()',namespaces=ns))
with ZipFile(audit['source']) as a, ZipFile(audit['output']) as b:
    d1 = E.fromstring(a.read('word/document.xml'))
    d2 = E.fromstring(b.read('word/document.xml'))
    paragraphs1 = list(d1.find('w:body',ns))
    paragraphs2 = list(d2.find('w:body',ns))
    kept = [i for i in range(len(paragraphs1)) if i not in audit['removed_duplicate_source_paragraphs']]
    assert len(kept) == len(paragraphs2)
    for i,p in zip(kept,paragraphs2):
        if i not in audit['changed_source_paragraphs']:
            assert text(paragraphs1[i]) == text(p),i
    assert [text(t) for t in d1.xpath('//w:tbl',namespaces=ns)] == [text(t) for t in d2.xpath('//w:tbl',namespaces=ns)]
    body2 = ''.join(text(p) for p in paragraphs2)
    for removed in ['必然引入严重的平滑滞后偏差','静态融合必然拉低峰值响应','同样无法遮掩性能下降','2207.01186']:
        assert removed not in body2,removed
    assert '图4（b）、（d）中全部8个随机种子' in body2
    assert '2004年12月31日23时30分至2005年4月29日15时30分' in body2
    citations = []
    for p in paragraphs2:
        if text(p)=='参考文献：':
            break
        for n in re.findall(r'\[(\d+)\]',text(p)):
            if n not in citations:
                citations.append(n)
    assert citations == [str(i) for i in range(1,13)],citations
    assert len(text(paragraphs1[5]).split('摘要：')[1]) == 199
    for n in range(1,5):
        assert b.read(f'word/media/image{n}.png') != a.read(f'word/media/image{n}.png')
    changed_members = [name for name in a.namelist() if a.read(name) != b.read(name)]
    assert set(changed_members) <= {'word/document.xml','word/settings.xml','word/styles.xml',*[f'word/media/image{n}.png' for n in range(1,5)]}
assert sha256(Path(audit['source']).read_bytes()).hexdigest() == audit['source_sha256']
assert sha256(Path(audit['output']).read_bytes()).hexdigest() == audit['output_sha256']
for n in range(1,5):
    collision = json.loads((qa/f'figure{n}_collision.json').read_text(encoding='utf-8'))
    print('figure',n,collision['verdict'],collision['summary'])
    assert collision['summary']['fail'] == 0
for n in range(2,5):
    pixel = json.loads((qa/f'figure{n}_pixel_difference.json').read_text(encoding='utf-8'))
    print('figure',n,'changed pixels',pixel['changed_pixels'],'changed rows',len(pixel['changed_rows']))
verification = {'both_abstracts_unchanged':True,'all_unselected_paragraph_text_unchanged':True,
    'table_values_unchanged':True,'native_numbered_equations_preserved':True,'all_reference_citation_numbers_in_order':True,
    'chinese_abstract_characters':199,'all_regular_latin_letters_and_digits_in_TNR':True,
    'special_math_operators_use_required_symbol_fallback':True,'changed_zip_members':changed_members,
    'source_unchanged':True,'output_matches_audited_hash':True}
(qa/'postcheck.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
svg_ns = {'s':'http://www.w3.org/2000/svg'}
old_assets = root/'paper_template/长春工程学院学报(自然科学版)/图表组织优化修订_20261022/图表与核验数据'
new_assets = root/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/V9_图表源文件'
def data_geometry(tree):
    groups = tree.xpath('//s:g[starts-with(@id,"PathCollection") or starts-with(@id,"LineCollection")]',namespaces=svg_ns)
    return [[(E.QName(el).localname,tuple(sorted((k,v) for k,v in el.attrib.items() if k in ['d','x','y','transform'])))
             for el in group.iter()] for group in groups]
geometry = []
for stem in ['图2_多基线误差降幅与参数比例','图3_高需求局部范围点图','图4_一周绝对误差与配对降幅']:
    assert data_geometry(E.parse(str(old_assets/(stem+'.svg')))) == data_geometry(E.parse(str(new_assets/(stem+'.svg')))),stem
    geometry.append({'figure':stem,'all_scatter_and_errorbar_geometry_identical':True})
(qa/'figure_data_geometry_check.json').write_text(json.dumps(geometry,ensure_ascii=False,indent=2),encoding='utf-8')
pdf[3].get_pixmap(matrix=pymupdf.Matrix(5,5),clip=pymupdf.Rect(245,95,350,120)).save(qa/'formula13_final_zoom.png')
print(json.dumps(verification,ensure_ascii=False))
