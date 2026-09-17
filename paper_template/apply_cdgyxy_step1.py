from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_SciPilot图表整合最新版.docx"
OUTPUT = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"

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


def set_single_spacing(root: etree._Element) -> None:
    for paragraph in root.xpath(".//w:p", namespaces=NS):
        p_pr = paragraph.find(w("pPr"))
        if p_pr is None:
            p_pr = etree.Element(w("pPr"))
            paragraph.insert(0, p_pr)
        spacing = p_pr.find(w("spacing"))
        if spacing is None:
            spacing = etree.SubElement(p_pr, w("spacing"))
        spacing.set(w("line"), "240")
        spacing.set(w("lineRule"), "auto")


def patch_document(payload: bytes) -> bytes:
    root = etree.fromstring(payload)
    set_single_spacing(root)
    for section in root.xpath(".//w:sectPr", namespaces=NS):
        margins = section.find(w("pgMar"))
        if margins is None:
            margins = etree.SubElement(section, w("pgMar"))
        margins.set(w("top"), "1757")     # 3.1 cm
        margins.set(w("bottom"), "1417")  # 2.5 cm
        margins.set(w("left"), "1134")    # 2.0 cm
        margins.set(w("right"), "1134")   # 2.0 cm
        columns = section.find(w("cols"))
        if columns is None:
            columns = etree.SubElement(section, w("cols"))
        columns.set(w("num"), "1")
        page_size = section.find(w("pgSz"))
        if page_size is not None:
            page_size.attrib.pop(w("orient"), None)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def patch_styles(payload: bytes) -> bytes:
    root = etree.fromstring(payload)
    doc_defaults = root.find(w("docDefaults"))
    if doc_defaults is None:
        doc_defaults = etree.Element(w("docDefaults"))
        root.insert(0, doc_defaults)
    r_pr_default = doc_defaults.find(w("rPrDefault"))
    if r_pr_default is None:
        r_pr_default = etree.SubElement(doc_defaults, w("rPrDefault"))
    r_pr = r_pr_default.find(w("rPr"))
    if r_pr is None:
        r_pr = etree.SubElement(r_pr_default, w("rPr"))
    r_fonts = r_pr.find(w("rFonts"))
    if r_fonts is None:
        r_fonts = etree.SubElement(r_pr, w("rFonts"))
    r_fonts.set(w("eastAsia"), "宋体")

    normal_styles = root.xpath(
        "./w:style[@w:type='paragraph' and (@w:default='1' or @w:styleId='Normal' "
        "or w:name/@w:val='Normal' or w:name/@w:val='正文')]",
        namespaces=NS,
    )
    if normal_styles:
        normal = normal_styles[0]
        normal_r_pr = normal.find(w("rPr"))
        if normal_r_pr is None:
            normal_r_pr = etree.SubElement(normal, w("rPr"))
        normal_fonts = normal_r_pr.find(w("rFonts"))
        if normal_fonts is None:
            normal_fonts = etree.SubElement(normal_r_pr, w("rFonts"))
        normal_fonts.set(w("eastAsia"), "宋体")
        normal_p_pr = normal.find(w("pPr"))
        if normal_p_pr is None:
            normal_p_pr = etree.SubElement(normal, w("pPr"))
        normal_spacing = normal_p_pr.find(w("spacing"))
        if normal_spacing is None:
            normal_spacing = etree.SubElement(normal_p_pr, w("spacing"))
        normal_spacing.set(w("line"), "240")
        normal_spacing.set(w("lineRule"), "auto")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def main() -> None:
    with ZipFile(SOURCE, "r") as source_zip, ZipFile(OUTPUT, "w") as output_zip:
        for info in source_zip.infolist():
            payload = source_zip.read(info.filename)
            if info.filename == "word/document.xml":
                payload = patch_document(payload)
            elif info.filename == "word/styles.xml":
                payload = patch_styles(payload)
            elif (
                info.filename.startswith("word/header")
                or info.filename.startswith("word/footer")
                or info.filename in {"word/footnotes.xml", "word/endnotes.xml"}
            ) and info.filename.endswith(".xml"):
                root = etree.fromstring(payload)
                set_single_spacing(root)
                payload = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            output_zip.writestr(clone_info(info), payload)
    print(OUTPUT)


if __name__ == "__main__":
    main()
