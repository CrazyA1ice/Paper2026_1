from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
TEMP = DOCX.with_suffix(".tmp.docx")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

KEYWORDS = "网络流量预测；多变量时间序列；多尺度学习；自适应加权；线性分解预测；频域分析"
CLASSIFICATION = "中图分类号：TP393　　文献标志码：A"
ENGLISH_TITLE = "A Multivariate Network Traffic Forecasting Method Based on Adaptive Multiscale Weighting"
ENGLISH_AUTHOR = "[Author Name]"
ENGLISH_AFFILIATION = "([Affiliation], [City] [Postcode], China; Corresponding author: [Name], E-mail: [E-mail])"


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


def clear_content(paragraph: etree._Element) -> None:
    for child in list(paragraph):
        if child.tag != w("pPr"):
            paragraph.remove(child)


def add_run(paragraph: etree._Element, text: str, r_pr: etree._Element | None = None, *, bold: bool = False) -> None:
    run = etree.SubElement(paragraph, w("r"))
    props = deepcopy(r_pr) if r_pr is not None else etree.Element(w("rPr"))
    if bold and props.find(w("b")) is None:
        etree.SubElement(props, w("b"))
    run.append(props)
    text_node = etree.SubElement(run, w("t"))
    text_node.text = text


def replace_plain(paragraph: etree._Element, text: str) -> None:
    first_r_pr = paragraph.find("w:r/w:rPr", namespaces=NS)
    clear_content(paragraph)
    add_run(paragraph, text, first_r_pr)


def center(paragraph: etree._Element) -> None:
    p_pr = paragraph.find(w("pPr"))
    if p_pr is None:
        p_pr = etree.Element(w("pPr"))
        paragraph.insert(0, p_pr)
    jc = p_pr.find(w("jc"))
    if jc is None:
        jc = etree.SubElement(p_pr, w("jc"))
    jc.set(w("val"), "center")


with ZipFile(DOCX, "r") as source_zip, ZipFile(TEMP, "w") as output_zip:
    for info in source_zip.infolist():
        payload = source_zip.read(info.filename)
        if info.filename == "word/document.xml":
            root = etree.fromstring(payload)
            paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
            if len(paragraphs) < 9:
                raise RuntimeError("未找到关键词、分类号或英文题录段落")

            keyword_runs = paragraphs[4].xpath("./w:r", namespaces=NS)
            keyword_label_r_pr = keyword_runs[0].find(w("rPr")) if keyword_runs else None
            keyword_body_r_pr = keyword_runs[1].find(w("rPr")) if len(keyword_runs) > 1 else None
            clear_content(paragraphs[4])
            add_run(paragraphs[4], "关键词：", keyword_label_r_pr, bold=True)
            add_run(paragraphs[4], KEYWORDS, keyword_body_r_pr)

            classification_runs = paragraphs[5].xpath("./w:r", namespaces=NS)
            classification_label_r_pr = classification_runs[0].find(w("rPr")) if classification_runs else None
            classification_body_r_pr = classification_runs[1].find(w("rPr")) if len(classification_runs) > 1 else None
            clear_content(paragraphs[5])
            add_run(paragraphs[5], "中图分类号：", classification_label_r_pr, bold=True)
            add_run(paragraphs[5], "TP393　　", classification_body_r_pr)
            add_run(paragraphs[5], "文献标志码：", classification_label_r_pr, bold=True)
            add_run(paragraphs[5], "A", classification_body_r_pr)
            replace_plain(paragraphs[6], ENGLISH_TITLE)
            replace_plain(paragraphs[7], ENGLISH_AUTHOR)
            replace_plain(paragraphs[8], ENGLISH_AFFILIATION)
            center(paragraphs[6])
            center(paragraphs[7])
            center(paragraphs[8])

            payload = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        output_zip.writestr(clone_info(info), payload)

TEMP.replace(DOCX)
print(DOCX)
