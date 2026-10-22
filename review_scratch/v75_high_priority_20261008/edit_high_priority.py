from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import hashlib,json,re
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v75_high_priority_20261008';src=root/'word_output/2026.10.07v74.docx';dst=root/'word_output/2026.10.08v75.docx'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='a6a4ab0e3d57004a9815dfe73a8886e1dac8a28050f9fa1cb6fc9035bd9589c1','Source changed; inspect again'
assert not dst.exists(),'Output already exists'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(src) as z:original={i.filename:z.read(i.filename) for i in z.infolist()};infos=z.infolist()
d=E.fromstring(original['word/document.xml']);pars=d.find('w:body',ns).findall('w:p',ns)
patches=[
(15,'路由网络负责尺度间融合','路由网络计算尺度融合权重，模型据此组合各尺度候选预测','H1'),
(17,'尺度路由网络使用原始时间分辨率的预处理输入的4项统计特征计算Softmax权重，对3个尺度候选预测的加权求和给出模型输出。','尺度路由网络根据原始时间分辨率预处理输入的4项统计特征计算Softmax权重；模型随后对3个尺度候选预测加权求和，得到最终输出。','H1'),
(49,'尺度路由网络是用于生成融合权重的门控网络，由多层感知器实现，其只负责给出各尺度的融合分数，完整的 OD 流量预测仍由对应的尺度专家独立完成。','尺度路由网络是用于生成融合权重的门控网络，由多层感知器实现。各尺度专家独立生成候选预测，模型根据归一化权重对候选预测加权求和，得到最终OD流量预测。','H1'),
(60,'再经路由模块加权融合后得到','再根据路由网络计算的权重进行加权融合，得到','H1'),
(105,'先对训练阶段保存的逐 OD 统计量进行逆标准化','先利用训练阶段保存的逐OD均值与标准差，对标准化预测值进行逆标准化','H2'),
(68,'沿用一套固定的超参数配置，不按模型搜索最优超参数。训练中，对尺度专家与可训练的融合参数进行共同优化，最终参数由验证集 MSE 选出后，再在测试集上重新评估。','各模型采用预先固定的超参数配置，未分别开展超参数搜索。对具有可训练融合参数的多尺度模型，尺度专家与融合参数共同优化；各模型均根据验证集MSE选择模型检查点，再在测试集上评价。','H3')]
changes=[]
for idx,old,new,reason in patches:
 p=pars[idx];nodes=p.xpath('.//w:t',namespaces=ns);before=''.join(n.text or '' for n in nodes);assert before.count(old)==1,(idx,old)
 start=before.index(old);end=start+len(old);pos=0;placed=False
 for n in nodes:
  t=n.text or '';a=pos;b=pos+len(t);pos=b
  if b<=start or a>=end:continue
  left=t[:max(0,start-a)];right=t[max(0,end-a):] if end<b else ''
  n.text=left+(new if not placed else '')+right;placed=True;n.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 assert ''.join(n.text or '' for n in nodes)==before.replace(old,new)
 changes.append({'paragraph_index':idx,'priority':reason,'before':before,'after':''.join(n.text or '' for n in nodes),'old_span':old,'new_span':new})
newxml=E.tostring(d,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(dst,'w') as z:
 for i in infos:z.writestr(i,newxml if i.filename=='word/document.xml' else original[i.filename])
with ZipFile(dst) as z:
 changed_parts=[k for k in original if original[k]!=z.read(k)];assert changed_parts==['word/document.xml'];nd=E.fromstring(z.read('word/document.xml'))
od=E.fromstring(original['word/document.xml'])
assert [E.tostring(a) for a in od.xpath('.//m:oMath',namespaces=ns)]==[E.tostring(a) for a in nd.xpath('.//m:oMath',namespaces=ns)]
assert [E.tostring(a) for a in od.xpath('.//w:tbl',namespaces=ns)]==[E.tostring(a) for a in nd.xpath('.//w:tbl',namespaces=ns)]
assert [E.tostring(a) for a in od.xpath('.//w:rPr|.//w:pPr|.//w:sectPr',namespaces=ns)]==[E.tostring(a) for a in nd.xpath('.//w:rPr|.//w:pPr|.//w:sectPr',namespaces=ns)]
for p in [3,9,90,100,110]:assert E.tostring(od.find('w:body',ns).findall('w:p',ns)[p])==E.tostring(nd.find('w:body',ns).findall('w:p',ns)[p])
result={'source':str(src),'output':str(dst),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'changes':changes,'changed_package_parts':changed_parts,'protected_math_count':len(nd.xpath('.//m:oMath',namespaces=ns)),'tables_preserved':True,'formatting_preserved':True,'other_package_parts_preserved':True}
(out/'edit_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(out/'v75_text.txt').write_text('\n\n'.join(f'[P{i}] '+''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns)) for i,p in enumerate(nd.find('w:body',ns).findall('w:p',ns))),encoding='utf8')
print('Completed six paragraph edits; formulas, tables, figures and formatting preserved.')
