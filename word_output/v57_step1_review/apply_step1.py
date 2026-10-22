from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re

from lxml import etree

ROOT = Path(r"C:\Users\Quant\Desktop\Paper2026_1\word_output")
SOURCE = ROOT / "2026.10.03v56.docx"
TARGET = ROOT / "2026.10.03v57.docx"
QA = ROOT / "v57_step1_review"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}


def text(element):
    return "".join(element.xpath(".//w:t/text() | .//m:t/text()", namespaces=NS))


def digest(data):
    return hashlib.sha256(data).hexdigest()


assert not TARGET.exists(), "Do not overwrite an existing revision"
QA.mkdir(exist_ok=True)
with ZipFile(SOURCE) as archive:
    source_members = {info.filename: archive.read(info.filename) for info in archive.infolist()}
    source_infos = archive.infolist()
original = etree.fromstring(source_members["word/document.xml"])
root = deepcopy(original)
body = root.find("w:body", NS)
changes = []


def find(prefix):
    matches = [p for p in body.findall("w:p", NS) if text(p).startswith(prefix)]
    assert len(matches) == 1, (prefix, len(matches))
    return matches[0]


def replace(prefix, new_text):
    paragraph = find(prefix)
    old_text = text(paragraph)
    assert not paragraph.xpath(".//m:oMath | .//w:drawing | .//w:fldChar", namespaces=NS)
    first_run = paragraph.find("w:r", NS)
    rpr = first_run.find("w:rPr", NS) if first_run is not None else None
    for child in list(paragraph):
        if child.tag != f"{{{NS['w']}}}pPr":
            paragraph.remove(child)
    run = etree.SubElement(paragraph, f"{{{NS['w']}}}r")
    if rpr is not None:
        run.append(deepcopy(rpr))
    node = etree.SubElement(run, f"{{{NS['w']}}}t")
    node.text = new_text
    changes.append({"type": "replace", "before": old_text, "after": new_text})


def remove(prefix, destination):
    paragraph = find(prefix)
    assert not paragraph.xpath(".//m:oMath | .//w:drawing", namespaces=NS)
    changes.append({"type": "merge", "before": text(paragraph), "after": destination})
    body.remove(paragraph)


overview = text(find("图1给出模型的整体流程。"))
replace("图1给出模型的整体流程。", overview.split("固定等权、全局可学习权重与恒定输入路由对照")[0])
remove("模型由多尺度池化、独立专家预测和窗口路由融合组成。", "对照模型定义集中到第2.1节。")
replace("实验包括外部基线比较、核心消融和路由分析。", "实验从总体预测性能、融合方式消融、预测与权重行为以及运行开销四方面评价模型。")
remove("2.2 对比模型与评价指标", "与第2.1节合并；指标公式和统计口径全部保留。")

replace("DLinear提供单尺度参照，LightTS为独立轻量模型基线。", "对比设置包括单尺度DLinear、独立轻量基线LightTS、固定等权多尺度、全局可学习权重、恒定输入路由及本文方法。四种多尺度模型采用相同的DLinear主干和尺度集合{1,2,4}，比较不同融合方式。")
replace("固定等权模型将各尺度权重设为1/3；", "固定等权模型将各尺度权重设为1/3；全局权重模型用3个由等权初始化的可训练参数，经Softmax生成全局固定权重；恒定输入路由保留本文方法的路由网络，训练与推理均输入全零特征向量，使所有窗口共用融合权重。三类对照的专家均接收真实历史窗口，用于区分多尺度信息、非等权融合与输入相关分配的作用。")

# Group the definitions immediately after the dataset table, before training settings.
settings = find("所有模型使用相同的数据划分、输入和预测长度、")
for prefix in ("对比设置包括单尺度DLinear、", "固定等权模型将各尺度权重设为1/3；"):
    paragraph = find(prefix)
    body.remove(paragraph)
    settings.addprevious(paragraph)

replace("所有模型使用相同的数据划分、输入和预测长度、", "所有模型使用相同的数据划分、输入和预测长度、评价指标及批量大小16，未分别搜索最优超参数。DLinear及各多尺度模型最多训练30轮，LightTS为50轮；可训练融合参数与尺度专家共同优化，各模型均按验证集MSE选择参数，测试集仅用于最终统计。")
replace("外部基线比较使用随机种子42～44共3个共同随机种子。", "外部基线比较使用随机种子42～44共3个共同随机种子；核心消融使用42～49共8个共同随机种子，比较DLinear、三类固定融合对照及本文方法，并以随机种子作为配对统计单位。")

for old, new in (
    ("2.3 总体预测性能与基线比较", "2.2 总体预测性能与基线比较"),
    ("2.4 八随机种子核心消融与稳定性", "2.3 八随机种子核心消融与稳定性"),
    ("2.5 预测行为与尺度权重分析", "2.4 预测行为与尺度权重分析"),
    ("2.6 运行开销与网络管理应用讨论", "2.5 运行开销与网络管理应用讨论"),
):
    replace(old, new)

replace("表2列出3个共同随机种子下的总体基线结果。", "表2列出3个共同随机种子下的总体基线结果。本文方法在Abilene上的MSE为0.186，在GÉANT上为0.434；逐种子计算后相对DLinear分别降低4.07%和4.54%，相对LightTS分别降低29.80%和46.89%，MAE呈相同方向变化。图2进一步展示本文方法与LightTS的逐种子、多指标结果及参数规模。")
replace("图2以LightTS为独立外部基线，", text(find("图2以LightTS为独立外部基线，")).replace("图2以LightTS为独立外部基线，使用两种方法共有的随机种子42～44。", "图2使用本文方法与LightTS共有的随机种子42～44。"))
replace("全局可学习权重与恒定输入路由均对所有窗口使用", text(find("全局可学习权重与恒定输入路由均对所有窗口使用")).split("相对这两种对照，", 1)[1].join(["相对全局可学习权重和恒定输入路由，", ""]))
replace("等权融合采用固定等权模型检验。", "表3的两类常权重对照中，本文方法在八次重复实验中的平均MSE较低；GÉANT种子43相对恒定输入路由退步12.78%。图4进一步汇总全测试点的预测偏差，并展示按真实序列波动选取的典型轨迹。")

timing = text(find("使用预测长度为24的8个随机种子检查点"))
replace("使用预测长度为24的8个随机种子检查点", timing.replace("计时运行于NVIDIA GTX 1060，预先加载测试张量，并将批量大小设为16。", "计时前预先加载测试张量，并将批量大小设为16。"))

document = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
with ZipFile(TARGET, "w") as output:
    for info in source_infos:
        output.writestr(info, document if info.filename == "word/document.xml" else source_members[info.filename])

# Verify immutable evidence and every unaffected OOXML part.
with ZipFile(TARGET) as output:
    for name, data in source_members.items():
        if name != "word/document.xml":
            assert output.read(name) == data, name
    final = etree.fromstring(output.read("word/document.xml"))
for query, label in (("//w:tbl", "tables"), ("//m:oMath", "equations"), ("//w:drawing", "figures")):
    before = [etree.tostring(x, method="c14n") for x in original.xpath(query, namespaces=NS)]
    after = [etree.tostring(x, method="c14n") for x in final.xpath(query, namespaces=NS)]
    assert before == after, label
refs_before = [text(p) for p in original.xpath("//w:body/w:p", namespaces=NS) if re.match(r"\[\d+\]", text(p))]
refs_after = [text(p) for p in final.xpath("//w:body/w:p", namespaces=NS) if re.match(r"\[\d+\]", text(p))]
assert refs_before == refs_after
all_text = text(final)
assert not re.search(r"NVIDIA|GTX|CPU|GPU|显卡|内存|处理器型号", all_text, re.I)
assert [text(p) for p in final.xpath("//w:body/w:p", namespaces=NS) if re.match(r"2\.\d+ ", text(p))] == [
    "2.1 数据集与实验设置", "2.2 总体预测性能与基线比较", "2.3 八随机种子核心消融与稳定性",
    "2.4 预测行为与尺度权重分析", "2.5 运行开销与网络管理应用讨论"]

audit = {"source": str(SOURCE), "target": str(TARGET), "source_sha256": digest(SOURCE.read_bytes()),
         "changes": changes, "preserved": {"figures": 5, "tables": 3, "math_objects": 41, "references": len(refs_after)},
         "hardware_configuration_removed": True}
(QA / "changes.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

lines = ["# v57第一步修改对比", "", "本步：集中实验设置和对照定义，精简重复说明；按作者要求移除硬件型号。", "",
         "图表、公式、实验数值及参考文献保持不变。原v56保留。", ""]
for i, change in enumerate(changes, 1):
    lines.extend([f"## 修改{i}", "", "**修改前：**", "", change["before"], "", "**修改后：**", "", change["after"], ""])
(ROOT / "2026.10.03v57_第一步修改对比.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"target": str(TARGET), "changes": len(changes), "preserved": audit["preserved"]}, ensure_ascii=False))
