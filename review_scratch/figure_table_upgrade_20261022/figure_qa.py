from pathlib import Path
import json
import os
import subprocess
import sys

QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
skill=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
scipilot=Path(r'C:\Users\Quant\.codex\skills\scipilot-figure-skill\scripts')
env=os.environ.copy()
env['PYTHONPATH']=str(ROOT/'review_scratch/figureqa_dependencies')+os.pathsep+env.get('PYTHONPATH','')
env['PYTHONIOENCODING']='utf-8'
data=json.loads((QA/'data_audit.json').read_text(encoding='utf-8'))
assets=Path(data['assets'])
runs=[]

def run(name,args):
    p=subprocess.run([sys.executable,*map(str,args)],env=env,encoding='utf-8',capture_output=True)
    (QA/(name+'.txt')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    runs.append(dict(check=name,returncode=p.returncode))
    return p

run('source_preflight',[skill/'validate_figure.py',QA/'plot_figures.py','--json'])
for number,stem in [(2,'图2_多基线误差降幅与参数比例'),(3,'图3_高需求局部范围点图'),(4,'图4_一周绝对误差与配对降幅')]:
    pdf=assets/(stem+'.pdf')
    run(f'figure{number}_text',[skill/'audit_pdf_text.py',pdf,'--min-pt','7.5','--json'])
    run(f'figure{number}_collision',[skill/'audit_figure_collisions.py',pdf,'--json-out',QA/f'figure{number}_collision.json','--overlay-pdf',QA/f'figure{number}_collision.pdf'])
    run(f'figure{number}_format',[scipilot/'check_figure.py',pdf,assets/(stem+'.png'),'--strict'])
for name,groups in [('图2_配对相对降幅',['dataset','baseline','metric']),('图3_高需求全部种子',['dataset','model']),('图4_168h绝对误差全部种子',['model'])]:
    args=[scipilot/'profile_data.py',assets/(name+'.csv'),'--json']
    for group in groups:args+=['--group',group]
    run('profile_'+str(len(runs)),args)
(QA/'figure_qa_runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(runs,ensure_ascii=False))
