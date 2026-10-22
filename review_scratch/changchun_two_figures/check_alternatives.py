from pathlib import Path
import hashlib,json,os,subprocess,sys
import fitz

sys.stdout.reconfigure(encoding='utf8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/改投内容修改第一版_20261020/图4备选'
SKILL=Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
env={**os.environ,'PYTHONIOENCODING':'utf-8'}

def run_json(script,args):
    result=subprocess.run([sys.executable,str(SKILL/script),*map(str,args)],capture_output=True,text=True,encoding='utf8',env=env)
    assert result.returncode==0,(script,result.stdout,result.stderr)
    return json.loads(result.stdout)

source=run_json('validate_figure.py',[QA/'make_alternatives.py','--json'])
assert source['summary']['counts']['FAIL']==0
(QA/'alternatives_source_preflight.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf8')
reports=[]
for stem in ['备选A_预测曲线','备选B_高需求柱状图']:
    pdf=OUT/(stem+'.pdf')
    glyphs=run_json('audit_pdf_text.py',[pdf,'--min-pt','7.5','--json'])
    assert glyphs['minimum_found_pt']>=7.5
    (QA/(stem+'.glyphs.json')).write_text(json.dumps(glyphs,ensure_ascii=False,indent=2),encoding='utf8')
    result=subprocess.run([sys.executable,str(SKILL/'audit_figure_collisions.py'),str(pdf),'--json-out',str(QA/(stem+'.collisions.json')),'--overlay-pdf',str(QA/(stem+'.collisions.pdf'))],capture_output=True,text=True,encoding='utf8',env=env)
    assert result.returncode==0,(stem,result.stdout,result.stderr)
    collision=json.loads((QA/(stem+'.collisions.json')).read_text(encoding='utf8'))
    assert collision['verdict']=='PASS'
    with fitz.open(pdf) as document:
        width_mm=document[0].rect.width/72*25.4
        assert abs(width_mm-138)<.05
    reports.append({'figure':stem,'width_mm':width_mm,'minimum_font_pt':glyphs['minimum_found_pt'],'collision':collision['verdict'],'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()})
manifest=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
assert hashlib.sha256(Path(manifest['output']).read_bytes()).hexdigest()==manifest['output_sha256']
report={'figures':reports,'word_unchanged':True,'source_preflight':source['summary'],'warning_review':'138 mm is the supplied journal width contract, confirmed from exported PDF.','visual_review_pending':True}
(QA/'alternatives_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
