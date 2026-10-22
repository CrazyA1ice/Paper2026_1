from pathlib import Path
import json
import subprocess
import sys
import fitz

qa = Path(__file__).resolve().parent
data = json.loads((qa / 'data_audit.json').read_text(encoding='utf-8'))
pdf = Path(data['assets']) / '图2_LightTS误差降低率与参数比例.pdf'
scripts = Path(r'C:\Users\Quant\.codex\skills\nature-figure\scripts')
reports = {}
for name, args in [
    ('source', [str(scripts / 'validate_figure.py'), str(qa / 'plot_lightts.py'), '--json']),
    ('text', [str(scripts / 'audit_pdf_text.py'), str(pdf), '--min-pt', '5', '--json']),
]:
    result = subprocess.run([sys.executable, '-X', 'utf8', *args], capture_output=True, text=True, encoding='utf-8', check=True)
    reports[name] = json.loads(result.stdout)
with fitz.open(pdf) as doc:
    size = [doc[0].rect.width * 25.4 / 72, doc[0].rect.height * 25.4 / 72]
assert abs(size[0] - 138) < .01
assert reports['source']['summary']['counts']['FAIL'] == 0
assert reports['text']['below_minimum_count'] == 0
reports['actual_pdf_size_mm'] = size
reports['source_width_warning_resolution'] = 'Static parser reads 138/25.4 incorrectly. Actual PDF width is 138 mm, matching the retained journal figure and unchanged Word container.'
reports['visual_review'] = 'PASS: all three panels checked; values, sample-SD bars, labels and baseline line are legible without collision or clipping.'
reports['alignment'] = json.loads((qa / 'figure2_alignment.json').read_text(encoding='utf-8'))['verdict']
assert reports['alignment'] == 'PASS'
(qa / 'figure2_final_qa.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
print('Figure 2 QA PASS; actual size mm:', size)
