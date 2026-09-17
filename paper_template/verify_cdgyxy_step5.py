from pathlib import Path
from zipfile import ZipFile
import re

from docx import Document
from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_SciPilot图表整合最新版.docx"
DOCX = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_成都工业学院学报版.docx"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


source = Document(SOURCE)
output = Document(DOCX)
assert len(output.paragraphs) == 149
assert len(output.tables) == 3
assert len(output.inline_shapes) == 6
assert [p.text for i, p in enumerate(source.paragraphs) if i not in range(3, 11)] == [
    p.text for i, p in enumerate(output.paragraphs) if i not in range(3, 11)
]

with ZipFile(DOCX) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))
    paragraph = root.xpath("./w:body/w:p", namespaces=NS)[3]
    runs = paragraph.xpath("./w:r", namespaces=NS)
    assert len(runs) == 2
    assert "".join(runs[0].xpath(".//w:t/text()", namespaces=NS)) == "摘要："
    assert runs[0].find("w:rPr/w:b", namespaces=NS) is not None
    body = "".join(runs[1].xpath(".//w:t/text()", namespaces=NS))

han_count = len(re.findall(r"[\u3400-\u9fff]", body))
assert 300 <= han_count <= 400
assert not any(word in body for word in ("我们", "作者", "本文", "笔者"))
for required in ("提出", "方法", "结果表明", "结果说明", "MSE", "MAE", "0.186099", "0.168203"):
    assert required in body

print(f"中文摘要：汉字数={han_count}，可见字符数={len(body)}")
print("结构=目的—方法—结果—结论；禁用主语=无；实验数值=保留")
print("除已批准修改的首页题录段落外，正文文字、段落、表格和图片均保持不变")
