from copy import deepcopy
from pathlib import Path
import re
import zipfile

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "2026.09.19v2.docx"
TARGET = ROOT / "word_output" / "2026.09.20v3.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def paragraph_text(paragraph):
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def set_paragraph_text(paragraph, new_text):
    runs = paragraph.xpath("./w:r", namespaces=NS)
    first_rpr = None
    if runs:
        rpr = runs[0].find(f"{{{W}}}rPr")
        if rpr is not None:
            first_rpr = deepcopy(rpr)

    for child in list(paragraph):
        if child.tag == f"{{{W}}}r":
            paragraph.remove(child)

    run = etree.Element(f"{{{W}}}r")
    if first_rpr is not None:
        run.append(first_rpr)
    text = etree.SubElement(run, f"{{{W}}}t")
    text.text = new_text
    paragraph.append(run)


def find_one(paragraphs, startswith):
    matches = [p for p in paragraphs if paragraph_text(p).startswith(startswith)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one paragraph starting with {startswith!r}, found {len(matches)}")
    return matches[0]


def main():
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {TARGET}")

    with zipfile.ZipFile(SOURCE, "r") as src:
        parts = {name: src.read(name) for name in src.namelist()}

    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(parts["word/document.xml"], parser)
    paragraphs = root.xpath("//w:body/w:p", namespaces=NS)

    training = find_one(paragraphs, "所有模型通过统一训练接口完成。")
    set_paragraph_text(
        training,
        "所有模型均通过统一训练接口完成，并采用Adam优化器和批量大小16。"
        "DLinear、固定等权多尺度和自适应多尺度模型的学习率为0.001，最多训练30轮，"
        "验证集MSE连续6轮未改善时提前停止；LightTS采用固定外部基线设置，学习率为0.0001，"
        "最多训练50轮，早停耐心为10。所有模型均以验证集MSE最低的参数进行测试。"
        "为避免不同重复次数造成统计口径混用，外部基线比较统一采用各模型共同完成的随机种子42—44；"
        "三个核心模型进一步采用42—49共8个随机种子进行机制稳定性分析。",
    )

    result_para = find_one(paragraphs, "两数据集的平均结果均表明，")
    old_result = paragraph_text(result_para)
    if "在统一训练设置下" not in old_result:
        raise RuntimeError("Expected training-setting phrase not found")
    set_paragraph_text(
        result_para,
        old_result.replace("在统一训练设置下", "在统一的数据划分、预处理和预测任务设置下"),
    )

    intro_network = find_one(paragraphs, "随着云计算")
    set_paragraph_text(intro_network, paragraph_text(intro_network).replace("[9]", "[6]"))

    intro_models = find_one(paragraphs, "网络流量在不同时间尺度上")
    updated_intro = paragraph_text(intro_models)
    for old, new in (("[7]", "[5]"), ("[10]", "[7]"), ("[11]", "[8]")):
        updated_intro = updated_intro.replace(old, new)
    set_paragraph_text(intro_models, updated_intro)

    ref_heading = find_one(paragraphs, "参考文献")
    body = ref_heading.getparent()
    ref_start = list(body).index(ref_heading)
    ref_paragraphs = [el for el in list(body)[ref_start + 1 :] if el.tag == f"{{{W}}}p"]

    remove_numbers = {5, 6, 8}
    renumber = {7: 5, 9: 6, 10: 7, 11: 8}
    for p in list(ref_paragraphs):
        txt = paragraph_text(p)
        match = re.match(r"^\[(\d+)\]", txt)
        if not match:
            continue
        number = int(match.group(1))
        if number in remove_numbers:
            body.remove(p)
        elif number in renumber:
            set_paragraph_text(p, re.sub(r"^\[\d+\]", f"[{renumber[number]}]", txt, count=1))

    parts["word/document.xml"] = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )
    with zipfile.ZipFile(TARGET, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in parts.items():
            out.writestr(name, data)

    # Package-level and manuscript-level guards.
    with zipfile.ZipFile(TARGET, "r") as check:
        check_root = etree.fromstring(check.read("word/document.xml"), parser)
        names = check.namelist()
    texts = [paragraph_text(p) for p in check_root.xpath("//w:body/w:p", namespaces=NS)]
    full_text = "\n".join(texts)
    ref_index = next(i for i, t in enumerate(texts) if t.strip() == "参考文献")
    body_text = "\n".join(texts[:ref_index])
    reference_text = "\n".join(texts[ref_index + 1 :])
    body_citations = {int(n) for n in re.findall(r"\[(\d+)\]", body_text)}
    reference_numbers = {int(n) for n in re.findall(r"(?m)^\[(\d+)\]", reference_text)}

    assert body_citations == reference_numbers == set(range(1, 9))
    assert "学习率为0.0001" in full_text and "最多训练50轮" in full_text and "早停耐心为10" in full_text
    assert "在统一训练设置下" not in full_text
    assert "在统一的数据划分、预处理和预测任务设置下" in full_text
    assert all(term not in body_text for term in ("频域门控", "FITS", "RFFT", "IRFFT", "cut ratio"))
    assert sum(name.startswith("word/media/") for name in names) == 6
    assert len(check_root.xpath("//w:tbl", namespaces=NS)) == 3

    print(TARGET)
    print(f"body citations={sorted(body_citations)}; references={sorted(reference_numbers)}")


if __name__ == "__main__":
    main()
