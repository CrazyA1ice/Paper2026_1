from copy import deepcopy
from hashlib import sha256
from html import escape
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '方法含义说明修订_20261022/自适应多尺度加权的多变量网络流量预测_方法含义说明稿.docx'
SOURCE_SHA = '814f0cf44e067e7a242e434318152582a57ea4237913be3813787dd0e9fde123'
OUTPUT = JOURNAL / '实验结果分析修订_20261022/自适应多尺度加权的多变量网络流量预测_实验结果分析稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
if OUTPUT.exists():
    assert sha256(OUTPUT.read_bytes()).hexdigest() == '34a136cfd35927ee594ac9167a1ae22646efe4eae0826014bda3a925f86221a8'
    (QA/'draft_before_removing_repeated_figure_summary.docx').write_bytes(OUTPUT.read_bytes())
evidence = json.loads((QA/'evidence_audit.json').read_text(encoding='utf-8'))
assert evidence['baseline_metric_records']==96 and evidence['high_demand_records']==80
assert evidence['weekly_records']==40 and evidence['weekly_positive_paired_comparisons']==64


def reduction(family, dataset, baseline, metric):
    rows=evidence[family]
    r=next(r for r in rows if r.get('dataset',dataset)==dataset and r['baseline']==baseline and r['metric']==metric)
    return f'{r["mean"]:.2f}%'


expected = [
 ('baseline_effects','abilene','lightts','mse','25.77%'), ('baseline_effects','geant','lightts','mse','43.74%'),
 ('baseline_effects','abilene','lightts','mae','12.66%'), ('baseline_effects','geant','lightts','mae','29.09%'),
 ('baseline_effects','abilene','dlinear','mae','8.01%'), ('baseline_effects','abilene','dlinear_scale_global','mae','8.91%'),
 ('baseline_effects','abilene','dlinear_scale_global','mse','1.80%'), ('baseline_effects','geant','dlinear_scale_global','mse','4.31%'),
 ('high_demand_effects','abilene','dlinear','mae','13.96%'), ('high_demand_effects','abilene','dlinear','mean_shortfall','16.07%'),
 ('high_demand_effects','abilene','dlinear_scale_static','mae','17.47%'), ('high_demand_effects','abilene','dlinear_scale_static','mean_shortfall','20.84%'),
 ('weekly_effects','geant','dlinear','mse','23.16%'), ('weekly_effects','geant','dlinear','mae','11.16%')]
for family,ds,control,metric,value in expected:
    assert reduction(family,ds,control,metric)==value
assert f'{evidence["weekly_router_share_pct"]:.2f}%'=='0.23%'
assert round(100-8339/130162*100,2)==93.59 and round(100-8339/384382*100,2)==97.83
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W,M='{'+NS['w']+'}','{'+NS['m']+'}'
with ZipFile(SOURCE) as z:
    infos=z.infolist(); members={i.filename:z.read(i.filename) for i in infos}
xml=members['word/document.xml']
old,new=E.fromstring(xml),E.fromstring(xml)
body=new.find('w:body',NS)
texts={
65:'表2中，本文方法在两套数据上的平均MSE和MAE均最优。相对LightTS，Abilene和GÉANT的MSE平均降低25.77%和43.74%，MAE降低12.66%和29.09%。结合图2，本文参数量为8339，相比LightTS的130162和384382分别减少93.59%和97.83%。',
72:'表3中，本文方法各项平均误差均最优。相对DLinear，两套数据的MSE平均降低2.77%和2.35%；相对全局权重，降低1.80%和4.31%。Abilene的MAE较二者降低8.01%和8.91%。GÉANT上，仅本文方法的平均MSE低于DLinear；恒定输入路由保留相同结构和参数量，其误差仍较高，支持窗口统计量驱动的融合设计。',
76:'图3中，本文方法在Abilene上的MAE与AUE为0.147和0.137，在GÉANT上为0.632和0.577，均值均低于所列对照。Abilene上，相对DLinear两项指标平均降低13.96%和16.07%，相对固定等权降低17.47%和20.84%，说明高需求点的预测误差和需求低估幅度均得到改善。',
82:'表4中，本文方法的平均MSE和MAE均最优，较DLinear降低23.16%和11.16%，较其余融合对照降低23.77%～26.11%和11.19%～12.39%。168 h模型含57587个参数，路由网络仍为131个，仅占0.23%。图4中，全部64个配对降幅（4种对照×2项指标×8个种子）均为正值，体现了本组一周预测实验中误差降低的一致性。'
}
edits=[]
for p,value in texts.items():
    nodes=body[p].xpath('./w:r/w:t',namespaces=NS)
    assert len(nodes)==1
    edits.append({'paragraph':p,'before':nodes[0].text,'after':value})
    nodes[0].text=value
figure_note = body[67].xpath('./w:r/w:t',namespaces=NS)[6]
short_note = figure_note.text.split('该结果表明，')[0]
assert short_note.endswith('给出本文模型的参数比例。')
edits.append({'paragraph':67,'run':6,'before':figure_note.text,'after':short_note})
figure_note.text = short_note
before_nodes,after_nodes=old.xpath('.//w:t',namespaces=NS),new.xpath('.//w:t',namespaces=NS)
matches=list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)',xml,re.S))
assert len(matches)==len(before_nodes)==len(after_nodes)
for i in range(len(matches)-1,-1,-1):
    if before_nodes[i].text!=after_nodes[i].text:
        mt=matches[i];xml=xml[:mt.start(2)]+escape(after_nodes[i].text,quote=False).encode('utf-8')+xml[mt.end(2):]

eq_template=body[59]
assert '(15)' in eq_template.xpath('.//w:t/text()',namespaces=NS)
original_math=eq_template.find('m:oMath',NS)
actual,predicted=[deepcopy(x) for x in original_math.findall('m:sSub',NS)]
math_run_props=deepcopy(actual.find('m:e/m:r/w:rPr',NS))
control_props=deepcopy(original_math.find('m:nary/m:naryPr/m:ctrlPr',NS))


def el(tag,text=None,**attrs):
    node=E.Element(M+tag,{M+k:v for k,v in attrs.items()})
    if text is not None:node.text=text
    return node


def run(text,upright=False):
    node=el('r');rp=el('rPr');rp.append(el('sty',val='p' if upright else 'i'));node.append(rp)
    node.append(deepcopy(math_run_props));node.append(el('t',text))
    return node


def sub(base,index):
    node=el('sSub');p=el('sSubPr');p.append(deepcopy(control_props));node.append(p)
    e=el('e');e.append(run(base));node.append(e)
    s=el('sub');s.append(run(index));node.append(s)
    return node


def delim(parts,left='(',right=')'):
    node=el('d');p=el('dPr');p.extend([el('begChr',val=left),el('endChr',val=right),el('grow',val='1'),deepcopy(control_props)])
    node.append(p);e=el('e');e.extend(parts);node.append(e)
    return node


def tuple_parts():
    return [run('n'),run(',',True),run('h'),run(',',True),run('c')]


def text_run(value):
    rr=deepcopy(body[74].find('w:r',NS))
    rr.find('w:t',NS).text=value
    return rr


setup=deepcopy(body[74])
for child in list(setup):
    if child.tag!=W+'pPr':setup.remove(child)
setup.append(text_run('以标准化训练集各OD变量的第90百分位为阈值'))
tau=el('oMath');tau.append(sub('τ','c'));setup.append(tau)
setup.append(text_run('，定义测试集高需求点集'))
omega=el('oMath');omega.extend([run('Ω'),run('=',True),delim([delim(tuple_parts()),run('|',True),deepcopy(actual),run('>',True),sub('τ','c')],'{','}')]);setup.append(omega)
setup.append(text_run('，在集合内全部目标点上计算MAE与平均低估误差（average underestimation error，AUE）：'))

equation=deepcopy(eq_template)
equation.attrib.clear()
math=el('oMath');math.extend([run('AUE',True),run('=',True)])
frac=el('f');fp=el('fPr');fp.append(deepcopy(control_props));frac.append(fp)
num=el('num');num.append(run('1',True));frac.append(num)
den=el('den');den.append(delim([run('Ω')],'|','|'));frac.append(den);math.append(frac)
sigma=el('nary');np=el('naryPr');np.extend([el('chr',val='∑'),el('limLoc',val='undOvr'),el('supHide',val='1'),deepcopy(control_props)]);sigma.append(np)
idx=el('sub');idx.extend([delim(tuple_parts()),run('∈',True),run('Ω')]);sigma.append(idx);sigma.append(el('sup'))
summand=el('e');func=el('func');funcp=el('funcPr');funcp.append(deepcopy(control_props));func.append(funcp)
fname=el('fName');fname.append(run('max',True));func.append(fname)
argument=el('e');argument.append(delim([run('0',True),run(',',True),deepcopy(actual),run('−',True),deepcopy(predicted)]));func.append(argument)
summand.append(func);sigma.append(summand);math.append(sigma);math.append(run('.',True))
equation.replace(equation.find('m:oMath',NS),math)
equation.xpath('.//w:t',namespaces=NS)[0].text='(16)'
edits.append({'paragraph':74,'before':''.join(body[74].xpath('.//w:t/text()',namespaces=NS)),
              'after':''.join(setup.xpath('.//w:t/text()',namespaces=NS)),'new_native_equation':16})
old_text=escape(''.join(body[74].xpath('.//w:t/text()',namespaces=NS)),quote=False).encode('utf-8')
blocks=[m for m in re.finditer(rb'<w:p(?:\s[^>]*)?>.*?</w:p>',xml,re.S) if old_text in m.group()]
assert len(blocks)==1
block=blocks[0];xml=xml[:block.start()]+E.tostring(setup)+E.tostring(equation)+xml[block.end():]
final=E.fromstring(xml)


def canonical(node):
    node=deepcopy(node);E.cleanup_namespaces(node)
    return E.tostring(node,method='c14n')


fb=final.find('w:body',NS);ob=old.find('w:body',NS)
assert len(fb)==len(ob)+1
for i,p in enumerate(ob):
    if i not in [65,67,72,74,76,82]:
        assert canonical(p)==canonical(fb[i if i<=74 else i+1]),i
for p in [65,67,72,76,82]:
    before,after=deepcopy(ob[p]),deepcopy(fb[p if p<=74 else p+1])
    for node in before.xpath('.//w:t',namespaces=NS)+after.xpath('.//w:t',namespaces=NS):node.text=''
    assert canonical(before)==canonical(after)
assert [canonical(x) for x in old.xpath('.//m:oMath',namespaces=NS)]==[canonical(x) for x in final.xpath('.//m:oMath',namespaces=NS)[:16]]
assert len(final.xpath('.//m:oMath',namespaces=NS))==19
assert [canonical(x) for x in old.xpath('.//w:tbl',namespaces=NS)]==[canonical(x) for x in final.xpath('.//w:tbl',namespaces=NS)]
assert [canonical(x) for x in old.xpath('.//w:r[w:rPr/w:vertAlign]',namespaces=NS)]==[canonical(x) for x in final.xpath('.//w:r[w:rPr/w:vertAlign]',namespaces=NS)]
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(OUTPUT,'w') as z:
    for info in infos:z.writestr(info,xml if info.filename=='word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:changed=[k for k,v in members.items() if z.read(k)!=v]
assert changed==['word/document.xml']
audit={'source':str(SOURCE),'source_sha256':SOURCE_SHA,'output':str(OUTPUT),
       'output_sha256':sha256(OUTPUT.read_bytes()).hexdigest(),'source_unchanged':True,'changed_package_parts':changed,
       'only_sections_2_2_through_2_5_changed':True,'all_existing_math_unchanged':True,'new_numbered_equation':16,
       'native_math':19,'original_tables_figures_references_and_format_properties_unchanged':True,
       'new_experiments':False,'no_observations_excluded':True,'edits':edits,'visual_review_pending':True}
(QA/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text(
 '# Results explanation revision\n\nRetain the accepted method-interpretation manuscript, SHA256 '+SOURCE_SHA+'. '
 'Revise only sections 2.2–2.5. Use the current eight-seed evidence and preserve all table entries, images, existing equations, citations, references, abstracts and methods. '
 'Keep parameter reduction, paired error reductions, training-defined high-demand evaluation, router share and the complete weekly paired comparison family. '
 'Classification: baseline/fusion/weekly error comparisons are core evidence; AUE definition is necessary reproducibility support; sample-SD stability, presumed smoothing/noise mechanisms, QoS outcomes, overfitting and autoregressive error accumulation are unsupported here and must not be added. '
 'The high-demand threshold is computed in the standardized training data; Ω contains all eligible test forecast targets, including each window/horizon/channel entry. '
 'Add AUE as editable native Word equation 16, plus inline threshold and set definitions. Existing numbered equations 1–15 are unchanged. '
 'Report paired mean reductions, no new significance testing. The 24-hour and 168-hour tasks use their respective complete test windows. '
 'All 64 weekly paired reductions are positive in the observed experiment; do not turn this into a population win-probability claim. '
 'Replace existing paragraphs instead of appending a second commentary layer. Keep evidence internal; no manuscript mention of supplementary material. '
 'Native Word export and packaged rasterization; inspect every final page.\n',encoding='utf-8')
for name in ['export_word.ps1','render_verify.py']:
    code=(ROOT/'review_scratch/method_interpretation_20261022'/name).read_text(encoding='utf-8').replace('method_interpretation_20261022','results_explanation_20261022')
    if name=='export_word.ps1':code=code.replace("Join-Path $contentQa 'render_checked'","Join-Path $contentQa 'render_verified'")
    else:
        code=code.replace("assert len(root.xpath('.//m:oMath', namespaces=ns)) == 16","assert len(root.xpath('.//m:oMath', namespaces=ns)) == 19")
        code=code.replace("'native_math': 16, 'tables': 4,","'native_math': 19, 'tables': 4,")
        code=code.replace("for token in ['表4GÉANT", "for token in ['(16)', 'AUE', '93.59%', '97.83%', '8.01%', '8.91%', '17.47%', '20.84%', '0.23%', '64个', '表4GÉANT")
    (QA/name).write_text(code,encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='edits'},ensure_ascii=False))
