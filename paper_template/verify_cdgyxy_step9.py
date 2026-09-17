from pathlib import Path
from zipfile import ZipFile
import re

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def text_of(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


with ZipFile(DOCX) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))
    paragraphs = root.xpath("./w:body/w:p", namespaces=NS)
    abstract_line = text_of(paragraphs[9])
    keyword_line = text_of(paragraphs[10])
    assert abstract_line.startswith("Abstract: ")
    abstract = abstract_line.removeprefix("Abstract: ")
    word_count = len(re.findall(r"\b[\w.-]+\b", abstract))
    assert 150 <= word_count <= 300
    for phrase in (
        "was developed", "were transformed", "were also evaluated", "were conducted", "achieved",
        "mean squared error (MSE)", "mean absolute error (MAE)", "0.186099", "0.168203",
        "is therefore", "serves as",
    ):
        assert phrase in abstract
    assert "This paper" not in abstract

    assert keyword_line.startswith("Key words: ")
    keywords = keyword_line.removeprefix("Key words: ").split("; ")
    assert len(keywords) == 6
    assert all(keyword == keyword.lower() for keyword in keywords)

print(f"英文摘要词数={word_count}；时态结构=通过；核心数值=一致")
print(f"英文关键词={len(keywords)}个：{'; '.join(keywords)}")
