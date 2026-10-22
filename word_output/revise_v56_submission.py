"""Apply the supplied journal requirements using local OOXML edits."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
import hashlib
import json
import re

from lxml import etree
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'word_output/2026.10.02v55.docx'
TARGET = ROOT / 'word_output/2026.10.03v56.docx'
QA = ROOT / 'word_output/v56_submission_review'
FIGURES = ROOT / 'paper_figures/v56_cdgyxy'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'w': W, 'm': M, 'r': R, 'wp': WP, 'a': A}

ABSTRACT = ('为提高小时级骨干网络流量的多步预测精度，构建了轻量自适应多尺度预测模型。'
 '模型将历史窗口转换为三种时间分辨率的序列，分别交由独立的分解线性专家处理，以兼顾局部变化和较慢趋势。'
 '路由网络提取窗口的总体水平、离散程度、末时状态和平均变化强度，经两层感知器生成融合权重，得到未来多步预测。'
 '在输入长度为96、预测长度为24的Abilene与GÉANT实验中，三个共同随机种子下的均方误差相对单尺度模型分别降低4.07%和4.54%，'
 '相对采样导向轻量模型分别降低29.80%和46.89%。八种子消融进一步比较全局可学习权重与恒定输入路由，'
 '前一数据集的平均改进率均约1.80%，后一数据集分别为4.31%和4.97%。结果表明，该结构在两套骨干网数据上取得了较低的平均预测误差，'
 '低维路由仅增加少量参数，可为未来一天的需求观察与容量规划提供预测参考。')
ENGLISH_ABSTRACT = ('A lightweight adaptive multiscale model was developed to improve multistep forecasting of hourly backbone traffic. '
 'Historical windows were represented at three temporal resolutions. Independent decomposition linear predictors captured local changes and slower trends. '
 'A two-layer perceptron used four window statistics to produce normalized fusion weights. '
 'Experiments on Abilene and GÉANT used an input length of 96 and a forecast length of 24. '
 'Across three common random seeds, mean squared error decreased by 4.07% and 4.54% relative to the single-scale model, '
 'and by 29.80% and 46.89% relative to the sampling-oriented lightweight model. '
 'Eight-seed ablations included learned global weights and a constant-input router. '
 'Mean seed-wise improvements over these controls were both approximately 1.80% on Abilene, and 4.31% and 4.97% on GÉANT, respectively. '
 'The model achieves lower mean errors on both backbone datasets with limited additional routing parameters. '
 'It provides forecasting information for next-day demand observation and capacity planning.')
CONCLUSION = ('自适应多尺度加权将独立分解线性专家与低维窗口路由结合，以较小参数规模完成小时级骨干网流量预测。'
 '两套数据的重复实验显示，其平均误差低于所设单尺度及固定融合对照，可为未来一天的需求分析提供参考。'
 '后续需在更多网络数据和预测长度下检验适用性。')

# Compress repeated explanations to meet the suggested 8,000-word ceiling.
# Keep all experimental results, definitions, references and native equations.
CONCISE = {
 12: '源—目的节点对（origin-destination，OD）流量描述骨干网节点对之间的通信需求。容量规划、拥塞预警、资源调度和流量工程需要判断未来流量，本文预测小时级OD需求，为未来一天的趋势观察与容量规划提供参考。云计算、视频业务和数据中心互联增加了业务迁移与聚集，使流量变化更复杂。周期变化、局部波动与突发变化叠加，各OD变量量级不同，模型需同时刻画较慢趋势与短时变化。',
 13: 'Lohrasbinasab等[1]综述了网络流量预测方法，指出机器学习与深度学习等数据驱动方法的应用不断增加。网络规模扩大后，仅分析单一序列难以覆盖OD变量之间的关联。Qin等[2]采用图神经网络处理空间关联与时间依赖；韦烜等[3]分析大型网际协议（Internet protocol，IP）网络流量矩阵的变量关联及时间变化；唐文杰等[4]在CycleLLH中引入周期性信息。这些研究从时间依赖、变量关联和周期结构等角度开展预测。',
 14: '原始时间分辨率保留局部细节，时间聚合平滑短时扰动并突出较慢趋势。Zhou等[5]采用深度回声状态网络提取多分辨率信息，利用各尺度互补性。分解线性模型（decomposition linear model，DLinear）[6]通过序列分解和线性映射预测，TimeMixer[7]采用多尺度混合，LightTS[8]以采样导向的多层感知器（multilayer perceptron，MLP）实现快速预测。本文兼顾多尺度信息与模型规模。',
 15: '常见流程先给定尺度，再按固定比例融合预测。输入窗口的短时波动和平缓趋势占比不同，单尺度难以覆盖多分辨率信息，固定融合也未使用窗口状态差异。本文据此计算输入相关权重，组合各尺度预测。',
 17: '本文采用样本级自适应多尺度结构：尺度1、2和4的独立DLinear专家生成候选预测，路由网络读取窗口的总体水平、离散程度、最近状态和变化强度，经Softmax生成融合权重，使尺度内预测与尺度间选择分开处理。在Abilene和GÉANT上比较DLinear、LightTS、固定等权、全局可学习权重和恒定输入路由，通过多随机种子实验及权重分析检验预测误差、结构消融与尺度分配行为。',
 20: '原始尺度保留局部变化，较粗尺度通过时间聚合突出慢趋势。各尺度独立预测，路由网络确定样本融合比例；统一采用DLinear专家控制规模，也为多尺度输入与样本级融合提供相同主干。',
 37: 'L=96时，尺度1保留原始96步序列；尺度2取相邻2点均值，得到48步；尺度4取相邻4点均值，得到24步。三者分别保留短时起伏、适度平滑局部变化及进一步突出慢趋势。非重叠平均池化无需训练参数，多尺度构造不增加模型参数。',
 38: '尺度组合{1,2,4}将96步历史分为整数长度序列，在细粒度信息、趋势信息与模型规模之间作出取舍。增加尺度会缩短序列并增加专家分支。同一尺度内，每个原始时间点仅参与一次聚合。',
 61: '模型由多尺度池化、独立专家预测和窗口路由融合组成。后续设置单尺度DLinear、固定等权、全局可学习权重、恒定输入路由和本文方法，以相同专家结构区分多尺度信息与样本级加权的作用。',
 64: '实验包括外部基线比较、核心消融和路由分析。LightTS为独立外部基线，DLinear为单尺度参照；三类固定融合对照与本文方法使用相同尺度专家，分别训练，比较多尺度、非等权及输入相关融合。八个共同种子的配对结果与权重分析用于评估结果波动。',
 66: '数据取自CESNET TS-Zoo[9]的1 h聚合Abilene[10]和GÉANT[11]流量矩阵。Abilene含4656个时间点、144维有效OD变量；GÉANT含2849个时间点，去除恒定通道后保留524维。两套数据均按时间顺序以6∶2∶2划分，采用L=96、H=24和第1.1节预处理，规模与窗口数见表1。',
 68: '所有模型使用相同的数据划分、输入和预测长度、评价指标及批量大小16，未分别搜索最优超参数。DLinear及各多尺度模型最多训练30轮，LightTS为50轮；均按验证集MSE选择参数，测试集仅用于最终统计。',
 71: 'DLinear提供单尺度参照，LightTS为独立轻量模型基线。固定等权、全局可学习权重和恒定输入路由与本文方法共用尺度集合{1,2,4}及DLinear主干，以控制结构差异并检验融合方式。后两类对照对全部窗口使用一组常权重。',
 73: '固定等权模型将各尺度权重设为1/3；全局权重模型用三个可训练参数经Softmax生成常权重；恒定输入路由保留完整网络，但训练与推理均输入全零窗口，使所有样本共用权重。三类对照的专家均接收真实历史窗口，用于区分多尺度、非等权与样本相关分配的作用。',
 77: '指标在标准化空间计算，越小越好。MSE对较大误差敏感，MAE反映平均绝对偏差，RMSE补充误差幅值。表2与表3分别以均值±标准差汇总种子42～44和42～49的结果，标准差反映种子间波动。相对改进率先按共同种子配对计算，再取平均，不使用表内四舍五入后的均值。',
 84: '本文方法在OD规模不同的两套数据上均优于LightTS，GÉANT的MSE降幅更高。下节以相同多尺度专家检验融合方式。',
 105: '运维模块可定期读取小时级历史OD序列，生成未来一天的需求估计，辅助识别高需求时段与容量变化，为趋势观察和容量规划提供参考。',
 106: '图4中各模型在高真实值区间均有低估，本文方法的分组平均偏差较小，有助于观察模型对高需求趋势的刻画。',
 107: '实验评估标准化OD流量。实际接入网络管理系统时，需恢复原始量纲，再结合拓扑、路由和链路容量，由OD需求分析链路负载。',
}


def q(tag, namespace=W):
    return f'{{{namespace}}}{tag}'


def child(parent, tag, first=False):
    item = parent.find(q(tag))
    if item is None:
        item = etree.Element(q(tag))
        parent.insert(0, item) if first else parent.append(item)
    return item


def text(paragraph):
    return ''.join(paragraph.xpath('.//w:t/text()', namespaces=NS))


def font(run, east='宋体', size=10.5, bold=None):
    props = child(run, 'rPr', first=True)
    fonts = child(props, 'rFonts')
    fonts.attrib.clear()
    for key, value in [('eastAsia', east), ('ascii', 'Times New Roman'), ('hAnsi', 'Times New Roman'), ('cs', 'Times New Roman')]:
        fonts.set(q(key), value)
    for name in ['sz', 'szCs']:
        child(props, name).set(q('val'), str(round(size * 2)))
    child(props, 'color').set(q('val'), '000000')
    if bold is not None:
        child(props, 'b').set(q('val'), '1' if bold else '0')


def paragraph_format(p, align=None, keep_next=False):
    props = child(p, 'pPr', first=True)
    spacing = child(props, 'spacing')
    spacing.set(q('line'), '240')
    spacing.set(q('lineRule'), 'auto')
    if align:
        child(props, 'jc').set(q('val'), align)
    for item in props.findall(q('pageBreakBefore')):
        props.remove(item)
    child(props, 'keepNext').set(q('val'), '1' if keep_next else '0')
    child(props, 'keepLines').set(q('val'), '1')


changes = []
def replace(p, value, label=None):
    before = text(p)
    for element in list(p):
        if element.tag != q('pPr'):
            p.remove(element)
    if label:
        r = etree.SubElement(p, q('r'))
        font(r, bold=True)
        label_text = etree.SubElement(r, q('t'))
        label_text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        label_text.text = label
    r = etree.SubElement(p, q('r'))
    font(r, bold=False)
    etree.SubElement(r, q('t')).text = value
    changes.append({'before': before, 'after': (label or '') + value})


def serialize(root):
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def main():
    QA.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as source:
        parts = {info.filename: source.read(info.filename) for info in source.infolist()}
        infos = source.infolist()
    root = etree.fromstring(parts['word/document.xml'])
    original = deepcopy(root)
    paragraphs = root.xpath('./w:body/w:p', namespaces=NS)
    assert len(paragraphs) == 124
    table_text_before = [t.xpath('.//w:t/text()', namespaces=NS) for t in root.xpath('./w:body/w:tbl', namespaces=NS)]
    math_text_before = [e.xpath('.//m:t/text()', namespaces=NS) for e in root.xpath('//m:oMath', namespaces=NS)]

    replace(paragraphs[3], ABSTRACT, '摘要：')
    replace(paragraphs[4], '网络流量预测；多变量时间序列；多尺度学习；自适应加权；线性分解预测', '关键词：')
    replace(paragraphs[9], ENGLISH_ABSTRACT, 'Abstract: ')
    replace(paragraphs[10], 'network traffic forecasting; multivariate time series; multiscale learning; adaptive weighting; linear decomposition forecasting', 'Key words: ')
    replace(paragraphs[11], '引言')
    replace(paragraphs[13], text(paragraphs[13]).replace('大型IP网络', '大型网际协议（Internet protocol，IP）网络'))
    replace(paragraphs[14], text(paragraphs[14])
            .replace('DLinear[6]', '分解线性模型（decomposition linear model，DLinear）[6]', 1)
            .replace('MLP结构', '多层感知器（multilayer perceptron，MLP）结构', 1))
    replace(paragraphs[50], text(paragraphs[50]).replace('其尺度分数计算为',
            '隐藏层采用修正线性单元（rectified linear unit，ReLU）。其尺度分数计算为'))
    replace(paragraphs[58], text(paragraphs[58]).replace('均方误差训练模型', '均方误差（mean squared error，MSE）训练模型', 1))
    replace(paragraphs[60], text(paragraphs[60]).replace('Adam优化器', '自适应矩估计（adaptive moment estimation，Adam）优化器', 1))
    replace(paragraphs[68], text(paragraphs[68]).replace('batch size统一为16', '批量大小统一为16'))
    replace(paragraphs[74], text(paragraphs[74])
            .replace('平均绝对误差（MAE）', '平均绝对误差（mean absolute error，MAE）')
            .replace('均方根误差（RMSE）', '均方根误差（root mean squared error，RMSE）'))
    replace(paragraphs[108], '3 结语')
    replace(paragraphs[109], CONCLUSION)
    for index, value in CONCISE.items():
        assert not paragraphs[index].xpath('.//m:oMath', namespaces=NS)
        replace(paragraphs[index], value)
    changes.append({'before': text(paragraphs[72]), 'after': '共用DLinear主干的说明并入上一段，删除重复段落'})
    paragraphs[72].getparent().remove(paragraphs[72])
    for index in [110, 111]:
        changes.append({'before': text(paragraphs[index]), 'after': '并入150字以内结语'})
        paragraphs[index].getparent().remove(paragraphs[index])
    # Put the detailed interpretation before Figure 4 as the journal asks;
    # this also uses the space left above the large composite figure.
    paragraphs[94].addprevious(paragraphs[96])

    author_expansions = {
        114: [('QIN L, GU H, WEI W', 'QIN Liang, GU Huaxi, WEI Wenting')],
        117: [('ZHOU J, HAN T, XIAO F', 'ZHOU Jian, HAN Taotao, XIAO Fu')],
        118: [('ZENG A, CHEN M, ZHANG L', 'ZENG Ailing, CHEN Muxi, ZHANG Lei'),
              ('[C]//Proceedings', '[J]. Proceedings')],
        119: [('WANG S, WU H, SHI X', 'WANG Shiyu, WU Haixu, SHI Xiaoming'),
              ('[C]//International Conference on Learning Representations. 2024.',
               '[C/OL]//International Conference on Learning Representations. 2024[2026-10-03]. https://openreview.net/forum?id=7oLshfEIC2.')],
        120: [('ZHANG T, ZHANG Y, CAO W', 'ZHANG Tianping, ZHANG Yizhuo, CAO Wei'),
              ('[2026-09-20]', '[2026-10-03]')],
        121: [('Management. 2025.', 'Management. New York: IEEE, 2025: 1-5.')],
        122: [('ZHANG Y, ROUGHAN M', 'ZHANG Yin, ROUGHAN M')],
    }
    for index, replacements in author_expansions.items():
        value = text(paragraphs[index])
        for before, after in replacements:
            assert before in value, before
            value = value.replace(before, after, 1)
        replace(paragraphs[index], value)

    # Default body font, explicit single spacing, and local hierarchy styles.
    for p in root.xpath('.//w:p', namespaces=NS):
        paragraph_format(p)
        for run in p.xpath('./w:r', namespaces=NS):
            font(run)
    for index in [0, 6, 1, 2, 7, 8]:
        p = paragraphs[index]
        paragraph_format(p, 'center', keep_next=True)
        east, size, bold = ('黑体', 18, True) if index == 0 else (
            ('宋体', 14, True) if index == 6 else ('楷体', 10.5 if index in [1, 7] else 9, False))
        for run in p.xpath('./w:r', namespaces=NS):
            font(run, east, size, bold)
    for p in root.xpath('./w:body/w:p', namespaces=NS):
        value = text(p).strip()
        if re.match(r'^\d+\s', value) or value in ['引言', '参考文献']:
            paragraph_format(p, 'left', keep_next=True)
            for run in p.xpath('./w:r', namespaces=NS):
                font(run, '黑体', 12, True)
        elif re.match(r'^\d+\.\d+\s', value):
            paragraph_format(p, 'left', keep_next=True)
            for run in p.xpath('./w:r', namespaces=NS):
                font(run, '黑体', 10.5, True)
        elif re.match(r'^[图表]\d+\s', value):
            paragraph_format(p, 'center', keep_next=value.startswith('表'))
            for run in p.xpath('./w:r', namespaces=NS):
                font(run, '黑体', 9, True)
        elif re.match(r'^\[\d+\]', value):
            for run in p.xpath('./w:r', namespaces=NS):
                font(run, '宋体', 9, False)
        if p.xpath('.//wp:inline', namespaces=NS):
            paragraph_format(p, 'center', keep_next=True)

    # Each equation remains a native, editable Word equation. Only the bold
    # matrix/vector style is corrected from upright bold to bold italic.
    styled = 0
    for element in root.xpath('//m:sty[@m:val="b"]', namespaces=NS):
        element.set(q('val', M), 'bi')
        styled += 1
    index_styles = 0
    for run in root.xpath('//m:sub//m:r|//m:sup//m:r', namespaces=NS):
        value = ''.join(run.xpath('./m:t/text()', namespaces=NS))
        if value in ['tr', 'te', 'T', 'R', 'MSE']:
            props = run.find(q('rPr', M))
            if props is None:
                props = etree.Element(q('rPr', M)); run.insert(0, props)
            style = props.find(q('sty', M))
            if style is None:
                style = etree.SubElement(props, q('sty', M))
            if style.get(q('val', M)) != 'p':
                style.set(q('val', M), 'p'); index_styles += 1
    for p in root.xpath('./w:body/w:p', namespaces=NS):
        if re.fullmatch(r'\s*\(\d+\)\s*', text(p)):
            props = child(p, 'pPr', first=True)
            tabs = child(props, 'tabs')
            tabs.clear()
            for alignment, position in [('center', '4819'), ('right', '9638')]:
                tab = etree.SubElement(tabs, q('tab'))
                tab.set(q('val'), alignment)
                tab.set(q('pos'), position)

    # Three-line tables: top, header separator, bottom; no vertical rules.
    for table in root.xpath('./w:body/w:tbl', namespaces=NS):
        borders = child(child(table, 'tblPr', first=True), 'tblBorders')
        borders.clear()
        for edge in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            line = etree.SubElement(borders, q(edge))
            line.set(q('val'), 'single' if edge in ['top', 'bottom'] else 'nil')
            line.set(q('sz'), '8')
            line.set(q('color'), '000000')
        rows = table.findall(q('tr'))
        for index, row in enumerate(rows):
            child(child(row, 'trPr', first=True), 'cantSplit')
            for cell in row.findall(q('tc')):
                props = child(cell, 'tcPr', first=True)
                cell_borders = child(props, 'tcBorders')
                cell_borders.clear()
                for edge in ['top', 'left', 'bottom', 'right']:
                    line = etree.SubElement(cell_borders, q(edge))
                    visible = (edge == 'top' and index == 0) or (edge == 'bottom' and index in [0, len(rows)-1])
                    line.set(q('val'), 'single' if visible else 'nil')
                    line.set(q('sz'), '6' if edge == 'bottom' and index == 0 else '8')
                    line.set(q('color'), '000000')
                child(props, 'vAlign').set(q('val'), 'center')
                for p in cell.findall(q('p')):
                    paragraph_format(p, keep_next=index < len(rows)-1)
            if index == 0:
                child(child(row, 'trPr', first=True), 'tblHeader')
    for index in [66, 79, 86]:
        paragraph_format(paragraphs[index], keep_next=True)

    for section in root.xpath('//w:sectPr', namespaces=NS):
        margins = child(section, 'pgMar')
        for name, value in [('top','1757'),('bottom','1417'),('left','1134'),('right','1134')]:
            margins.set(q(name), value)
        child(section, 'cols').set(q('num'), '1')
        child(section, 'pgSz').attrib.pop(q('orient'), None)

    relation = etree.fromstring(parts['word/_rels/document.xml.rels'])
    targets = {e.get('Id'): 'word/' + e.get('Target') for e in relation}
    figure_changes = []
    pictures = root.xpath('//wp:inline', namespaces=NS)
    assert len(pictures) == 5
    for number, inline in enumerate(pictures, 1):
        blip = inline.find('.//' + q('blip', A))
        media = targets[blip.get(q('embed', R))]
        image_path = FIGURES / f'fig{number}.png'
        with Image.open(image_path) as image:
            width, height = image.size
        extent = inline.find(q('extent', WP))
        cx = 5829300  # 161.925 mm, same as selected Figure 1 in v55.
        cy = round(cx * height / width)
        for size in [extent] + inline.findall('.//' + q('ext', A)):
            size.set('cx', str(cx)); size.set('cy', str(cy))
        parts[media] = image_path.read_bytes()
        figure_changes.append({'figure': number, 'media': media, 'width_mm': 161.925,
                               'height_mm': cy/36000, 'sha256': hashlib.sha256(parts[media]).hexdigest()})

    styles = etree.fromstring(parts['word/styles.xml'])
    for props in styles.xpath('//w:docDefaults/w:rPrDefault/w:rPr|//w:style/w:rPr', namespaces=NS):
        fonts = child(props, 'rFonts')
        if props.getparent().get(q('styleId')) != 'Equation':
            fonts.set(q('eastAsia'), '宋体')
            fonts.set(q('ascii'), 'Times New Roman')
            fonts.set(q('hAnsi'), 'Times New Roman')
    for spacing in styles.xpath('//w:spacing', namespaces=NS):
        spacing.set(q('line'), '240'); spacing.set(q('lineRule'), 'auto')
    parts['word/styles.xml'] = serialize(styles)
    for name in list(parts):
        if re.match(r'word/(footer|header)\d+\.xml$', name):
            item = etree.fromstring(parts[name])
            for p in item.xpath('//w:p', namespaces=NS):
                if text(p).startswith('收稿日期：'):
                    replace(p, '收稿日期：[编辑部填写]')
            for p in item.xpath('//w:p', namespaces=NS):
                paragraph_format(p)
                for run in p.xpath('./w:r', namespaces=NS):
                    font(run, '宋体', 9)
            parts[name] = serialize(item)

    assert table_text_before == [t.xpath('.//w:t/text()', namespaces=NS) for t in root.xpath('./w:body/w:tbl', namespaces=NS)]
    assert math_text_before == [e.xpath('.//m:t/text()', namespaces=NS) for e in root.xpath('//m:oMath', namespaces=NS)]
    assert 300 <= len(re.sub(r'\s', '', ABSTRACT)) <= 400
    assert len(CONCLUSION) <= 150
    assert not any(word in ABSTRACT for word in ['本文','我们','作者','笔者'])
    parts['word/document.xml'] = serialize(root)
    with ZipFile(TARGET, 'w') as output:
        for info in infos:
            output.writestr(info, parts[info.filename])
    record = dict(source=str(SOURCE), output=str(TARGET), text_changes=changes,
                  abstract_characters=len(re.sub(r'\s','',ABSTRACT)), conclusion_characters=len(CONCLUSION),
                  figures=figure_changes, native_equations=len(math_text_before),
                  math_style_changes=styled, upright_index_changes=index_styles,
                  moved_paragraphs=['图4详细说明移到图4前'],
                  math_expressions_unchanged=True, table_values_unchanged=True)
    (QA / 'change_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(TARGET)
    print('Abstract:', record['abstract_characters'], 'Conclusion:', record['conclusion_characters'])


if __name__ == '__main__':
    main()
