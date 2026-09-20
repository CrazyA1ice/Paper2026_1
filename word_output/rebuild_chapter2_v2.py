from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "2026.09.19v2.docx"
FIG2 = ROOT / "abilene_forecasting" / "paper_figures" / "exports" / "color" / "fig2_core_weight_pairing_color.png"
FIG3 = ROOT / "abilene_forecasting" / "paper_figures" / "exports" / "color" / "fig3_router_weight_dynamics_color.png"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
W = "{%s}" % NS["w"]
R = "{%s}" % NS["r"]

def text(el):
    return "".join(e.text or "" for e in el.iter() if etree.QName(e).localname == "t")

def clone_info(info):
    copied = ZipInfo(info.filename, info.date_time)
    copied.compress_type = ZIP_DEFLATED
    copied.comment = info.comment
    copied.extra = info.extra
    copied.create_system = info.create_system
    copied.external_attr = info.external_attr
    copied.internal_attr = info.internal_attr
    copied.flag_bits = info.flag_bits
    return copied

def first_run_rpr(p):
    r = p.find("w:r", NS)
    if r is None:
        return None
    rpr = r.find("w:rPr", NS)
    return deepcopy(rpr) if rpr is not None else None

def set_para_text(p, value):
    ppr = p.find("w:pPr", NS)
    rpr = first_run_rpr(p)
    for child in list(p):
        if child is not ppr:
            p.remove(child)
    r = etree.SubElement(p, W + "r")
    if rpr is not None:
        r.append(rpr)
    t = etree.SubElement(r, W + "t")
    t.text = value
    return p

def make_para(template, value):
    p = deepcopy(template)
    return set_para_text(p, value)

def set_cell_text(tc, value, template_p):
    tcpr = tc.find("w:tcPr", NS)
    for child in list(tc):
        if child is not tcpr:
            tc.remove(child)
    p = make_para(template_p, value)
    tc.append(p)

def ensure_tbl_borders(tblpr):
    old = tblpr.find("w:tblBorders", NS)
    if old is not None:
        tblpr.remove(old)
    borders = etree.SubElement(tblpr, W + "tblBorders")
    for edge, val, size in [
        ("top", "single", "8"),
        ("left", "nil", "0"),
        ("bottom", "single", "8"),
        ("right", "nil", "0"),
        ("insideH", "nil", "0"),
        ("insideV", "nil", "0"),
    ]:
        e = etree.SubElement(borders, W + edge)
        e.set(W + "val", val)
        if val != "nil":
            e.set(W + "sz", size)
            e.set(W + "space", "0")
            e.set(W + "color", "000000")

def set_header_bottom(tc):
    tcpr = tc.find("w:tcPr", NS)
    if tcpr is None:
        tcpr = etree.Element(W + "tcPr")
        tc.insert(0, tcpr)
    old = tcpr.find("w:tcBorders", NS)
    if old is not None:
        tcpr.remove(old)
    borders = etree.SubElement(tcpr, W + "tcBorders")
    bottom = etree.SubElement(borders, W + "bottom")
    bottom.set(W + "val", "single")
    bottom.set(W + "sz", "8")
    bottom.set(W + "space", "0")
    bottom.set(W + "color", "000000")

def build_table(template, rows, widths):
    tbl = etree.Element(W + "tbl")
    tblpr = deepcopy(template.find("w:tblPr", NS))
    ensure_tbl_borders(tblpr)
    tbl.append(tblpr)

    grid = etree.SubElement(tbl, W + "tblGrid")
    for width in widths:
        gc = etree.SubElement(grid, W + "gridCol")
        gc.set(W + "w", str(width))

    old_rows = template.findall("w:tr", NS)
    header_row = old_rows[0]
    data_row = old_rows[1] if len(old_rows) > 1 else old_rows[0]
    header_cell = header_row.find("w:tc", NS)
    data_cell = data_row.find("w:tc", NS)
    header_p = header_cell.find("w:p", NS)
    data_p = data_cell.find("w:p", NS)

    for ri, values in enumerate(rows):
        row_template = header_row if ri == 0 else data_row
        tr = etree.Element(W + "tr")
        trpr = row_template.find("w:trPr", NS)
        if trpr is not None:
            tr.append(deepcopy(trpr))
        for ci, value in enumerate(values):
            base = header_cell if ri == 0 else data_cell
            tc = deepcopy(base)
            set_cell_text(tc, value, header_p if ri == 0 else data_p)
            tcpr = tc.find("w:tcPr", NS)
            tcw = tcpr.find("w:tcW", NS) if tcpr is not None else None
            if tcpr is None:
                tcpr = etree.Element(W + "tcPr")
                tc.insert(0, tcpr)
            if tcw is None:
                tcw = etree.SubElement(tcpr, W + "tcW")
            tcw.set(W + "w", str(widths[ci]))
            tcw.set(W + "type", "dxa")
            if ri == 0:
                set_header_bottom(tc)
            tr.append(tc)
        tbl.append(tr)
    return tbl

def drawing_before_caption(children, caption_text):
    ci = next(i for i, el in enumerate(children)
              if el.tag == W + "p" and text(el).strip() == caption_text)
    for i in range(ci - 1, max(-1, ci - 5), -1):
        el = children[i]
        if el.tag == W + "p" and el.xpath(".//a:blip", namespaces=NS):
            return deepcopy(el)
    raise RuntimeError("Drawing not found before " + caption_text)

def media_target(fig_p, rels):
    blips = fig_p.xpath(".//a:blip", namespaces=NS)
    if len(blips) != 1:
        raise RuntimeError("Expected exactly one image in figure paragraph")
    rid = blips[0].get(R + "embed")
    rel = next(e for e in rels if e.get("Id") == rid)
    return "word/" + rel.get("Target")

def main():
    with ZipFile(DOCX, "r") as zin:
        document = etree.fromstring(zin.read("word/document.xml"))
        rels = etree.fromstring(zin.read("word/_rels/document.xml.rels"))
        body = document.find("w:body", NS)
        children = list(body)

        ch2_idx = next(i for i, el in enumerate(children)
                       if el.tag == W + "p" and text(el).strip() == "2 实验与结果分析")
        concl_idx = next(i for i, el in enumerate(children)
                         if i > ch2_idx and el.tag == W + "p" and text(el).strip() == "3 结论")

        # Templates are cloned before the old Chapter 2 is removed.
        heading_t = next(el for el in children[ch2_idx+1:concl_idx]
                         if el.tag == W + "p" and text(el).strip() == "2.1 数据集与实验设置")
        body_t = next(el for el in children[ch2_idx+1:concl_idx]
                      if el.tag == W + "p" and text(el).strip().startswith("实验使用CESNET"))
        table_caption_t = next(el for el in children[ch2_idx+1:concl_idx]
                               if el.tag == W + "p" and text(el).strip() == "表1 基础模型消融结果")
        table_t = next(el for el in children[ch2_idx+1:concl_idx] if el.tag == W + "tbl")
        formula15 = next(deepcopy(el) for el in children[ch2_idx+1:concl_idx]
                         if el.tag == W + "p" and "(15)" in text(el))
        formula16 = next(deepcopy(el) for el in children[ch2_idx+1:concl_idx]
                         if el.tag == W + "p" and "(16)" in text(el))

        # Use the already journal-formatted Figure 1 caption as the caption template.
        fig_caption_t = next(el for el in children[:ch2_idx]
                             if el.tag == W + "p" and text(el).strip().startswith("图1 "))
        fig2_p = drawing_before_caption(children, "图2 基础模型消融结果")
        fig3_p = drawing_before_caption(children, "图3 自适应权重消融结果")
        fig2_target = media_target(fig2_p, rels)
        fig3_target = media_target(fig3_p, rels)

        # Remove old Chapter 2 content, retaining the Chapter 2 title and Chapter 3 onward.
        for el in children[ch2_idx+1:concl_idx]:
            body.remove(el)

        seq = []
        seq.append(make_para(heading_t, "2.1 数据集与实验设置"))
        seq.append(make_para(body_t,
            "实验选用CESNET TS-Zoo中的Abilene和GÉANT骨干网1 h聚合流量矩阵。"
            "Abilene从matrix_avg_realOD提取144维有效OD流量，共4656个时间点；"
            "GÉANT从matrix_avg_bandwidth_kbps读取529维矩阵，去除5个恒定通道后保留524维有效变量，共2849个时间点。"
            "两数据集均按时间顺序以6∶2∶2划分训练集、验证集和测试集，并分别在各集合内部构造滑动窗口，避免跨集合泄漏。"
            "输入长度L=96，预测长度H=24；预处理与第1.1节一致，先进行log(1+x)变换，再仅使用训练集统计量逐变量标准化。数据规模见表1。"
        ))
        seq.append(make_para(table_caption_t, "表1 数据集与预测任务设置"))
        seq.append(build_table(table_t, [
            ["数据集", "时间点", "有效变量C", "训练/验证/测试时间点", "训练/验证/测试窗口", "L/H"],
            ["Abilene", "4656", "144", "2793/931/932", "2674/812/813", "96/24"],
            ["GÉANT", "2849", "524", "1709/570/570", "1590/451/451", "96/24"],
        ], [1200, 1100, 1100, 2300, 2300, 1000]))
        seq.append(make_para(body_t,
            "所有模型通过统一训练接口完成。采用Adam优化器，学习率为0.001，批量大小为16，最多训练30轮；"
            "若验证集MSE连续6轮未改善则提前停止，并以验证集MSE最低的模型参数进行测试。"
            "为避免不同重复次数造成统计口径混用，外部基线比较统一采用各模型共同完成的随机种子42—44；"
            "DLinear、固定等权多尺度和自适应多尺度进一步采用42—49共8个随机种子进行核心机制稳定性分析。"
        ))

        seq.append(make_para(heading_t, "2.2 对比模型与评价指标"))
        seq.append(make_para(body_t,
            "对比模型包括单尺度DLinear、外部轻量基线LightTS、固定等权多尺度模型和本文自适应多尺度模型。"
            "其中，LightTS采用Time-Series-Library中固定版本的原始模型逻辑，并通过适配器接入与其他模型相同的数据划分、预处理和训练接口；"
            "固定等权多尺度与本文方法使用相同的尺度集合{1,2,4}和DLinear专家，仅将三个尺度权重固定为1/3，用于隔离样本级动态加权的贡献。"
        ))
        seq.append(make_para(body_t,
            "采用均方误差（mean squared error，MSE）、平均绝对误差（mean absolute error，MAE）和均方根误差（root mean squared error，RMSE）评价预测性能。"
            "MSE按式（14）计算；设测试集包含Nte个窗口，则MAE和RMSE分别为"
        ))
        seq.append(formula15)
        seq.append(formula16)
        seq.append(make_para(body_t,
            "上述指标均在标准化空间中计算，数值越小表示预测误差越低。由于RMSE是MSE的单调变换，正文表格主要报告MSE和MAE。"
            "外部基线比较以3个共同随机种子的均值±样本标准差表示；核心机制分析以8个随机种子的均值±样本标准差表示，"
            "并对相同随机种子下的模型结果进行双侧配对t检验和95%置信区间分析。测试窗口仅用于计算误差，不作为独立统计重复。"
        ))

        seq.append(make_para(heading_t, "2.3 两数据集外部基线比较"))
        seq.append(make_para(body_t,
            "为保证外部模型比较的重复次数一致，表2仅统计随机种子42、43和44。"
            "在Abilene上，本文方法的MSE和MAE分别为0.186±0.002和0.168±0.001，"
            "相较DLinear分别降低4.06%和10.52%，相较LightTS分别降低29.89%和17.65%。"
            "在GÉANT上，本文方法的MSE和MAE分别为0.434±0.051和0.370±0.031，"
            "相较DLinear分别降低4.43%和3.46%，相较LightTS分别降低46.83%和29.29%。"
        ))
        seq.append(make_para(table_caption_t, "表2 三随机种子外部基线比较"))
        seq.append(build_table(table_t, [
            ["数据集", "模型", "参数量", "MSE", "MAE"],
            ["Abilene", "DLinear", "4656", "0.194±0.002", "0.188±0.009"],
            ["Abilene", "LightTS", "130162", "0.265±0.011", "0.204±0.008"],
            ["Abilene", "本文方法", "8339", "0.186±0.002", "0.168±0.001"],
            ["GÉANT", "DLinear", "4656", "0.454±0.007", "0.383±0.006"],
            ["GÉANT", "LightTS", "384382", "0.817±0.024", "0.523±0.014"],
            ["GÉANT", "本文方法", "8339", "0.434±0.051", "0.370±0.031"],
        ], [1300, 2500, 1200, 2000, 2000]))
        seq.append(make_para(body_t,
            "两数据集的平均结果均表明，自适应多尺度融合能够在统一训练设置下降低预测误差。"
            "同时，本文方法仅含8339个可训练参数，明显少于当前适配下的LightTS；但参数量仅反映模型规模，不等同于训练或推理速度。"
            "此外，GÉANT上的标准差明显高于Abilene，因此外部基线结果用于说明当前统一实验协议下的相对表现，"
            "不据此推断本文方法在其他任务上普遍优于LightTS。"
        ))

        seq.append(make_para(heading_t, "2.4 八随机种子核心消融与稳定性"))
        seq.append(make_para(body_t,
            "表3进一步使用随机种子42—49比较DLinear、固定等权多尺度和自适应多尺度。"
            "在Abilene上，本文方法相较DLinear的MSE和MAE分别降低2.77%和8.23%，"
            "相较固定等权多尺度分别降低1.67%和9.04%；在GÉANT上，相应降幅分别为2.37%、1.35%以及4.68%、3.14%。"
            "固定等权模型含8208个参数，而本文方法含8339个参数，说明样本级路由仅增加131个参数。"
        ))
        seq.append(make_para(table_caption_t, "表3 八随机种子核心模型结果"))
        seq.append(build_table(table_t, [
            ["数据集", "模型", "参数量", "MSE", "MAE"],
            ["Abilene", "DLinear", "4656", "0.194±0.002", "0.189±0.008"],
            ["Abilene", "固定等权多尺度", "8208", "0.192±0.002", "0.191±0.006"],
            ["Abilene", "本文方法", "8339", "0.189±0.003", "0.173±0.008"],
            ["GÉANT", "DLinear", "4656", "0.437±0.016", "0.371±0.011"],
            ["GÉANT", "固定等权多尺度", "8208", "0.447±0.014", "0.377±0.009"],
            ["GÉANT", "本文方法", "8339", "0.426±0.029", "0.366±0.018"],
        ], [1300, 2500, 1200, 2000, 2000]))
        seq.append(make_para(body_t,
            "同种子配对结果见图2。Abilene中，自适应模型相对固定等权模型在8个种子中的6个取得更低MSE；"
            "GÉANT中为7个。Abilene上，自适应模型相对DLinear的MSE平均配对差为0.00537，"
            "95%置信区间为[0.00338,0.00736]，p<0.001；相对固定等权模型的MSE差异p=0.061，"
            "而MAE差异p=0.004。GÉANT上，自适应模型相对DLinear和固定等权模型的MSE配对检验p值分别为0.305和0.149。"
            "因此，两个数据集的平均误差方向均支持自适应加权，但不能表述为所有随机种子均提升；尤其GÉANT仍存在较明显的跨种子波动。"
        ))
        seq.append(fig2_p)
        seq.append(make_para(fig_caption_t, "图2 固定等权与自适应权重的八随机种子配对MSE"))

        seq.append(make_para(heading_t, "2.5 路由行为与适用范围"))
        seq.append(make_para(body_t,
            "为观察样本级路由器是否退化为固定平均融合，图3固定选取随机种子42，并展示两个数据集测试集前150个窗口的三尺度权重。"
            "该选择规则在两数据集间保持一致，仅用于机制可视化，不参与模型优劣的统计比较。"
        ))
        seq.append(fig3_p)
        seq.append(make_para(fig_caption_t, "图3 两数据集样本级路由权重变化（随机种子42）"))
        seq.append(make_para(body_t,
            "图3中三个尺度权重均随测试窗口发生变化，并未长期固定在1/3附近，说明路由器能够依据输入窗口统计状态动态调整尺度组合。"
            "以随机种子42为例，两数据集均表现出较明显的尺度偏好变化；但不同随机种子的平均权重并不完全一致，"
            "因此不能将某一尺度解释为所有网络场景下持续占优的固定尺度。"
        ))
        seq.append(make_para(body_t,
            "综合表2、表3和图2可见，样本级自适应尺度加权的平均收益已在Abilene和GÉANT两个骨干网数据集上得到验证，"
            "但GÉANT上的跨种子方差更大，稳定性仍有提升空间。当前实验仅考察L=96、H=24的单一预测设置，"
            "未显式建模网络拓扑，外部模型也仅包含LightTS一种轻量基线；同时，本文“轻量”主要指参数规模，而非训练时间最短。"
            "因此，后续仍需在更多网络、预测长度和拓扑约束条件下进一步检验泛化性。"
        ))

        # Insert new sequence immediately after Chapter 2 title.
        insert_at = list(body).index(next(el for el in body if el.tag == W+"p" and text(el).strip()=="2 实验与结果分析")) + 1
        for offset, el in enumerate(seq):
            body.insert(insert_at + offset, el)

        all_text = "\n".join(text(el) for el in body if el.tag == W+"p")
        ch2_text = all_text[all_text.index("2 实验与结果分析"):all_text.index("3 结论")]
        for forbidden in ["频率保留比例", "频域门控", "FITS", "r=0.50", "r=0.75", "48次正式训练"]:
            if forbidden in ch2_text:
                raise RuntimeError("Legacy Chapter 2 content remains: " + forbidden)
        for required in ["GÉANT", "LightTS", "随机种子42—49", "八随机种子核心模型结果",
                         "图2 固定等权与自适应权重的八随机种子配对MSE",
                         "图3 两数据集样本级路由权重变化"]:
            if required not in ch2_text:
                raise RuntimeError("Required Chapter 2 content missing: " + required)

        new_document = etree.tostring(document, xml_declaration=True, encoding="UTF-8", standalone=True)
        replacements = {
            "word/document.xml": new_document,
            fig2_target: FIG2.read_bytes(),
            fig3_target: FIG3.read_bytes(),
        }

        tmp = DOCX.with_suffix(".tmp.docx")
        with ZipFile(tmp, "w", ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                payload = replacements.get(info.filename, zin.read(info.filename))
                zout.writestr(clone_info(info), payload)
        tmp.replace(DOCX)

    print("Updated", DOCX)
    print("Figure 2 media:", fig2_target)
    print("Figure 3 media:", fig3_target)

if __name__ == "__main__":
    main()
