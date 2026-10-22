from pathlib import Path
import json
QA=Path(__file__).resolve().parent
old=QA.parent/'v74_aigc'
revision=(old/'revise.py').read_text(encoding='utf-8')
revision=revision.replace("SOURCE=ROOT/'word_output/2026.10.07v73.docx'", "SOURCE=ROOT/'word_output/2026.10.07v74.docx'")
revision=revision.replace("TARGET=ROOT/'word_output/2026.10.07v74.docx'", "TARGET=ROOT/'word_output/2026.10.07v75.docx'")
revision=revision.replace("QA/'v74.txt'", "QA/'v75.txt'")
(QA/'revise.py').write_text(revision,encoding='utf-8')
replacements='''from pathlib import Path
import json,importlib.util
from root_edits import EDITS as ROOT_EDITS
QA=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('previous_replacements',QA.parent/'v74_aigc/replacements.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
TERMS=previous.TERMS
EDITS=dict(ROOT_EDITS)
method=json.loads((QA/'method_edits.json').read_text(encoding='utf-8'))
for index,record in method.items():
    assert int(index) not in EDITS
    EDITS[int(index)]=[(x['old'],x['new']) for x in record['entries']]
EDITS=dict(sorted(EDITS.items()))
'''
(QA/'replacements.py').write_text(replacements,encoding='utf-8')
export=(old/'export.ps1').read_text(encoding='utf-8')
export=export.replace('v74_aigc','v75_aigc').replace('2026.10.07v74.docx','2026.10.07v75.docx').replace('render_v74.docx','render_v75.docx').replace('v74_review.pdf','v75_review.pdf')
(QA/'export.ps1').write_text(export,encoding='utf-8')
verify=(old/'verify_render.py').read_text(encoding='utf-8')
verify=verify.replace('2026.10.07v74.docx','2026.10.07v75.docx').replace('2026.10.07v73.docx','2026.10.07v74.docx').replace('render_v74.docx','render_v75.docx').replace('v74_review.pdf','v75_review.pdf')
(QA/'verify_render.py').write_text(verify,encoding='utf-8')
print('Prepared surgical revision and preservation checks.')
