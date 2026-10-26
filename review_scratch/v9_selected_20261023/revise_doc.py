from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
FOLDER = ROOT/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023'
ASSETS = FOLDER/'V9_图表源文件'
SOURCE = FOLDER/'自适应多尺度加权的多变量网络流量预测_ccgcxyxbV8_指定项目修订稿.docx'
OUTPUT = FOLDER/'自适应多尺度加权的多变量网络流量预测_ccgcxyxbV9_投稿规范修订稿.docx'
SOURCE_SHA = '6c832ce97b2f8ec4b5eaec54dcba67ae195618b960c84af292faa23ea8db773d'
ACCEPTED = ['01','02','03','04','05','10','11','14','16']
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
if OUTPUT.exists():
    prior = json.loads((QA/'audit.json').read_text(encoding='utf-8'))
    assert sha256(OUTPUT.read_bytes()).hexdigest() == prior['output_sha256']
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
w = '{'+ns['w']+'}'
m = '{'+ns['m']+'}'
with ZipFile(SOURCE) as archive:
    infos = archive.infolist()
    members = {i.filename: archive.read(i.filename) for i in infos}
doc = E.fromstring(members['word/document.xml'])
settings = E.fromstring(members['word/settings.xml'])
body = doc.find('w:body',ns)
original = list(body)
original_copy = deepcopy(body)
changed = set()
removed = set()
edits = []

def text(node):
    return ''.join(node.xpath('.//w:t/text() | .//m:t/text()',namespaces=ns))

def canonical(node):
    return E.tostring(node,method='c14n',exclusive=True) if node is not None else None

def replace(index,before,after,issues):
    p = original[index]
    nodes = p.xpath('.//w:t | .//m:t',namespaces=ns)
    joined = ''.join(n.text or '' for n in nodes)
    assert joined.count(before) == 1, (index,before)
    start = joined.index(before)
    end = start+len(before)
    offset = 0
    inserted = False
    for n in nodes:
        v = n.text or ''
        a,b = offset,offset+len(v)
        offset = b
        if a < end and b > start:
            left,right = max(start-a,0),min(end-a,len(v))
            n.text = v[:left]+(after if not inserted else '')+v[right:]
            inserted = True
    for eq in p.xpath('.//m:oMath',namespaces=ns):
        if not text(eq):
            eq.getparent().remove(eq)
    assert text(p) == joined[:start]+after+joined[end:]
    changed.add(index)
    edits.append({'issues':issues,'source_index':index,'before':before,'after':after})

def remove(index):
    body.remove(original[index])
    removed.add(index)
    edits.append({'issues':['03','16'],'source_index':index,'before':text(original[index]),'after':''})

# 01: a published review actually discussing LightTS replaces the unpublished paper.
metadata = json.loads((QA/'reference8_crossref.json').read_text(encoding='utf-8'))['message']
assert metadata['DOI'] == '10.3390/math12101504'
assert [a['family'] for a in metadata['author']] == ['Liu','Wang']
replace(109,text(original[109]),
        '[8] LIU Xinhe, WANG Wenmin. Deep time series forecasting models: a comprehensive survey[J]. '
        'Mathematics, 2024, 12(10): 1504. DOI: 10.3390/math12101504.', ['01'])

# 02: fixed source commit metadata, rather than a guessed web modification date.
commit = json.loads((QA/'reference12_commit.json').read_text(encoding='utf-8'))
assert commit['sha'] == '4e938a1767106324dd753b2a44832bf870a0252e'
date = commit['commit']['committer']['date'][:10]
assert date == '2026-04-18'
replace(113,'Time-Series-Library[CP/OL]. [2026-10-23].',
        'Time-Series-Library[CP/OL]. (2026-04-18)[2026-10-23].',['02'])

# 03,16: remove duplicate procedural explanations, not data or results.
for index in [26,69,77]:
    remove(index)
replace(78,'具体而言，保持三个独立DLinear专家与尺度集合不变，比较融合方式。',
        '保持三个独立DLinear专家与尺度集合不变，比较融合方式。',['03','16'])
replace(73,text(original[73]),
        '图2给出了逐种子配对的误差降幅及参数比例。相对LightTS，本文方法在Abilene和GÉANT上的MSE平均降低25.77%和43.74%，'
        'MAE平均降低12.66%和29.09%。两套LightTS配置分别含130162和384382个参数；本文方法通过变量间共享映射与低维路由，'
        '将参数量保持为8339，分别为LightTS的6.41%和2.17%，即缩减93.59%和97.83%。因此，以不到LightTS十五分之一乃至四十六分之一的参数代价，'
        '实现了近26%～44%的误差削减，相对LightTS取得了较少参数与较低平均误差的组合优势。',['03','16'])
replace(95,'，大幅领先于所有四种对照模型。','。',['03','16'])

# 10: replace the claim of inevitable static-fusion failure with the observed comparison.
replace(82,'，这一现象有力地证明：多尺度表征并非简单叠加即可奏效，粗粒度尺度（s=2,4）'
        '在提取平滑趋势的同时不可避免地损失了高频细节，若采用不随样本窗口变化的静态权重进行无差别融合，'
        '在流量剧烈波动的窗口中必然引入严重的平滑滞后偏差，导致多尺度负迁移。',
        '。这表明，在本实验设置下，静态多尺度融合未取得低于单尺度DLinear的平均MSE。',['03','10'])
replace(82,'同样无法遮掩性能下降，','其平均误差仍高于本文方法；',['16'])
replace(88,'同样值得注意的是，静态多尺度方法（固定等权、全局权重）在两套数据的高需求点上再次出现误差劣于单尺度DLinear的现象，'
        '原因在于均值池化削平了波峰，静态融合必然拉低峰值响应。',
        '在本实验的两套数据上，固定等权与全局权重方法在高需求点上的平均误差均高于单尺度DLinear。',['03','10'])

# 11: only the two right-hand panels have a zero-centered improvement axis.
replace(96,'此外，图4中全部8个随机种子下的单次实验散点',
        '此外，图4（b）、（d）中全部8个随机种子下的单次实验散点',['11'])

# 14: exact UTC endpoints from the complete time grid, verified against actual NPZ inputs.
data = json.loads((QA/'data_metadata_raw.json').read_text(encoding='utf-8'))
assert data['cesnet_tszoo_version'] == '2.2.0'
for record in data['data']:
    assert record['preprocessing_reconstructed_and_matches_saved_data_exactly']
    assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256']
    assert sha256(Path(record['processed_path']).read_bytes()).hexdigest() == record['processed_sha256']
assert [r['first_utc'] for r in data['data']] == ['2004-03-01T00:00:00+00:00','2004-12-31T23:30:00+00:00']
assert [r['last_utc'] for r in data['data']] == ['2004-09-10T23:00:00+00:00','2005-04-29T15:30:00+00:00']
replace(58,'两套数据均取自matrix子集的1_hour聚合文件，',
        '实验使用CESNET TS-Zoo 2.2.0读取两套matrix子集的1_hour聚合文件。按文件时间戳（UTC）计，'
        'Abilene覆盖2004年3月1日0时至9月10日23时，GÉANT覆盖2004年12月31日23时30分至2005年4月29日15时30分。',['14'])

# All unselected substantive claims and the two approved abstracts remain untouched.
for index in [1,2,5,13,43,72,84,98,99,119]:
    assert canonical(original[index]) == canonical(original_copy[index]), index
joined = ''.join(text(p) for p in body)
protected = ['最优的综合预测精度与稳定性','99.23%','106.26%','不同随机初始化的鲁棒性',
             '唯一成功突破单尺度DLinear性能上限','可靠性与普适优势','胜率达100%',
             '具备更强的工程实用价值','近26%～44%的误差削减']
for needle in protected:
    assert needle in joined, needle
assert text(original[5]) == text(original_copy[5])
assert text(original[119]) == text(original_copy[119])

# 05: keep OMML structures and style semantics; regular font overrides keep letters/numbers TNR.
# Stretchy operators remain native Office math, never rasterized.
formula_semantics = [E.tostring(x) for x in doc.xpath('//m:oMath',namespaces=ns)]
font_changes = 0
for part_name in ['word/document.xml','word/styles.xml','word/settings.xml']:
    part = doc if part_name=='word/document.xml' else settings if part_name=='word/settings.xml' else E.fromstring(members[part_name])
    for fonts in part.xpath('//w:rFonts',namespaces=ns):
        for attribute in ['ascii','hAnsi','cs']:
            if fonts.get(w+attribute)=='Cambria Math':
                fonts.set(w+attribute,'Times New Roman')
                font_changes += 1
    # Keep a MATH-table font for stretchy sums/radicals. Letters/digits use the TNR overrides below.
    if part_name=='word/document.xml':
        for run in part.xpath('//m:r',namespaces=ns):
            mathpr = run.find(m+'rPr')
            if '∈' in ''.join(run.xpath('.//m:t/text()',namespaces=ns)):
                # Times New Roman lacks this glyph; keep native math rendering for membership symbols.
                for fonts in run.xpath('./w:rPr/w:rFonts',namespaces=ns):
                    for attribute in ['ascii','hAnsi','cs']:
                        fonts.set(w+attribute,'Cambria Math')
                continue
            if mathpr is not None and mathpr.find(m+'scr') is not None:
                # A blackboard-bold R is a mathematical set symbol, not an ordinary Latin letter.
                continue
            if mathpr is None:
                mathpr = E.Element(m+'rPr')
                run.insert(0,mathpr)
            style = mathpr.find(m+'sty')
            in_function_name = any(a.tag == m+'fName' for a in run.iterancestors())
            style_value = style.get(m+'val') if style is not None else ('p' if in_function_name else 'i')
            normal = mathpr.find(m+'nor')
            if normal is None:
                normal = E.SubElement(mathpr,m+'nor')
            normal.set(m+'val','1')
            runpr = run.find(w+'rPr')
            if runpr is None:
                runpr = E.SubElement(run,w+'rPr')
            fonts = runpr.find(w+'rFonts')
            if fonts is None:
                fonts = E.SubElement(runpr,w+'rFonts')
            for attribute in ['ascii','hAnsi','cs']:
                fonts.set(w+attribute,'Times New Roman')
            for attribute,enabled in [('b',style_value in ['b','bi']),('i',style_value in ['i','bi'])]:
                node = runpr.find(w+attribute)
                if node is None:
                    node = E.SubElement(runpr,w+attribute)
                node.set(w+'val','1' if enabled else '0')
    members[part_name] = E.tostring(part,xml_declaration=True,encoding='UTF-8',standalone=True)

def semantic_equation(xml):
    equation = E.fromstring(xml)
    for props in equation.xpath('.//w:rPr | .//m:rPr | .//m:ctrlPr',namespaces=ns):
        if props.getparent() is not None:
            props.getparent().remove(props)
    return canonical(equation)

math_after = doc.xpath('//m:oMath',namespaces=ns)
assert [semantic_equation(x) for x in formula_semantics] == [semantic_equation(E.tostring(x)) for x in math_after]
assert len(math_after) == 35
assert all(canonical(a) == canonical(b) for a,b in zip(original_copy.findall(w+'tbl'),body.findall(w+'tbl')))
assert len(original_copy.findall(w+'tbl')) == len(body.findall(w+'tbl')) == 4
# Paragraph styles/spacing and section properties stay as the V8 template version.
for index,node in enumerate(original):
    if index in removed:
        continue
    before_props = original_copy[index].find(w+'pPr')
    after_props = node.find(w+'pPr')
    assert canonical(before_props) == canonical(after_props)

for number,stem in [(1,'图1_样本窗口符号统一'),(2,'图2_多基线误差降幅与参数比例'),(3,'图3_高需求局部范围点图'),(4,'图4_一周绝对误差与配对降幅')]:
    members[f'word/media/image{number}.png'] = (ASSETS/(stem+'.png')).read_bytes()
    edits.append({'issues':['05'] if number==1 else ['04'], 'operation':'replace_figure','figure':number,
                  'scientific_values_and_panel_organization_unchanged':True})

with ZipFile(OUTPUT,'w') as archive:
    for info in infos:
        archive.writestr(info,members[info.filename])
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
audit = {'source':str(SOURCE),'source_sha256':SOURCE_SHA,'output':str(OUTPUT),
         'output_sha256':sha256(OUTPUT.read_bytes()).hexdigest(), 'accepted_issues':ACCEPTED,
         'changed_source_paragraphs':sorted(changed), 'removed_duplicate_source_paragraphs':sorted(removed),
         'both_abstracts_unchanged':True,'all_table_cells_unchanged':True,'numbered_equation_structures_unchanged':True,
         'math_objects_before':36,'math_objects_after':35,'removed_inline_math_in_replaced_static_claim':1,
         'font_attribute_changes':font_changes,'data_inputs_unchanged':True,'original_unchanged':True,
         'unselected_claims_preserved':protected,'edits':edits,'visual_review_pending':True}
(QA/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text('# V9 selected compliance revision\n\nAccepted issues: '+', '.join(ACCEPTED)+'.\n'
    'Preserve both abstracts, unselected claims, all table data, original input data and numbered formulas. '
    'Use published review support for LightTS and preserve separate pinned code provenance. '
    'Add verified UTC time ranges and library version; shorten only repetitions and the selected static-causality claims. '
    'Retain the journal paragraph styles, native editable mathematics, and scientific figure organization. '
    'Check final Word count <=7500 and inspect every rendered page and changed figure.\n',encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='edits'},ensure_ascii=False))
