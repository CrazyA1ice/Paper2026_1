from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '模板规范修订_20261021/自适应多尺度加权的多变量网络流量预测_期刊模板稿.docx'
OUTPUT = JOURNAL / '内容精修_20261022/自适应多尺度加权的多变量网络流量预测_内容精修稿.docx'
SOURCE_SHA = '1cce46cf2217fb245f43ff3f0586597f5f631b77637884421a8efc943a06be3d'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'v': 'urn:schemas-microsoft-com:vml'}
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
with ZipFile(SOURCE) as z:
    package = {i.filename: z.read(i.filename) for i in z.infolist()}
    infos = z.infolist()
xml = package['word/document.xml']
old_root = E.fromstring(xml)
root = E.fromstring(xml)
body = root.find('w:body', NS)
edits = []


def replace_run(p, r, new, reason):
    run = body[p].findall('w:r', NS)[r]
    nodes = run.findall('w:t', NS)
    assert len(nodes) == 1, (p, r)
    node = nodes[0]
    old = node.text or ''
    assert old and old != new
    node.text = new
    edits.append({'paragraph': p, 'run': r, 'before': old, 'after': new, 'purpose': reason})


replace_run(5, 1,
    '针对小时级网络流量预测，提出自适应多尺度加权方法。以三个分解线性模型（DLinear）处理多尺度输入，通过四维窗口统计量生成融合权重。8次重复实验中，Abilene和GÉANT的24 h预测均方误差较DLinear平均降低2.77%和2.35%；GÉANT的168 h预测均方误差和平均绝对误差分别降低23.16%和11.16%。24 h模型含8339个参数，为流量需求分析提供预测依据。',
    '简化重复实验表述，保留全部结果并明确应用对象')
replace_run(12, 6,
    '采用可分解多尺度混合；TimesNet公开基准',
    '将文献[8]明确对应到公开基准')
replace_run(12, 8,
    '则将基于多层感知机（multilayer perceptron，MLP）的LightTS纳入比较。本文关注以低维窗口特征调整不同尺度预测的融合权重。',
    '区分基准出处与模型名称，集中表述研究切入点')
replace_run(13, 0,
    '本文据此将三个独立DLinear专家与四维统计特征驱动的尺度路由相结合。时间聚合形成多尺度输入，各专家在OD变量间共享时间映射，路由网络则随窗口状态调整融合权重，以较少参数完成样本级融合。在Abilene和GÉANT上，以过去96 h预测未来24 h，通过基线比较、融合消融与高需求分析评价模型，并在GÉANT上考察未来168 h的一周预测表现。',
    '突出低维窗口融合与变量间共享映射的设计贡献')
replace_run(18, 4,
    '个OD变量。沿时间轴以1 h步长构造滑动窗口，第',
    '补明现有数据生成流程的窗口步长')
replace_run(18, 14,
    '组成，其中行对应时间点，列对应OD变量：',
    '简化矩阵维度说明，避免段尾单字独占一行')
replace_run(53, 6,
    '流量矩阵，两套数据分别含4656和2849个时间点。按时间顺序以6∶2∶2划分训练集、验证集和测试集，并独立训练和评价。对数变换后，仅保留训练集标准差大于10⁻⁸的变量，Abilene保留144个OD变量，GÉANT保留524个OD变量。两套数据均开展24 h预测，GÉANT另设168 h预测任务，数据划分与样本窗口数见表1。',
    '补明现有预处理流程的变量筛选阈值')
replace_run(56, 0,
    '基础实验中，各模型均以96 h历史预测未来24 h，批量大小为16。DLinear及多尺度模型的学习率为0.001，最多训练30轮，早停耐心值为6；LightTS采用TimesNet公开基准代码库的实现',
    '说明现有LightTS实现的基准来源，不改配置或引文格式')
replace_run(57, 0,
    '表2与图2采用42～44三个共同随机种子，表3、图3和图4采用42～49八个共同随机种子重复训练。误差报告均值与样本标准差，误差线表示样本标准差；相对降幅按相同种子下的结果计算，再取平均。',
    '统一重复训练和相对降幅的说明')
replace_run(65, 0,
    '表2中，本文方法在两套数据上的平均MSE和MAE均低于所列基线。图2给出相对LightTS的误差降幅与参数比例：在Abilene和GÉANT上，MSE平均相对降幅分别为29.80%和46.89%，MAE为17.57%和29.15%。本文模型均含8339个参数，LightTS两套配置分别含130162和384382个参数，对应比例为6.41%和2.17%。',
    '采用已在实验设置中定义的平均相对降幅术语')
replace_run(67, 6,
    ')以对应LightTS配置的参数量为100%，给出本文模型的参数比例。该结果表明，在所设24 h任务中，多尺度线性预测与低维窗口融合能够兼顾参数规模和预测误差。',
    '将参数比较与模型设计联系起来，减少结果复述')
replace_run(69, 0,
    '保持三个独立DLinear专家与尺度集合不变，比较融合方式。固定等权模型将权重设为1/3；全局可学习权重模型（图中简称“全局权重”）以三个可训练分数生成所有窗口共用的权重；恒定输入路由模型（图中简称“恒定路由”）保留两层路由网络，并输入全零特征。各对照均以真实历史序列驱动尺度专家，结果见表3。',
    '说明三个融合对照各自考察的设计因素')
replace_run(72, 0,
    '表3中，本文方法在两套数据上的平均MSE和MAE均低于所列对照。相对DLinear，MSE的平均相对降幅分别为2.77%和2.35%；相对全局可学习权重，分别为1.80%和4.31%。全局权重在窗口间保持一致，而本文方法以窗口统计量调整尺度组合；结合恒定输入路由的对照，结果支持了在该24 h任务中依据窗口信息进行融合预测的设计。',
    '在既有消融结果支持范围内解释窗口信息的作用')
replace_run(76, 0,
    '图3中，本文方法在Abilene上的MAE与平均低估误差分别为0.147和0.137，在GÉANT上分别为0.632和0.577，两项均值均低于所列对照。MAE反映总体偏差，平均低估误差侧重于预测需求不足的幅度，二者共同反映了该24 h任务中高需求点估计的改善，可为容量需求分析提供参考。',
    '解释高需求指标分别反映的含义及其需求分析用途')
replace_run(78, 0,
    '为评价较长预测区间的流量需求估计能力，在GÉANT上设置',
    '将一周任务的目的与需求估计衔接')
replace_run(80, 0,
    '本文方法的MSE和MAE分别为0.841±0.088和0.536±0.028，低于图4中的四种对照。相对DLinear，两项指标的平均相对降幅分别为23.16%和11.16%。在覆盖一周的同时保留逐小时输出，使预测结果能够描述较长区间内的需求变化；上述误差比较为开展这一时间范围的流量需求分析提供了实验依据。',
    '突出一周范围与逐小时输出的关系，不扩展到未报告时长')
replace_run(83, 0,
    '24 h任务的基线比较和融合消融表明，本文方法在Abilene和GÉANT上均取得了较低的平均预测误差。相对LightTS，MSE的平均相对降幅分别为29.80%和46.89%，参数量分别为对应LightTS配置的6.41%和2.17%。在GÉANT的一周任务中，MSE与MAE相对DLinear的平均相对降幅分别为23.16%和11.16%。结合高需求点的预测结果，这些实验为利用低维窗口信息融合多尺度预测提供了依据，可为小时级OD流量需求分析提供方法参考。',
    '统一术语，并使结语覆盖高需求分析')
replace_run(102, 1,
    ' An adaptive multiscale weighting method is proposed for hourly network traffic forecasting. Three decomposition linear models (DLinear) process multiscale inputs, and four window statistics determine their fusion weights. Across eight training runs with different random seeds, the mean relative reductions in mean squared error against DLinear are 2.77% on Abilene and 2.35% on GÉANT for 24-hour forecasting. For the 168-hour GÉANT task, the corresponding reductions in mean squared error and mean absolute error are 23.16% and 11.16%. The 24-hour model contains 8,339 parameters, providing a forecasting method for traffic demand analysis.',
    '同步中英文摘要的实验口径和应用表述')

# Patch only existing text payloads. Every tag, attribute, run, paragraph, and
# package part other than these payloads retains its original bytes.
old_texts = old_root.xpath('.//w:t', namespaces=NS)
new_texts = root.xpath('.//w:t', namespaces=NS)
assert len(old_texts) == len(new_texts)
matches = list(re.finditer(rb'(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)', xml, re.S))
assert len(matches) == len(old_texts)
changed_text_indices = []
out_xml = xml
for i in range(len(matches) - 1, -1, -1):
    if (old_texts[i].text or '') != (new_texts[i].text or ''):
        m = matches[i]
        encoded = escape(new_texts[i].text or '', quote=False).encode('utf-8')
        out_xml = out_xml[:m.start(2)] + encoded + out_xml[m.end(2):]
        changed_text_indices.append(i)
new_root = E.fromstring(out_xml)

def no_text(tree):
    tree = deepcopy(tree)
    for t in tree.xpath('.//w:t', namespaces=NS):
        t.text = ''
    return E.tostring(tree)

assert no_text(old_root) == no_text(new_root), 'Non-text XML change'
for xpath in ['.//w:tbl', './/m:oMath', './/v:shape', './/w:sectPr', './/w:pPr', './/w:rPr']:
    before = old_root.xpath(xpath, namespaces=NS)
    after = new_root.xpath(xpath, namespaces=NS)
    assert [E.tostring(e) for e in before] == [E.tostring(e) for e in after], xpath
for edit in edits:
    p = edit['paragraph']
    # No removal or modification of existing numeric results. Allowed additions
    # express the existing eight-seed protocol, window stride, and filter threshold.
    numbers = lambda s: Counter(re.findall(r'\d+(?:\.\d+)?', s))
    before, after = numbers(edit['before']), numbers(edit['after'])
    assert not (before - after), (p, before - after)
    added = after - before
    assert not added or p in [5, 18, 53], (p, added)
    edit['added_numeric_tokens'] = dict(added)
cn_abs = ''.join(body[5].xpath('.//w:t/text()', namespaces=NS)).removeprefix('摘要：')
assert len(cn_abs) <= 200
all_text = ''.join(new_root.xpath('.//w:t/text()', namespaces=NS))
for token in ['八种子', '逐种子', '补充材料', 'CPU', 'GPU', '显卡', '显著优于']:
    assert token not in all_text, token
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    previous = json.loads((QA / 'audit.json').read_text(encoding='utf-8'))
    assert sha256(OUTPUT.read_bytes()).hexdigest() == previous['output_sha256'], 'Output changed outside this revision'
with ZipFile(OUTPUT, 'w') as z:
    for info in infos:
        z.writestr(info, out_xml if info.filename == 'word/document.xml' else package[info.filename])
with ZipFile(OUTPUT) as z:
    changed_parts = [name for name, data in package.items() if z.read(name) != data]
assert changed_parts == ['word/document.xml']
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
report = {
    'source': str(SOURCE), 'source_sha256': SOURCE_SHA,
    'output': str(OUTPUT), 'output_sha256': sha256(OUTPUT.read_bytes()).hexdigest(),
    'changed_package_parts': changed_parts, 'only_existing_text_payloads_changed': True,
    'format_properties_unchanged': True, 'tables_byte_equivalent': True,
    'math_byte_equivalent': True, 'figure_shapes_byte_equivalent': True,
    'all_other_package_parts_byte_identical': True,
    'original_numeric_tokens_preserved_in_each_edited_run': True,
    'source_unchanged': True, 'chinese_abstract_characters': len(cn_abs),
    'paragraphs_changed': sorted({e['paragraph'] for e in edits}),
    'text_payloads_changed': len(changed_text_indices),
    'visual_review_pending': True, 'edits': edits,
    'external_verification': {
        'TimesNet_benchmark': 'https://arxiv.org/pdf/2210.02186',
        'published_code_redirect': 'https://github.com/thuml/TimesNet',
        'local_implementation': 'abilene_forecasting/external/lightts/README.md',
        'preprocessing': 'abilene_forecasting/prepare_dataset.py',
        'window_stride': 'abilene_forecasting/src/data.py'
    }
}
(QA / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'artifact.md').write_text(
    '# Content-only revision contract\n\n'
    'Authority: final template manuscript with SHA256 ' + SOURCE_SHA + '.\n\n'
    'Change only existing text payloads. Preserve the complete non-text XML tree, all run and paragraph '
    'properties, headings, sections, native math, tables, figure text boxes, image assets, styles, '
    'relationships, reference entries, citation runs, and original numeric tokens. No new experiments. '
    'Only add implementation-confirmed stride and variable-filter threshold. Keep Chinese abstract '
    'within 200 characters and synchronize its English version. Claims stay within the reported tasks.\n\n'
    'Verification: only document.xml changes; removing text values yields exactly the original XML tree. '
    'All other package members retain their bytes. Preserve original manuscript. Native Word read-only '
    'export and packaged rasterizer will be used for every-page visual QA.\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ['edits', 'external_verification']}, ensure_ascii=False))
