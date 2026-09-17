from pathlib import Path
from zipfile import ZipFile
import re

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def text_of(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


with ZipFile(DOCX) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))
    paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
    keywords_line = text_of(paragraphs[4])
    classification = text_of(paragraphs[5])
    english_title = text_of(paragraphs[6])
    english_author = text_of(paragraphs[7])
    english_affiliation = text_of(paragraphs[8])

    keywords = keywords_line.removeprefix("关键词：").split("；")
    assert 3 <= len(keywords) <= 8
    assert all(re.fullmatch(r"[\u3400-\u9fff]+", keyword) for keyword in keywords)
    assert classification == "中图分类号：TP393　　文献标志码：A"
    assert english_title == "A Multivariate Network Traffic Forecasting Method Based on Adaptive Multiscale Weighting"
    assert english_author == "[Author Name]"
    assert "China" in english_affiliation and "Corresponding author" in english_affiliation
    for index in (6, 7, 8):
        assert paragraphs[index].find("w:pPr/w:jc", namespaces=NS).get(w("val")) == "center"

print(f"关键词={len(keywords)}个：{'；'.join(keywords)}")
print(f"分类信息={classification}")
print(f"英文题名={english_title}")
print(f"英文作者={english_author}")
print(f"英文单位与通信作者行={english_affiliation}")
