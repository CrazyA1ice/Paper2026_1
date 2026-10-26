from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
JOURNAL=ROOT/'paper_template/长春工程学院学报(自然科学版)'
SOURCE=JOURNAL/'英文摘要同步及全文核查_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV5_英文摘要同步稿.docx'
OUTPUT=JOURNAL/'逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV6_摘要局部修订稿.docx'
SOURCE_SHA='3b4b12be780ae850d5f9fa6c9234508f7d3aadbeee203f42f4ae884c9d77435e'
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
assert not OUTPUT.exists()
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(SOURCE) as z:
    infos=z.infolist();members={i.filename:z.read(i.filename) for i in infos}
old=E.fromstring(members['word/document.xml'])
new=E.fromstring(members['word/document.xml'])
body=new.find('w:body',NS)
edits={
    '摘要：':[
        ('参数冗且','参数冗余且'),
        ('分别显著降低23.16%和11.16%','分别降低23.16%和11.16%'),
        ('展现出优异的精度—复杂度平衡性与工程预测稳健性，',''),
        ('提供可靠支撑','提供预测参考'),
    ],
    'Abstract:':[
        ('decrease substantially by 23.16% and 11.16%','decrease by 23.16% and 11.16%'),
        ('demonstrate a favorable accuracy-complexity balance and robust forecasting performance for engineering applications, providing reliable support',
         'provide a forecasting reference'),
    ],
}
changed=[]
for prefix,replacements in edits.items():
    candidates=[(i,p) for i,p in enumerate(body) if ''.join(p.xpath('.//w:t/text()',namespaces=NS)).startswith(prefix)]
    assert len(candidates)==1
    index,p=candidates[0]
    before=''.join(p.xpath('.//w:t/text()',namespaces=NS))
    after=before
    for original,replacement in replacements:
        assert after.count(original)==1,(prefix,original)
        nodes=[n for n in p.xpath('.//w:t',namespaces=NS) if original in (n.text or '')]
        assert len(nodes)==1
        nodes[0].text=nodes[0].text.replace(original,replacement)
        after=after.replace(original,replacement)
    assert ''.join(p.xpath('.//w:t/text()',namespaces=NS))==after
    assert re.findall(r'\d+(?:[.,]\d+)*%?',before)==re.findall(r'\d+(?:[.,]\d+)*%?',after)
    changed.append({'index':index,'before':before,'after':after,'approved_replacements':replacements})

def canon(node):
    node=deepcopy(node);E.cleanup_namespaces(node)
    return E.tostring(node,method='c14n')

for index,(a,b) in enumerate(zip(old.find('w:body',NS),body)):
    if index not in {x['index'] for x in changed}:assert canon(a)==canon(b),index
    else:
        a,b=deepcopy(a),deepcopy(b)
        for n in a.xpath('.//w:t',namespaces=NS)+b.xpath('.//w:t',namespaces=NS):n.text=''
        assert canon(a)==canon(b),index
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(OUTPUT,'w') as z:
    for info in infos:z.writestr(info,E.tostring(new,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    assert [k for k,v in members.items() if z.read(k)!=v]==['word/document.xml']
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
cn=next(x for x in changed if x['after'].startswith('摘要：'))['after'][3:]
audit={'source':str(SOURCE),'source_sha256':SOURCE_SHA,'output':str(OUTPUT),'output_sha256':sha256(OUTPUT.read_bytes()).hexdigest(),
       'source_unchanged':True,'only_approved_abstract_edits':True,'all_numerical_values_unchanged':True,
       'all_other_body_nodes_unchanged':True,'all_styles_figures_tables_equations_unchanged':True,
       'chinese_abstract_characters':len(cn),'abstract_length_not_compressed':True,
       'edits':changed,'visual_review_pending':True}
(QA/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text('# Approved local abstract edits\n\nSource '+str(SOURCE)+'\nSHA256 '+SOURCE_SHA+'\n\nApply exactly the four Chinese edits confirmed by the user and synchronize their English equivalents. Keep all other prose, numbers, formulas, images, tables, styles, geometry and paragraph properties unchanged. Preserve source file. Do not compress or rewrite the abstract. Render and inspect all final pages.\n',encoding='utf-8')
print(json.dumps({'output':str(OUTPUT),'chinese_abstract_characters':len(cn),'only_approved_changes':True},ensure_ascii=False))
