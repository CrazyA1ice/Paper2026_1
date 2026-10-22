from copy import deepcopy
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

from lxml import etree as E
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '窗口动机衔接修订_20261022/自适应多尺度加权的多变量网络流量预测_窗口动机修订稿.docx'
OUT = JOURNAL / '八次重复统一修订_20261022'
OUTPUT = OUT / '自适应多尺度加权的多变量网络流量预测_八次重复统一稿.docx'
SOURCE_SHA = '7d77ec216d7f57ba108bce2d98b30196ce34268af5e76aa977885e4684292297'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert not OUTPUT.exists()
data = json.loads((QA / 'data_audit.json').read_text(encoding='utf-8'))
assert data['metric_files_verified'] == data['prediction_archives_verified'] == 48
assert data['no_rows_excluded'] and data['all_test_targets_identical_within_dataset']
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    infos = z.infolist()
    members = {i.filename: z.read(i.filename) for i in infos}
xml = members['word/document.xml']
old, new = E.fromstring(xml), E.fromstring(xml)
body = new.find('w:body', NS)
edits = []


def replace_node(node, value, location):
    assert node.text
    if node.text != value:
        edits.append({'location': location, 'before': node.text, 'after': value})
        node.text = value


def replace_run(p, r, value):
    nodes = body[p].findall('w:r', NS)[r].xpath('.//w:t', namespaces=NS)
    assert len(nodes) == 1
    replace_node(nodes[0], value, f'body[{p}].run[{r}]')


replace_run(57, 0, '各模型均采用42～49八个共同随机种子重复训练。误差报告均值与样本标准差，误差线表示样本标准差；相对降幅按相同种子下的结果计算，再取平均。')
assert '3次重复' in body[63].find('w:r/w:t', NS).text
replace_run(63, 0, '表2 基线模型的24 h预测误差（8次重复）')
effects = {(r['dataset'], r['metric']): r['mean'] for r in data['effects']}
for p in [65, 83]:
    text = body[p].find('w:r/w:t', NS).text
    for before, key in [('29.80%', ('abilene', 'mse')), ('46.89%', ('geant', 'mse')),
                        ('17.57%', ('abilene', 'mae')), ('29.15%', ('geant', 'mae'))]:
        if before in text:
            assert text.count(before) == 1
            text = text.replace(before, f'{effects[key]:.2f}%')
    replace_run(p, 0, text)
node = body[67].findall('w:r', NS)[4].find('w:t', NS)
assert '三个共同种子' in node.text
replace_run(67, 4, node.text.replace('三个共同种子', '八个共同种子'))

tables = new.xpath('.//w:tbl', namespaces=NS)
summary = {(r['dataset'], r['model']): r for r in data['summary']}
for i, (dataset, model) in enumerate([(d, m) for d in ['abilene', 'geant']
                                    for m in ['dlinear', 'lightts', 'dlinear_scale']], 1):
    cells = tables[1].findall('w:tr', NS)[i].findall('w:tc', NS)
    row = summary[dataset, model]
    for j, metric in [(2, 'mse'), (3, 'mae')]:
        nodes = cells[j].xpath('.//w:t', namespaces=NS)
        assert len(nodes) == 1
        replace_node(nodes[0], f'{row[metric+"_mean"]:.3f}±{row[metric+"_sd"]:.3f}', f'table2.row[{i}].cell[{j}]')

# Identical tasks/models must use exactly the same display values in both tables.
for table2_row, table3_row in [(1, 1), (3, 5), (4, 6), (6, 10)]:
    rows = [tables[1].findall('w:tr', NS)[table2_row], tables[2].findall('w:tr', NS)[table3_row]]
    values = [[''.join(c.xpath('.//w:t/text()', namespaces=NS)) for c in r.findall('w:tc', NS)] for r in rows]
    assert values[0] == values[1], values

before_nodes, after_nodes = old.xpath('.//w:t', namespaces=NS), new.xpath('.//w:t', namespaces=NS)
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
assert len(before_nodes) == len(after_nodes) == len(matches)
for i in range(len(matches) - 1, -1, -1):
    if before_nodes[i].text != after_nodes[i].text:
        match = matches[i]
        xml = xml[:match.start(2)] + escape(after_nodes[i].text or '', quote=False).encode('utf-8') + xml[match.end(2):]
final = E.fromstring(xml)


def without_text(tree):
    tree = deepcopy(tree)
    for n in tree.xpath('.//w:t', namespaces=NS):
        n.text = ''
    return E.tostring(tree)


assert without_text(old) == without_text(final), 'Formatting changed'
for path in ['.//m:oMath', './/w:pPr', './/w:rPr', './/w:sectPr']:
    assert [E.tostring(x) for x in old.xpath(path, namespaces=NS)] == [E.tostring(x) for x in final.xpath(path, namespaces=NS)]
old_tables, final_tables = old.xpath('.//w:tbl', namespaces=NS), final.xpath('.//w:tbl', namespaces=NS)
assert E.tostring(old_tables[0]) == E.tostring(final_tables[0])
assert E.tostring(old_tables[2]) == E.tostring(final_tables[2])
plain = ''.join(final.xpath('.//w:t/text()', namespaces=NS))
for prohibited in ['三个共同种子', '三个共同随机种子', '3次重复', '29.80%', '46.89%', '17.57%', '29.15%']:
    assert prohibited not in plain, prohibited
image_member = 'word/media/journal_figure2.png'
image = (Path(data['assets']) / '图2_LightTS误差降低率与参数比例.png').read_bytes()
with Image.open(BytesIO(members[image_member])) as previous, Image.open(BytesIO(image)) as updated:
    assert previous.size == updated.size
OUT.mkdir(exist_ok=True)
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        value = xml if info.filename == 'word/document.xml' else image if info.filename == image_member else members[info.filename]
        z.writestr(info, value)
with ZipFile(OUTPUT) as z:
    changed = [name for name, value in members.items() if z.read(name) != value]
assert changed == ['word/document.xml', image_member]
report = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'output': str(OUTPUT),
          'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'source_unchanged': True,
          'changed_package_parts': changed, 'styles_and_format_properties_unchanged': True,
          'all_native_math_unchanged': True, 'tables_1_and_3_unchanged': True,
          'figures_1_3_4_unchanged': True, 'table2_and_table3_identical_for_shared_models': True,
          'figure2_container_geometry_unchanged': True, 'edits': edits, 'visual_review_pending': True}
(QA / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Eight-seed unification\n\nAuthority: retain the accepted journal manuscript and all its format properties. '
    'Unify baseline comparison and fusion ablations to seeds 42–49. Only LightTS seeds 45–49 are newly trained; '
    'use all original runs and all prespecified new runs. Refresh table 2, figure 2, repeat descriptions and the '
    'associated Results/Conclusion percentages. Preserve introduction revision, algorithms, data splits, '
    'native equations, other tables/figures, references, fonts and geometry.\n', encoding='utf-8')
for name in ['export_word.ps1', 'render_verify.py']:
    code = (ROOT / 'review_scratch/window_motivation_20261022' / name).read_text(encoding='utf-8')
    code = code.replace('window_motivation_20261022', 'eight_seed_unification_20261022')
    if name == 'render_verify.py':
        code = code.replace("'2.77%', '2.35%', '29.80%', '46.89%', '23.16%', '11.16%',",
                            f"'2.77%', '2.35%', '{effects['abilene','mse']:.2f}%', '{effects['geant','mse']:.2f}%', '23.16%', '11.16%',")
    (QA / name).write_text(code, encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'edits'}, ensure_ascii=False))
