from pathlib import Path
import json
import os
import subprocess
import sys

QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
S=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
env['PYTHONPATH']=str(ROOT/'review_scratch/figureqa_dependencies')+os.pathsep+env.get('PYTHONPATH','')
exports=json.loads((QA/'exports.json').read_text(encoding='utf-8'))
requested=set(sys.argv[1:])
results=[]
for item in exports:
    tag=item['tag']
    if requested and tag not in requested:continue
    pdf=Path(item['prefix']).with_suffix('.pdf')
    for label,args in [('text',[S/'audit_pdf_text.py',pdf,'--min-pt','7.5','--json']),
                       ('collision',[S/'audit_figure_collisions.py',pdf,'--json-out',QA/f'{tag}_collision.json','--overlay-pdf',QA/f'{tag}_collision.pdf'])]:
        p=subprocess.run([sys.executable,*map(str,args)],env=env,capture_output=True,encoding='utf-8')
        (QA/f'{tag}_{label}.txt').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
        results.append(dict(tag=tag,check=label,returncode=p.returncode))
        print(tag,label,p.returncode,flush=True)
(QA/'qa_runs.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
