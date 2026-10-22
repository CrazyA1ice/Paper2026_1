from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import sys

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Quant\Desktop\Paper2026_1\word_output")
SOURCE = ROOT / "2026.10.03v57.docx"
TARGET = ROOT / "2026.10.03v58.docx"
QA = ROOT / "v58_step2_review"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}


def text(element):
    return "".join(element.xpath(".//w:t/text() | .//m:t/text()", namespaces=NS))


if TARGET.exists():
    previous_audit = json.loads((QA / "changes.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest() == previous_audit["target_sha256"], "Revision changed externally"
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
QA.mkdir(exist_ok=True)
with ZipFile(SOURCE) as archive:
    members = {info.filename: archive.read(info.filename) for info in archive.infolist()}
    infos = archive.infolist()
original = etree.fromstring(members["word/document.xml"])
root = deepcopy(original)
body = root.find("w:body", NS)
changes = []


def replace(prefix, new_text, section, reason):
    matches = [p for p in body.findall("w:p", NS) if text(p).startswith(prefix)]
    assert len(matches) == 1, (prefix, len(matches))
    paragraph = matches[0]
    assert not paragraph.xpath(".//m:oMath | .//w:drawing | .//w:fldChar", namespaces=NS)
    before = text(paragraph)
    first_run = paragraph.find("w:r", NS)
    rpr = first_run.find("w:rPr", NS) if first_run is not None else None
    label = prefix if prefix in ("摘要：", "Abstract:") else None
    content_rpr = paragraph.findall("w:r", NS)[1].find("w:rPr", NS) if label else rpr
    for child in list(paragraph):
        if child.tag != f"{{{NS['w']}}}pPr":
            paragraph.remove(child)
    for value, properties in ([(label, rpr), (new_text[len(label):], content_rpr)] if label else [(new_text, rpr)]):
        run = etree.SubElement(paragraph, f"{{{NS['w']}}}r")
        if properties is not None:
            run.append(deepcopy(properties))
        node = etree.SubElement(run, f"{{{NS['w']}}}t")
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        node.text = value
    changes.append({"section": section, "before": before, "after": new_text, "reason": reason})


replace("摘要：", "摘要：为提高小时级骨干网络流量的多步预测精度，构建了轻量自适应多尺度预测模型。模型将历史窗口转换为三种时间分辨率的序列，分别由独立分解线性专家生成候选预测，兼顾局部变化与较慢趋势。路由网络提取窗口的总体水平、离散程度、末时状态和平均变化强度，经两层感知器生成融合权重。在输入96步、预测24步的Abilene和GÉANT实验中，3个共同随机种子的均方误差相对单尺度分解线性模型分别降低4.07%和4.54%，相对采样导向轻量模型LightTS分别降低29.80%和46.89%。8种子消融中，相对全局可学习权重和恒定输入路由的逐种子平均改进率在Abilene上均约1.80%，在GÉANT上分别为4.31%和4.97%。结果表明，多尺度预测与低维路由结合取得了较低的平均误差，仅增加少量融合参数，可为未来一天的网络需求分析与容量规划提供参考。", "中文摘要", "明确单尺度分解线性模型与LightTS两个比较对象；用数据集名称替代“前一/后一”，保留全部结果百分比及3/8种子口径。")

replace("Abstract:", "Abstract: A lightweight adaptive multiscale model was developed to improve multistep forecasting of hourly backbone traffic. Historical windows were represented at three temporal resolutions, and independent decomposition linear (DLinear) predictors generated candidate forecasts. A two-layer perceptron used four window statistics to calculate fusion weights: overall level, dispersion, final-time state and mean absolute change. Experiments on Abilene and GÉANT used an input length of 96 and a forecast length of 24. Across three common random seeds, mean squared error decreased by 4.07% and 4.54% relative to single-scale DLinear, respectively. The corresponding reductions relative to the sampling-oriented lightweight model LightTS were 29.80% and 46.89%. Eight-seed ablations compared the model with learned global weights and a constant-input router. Mean seed-wise improvements over both controls were approximately 1.80% on Abilene. On GÉANT, the improvements over learned global weights and the constant-input router were 4.31% and 4.97%, respectively. Combining multiscale forecasting with low-dimensional routing achieves lower mean errors with few additional fusion parameters. The forecasts provide a reference for next-day network demand analysis and capacity planning.", "英文摘要", "与中文摘要逐项对应，明确DLinear与LightTS；工作和结果用过去时，结论用现在时。")

replace("源—目的节点对（", "源—目的节点对（origin-destination，OD）流量描述骨干网节点对之间的通信需求。容量规划需要了解各节点对未来的需求变化。本文面向小时级OD流量，预测未来一天的需求，为高需求时段观察和容量安排提供参考。云计算、视频业务和数据中心互联增加了业务迁移与聚集，使流量变化更复杂。周期变化、局部波动与突发变化叠加，各OD变量量级不同，预测模型需同时刻画较慢趋势与短时变化。", "引言第1段", "将研究任务与容量规划的需求连接，集中说明小时级OD预测的用途。")

replace("原始时间分辨率保留局部细节，", "原始时间分辨率保留局部细节，时间聚合平滑短时扰动并突出较慢趋势。Zhou等[5]采用深度回声状态网络提取多分辨率信息，利用各尺度互补性。分解线性模型（decomposition linear model，DLinear）[6]通过序列分解和线性映射预测，TimeMixer[7]采用多尺度混合，LightTS[8]以采样导向的多层感知器（multilayer perceptron，MLP）实现快速预测。这些方法为多分辨率建模和轻量预测提供了基础，本文在分解线性预测的主干上研究尺度间的融合方式。", "引言第3段", "保留全部文献和原有方法描述，将文献介绍过渡到本文关注的尺度融合。")

replace("常见流程先给定尺度，", "对于同一历史窗口，不同时间分辨率保留的信息并不相同。将各尺度预测按固定比例融合，可以利用多尺度信息，但融合比例不会随输入状态变化。因此，本文研究在保持尺度专家结构一致的条件下，依据窗口状态生成融合权重是否能够进一步降低整体预测误差。", "引言第4段", "把对“常见流程”的笼统判断改为明确的融合设计问题，不将既有多尺度方法一概描述为固定权重。")

replace("本文采用样本级自适应多尺度结构：", "本文以独立DLinear专家处理尺度1、2和4的序列，用低维窗口统计量驱动路由网络，生成归一化融合权重。尺度专家负责各分辨率的候选预测，路由网络负责尺度间融合，在保留多尺度信息的同时控制参数规模。在Abilene和GÉANT上，通过外部基线比较、固定融合对照及多随机种子实验评价整体预测精度，并结合预测轨迹和权重分布分析模型行为。", "引言第5段", "说明专家与路由的分工及验证路径，减少与摘要、方法和实验设置重复的细节清单。")

replace("运维模块可定期读取小时级历史OD序列，", "在小时级网络管理场景中，运维模块可随观测序列更新，读取最近96 h的各OD流量，按训练阶段的预处理规则构造历史窗口，输出未来24 h各OD的逐小时需求估计。一次预测同时覆盖全部有效OD变量，便于按时间和节点对组织后续需求分析。", "第2.5节应用说明第1段", "明确应用输入、更新方式和输出组织；96 h与24 h均来自原任务设置。")

replace("图4中各模型在高真实值区间均有低估，", "预测输出处于标准化空间。用于实际需求分析时，应先利用训练阶段保存的逐OD统计量逆标准化，再作逆对数变换，恢复原始流量量纲。随后可结合网络拓扑和路由关系，将各OD的预测需求汇总到对应链路，并与链路容量比较，为容量安排提供参考。", "第2.5节应用说明第2段", "将原第3段的量纲恢复与链路负载接口移至输入输出说明之后，补清正确的逆变换顺序。")

replace("实验评估标准化OD流量。", "图4中各模型在高真实值区间均有低估，本文方法的分组平均偏差相对较小。这一结果说明模型对高需求水平的估计有所改善，可为需求上升时段的观察和容量复核提供预测参考。", "第2.5节应用说明第3段", "保留图4的高值区间结果及低估现象，将其与需求观察联系；不新增已部署或节省容量的结论。")

document = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
with ZipFile(TARGET, "w") as output:
    for info in infos:
        output.writestr(info, document if info.filename == "word/document.xml" else members[info.filename])

with ZipFile(TARGET) as output:
    for name, data in members.items():
        if name != "word/document.xml":
            assert output.read(name) == data, name
    final = etree.fromstring(output.read("word/document.xml"))

preserved = {}
for query, label in (("//w:tbl", "tables"), ("//m:oMath", "math_objects"), ("//w:drawing", "figures")):
    before = [etree.tostring(x, method="c14n") for x in original.xpath(query, namespaces=NS)]
    after = [etree.tostring(x, method="c14n") for x in final.xpath(query, namespaces=NS)]
    assert before == after, label
    preserved[label] = len(before)

old_paragraphs = original.xpath("//w:body/w:p", namespaces=NS)
new_paragraphs = final.xpath("//w:body/w:p", namespaces=NS)
assert len(old_paragraphs) == len(new_paragraphs)
allowed = {item["before"] for item in changes}
for before, after in zip(old_paragraphs, new_paragraphs):
    if text(before) not in allowed:
        assert etree.tostring(before, method="c14n") == etree.tostring(after, method="c14n"), text(before)
    else:
        assert etree.tostring(before.find("w:pPr", NS)) == etree.tostring(after.find("w:pPr", NS))
refs_before = [text(p) for p in old_paragraphs if re.match(r"\[\d+\]", text(p))]
refs_after = [text(p) for p in new_paragraphs if re.match(r"\[\d+\]", text(p))]
assert refs_before == refs_after
preserved["references"] = len(refs_after)
for item in changes[:2]:
    assert re.findall(r"\d+(?:\.\d+)?%", item["before"]) == re.findall(r"\d+(?:\.\d+)?%", item["after"])
intro_before = "".join(text(p) for p in old_paragraphs[12:18])
intro_after = "".join(text(p) for p in new_paragraphs[12:18])
assert re.findall(r"\[\d+\]", intro_before) == re.findall(r"\[\d+\]", intro_after)
cn = changes[0]["after"].removeprefix("摘要：")
abstract_characters = len(re.sub(r"\s", "", cn))
assert 300 <= abstract_characters <= 400, abstract_characters
assert not any(term in cn for term in ("本文", "我们", "笔者", "作者"))
assert not re.search(r"NVIDIA|GTX|CPU|GPU|显卡|内存|处理器型号", text(final), re.I)
assert source_hash == hashlib.sha256(SOURCE.read_bytes()).hexdigest()

audit = {"source": str(SOURCE), "target": str(TARGET), "source_sha256": source_hash,
         "target_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(), "changes": changes,
         "preserved": preserved, "abstract_nonspace_characters_without_label": abstract_characters,
         "all_other_paragraphs_identical": True, "all_other_zip_members_identical": True,
         "hardware_configuration_absent": True}
(QA / "changes.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

lines = ["# v58第二步修改对比报告", "", "## 修改范围与结果", "",
         "在v57基础上修改中英文摘要、引言4段及第2.5节应用说明3段，共9处。保留原v57。",
         "本步完成“摘要明确指代、引言明确问题、应用说明明确输入输出和使用接口”。应用内容为可采用的流程说明，未将其写成已经实施的部署实验。", "",
         "## 保留项核对", "",
         "| 检查项 | 结果 |", "|---|---|",
         "| 图片和嵌入资源 | 5幅图及全部媒体、关系文件保持原样 |",
         "| 原生表格 | 3张表的OOXML逐项相同 |",
         "| 公式 | 41个原生数学对象逐项相同，编号及符号不变 |",
         "| 实验结果 | 结果段、表格、图片和计时段未改；中英文摘要的结果百分比及顺序相同 |",
         "| 参考文献 | 11条著录及引言引用顺序不变 |",
         "| 硬件配置 | 未出现CPU/GPU、显卡、内存或硬件型号 |",
         f"| 中文摘要 | 不含摘要标签，共{abstract_characters}个非空字符；第三人称，目的、方法、结果、结论齐全 |",
         "| 修改范围 | 其余正文段落及段落格式逐项相同；标题、关键词、结语不变 |", "",
         "## 术语对应", "",
         "| 本步使用名称 | 对应与处理 |", "|---|---|",
         "| 单尺度分解线性模型 | 对应DLinear；中文摘要使用中文名称，正文保留首次全称定义，英文摘要明确DLinear |",
         "| 采样导向轻量模型LightTS | 对应原有LightTS基线；未替换或新增模型 |",
         "| 全局可学习权重、恒定输入路由 | 两类固定融合对照；保留原名及比较次序 |",
         "| 样本级路由 | 指融合权重由窗口统计量计算；不扩写为已经准确识别各窗口的尺度需求 |",
         "| OD需求、链路负载 | 前者是模型预测对象；后者需结合拓扑与路由作进一步分析 |", "",
         "## 逐处修改前后", ""]
for i, change in enumerate(changes, 1):
    lines.extend([f"### {i}. {change['section']}", "", "**修改前：**", "", change["before"], "",
                  "**修改后：**", "", change["after"], "", "**修改原因：** " + change["reason"], ""])
lines.extend(["## 本步后的下一项", "", "第三步处理图题、图注和图3/图4的分页关系。本步未改动图像、图片尺寸及段落分页属性，仍需在下一步集中调整。", ""])
(ROOT / "2026.10.03v58_第二步修改对比.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"target": str(TARGET), "changes": len(changes), "preserved": preserved,
                  "abstract_characters": abstract_characters}, ensure_ascii=False))
