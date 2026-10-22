from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,re,hashlib
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');o=root/'review_scratch/v75_presubmission_20261008';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(root/'word_output/2026.10.08v75.docx') as z:
 x=E.fromstring(z.read('word/document.xml'));ps=x.find('w:body',ns).findall('w:p',ns);texts=[''.join(n.text or '' for n in p.iter() if n.tag in ['{'+ns['w']+'}t','{'+ns['m']+'}t']) for p in ps]
 abstract=texts[3].removeprefix('摘要：');footers=[''.join(E.fromstring(z.read(n)).xpath('//w:t/text()',namespaces=ns)) for n in z.namelist() if re.match(r'word/footer\d+\.xml$',n)]
 result={'abstract_nonspace':len(''.join(abstract.split())),'conclusion_nonspace':len(''.join(texts[110].split())),'equation_numbers':[int(re.search(r'\((\d+)\)$',t).group(1)) for p,t in zip(ps,texts) if p.xpath('.//m:oMath',namespaces=ns) and re.search(r'\((\d+)\)$',t)],'footer':footers,'main_citations':[r for r in json.loads((o/'audit_extract.json').read_text(encoding='utf8'))['citation_runs'] if r['paragraph']<111],'section_xml':E.tostring(x.find('w:body/w:sectPr',ns),encoding='unicode'),'source_hash':hashlib.sha256((root/'word_output/2026.10.08v75.docx').read_bytes()).hexdigest()}
 assert result['equation_numbers']==list(range(1,17))
 assert all(r['vertical']==['superscript'] for r in result['main_citations'])
 (o/'final_structure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('Structural checks passed')
