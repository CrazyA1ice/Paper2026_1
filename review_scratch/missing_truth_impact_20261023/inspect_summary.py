import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import sys

sys.stdout.reconfigure(encoding='utf-8')
qa = Path(__file__).resolve().parent
main = json.loads((qa/'summary.json').read_text(encoding='utf-8'))
weekly = json.loads((qa/'weekly_summary.json').read_text(encoding='utf-8'))
for name, result in [('24h', main), ('168h', weekly)]:
    print(name)
    for case in ['original_all', 'observed_targets', 'complete_windows', 'complete_channel_windows', 'high_observed_same_threshold', 'high_observed_training_q90']:
        print('CASE', case)
        for r in result['summary']:
            if r['case'] == case:
                print(r)
        for e in result['effects']:
            if e['case'] == case and (name == '168h' or e['baseline'] in ['dlinear', 'lightts']):
                print(e)
paper = qa.parents[1]/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV9_投稿规范修订稿.docx'
with ZipFile(paper) as f:
    xml = ET.fromstring(f.read('word/document.xml'))
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
print('PAPER_SELECTED')
for p in xml.findall('.//w:p', ns):
    t = ''.join(p.itertext())
    if any(k in t for k in ['摘要', '25.7', '29.8', '43.7', '46.8', '2.77', '2.35', '23.16', '结论', '稳定性', '8.01']):
        print(t)
for filename in ['audit.json', 'weekly_audit.json']:
    a = json.loads((qa/filename).read_text(encoding='utf-8'))
    print('AUDIT', filename, {k: v for k, v in a.items() if k not in ['sources', 'protocol', 'metadata']})
