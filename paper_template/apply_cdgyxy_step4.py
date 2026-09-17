from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
TEMP = DOCX.with_suffix(".tmp.docx")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


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


def get_or_add(parent: etree._Element, tag: str, *, first: bool = False) -> etree._Element:
    child = parent.find(w(tag))
    if child is None:
        child = etree.Element(w(tag))
        if first:
            parent.insert(0, child)
        else:
            parent.append(child)
    return child


with ZipFile(DOCX, "r") as source_zip, ZipFile(TEMP, "w") as output_zip:
    for info in source_zip.infolist():
        payload = source_zip.read(info.filename)
        if info.filename == "word/document.xml":
            root = etree.fromstring(payload)
            paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
            if len(paragraphs) < 3:
                raise RuntimeError("未找到作者单位段落")
            paragraph = paragraphs[2]
            p_pr = get_or_add(paragraph, "pPr", first=True)
            jc = get_or_add(p_pr, "jc")
            jc.set(w("val"), "center")
            for run in paragraph.xpath("./w:r", namespaces=NS):
                r_pr = get_or_add(run, "rPr", first=True)
                fonts = get_or_add(r_pr, "rFonts")
                fonts.set(w("eastAsia"), "楷体")
                fonts.set(w("ascii"), "Times New Roman")
                fonts.set(w("hAnsi"), "Times New Roman")
                fonts.set(w("cs"), "Times New Roman")
                size = get_or_add(r_pr, "sz")
                size.set(w("val"), "18")
                size_cs = get_or_add(r_pr, "szCs")
                size_cs.set(w("val"), "18")
                color = get_or_add(r_pr, "color")
                color.set(w("val"), "000000")
            payload = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        output_zip.writestr(clone_info(info), payload)

TEMP.replace(DOCX)
print(DOCX)
