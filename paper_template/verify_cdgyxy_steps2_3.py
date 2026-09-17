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
    paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
    for paragraph, font, size in ((paragraphs[0], "黑体", "36"), (paragraphs[1], "楷体", "21")):
        assert paragraph.find("w:pPr/w:jc", namespaces=NS).get(w("val")) == "center"
        runs = paragraph.xpath("./w:r", namespaces=NS)
        assert runs
        assert all(run.find("w:rPr/w:rFonts", namespaces=NS).get(w("eastAsia")) == font for run in runs)
        assert all(run.find("w:rPr/w:sz", namespaces=NS).get(w("val")) == size for run in runs)
        assert all(run.find("w:rPr/w:szCs", namespaces=NS).get(w("val")) == size for run in runs)

    title_text = "".join(paragraphs[0].xpath(".//w:t/text()", namespaces=NS))
    author_text = "".join(paragraphs[1].xpath(".//w:t/text()", namespaces=NS))

print(f"题目：{title_text}；黑体18磅；居中")
print(f"作者行：{author_text}；楷体10.5磅；居中")
