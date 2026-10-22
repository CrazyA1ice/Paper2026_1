from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,hashlib,re
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');out=root/'review_scratch/v75_high_priority_20261008';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
with ZipFile(root/'word_output/2026.10.08v75.docx') as z:
 d=E.fromstring(z.read('word/document.xml'));ps=d.find('w:body',ns).findall('w:p',ns);txt=[''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns)) for p in ps]
 equations=[];refs=[]
 for i,p in enumerate(ps):
  if p.xpath('.//m:oMath',namespaces=ns):
   a=re.search(r'\((\d+)\)$',txt[i])
   if a:equations.append(int(a.group(1)))
  if i<111:
   for r in p.findall('w:r',ns):
    t=''.join(r.xpath('.//w:t/text()',namespaces=ns))
    if re.fullmatch(r'\[\d+\]',t):refs.append({'p':i,'reference':int(t[1:-1]),'superscript':r.xpath('./w:rPr/w:vertAlign/@w:val',namespaces=ns)==['superscript']})
 rel=E.fromstring(z.read('word/_rels/document.xml.rels'));mapping={a.get('Id'):'word/'+a.get('Target') for a in rel};figs=[]
 for j,drawing in enumerate(d.xpath('.//w:drawing',namespaces=ns),1):
  key=drawing.xpath('.//a:blip/@r:embed',namespaces=ns)[0];b=z.read(mapping[key]);matched=[]
  for candidate in [root/f'paper_figures/v56_cdgyxy/fig{j}.png',root/f'paper_figures/v70_terminology/fig{j}.png']:
   if candidate.exists() and candidate.read_bytes()==b:matched.append(str(candidate))
  figs.append({'number':j,'matched_figure_sources':matched,'sha256':hashlib.sha256(b).hexdigest()})
 absolute='\n'.join(d.xpath('.//w:t/text()',namespaces=ns));abstract=txt[3].removeprefix('摘要：');footer=''.join(E.fromstring(z.read('word/footer1.xml')).xpath('.//w:t/text()',namespaces=ns))
 result={'equation_numbers':equations,'first_reference_order':list(dict.fromkeys(r['reference'] for r in refs)),'all_citations_superscript':all(r['superscript'] for r in refs),'citation_occurrences':len(refs),'abstract_nonspace':len(''.join(abstract.split())),'abstract_han':sum('\u4e00'<=c<='\u9fff' for c in abstract),'conclusion_nonspace':len(''.join(txt[110].split())),'source_han_count':sum('\u4e00'<=c<='\u9fff' for c in absolute),'figures':figs,'footer':footer,'body_has_corresponding_author_mark':'通信作者' in absolute or '通信作者' in footer,'body_has_funding':'基金项目' in absolute or '基金项目' in footer,'captions':[{ 'index':i,'text':t,'center':ps[i].xpath('./w:pPr/w:jc/@w:val',namespaces=ns),'sizes':ps[i].xpath('./w:r/w:rPr/w:sz/@w:val',namespaces=ns)} for i,t in enumerate(txt) if re.match(r'^(图[1-5]|表[1-3]) ',t)],'section':E.tostring(d.find('w:body/w:sectPr',ns),encoding='unicode')}
 assert result['equation_numbers']==list(range(1,17));assert result['first_reference_order']==list(range(1,12));assert result['all_citations_superscript']
 with ZipFile(root/'word_output/2026.10.07v74.docx') as old:
  od=E.fromstring(old.read('word/document.xml'));ots=[''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns)) for p in od.find('w:body',ns).findall('w:p',ns)]
  assert all(re.findall(r'\d+(?:\.\d+)?',a)==re.findall(r'\d+(?:\.\d+)?',b) for a,b in zip(txt,ots))
 result['all_paragraph_numeric_sequences_preserved']=True
(out/'submission_structural_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('Submission structural audit complete')
