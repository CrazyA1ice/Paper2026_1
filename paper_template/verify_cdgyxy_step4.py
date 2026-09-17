from pathlib import Path
from zipfile import ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


with ZipFile(DOCX) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))
    paragraph = root.xpath("./w:body/w:p", namespaces=NS)[2]
    assert paragraph.find("w:pPr/w:jc", namespaces=NS).get(w("val")) == "center"
    runs = paragraph.xpath("./w:r", namespaces=NS)
    assert runs
    assert all(run.find("w:rPr/w:rFonts", namespaces=NS).get(w("eastAsia")) == "楷体" for run in runs)
    assert all(run.find("w:rPr/w:sz", namespaces=NS).get(w("val")) == "18" for run in runs)
    assert all(run.find("w:rPr/w:szCs", namespaces=NS).get(w("val")) == "18" for run in runs)
    text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))

print(f"作者单位行：{text}；楷体9磅；居中")
