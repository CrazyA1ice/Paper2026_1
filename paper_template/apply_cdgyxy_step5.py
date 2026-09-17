from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
TEMP = DOCX.with_suffix(".tmp.docx")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

ABSTRACT = (
    "为提高骨干网源—目的节点对流量短期预测的尺度适应能力，提出一种基于样本级自适应多尺度加权的轻量预测方法。"
    "该方法将长度为96的输入窗口按尺度1、2和4进行非重叠平均池化，构造三种时间分辨率视图；分别采用独立DLinear专家分解趋势项与余项并预测未来24个时刻；"
    "再由窗口均值、标准差、末时刻均值和平均绝对一阶差分驱动两层路由器，生成Softmax权重并融合三路144维预测。"
    "同时设置可学习低频门控及不同频率保留比例，用于检验频域平滑的作用边界。"
    "在CESNET TS-Zoo公开Abilene数据集上完成48次正式训练。"
    "结果表明，无频域门控模型的均方误差（MSE）和平均绝对误差（MAE）分别为0.186099和0.168203，较单尺度DLinear分别降低4.06%和10.52%；"
    "在尺度及专家结构相同条件下，MSE较固定等权融合降低3.95%。"
    "频率保留比例由0.25增至0.75时，含门控模型误差逐步下降，但仍未优于无频域主模型。"
    "结果说明，样本级自适应尺度加权能够利用不同时间分辨率的互补信息，是性能提升的主要来源；"
    "低频门控适合作为依赖数据特征的辅助机制。"
)


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def clone_info(info: ZipInfo) -> ZipInfo:
    copied = ZipInfo(info.filename, info.date_time)
    copied.compress_type = ZIP_DEFLATED
    copied.comment = info.comment
    copied.extra = info.extra
    copied.create_system = info.create_system
    copied.external_attr = info.external_attr
    copied.internal_attr = info.internal_attr
    copied.flag_bits = info.flag_bits
    return copied


def make_run(text: str, *, bold: bool = False) -> etree._Element:
    run = etree.Element(w("r"))
    r_pr = etree.SubElement(run, w("rPr"))
    fonts = etree.SubElement(r_pr, w("rFonts"))
    fonts.set(w("eastAsia"), "宋体")
    fonts.set(w("ascii"), "Times New Roman")
    fonts.set(w("hAnsi"), "Times New Roman")
    fonts.set(w("cs"), "Times New Roman")
    color = etree.SubElement(r_pr, w("color"))
    color.set(w("val"), "000000")
    if bold:
        etree.SubElement(r_pr, w("b"))
        etree.SubElement(r_pr, w("bCs"))
    node = etree.SubElement(run, w("t"))
    node.text = text
    return run


with ZipFile(DOCX, "r") as source_zip, ZipFile(TEMP, "w") as output_zip:
    for info in source_zip.infolist():
        payload = source_zip.read(info.filename)
        if info.filename == "word/document.xml":
            root = etree.fromstring(payload)
            paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
            if len(paragraphs) < 4:
                raise RuntimeError("未找到中文摘要段落")
            paragraph = paragraphs[3]
            for child in list(paragraph):
                if child.tag != w("pPr"):
                    paragraph.remove(child)
            paragraph.append(make_run("摘要：", bold=True))
            paragraph.append(make_run(ABSTRACT))
            payload = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        output_zip.writestr(clone_info(info), payload)

TEMP.replace(DOCX)
print(DOCX)
