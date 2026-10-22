from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,csv,re
import numpy as np
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v74_manual_audit_20261008'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def flat(node):
 return {} if node is None else {E.QName(c).localname:{E.QName(k).localname:v for k,v in c.attrib.items()} for c in node}
lines=[]
with ZipFile(root/'word_output/2026.10.07v74.docx') as z:
 d=E.fromstring(z.read('word/document.xml'));s=E.fromstring(z.read('word/styles.xml'));default=s.find('w:docDefaults/w:rPrDefault/w:rPr',ns)
 sm={a.get('{'+ns['w']+'}styleId'):a for a in s.findall('w:style',ns)}
 def sty(sid):
  a=sm.get(sid)
  if a is None:return {}
  b=a.find('w:basedOn',ns)
  return {**(sty(b.get('{'+ns['w']+'}val')) if b is not None else {}),**flat(a.find('w:rPr',ns))}
 pars=d.find('w:body',ns).findall('w:p',ns)
 for i,p in enumerate(pars):
  if i not in [0,1,2,3,4,6,7,8,9,10,11,16,19,22,33,44,56,65,77,84,88,94,98,109,110,111,112,118]:continue
  ps=p.find('w:pPr/w:pStyle',ns);sid=ps.get('{'+ns['w']+'}val') if ps is not None else 'Normal';props=[]
  for r in p.findall('w:r',ns):
   t=''.join(r.xpath('.//w:t/text()',namespaces=ns))
   if t:props.append({'text':t[:30],'effective':{**flat(default),**sty(sid),**flat(r.find('w:rPr',ns))}})
  lines.append('P'+str(i)+' '+json.dumps({'paragraph':flat(p.find('w:pPr',ns)),'runs':props[:4]},ensure_ascii=False))
 for i,t in enumerate(d.xpath('.//w:tbl',namespaces=ns),1):lines.append('TABLE'+str(i)+' '+json.dumps({'borders':flat(t.find('w:tblPr/w:tblBorders',ns)),'cells':[flat(c.find('w:tcPr/w:tcBorders',ns)) for c in t.xpath('./w:tr/w:tc',namespaces=ns)]},ensure_ascii=False))
 for n in z.namelist():
  if re.match('word/(footer|header).*xml$',n):lines.append(n+' '+''.join(E.fromstring(z.read(n)).xpath('.//w:t/text()',namespaces=ns)))
 for i in [24,25,27,29,35,39,40,42,46,47,50,52,54,58,72,73]:
  p=pars[i];lines.append('FORMULA P'+str(i)+' '+json.dumps({'text':p.xpath('.//m:t/text()',namespaces=ns),'components':[E.QName(n).localname for n in p.xpath('.//m:oMath//*',namespaces=ns) if E.QName(n).localname in ['acc','f','rad','nary','sSub','sSup','sSubSup']],'accents':p.xpath('.//m:accPr/m:chr/@m:val',namespaces=ns),'nary':p.xpath('.//m:naryPr/m:chr/@m:val',namespaces=ns)},ensure_ascii=False))
 lines.append('SECTION '+json.dumps(flat(d.find('w:body/w:sectPr',ns)),ensure_ascii=False))
a=json.loads((out/'numerical_audit.json').read_text(encoding='utf8'));lines.append('CITATIONS '+json.dumps(a['citations'],ensure_ascii=False))
for v in a['paired']:
 if v['dataset']=='geant' and v['baseline']=='dlinear_scale_constant_router' and v['metric']=='mse' and v['seeds']==8:lines.append('SEED43_INCREASE '+format(-v['values'][1],'.8f')+' rounded '+format(-v['values'][1],'.2f'))
for ds,ch,wins in [('abilene',47,[279,619]),('geant',297,[398,170])]:
 res={'dataset':ds,'channel':ch,'windows':[]}
 with np.load(root/f'abilene_forecasting/data/processed/{ds}_1hour.npz') as z:res['original_channel_index']=int(z['active_indices'][ch])
 for win in wins:
  vals={}
  for model in ['dlinear','dlinear_scale_static','dlinear_scale_constant_router','dlinear_scale']:
   folder='results/constant_router_ablation' if model=='dlinear_scale_constant_router' else 'results'
   with np.load(root/f'abilene_forecasting/{folder}/{ds}/{model}_seed42/predictions.npz') as z:vals[model]=float(np.mean((z['prediction'][win,:,ch]-z['truth'][win,:,ch])**2))
  res['windows'].append({'index':win,'mse':vals})
 lines.append('FIG4 '+json.dumps(res))
p=root/'abilene_forecasting/paper_figures/source_data_v2/candidate2_router_weight_distribution_8seeds.csv'
with p.open(encoding='utf8') as f:rows=list(csv.DictReader(f))
lines.append('WEIGHT_CSV_COLUMNS '+str(list(rows[0])))
for ds in sorted({r['dataset'] for r in rows}):
 sel=[r for r in rows if r['dataset']==ds];means={k:float(np.mean([float(r[k]) for r in sel])) for k in sel[0] if k.startswith('alpha')};lines.append('WEIGHTS '+ds+' '+str(means))
(out/'final_format_data_audit.txt').write_text('\n'.join(lines),encoding='utf8')
print('Complete')
