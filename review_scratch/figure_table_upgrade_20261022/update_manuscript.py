from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import re
import sys

from lxml import etree as E
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
audit=json.loads((QA/'data_audit.json').read_text(encoding='utf-8'))
SOURCE=Path(audit['source']);OUT=Path(audit['out']);ASSETS=Path(audit['assets'])
OUTPUT=OUT/'自适应多尺度加权的多变量网络流量预测_图表优化稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest()==audit['source_sha256']
if OUTPUT.exists():
    assert sha256(OUTPUT.read_bytes()).hexdigest()=='c24f50bd81107eaaa551610f2691820463e91ff328881f6b3c9f7bbac72c6f72'
    (QA/'iteration2.docx').write_bytes(OUTPUT.read_bytes())
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main','v':'urn:schemas-microsoft-com:vml'}
W='{'+NS['w']+'}'
with ZipFile(SOURCE) as z:
    infos=z.infolist();members={i.filename:z.read(i.filename) for i in infos}
old=E.fromstring(members['word/document.xml']);new=deepcopy(old)
ob=old.find('w:body',NS);body=new.find('w:body',NS)
edits=[]

def canonical(node):
    node=deepcopy(node);E.cleanup_namespaces(node)
    return E.tostring(node,method='c14n')

def change_text(p,value):
    nodes=body[p].xpath('.//w:t',namespaces=NS)
    assert len(nodes)==1
    edits.append(dict(paragraph=p,before=nodes[0].text,after=value))
    nodes[0].text=value

change_text(65,'表2中，本文方法在两套数据上的平均MSE与MAE均最优。相对LightTS，Abilene和GÉANT的MSE平均降低25.77%和43.74%，MAE降低12.66%和29.09%；参数量分别减少93.59%和97.83%。')
change_text(66,'图2 相对DLinear与LightTS的配对误差降幅（8次重复）')
paragraph=body[67]
old_note=''.join(paragraph.xpath('.//w:t/text()',namespaces=NS))
new_note='图2中，点为单次配对结果，菱形及横线为均值与样本标准差；下方为相对LightTS的参数比例。'
first=deepcopy(paragraph.find('w:r',NS));first.find('w:t',NS).text=new_note
for r in paragraph.findall('w:r',NS):paragraph.remove(r)
paragraph.append(first)
edits.append(dict(paragraph=67,before=old_note,after=new_note))
change_text(76,'图3 高需求点的MAE与AUE（8次重复，均值±样本标准差）')
old_results=''.join(body[77].xpath('.//w:t/text()',namespaces=NS))
change_text(77,old_results.replace('，说明高需求点的预测误差和需求低估幅度均得到改善。','。横轴为局部范围，虚线为DLinear均值。'))
change_text(82,'图4 GÉANT一周预测的绝对误差与配对降幅（8次重复）')
change_text(83,'表4中，本文方法的平均MSE和MAE均最优，较DLinear降低23.16%和11.16%，较其余融合对照降低23.77%～26.11%和11.19%～12.39%。168 h模型含57587个参数，路由网络仍为131个，仅占0.23%。图4左列展示绝对误差，右列中全部64个配对降幅均为正值。')
setup_nodes=body[79].xpath('./w:r/w:t',namespaces=NS)
assert len(setup_nodes)==3 and setup_nodes[1].text=='H'
before_setup=''.join(n.text for n in setup_nodes)
setup_nodes[0].text='设置'
setup_nodes[2].text='=168，保持96 h输入及原有划分和预处理；五种模型按2.1节设置独立训练，在GÉANT全部307个测试窗口上评价。'
edits.append(dict(paragraph=79,before=before_setup,after=''.join(n.text for n in setup_nodes),reason='retain the same task and training protocol without repeated setup prose'))

# Add one architecture-count column without altering any reported error values.
table=body[64]
assert table.tag==W+'tbl'
with (ASSETS/'24h均值与标准差.csv').open(encoding='utf-8-sig',newline='') as f:
    summary={(r['dataset'],r['model']):r for r in csv.DictReader(f)}
rowkeys=[(ds,model) for ds in ['abilene','geant'] for model in ['dlinear','lightts','dlinear_scale']]
counts=[int(summary[k]['parameters']) for k in rowkeys]
assert counts==[4656,130162,8339,4656,384382,8339]
grid=table.find('w:tblGrid',NS)
old_width=sum(int(x.get(W+'w')) for x in grid)
widths=[1134,2100,2100,2100,1410]
assert sum(widths)==old_width
for x in list(grid):grid.remove(x)
for width in widths:E.SubElement(grid,W+'gridCol',{W+'w':str(width)})
rows=table.findall('w:tr',NS)
for i,row in enumerate(rows):
    cells=row.findall('w:tc',NS)
    new_cell=deepcopy(cells[-1])
    texts=new_cell.xpath('.//w:t',namespaces=NS)
    assert len(texts)==1
    texts[0].text='参数量' if i==0 else str(counts[i-1])
    if i:
        for node in new_cell.xpath('.//w:b|.//w:bCs',namespaces=NS):node.getparent().remove(node)
    row.append(new_cell)
    for cell,width in zip(row.findall('w:tc',NS),widths):cell.find('w:tcPr/w:tcW',NS).set(W+'w',str(width))
edits.append(dict(table=2,added_column='参数量',values=counts,total_width_unchanged=True))

# Figure 4 gains a second row. Other image dimensions stay exactly as retained.
figure=body[82]
old_cy=int(figure.find('.//wp:extent',NS).get('cy'))
new_cy=round(66*36000)
for node in figure.xpath('.//wp:extent|.//a:ext',namespaces=NS):
    assert int(node.get('cy'))==old_cy
    node.set('cy',str(new_cy))
shape=figure.find('.//v:shape',NS)
match=re.search(r'height:([\d.]+)pt',shape.get('style'))
new_height=float(match.group(1))+(new_cy-old_cy)/12700
shape.set('style',shape.get('style')[:match.start(1)]+f'{new_height:.4f}'+shape.get('style')[match.end(1):])
edits.append(dict(figure=4,width_mm=138,new_height_mm=66,reason='two rows of absolute and paired-effect panels at original 7.5 pt text'))

changed_indices={64,65,66,67,76,77,79,82,83}
assert len(body)==len(ob)
for i,(before,after) in enumerate(zip(ob,body)):
    if i not in changed_indices:assert canonical(before)==canonical(after),i
assert [canonical(x) for x in old.xpath('.//m:oMath',namespaces=NS)]==[canonical(x) for x in new.xpath('.//m:oMath',namespaces=NS)]
assert len(new.xpath('.//m:oMath',namespaces=NS))==19
old_tables,new_tables=[r.xpath('.//w:tbl',namespaces=NS) for r in [old,new]]
for i in [0,2,3]:assert canonical(old_tables[i])==canonical(new_tables[i])
for before,after in zip(old_tables[1].findall('w:tr',NS),new_tables[1].findall('w:tr',NS)):
    for a,b in zip(before.findall('w:tc',NS),after.findall('w:tc',NS)[:4]):
        a,b=deepcopy(a),deepcopy(b)
        a.find('w:tcPr/w:tcW',NS).set(W+'w','0');b.find('w:tcPr/w:tcW',NS).set(W+'w','0')
        assert canonical(a)==canonical(b)
for t,indices in [(new_tables[1],[3,6]),(new_tables[2],[5,10])]:
    for row in indices:
        for cell in t.findall('w:tr',NS)[row].findall('w:tc',NS)[2:4]:
            assert cell.xpath('.//w:rPr/w:b[not(@w:val="0")]',namespaces=NS)
for p in [65,66,67,76,77,79,82,83]:
    assert canonical(ob[p].find('w:pPr',NS))==canonical(body[p].find('w:pPr',NS))

images={}
for number,stem in [(2,'图2_多基线误差降幅与参数比例'),(3,'图3_高需求局部范围点图'),(4,'图4_一周绝对误差与配对降幅')]:
    member=f'word/media/journal_figure{number}.png'
    data=(ASSETS/(stem+'.png')).read_bytes()
    with Image.open(BytesIO(data)) as im:
        assert im.width==3259 and im.info['dpi'][0]>599
    images[member]=data
new_xml=E.tostring(new,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUTPUT,'w') as z:
    for info in infos:z.writestr(info,new_xml if info.filename=='word/document.xml' else images.get(info.filename,members[info.filename]))
with ZipFile(OUTPUT) as z:parts=[k for k,v in members.items() if z.read(k)!=v]
assert set(parts)=={'word/document.xml',*images}
result=dict(source=str(SOURCE),source_sha256=audit['source_sha256'],output=str(OUTPUT),output_sha256=sha256(OUTPUT.read_bytes()).hexdigest(),changed_package_parts=parts,
    source_unchanged=True,all_original_error_data_unchanged=True,native_math=19,all_existing_math_unchanged=True,
    original_page_styles_margins_and_fonts_unchanged=True,figure1_unchanged=True,table1_3_4_unchanged=True,
    table2_new_parameter_column=True,all_best_error_values_bold=True,no_new_experiments=True,no_seed_exclusions=True,
    visual_review_pending=True,edits=edits)
(QA/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text((QA/'figure_contract.md').read_text(encoding='utf-8')+'\nSource: '+str(SOURCE)+'\nSHA256: '+audit['source_sha256']+'\nEdit slots: body children 64–67, 76–77, 82–83; embedded figures 2–4. Other body children and all native math preserved. Table 2 overall width retained; added column redistributes its existing grid. Figure 4 width retained and height locally increased to 66 mm.\n',encoding='utf-8')
code=(ROOT/'review_scratch/results_explanation_20261022/export_word.ps1').read_text(encoding='utf-8').replace('results_explanation_20261022','figure_table_upgrade_20261022').replace("Join-Path $contentQa 'render_verified'","Join-Path $contentQa 'render_submission'")
(QA/'export_word.ps1').write_text(code,encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='edits'},ensure_ascii=False))
