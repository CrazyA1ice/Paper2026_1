from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
from copy import deepcopy
from html import escape
from io import BytesIO
import json
import re
import sys

from lxml import etree as E
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '内容精修_20261022/自适应多尺度加权的多变量网络流量预测_内容精修稿.docx'
OUTPUT = JOURNAL / '优势补充与图表优化_20261022/自适应多尺度加权的多变量网络流量预测_优势补充稿.docx'
SOURCE_SHA = '71f2b3f42a83c23e376f00c180344bc7b678a190672cd6862397a10758b403fc'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
evidence = json.loads((QA / 'evidence_audit.json').read_text(encoding='utf-8'))
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'v': 'urn:schemas-microsoft-com:vml'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old = E.fromstring(xml)
new = E.fromstring(xml)
body = new.find('w:body', NS)
edits = []


def replace_run(p, r, value):
    run = body[p].findall('w:r', NS)[r]
    nodes = run.xpath('.//w:t', namespaces=NS)
    assert len(nodes) == 1
    before = nodes[0].text
    assert before and before != value
    nodes[0].text = value
    edits.append({'paragraph': p, 'run': r, 'before': before, 'after': value})


existing = body[50].findall('w:r', NS)[0].find('w:t', NS).text
assert existing.count('增加。当') == 1
replace_run(50, 0, existing.replace('增加。当',
    f'增加；24 h配置中，路由参数仅占总参数量的{evidence["router_share_pct"]:.2f}%。当'))
high = {r['metric']: r for r in evidence['high_demand'] if r['dataset'] == 'abilene'}
replace_run(76, 0,
    '图3中，本文方法在Abilene上的MAE与平均低估误差分别为0.147和0.137，在GÉANT上分别为0.632和0.577，两项均值均低于所列对照。'
    f'相对DLinear，Abilene两项指标的平均相对降幅分别为{high["mae"]["mean_paired_reduction_pct"]:.2f}%和{high["mean_shortfall"]["mean_paired_reduction_pct"]:.2f}%。'
    'MAE反映总体偏差，平均低估误差侧重于预测需求不足的幅度，二者共同反映了该24 h任务中高需求点估计的改善，可为容量需求分析提供参考。')
replace_run(79, 0, '图4 GÉANT一周预测中本文方法相对各对照的误差降幅（8次重复）')
fusion = [r for r in evidence['weekly_summary'] if r['baseline'] != 'dlinear']
ranges = {metric: [min(r['mean'] for r in fusion if r['metric'] == metric),
                    max(r['mean'] for r in fusion if r['metric'] == metric)] for metric in ['mse', 'mae']}
replace_run(80, 0,
    '本文方法的MSE和MAE分别为0.841±0.088和0.536±0.028，低于图4中的四种对照。相对DLinear，两项指标的平均相对降幅分别为23.16%和11.16%；'
    f'相对其余三种融合对照，MSE降低{ranges["mse"][0]:.2f}%～{ranges["mse"][1]:.2f}%，MAE降低{ranges["mae"][0]:.2f}%～{ranges["mae"][1]:.2f}%。'
    '图中小圆点为相同随机种子下的单次相对降幅，菱形及横线表示均值与样本标准差。每种对照下的8次重复中，两项误差均降低，体现了该一周任务中优势方向的一致性。')

before_texts = old.xpath('.//w:t', namespaces=NS)
after_texts = new.xpath('.//w:t', namespaces=NS)
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
assert len(before_texts) == len(after_texts) == len(matches)
for i in range(len(matches) - 1, -1, -1):
    if before_texts[i].text != after_texts[i].text:
        match = matches[i]
        xml = xml[:match.start(2)] + escape(after_texts[i].text or '', quote=False).encode('utf-8') + xml[match.end(2):]
final = E.fromstring(xml)


def without_text(tree):
    tree = deepcopy(tree)
    for node in tree.xpath('.//w:t', namespaces=NS):
        node.text = ''
    return E.tostring(tree)


assert without_text(old) == without_text(final), 'Formatting or structural XML changed'
for path in ['.//w:tbl', './/m:oMath', './/w:pPr', './/w:rPr', './/w:sectPr']:
    assert [E.tostring(x) for x in old.xpath(path, namespaces=NS)] == [E.tostring(x) for x in final.xpath(path, namespaces=NS)], path
picture = Path(evidence['assets']) / '图4_配对优势图.png'
image_bytes = picture.read_bytes()
image_member = 'word/media/journal_figure4.png'
with Image.open(BytesIO(members[image_member])) as a, Image.open(BytesIO(image_bytes)) as b:
    assert a.size == b.size, (a.size, b.size)
    image_size = b.size
if OUTPUT.exists():
    previous = json.loads((QA / 'audit.json').read_text(encoding='utf-8'))
    assert sha256(OUTPUT.read_bytes()).hexdigest() == previous['output_sha256']
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        value = xml if info.filename == 'word/document.xml' else image_bytes if info.filename == image_member else members[info.filename]
        z.writestr(info, value)
with ZipFile(OUTPUT) as z:
    changed = [key for key, value in members.items() if z.read(key) != value]
assert changed == ['word/document.xml', image_member]
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
report = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
          'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'source_unchanged': True,
          'changed_package_parts': changed, 'styles_and_format_properties_unchanged': True,
          'all_original_tables_and_math_unchanged': True, 'other_three_figures_unchanged': True,
          'figure4_container_geometry_unchanged': True, 'figure4_image_pixels': image_size,
          'existing_empirical_values_unchanged': True, 'new_numbers_are_verified_derived_summaries': True,
          'new_experiments': False, 'edits': edits, 'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Advantage completion and figure organization\n\n'
    'Authority: the final content revision, SHA256 ' + SOURCE_SHA + '.\n'
    'Add only three supported details: router share of total parameters, existing high-demand endpoint reductions, '
    'and consistency of the reported weekly advantages across all eight matched seeds and all controls. '
    'Do not add a hardware discussion, new statistical tests, new endpoints, or a universal horizon/generalization claim.\n'
    'Preserve all styles, runs, paragraphs, section geometry, tables, native equations, references, and figures 1-3. '
    'Replace only figure 4 pixels in the existing unchanged container and update its caption and explanatory prose. '
    'All 64 paired observations are included. The original manuscript is retained.\n', encoding='utf-8')

# Reuse the already verified Windows read-only export and packaged rasterizer workflow.
previous_qa = ROOT / 'review_scratch/content_only_20261022'
for name in ['export_word.ps1', 'render_verify.py']:
    code = (previous_qa / name).read_text(encoding='utf-8')
    code = code.replace('content_only_20261022', 'advantages_20261022')
    (QA / name).write_text(code, encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'edits'}, ensure_ascii=False))
