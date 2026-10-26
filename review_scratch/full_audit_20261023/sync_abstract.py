from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
JOURNAL=ROOT/'paper_template/长春工程学院学报(自然科学版)'
SOURCE=JOURNAL/'截图逐项修改_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV4_截图逐项修改稿.docx'
OUTPUT=JOURNAL/'英文摘要同步及全文核查_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV5_英文摘要同步稿.docx'
SOURCE_SHA='11a1c619de23ad5616dc4cf7b0b8cbe225d93b594769cfa8552d1429a7568068'
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
if OUTPUT.exists():
    prior=json.loads((QA/'audit.json').read_text(encoding='utf-8'))
    assert sha256(OUTPUT.read_bytes()).hexdigest()==prior['output_sha256'], 'Do not replace an externally edited draft.'

ABSTRACT=(
    'An adaptive multiscale weighting method is proposed for multivariate network traffic forecasting to address the coexistence of high-frequency burst fluctuations and long-term evolution in hourly origin-destination (OD) traffic series of backbone networks, as well as parameter redundancy and noise-sensitive static fusion in conventional multiscale models. '
    'Non-overlapping temporal aggregation constructs multiresolution inputs, and three independently parameterized decomposition linear models (DLinear) extract trend and residual components at each scale. '
    'A lightweight window router with only 131 parameters then extracts four time-domain statistics from each historical window to generate sample-specific multiscale fusion weights. '
    'Repeated experiments on the Abilene and GÉANT backbone-network datasets show that, for 24-hour forecasting, the proposed method achieves mean relative reductions in mean squared error (MSE) of 25.77% and 43.74%, respectively, using only 8,339 parameters, equivalent to 6.41% and 2.17% of the respective LightTS parameter counts. '
    'Compared with single-scale DLinear and static multiscale fusion strategies, the maximum MSE reduction reaches 4.97%. In addition, the average underestimation error at high-demand peak points on Abilene decreases by 16.07% relative to DLinear. '
    'For 168-hour forecasting on GÉANT, MSE and mean absolute error (MAE) decrease substantially by 23.16% and 11.16%, respectively, relative to DLinear. '
    'These results demonstrate a favorable accuracy-complexity balance and robust forecasting performance for engineering applications, providing reliable support for backbone-network capacity planning and resource scheduling.'
)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}'
with ZipFile(SOURCE) as z:
    infos=z.infolist();members={i.filename:z.read(i.filename) for i in infos}
old=E.fromstring(members['word/document.xml'])
new=E.fromstring(members['word/document.xml'])
body=new.find('w:body',NS)
indices=[i for i,p in enumerate(body) if ''.join(p.xpath('.//w:t/text()',namespaces=NS)).startswith('Abstract:')]
assert len(indices)==1
i=indices[0]
p=body[i]
before=''.join(p.xpath('.//w:t/text()',namespaces=NS))
for node in list(p):
    if node.tag!=W+'pPr':p.remove(node)
label=E.SubElement(p,W+'r');props=E.SubElement(label,W+'rPr');E.SubElement(props,W+'b')
tt=E.SubElement(label,W+'t');tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve');tt.text='Abstract: '
rr=E.SubElement(p,W+'r');E.SubElement(rr,W+'t').text=ABSTRACT

def canonical(x):
    x=deepcopy(x);E.cleanup_namespaces(x)
    return E.tostring(x,method='c14n')

for j,(a,b) in enumerate(zip(old.find('w:body',NS),body)):
    if j!=i:assert canonical(a)==canonical(b),j
assert canonical(old.find('w:body',NS)[i].find('w:pPr',NS))==canonical(p.find('w:pPr',NS))
assert [canonical(x) for x in old.xpath('.//m:oMath',namespaces=NS)]==[canonical(x) for x in new.xpath('.//m:oMath',namespaces=NS)]
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(OUTPUT,'w') as z:
    for info in infos:z.writestr(info,E.tostring(new,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    assert [k for k,v in members.items() if z.read(k)!=v]==['word/document.xml']
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
audit={'source':str(SOURCE),'source_sha256':SOURCE_SHA,'output':str(OUTPUT),'output_sha256':sha256(OUTPUT.read_bytes()).hexdigest(),
       'only_english_abstract_changed':True,'source_unchanged':True,'paragraph_index':i,'before':before,'after':'Abstract: '+ABSTRACT,
       'all_other_body_nodes_unchanged':True,'native_math_unchanged':True,'format_unchanged':True,'visual_review_pending':True}
(QA/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text('# English abstract synchronization\n\nSource '+str(SOURCE)+'\nSHA256 '+SOURCE_SHA+'\n\nReplace only the English abstract with a faithful counterpart of the current Chinese abstract. Preserve all numerical values, paragraph style and pagination properties. All other manuscript contents, figures, tables, equations and package parts remain unchanged. Render and inspect all pages before delivery. The full audit is read-only and is delivered separately as a problem list.\n',encoding='utf-8')
print(json.dumps({'output':str(OUTPUT),'english_word_count':len(ABSTRACT.split()),'only_english_abstract_changed':True},ensure_ascii=False))
