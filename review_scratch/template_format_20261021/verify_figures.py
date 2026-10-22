from pathlib import Path
import json,subprocess,sys
sys.stdout.reconfigure(encoding='utf8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
S=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
ASSETS=ROOT/'paper_template/长春工程学院学报(自然科学版)/模板规范修订_20261021/图表源文件'
reports=[]
for number in range(1,5):
    pdf=ASSETS/f'图{number}.pdf'
    c=subprocess.run([sys.executable,str(S/'audit_figure_collisions.py'),str(pdf),'--json-out',str(QA/f'figure{number}_collision.json')],capture_output=True,text=True,encoding='utf8',errors='replace')
    f=subprocess.run([sys.executable,str(S/'audit_pdf_text.py'),str(pdf),'--min-pt','5','--json'],capture_output=True,text=True,encoding='utf8',errors='replace')
    (QA/f'figure{number}_font.json').write_text(f.stdout,encoding='utf8')
    collision=json.loads((QA/f'figure{number}_collision.json').read_text(encoding='utf8'))
    font=json.loads(f.stdout)
    reports.append({'figure':number,'collision_verdict':collision['verdict'],'collision_returncode':c.returncode,'font_minimum':font.get('minimum_found_pt'),'font_returncode':f.returncode})
v=subprocess.run([sys.executable,str(S/'validate_figure.py'),str(QA/'format_figures.py'),'--json'],capture_output=True,text=True,encoding='utf8',errors='replace')
(QA/'figure_source_preflight.json').write_text(v.stdout,encoding='utf8')
(QA/'figure_qa_summary.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(reports,ensure_ascii=False))
