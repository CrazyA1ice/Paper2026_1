from collections import Counter
from pathlib import Path
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops

sys.stdout.reconfigure(encoding='utf-8')
qa = Path(__file__).resolve().parent
root = qa.parents[1]
assets = root/'paper_template/长春工程学院学报(自然科学版)/逐项修订_20261023/V9_图表源文件'
old_assets = root/'paper_template/长春工程学院学报(自然科学版)/图表组织优化修订_20261022/图表与核验数据'
skill = Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
env = os.environ.copy()
env['PYTHONPATH'] = str(root/'review_scratch/figureqa_dependencies')+os.pathsep+env.get('PYTHONPATH','')
env['PYTHONIOENCODING'] = 'utf-8'
runs = []
figures = [(1,'图1_样本窗口符号统一'),(2,'图2_多基线误差降幅与参数比例'),
           (3,'图3_高需求局部范围点图'),(4,'图4_一周绝对误差与配对降幅')]

def run(name,args):
    result = subprocess.run([sys.executable,*map(str,args)], env=env,capture_output=True,encoding='utf-8')
    (qa/(name+'.txt')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    runs.append({'check':name,'returncode':result.returncode})

for filename in ['plot_figure1.py','plot_figures234.py']:
    run(filename+'_source',[skill/'validate_figure.py',qa/filename,'--json'])
for number,stem in figures:
    pdf = assets/(stem+'.pdf')
    run(f'figure{number}_text',[skill/'audit_pdf_text.py',pdf,'--min-pt','5','--json'])
    run(f'figure{number}_collision',[skill/'audit_figure_collisions.py',pdf,
        '--json-out',qa/f'figure{number}_collision.json','--overlay-pdf',qa/f'figure{number}_collision.pdf'])
    if number>1:
        before = Image.open(old_assets/(stem+'.png')).convert('RGB')
        after = Image.open(assets/(stem+'.png')).convert('RGB')
        assert before.size == after.size
        difference = ImageChops.difference(before,after)
        pixels = np.asarray(difference).max(axis=2)>0
        rows = np.where(pixels.any(axis=1))[0]
        (qa/f'figure{number}_pixel_difference.json').write_text(json.dumps({
            'same_dimensions':True,'changed_pixels':int(pixels.sum()),'changed_rows':rows.tolist(),
            'all_other_pixels_identical':True,'bbox':difference.getbbox()},ensure_ascii=False,indent=2),encoding='utf-8')
sys.path.insert(0,str(root/'review_scratch/figureqa_dependencies'))
import pymupdf
font_audit = {}
for number,stem in figures:
    pdf = pymupdf.open(assets/(stem+'.pdf'))
    spans = [s for page in pdf for b in page.get_text('dict')['blocks'] if 'lines' in b
             for line in b['lines'] for s in line['spans']]
    font_audit[str(number)] = {'fonts':dict(Counter(s['font'] for s in spans)),
        'minimum_glyph_size':min(s['size'] for s in spans),
        'non_tnr_math_or_foreign_glyphs':[
            {'text':s['text'],'font':s['font']} for s in spans
            if not any(name in s['font'] for name in ['Times','SimSun','SimHei','NSimSun'])]}
    pdf.close()
(qa/'figure_font_audit.json').write_text(json.dumps(font_audit,ensure_ascii=False,indent=2),encoding='utf-8')
(qa/'figure_checks.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(runs,ensure_ascii=False))
print(json.dumps(font_audit,ensure_ascii=False))
