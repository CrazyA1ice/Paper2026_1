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
    "To improve scale adaptability in short-term backbone origin-destination traffic forecasting, "
    "a lightweight method based on sample-wise adaptive multiscale weighting was developed. "
    "Input windows of 96 time steps were transformed into three temporal views by non-overlapping average pooling at scales 1, 2, and 4. "
    "Independent DLinear experts decomposed each view into trend and residual components and predicted the next 24 time steps. "
    "A two-layer router used the window mean, standard deviation, mean at the latest time step, and mean absolute first difference "
    "to generate Softmax weights for fusing three 144-variable forecasts. "
    "Learnable low-frequency gates with different frequency-retention ratios were also evaluated. "
    "Forty-eight training runs were conducted on the public Abilene dataset from CESNET TS-Zoo. "
    "The ungated adaptive multiscale model achieved a mean squared error (MSE) of 0.186099 and a mean absolute error (MAE) of 0.168203, "
    "reducing the two errors by 4.06% and 10.52%, respectively, relative to single-scale DLinear. "
    "With identical scales and expert structures, adaptive weighting reduced MSE by 3.95% relative to fixed equal weighting. "
    "Increasing the retention ratio from 0.25 to 0.75 reduced errors in gated models, but none outperformed the ungated model. "
    "Sample-wise adaptive weighting is therefore the main source of improvement, whereas low-frequency gating serves as a data-dependent auxiliary mechanism."
)

KEYWORDS = (
    "network traffic forecasting; multivariate time series; multiscale learning; adaptive weighting; "
    "linear decomposition forecasting; frequency-domain analysis"
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


def clear_content(paragraph: etree._Element) -> None:
    for child in list(paragraph):
        if child.tag != w("pPr"):
            paragraph.remove(child)


def add_run(paragraph: etree._Element, text: str, *, bold: bool = False) -> None:
    run = etree.SubElement(paragraph, w("r"))
    r_pr = etree.SubElement(run, w("rPr"))
    fonts = etree.SubElement(r_pr, w("rFonts"))
    for attribute in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(w(attribute), "Times New Roman")
    color = etree.SubElement(r_pr, w("color"))
    color.set(w("val"), "000000")
    if bold:
        etree.SubElement(r_pr, w("b"))
        etree.SubElement(r_pr, w("bCs"))
    text_node = etree.SubElement(run, w("t"))
    if text.startswith(" ") or text.endswith(" "):
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_node.text = text


with ZipFile(DOCX, "r") as source_zip, ZipFile(TEMP, "w") as output_zip:
    for info in source_zip.infolist():
        payload = source_zip.read(info.filename)
        if info.filename == "word/document.xml":
            root = etree.fromstring(payload)
            paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
            if len(paragraphs) < 11:
                raise RuntimeError("未找到英文摘要或英文关键词段落")

            clear_content(paragraphs[9])
            add_run(paragraphs[9], "Abstract: ", bold=True)
            add_run(paragraphs[9], ABSTRACT)

            clear_content(paragraphs[10])
            add_run(paragraphs[10], "Key words: ", bold=True)
            add_run(paragraphs[10], KEYWORDS)

            payload = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        output_zip.writestr(clone_info(info), payload)

TEMP.replace(DOCX)
print(DOCX)
