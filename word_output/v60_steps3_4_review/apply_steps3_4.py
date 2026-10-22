from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import argparse
import csv
import hashlib
import json
import re
import statistics
import sys

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Quant\Desktop\Paper2026_1")
OUTPUT = ROOT / "word_output"
QA = OUTPUT / "v60_steps3_4_review"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}


def text(element):
    return "".join(element.xpath(".//w:t/text() | .//m:t/text()", namespaces=NS))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find(body, prefix):
    found = [p for p in body.findall("w:p", NS) if text(p).startswith(prefix)]
    assert len(found) == 1, (prefix, len(found))
    return found[0]


def set_property(paragraph, name, **attributes):
    ppr = paragraph.find("w:pPr", NS)
    if ppr is None:
        ppr = etree.Element(f"{{{NS['w']}}}pPr")
        paragraph.insert(0, ppr)
    prop = ppr.find(f"w:{name}", NS)
    if prop is None:
        prop = etree.SubElement(ppr, f"{{{NS['w']}}}{name}")
    for key, value in attributes.items():
        prop.set(f"{{{NS['w']}}}{key}", str(value))


def replace(paragraph, value, changes, reason):
    assert not paragraph.xpath(".//m:oMath | .//w:drawing | .//w:fldChar", namespaces=NS)
    before = text(paragraph)
    run = paragraph.find("w:r", NS)
    properties = deepcopy(run.find("w:rPr", NS)) if run is not None else None
    for child in list(paragraph):
        if child.tag != f"{{{NS['w']}}}pPr":
            paragraph.remove(child)
    run = etree.SubElement(paragraph, f"{{{NS['w']}}}r")
    if properties is not None:
        run.append(properties)
    node = etree.SubElement(run, f"{{{NS['w']}}}t")
    node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    node.text = value
    changes.append({"before": before, "after": value, "reason": reason})


def paragraph(template, value, is_note=False):
    p = deepcopy(template)
    unused = []
    replace(p, value, unused, "新增说明")
    set_property(p, "keepNext", val=0)
    set_property(p, "keepLines", val=1)
    if is_note:
        set_property(p, "spacing", before=0, after=60, line=240, lineRule="auto")
        set_property(p, "ind", firstLine=0, firstLineChars=0)
        set_property(p, "jc", val="left")
        rpr = p.find("w:r/w:rPr", NS)
        if rpr is None:
            rpr = etree.Element(f"{{{NS['w']}}}rPr")
            p.find("w:r", NS).insert(0, rpr)
        for name, val in (("sz", "15"), ("szCs", "15"), ("b", "0")):
            prop = rpr.find(f"w:{name}", NS)
            if prop is None:
                prop = etree.SubElement(rpr, f"{{{NS['w']}}}{name}")
            prop.set(f"{{{NS['w']}}}val", val)
        fonts = rpr.find("w:rFonts", NS)
        if fonts is None:
            fonts = etree.SubElement(rpr, f"{{{NS['w']}}}rFonts")
        for key, value in (("eastAsia", "宋体"), ("ascii", "Times New Roman"), ("hAnsi", "Times New Roman")):
            fonts.set(f"{{{NS['w']}}}{key}", value)
    return p


def read_source(source, target, step):
    QA.mkdir(exist_ok=True)
    if target.exists():
        previous = json.loads((QA / f"step{step}_changes.json").read_text(encoding="utf-8"))
        assert sha(target) == previous["target_sha256"], "Target modified outside this script"
    with ZipFile(source) as z:
        members = {i.filename: z.read(i.filename) for i in z.infolist()}
        infos = z.infolist()
    original = etree.fromstring(members["word/document.xml"])
    return original, deepcopy(original), members, infos, sha(source)


def save_verify(source, target, step, original, root, members, infos, source_hash, changes):
    document = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    with ZipFile(target, "w") as z:
        for info in infos:
            z.writestr(info, document if info.filename == "word/document.xml" else members[info.filename])
    with ZipFile(target) as z:
        for key, value in members.items():
            if key != "word/document.xml":
                assert z.read(key) == value, key
    protected = {}
    for query, label in (("//w:tbl", "tables"), ("//m:oMath", "math_objects"), ("//w:drawing", "figures")):
        before = [etree.tostring(x, method="c14n") for x in original.xpath(query, namespaces=NS)]
        after = [etree.tostring(x, method="c14n") for x in root.xpath(query, namespaces=NS)]
        assert before == after, label
        protected[label] = len(before)
    refs = lambda r: [text(p) for p in r.xpath("//w:body/w:p", namespaces=NS) if re.match(r"\[\d+\]", text(p))]
    assert refs(original) == refs(root)
    protected["references"] = len(refs(root))
    # Figure notes only relocate statistical descriptions; every percentage stays the same.
    if step == 3:
        assert Counter(re.findall(r"[−-]?\d+(?:\.\d+)?%", text(original))) == Counter(re.findall(r"[−-]?\d+(?:\.\d+)?%", text(root)))
    assert not re.search(r"NVIDIA|GTX|CPU|GPU|显卡|内存|处理器型号|GeForce|Intel Core", text(root), re.I)
    assert sha(source) == source_hash
    audit = {"source": str(source), "target": str(target), "source_sha256": source_hash,
             "target_sha256": sha(target), "changes": changes, "preserved": protected,
             "all_other_zip_members_identical": True, "figure_geometry_identical": True,
             "hardware_configuration_absent": True}
    (QA / f"step{step}_changes.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"step": step, "target": str(target), "changes": len(changes), "preserved": protected}, ensure_ascii=False))


def step3():
    source, target = OUTPUT / "2026.10.03v58.docx", OUTPUT / "2026.10.03v59.docx"
    original, root, members, infos, source_hash = read_source(source, target, 3)
    body = root.find("w:body", NS)
    changes = []
    template = find(body, "原始尺度保留局部变化，")
    captions = [find(body, f"图{i} ") for i in range(1, 6)]
    titles = ["图1 自适应多尺度预测框架", "图2 相对LightTS的误差降低率与参数规模",
              "图3 相对两类基线的多指标改进分布", "图4 分组预测校准与典型窗口轨迹", "图5 尺度权重分布与种子均值"]
    notes = [
        "注：曲边连接表示DLinear专家内部的展开；实线为预测计算流程，虚线为窗口特征及融合权重的传递。图中省略样本下标n，矩阵、曲线及色块仅作计算过程示意。",
        "注：使用共同随机种子42～44。误差降低率按（LightTS误差−本文方法误差）/LightTS误差计算；参数比例以各数据集的LightTS参数量为参照。",
        "注：使用共同随机种子42～49，n=8。散点为单个种子的改进率，半小提琴汇总其分布；黑色菱形为均值，横向误差线为95%置信区间，0%虚线表示误差相同。",
        "注：（a、b）汇总种子42～49的全部测试窗口、24个预测步及有效OD通道；真实值按分位点分为最多40组，曲线为分组平均预测，浅色带为种子间±1个标准差，灰色虚线为理想线。（c～f）使用种子42，选取真实序列标准差接近第75百分位的OD通道及波动程度接近中位数、第90百分位的窗口；选例仅依据真实序列。",
        "注：使用种子42～49，n=8。蓝、绿、橙分别对应尺度1、2、4；小提琴汇总全部种子与测试窗口，彩色点为各种子的窗口平均权重，黑色菱形及误差线为8个种子均值的均值±1个标准差。水平虚线为固定等权1/3，短横线为汇总分布中位数；小提琴宽度包含种子间与窗口间差异。",
    ]
    note_nodes = []
    for cap, title, note in zip(captions, titles, notes):
        replace(cap, title, changes, "缩短图题，读图口径移至图下注。")
        set_property(cap, "keepNext", val=1)
        set_property(cap, "spacing", before=40, after=40, line=240, lineRule="auto")
        note_node = paragraph(template, note, True)
        cap.addnext(note_node)
        note_nodes.append(note_node)
        changes.append({"before": "读图说明原位于正文。", "after": note, "reason": "新增就近图注，中文宋体、外文Times New Roman，6号字。"})

    overview = find(body, "图1给出模型的整体流程。")
    replace(overview, text(overview).split("图中省略样本下标n，")[0], changes, "正文保留方法流程，线型和示意说明移至图1下注。")
    figure1 = captions[0].getprevious()
    assert figure1.xpath(".//w:drawing", namespaces=NS)
    for element in (figure1, captions[0], note_nodes[0]):
        body.remove(element)
    anchor = overview
    for element in (figure1, captions[0], note_nodes[0]):
        anchor.addnext(element)
        anchor = element
    changes.append({"before": "图1位于第1.1节之后。", "after": "图1位于方法总览段之后、第1.1节之前。", "reason": "框架图紧接其首次说明，不改变图片尺寸。"})

    figure2_result = find(body, "图2使用本文方法与LightTS共有的随机种子")
    replace(figure2_result, text(figure2_result).split("MSE、MAE和RMSE的平均降幅", 1)[1].join(["MSE、MAE和RMSE的平均降幅", ""]), changes, "图2计算口径移入图注，正文保留全部结果数值。")
    body.remove(figure2_result)
    note_nodes[1].addnext(figure2_result)

    result3 = find(body, "图3以DLinear和固定等权多尺度模型为对照，")
    lead3 = paragraph(template, "图3进一步展示本文方法相对DLinear和固定等权多尺度模型的逐种子改进分布。")
    result3.addprevious(lead3)
    replace(result3, "相对DLinear时，" + text(result3).split("相对DLinear时，", 1)[1], changes, "图3图形编码移入图注，结果解释放在图后；保留全部改进率及例外。")
    body.remove(result3)
    note_nodes[2].addnext(result3)
    set_property(result3, "keepLines", val=0)
    set_property(result3, "widowControl", val=1)

    result4 = find(body, "图4(a、b)汇总随机种子42～49")
    old4 = text(result4)
    lead4 = paragraph(template, "图4从全测试点分组预测与典型窗口轨迹两个层面展示预测行为。")
    result4.addprevious(lead4)
    observation = old4.split("高真实值区间中，", 1)[1].split("图4(c～f)", 1)[0]
    examples = old4.split("本文方法在四例中的三例", 1)[1]
    replace(result4, "高真实值区间中，" + observation + "本文方法在四例中的三例" + examples, changes, "汇总和选例规则移至图注，预测表现解释紧跟图4；保留Abilene例外及24步误差说明。")
    body.remove(result4)
    note_nodes[3].addnext(result4)
    set_property(result4, "keepLines", val=0)
    set_property(result4, "widowControl", val=1)

    lead5 = find(body, "随机种子42～49的三个尺度权重见图5，")
    replace(lead5, "图5展示3个尺度的权重分布及各随机种子的平均权重。", changes, "图5的种子、色彩和误差线定义移至图注，数值和权重方差分析保持原样。")
    for lead in (lead3, lead4, lead5):
        set_property(lead, "keepNext", val=1)

    save_verify(source, target, 3, original, root, members, infos, source_hash, changes)


def config_audit():
    results = ROOT / "abilene_forecasting/results"
    groups = defaultdict(list)
    evidence = []
    for dataset in ("abilene", "geant"):
        for model in ("dlinear", "dlinear_scale", "dlinear_scale_static", "lightts", "dlinear_scale_global", "dlinear_scale_constant_router"):
            branch = "global_weight_ablation" if model == "dlinear_scale_global" else "constant_router_ablation" if model == "dlinear_scale_constant_router" else ""
            seeds = range(42, 45) if model == "lightts" else range(42, 50)
            for seed in seeds:
                path = results / branch / dataset / f"{model}_seed{seed}" / "metrics.json"
                record = json.loads(path.read_text(encoding="utf-8"))
                fields = {k: record[k] for k in ("input_len", "pred_len", "batch_size", "epochs_max", "patience", "learning_rate")}
                expected = {"input_len": 96, "pred_len": 24, "batch_size": 16, "epochs_max": 50 if model == "lightts" else 30, "patience": 10 if model == "lightts" else 6, "learning_rate": 0.0001 if model == "lightts" else 0.001}
                assert fields == expected, path
                if model == "lightts":
                    assert record["model_config"]["d_model"] == 512
                    assert record["model_config"]["chunk_size"] == 24
                    assert record["model_config"]["dropout"] == 0.1
                    assert record["model_config"]["source_commit"] == "4e938a1767106324dd753b2a44832bf870a0252e"
                groups[model].append(fields)
                evidence.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "configuration": fields,
                                 "model_config": record.get("model_config", {})})
    folder = results / "inference_benchmark"
    metadata = json.loads((folder / "benchmark_metadata.json").read_text(encoding="utf-8"))
    with (folder / "inference_benchmark_raw.csv").open(encoding="utf-8", newline="") as f:
        raw = list(csv.DictReader(f))
    assert len(raw) == 48
    for row in raw:
        assert int(row["warmup_steps"]) == 20 and int(row["timed_repeats"]) == 10
        assert int(row["batch_size"]) == 16
        repeats = json.loads(row["repeat_seconds"])
        assert len(repeats) == 10
        reconstructed = statistics.mean(repeats) / int(row["batch_count"]) * 1000
        assert abs(reconstructed - float(row["batch_latency_ms_mean"])) < 1e-9
    with (folder / "inference_benchmark_summary.csv").open(encoding="utf-8", newline="") as f:
        summary = list(csv.DictReader(f))
    expected_latency = {("abilene", "dlinear"): "0.77", ("abilene", "dlinear_scale_static"): "2.38", ("abilene", "dlinear_scale"): "2.65", ("geant", "dlinear"): "0.70", ("geant", "dlinear_scale_static"): "2.10", ("geant", "dlinear_scale"): "2.61"}
    for row in summary:
        assert f"{float(row['latency_ms_mean']):.2f}" == expected_latency[(row["dataset"], row["model"])]
        values = [float(x["batch_latency_ms_mean"]) for x in raw if x["dataset"] == row["dataset"] and x["model"] == row["model"]]
        assert len(values) == 8
        assert abs(statistics.mean(values) - float(row["latency_ms_mean"])) < 1e-12
    for name in ("benchmark_metadata.json", "inference_benchmark_raw.csv", "inference_benchmark_summary.csv"):
        evidence.append({"path": str((folder / name).relative_to(ROOT)), "sha256": sha(folder / name)})
    audit = {"training_run_count": len(evidence) - 3, "training_groups": {k: {"count": len(v), "configuration": v[0]} for k, v in groups.items()},
             "lightts_source_commit": "4e938a1767106324dd753b2a44832bf870a0252e",
             "timing_record_count": len(raw), "warmup_steps": 20, "full_test_repeats": 10,
             "software": {"python": metadata["hardware"]["python"], "torch": metadata["hardware"]["torch"]},
             "timing_backend_not_recorded_in_original_batch": "timing_backend" not in metadata,
             "timing_data_reconstructed": True, "evidence": evidence}
    (QA / "configuration_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def step4():
    audit = config_audit()
    source, target = OUTPUT / "2026.10.03v59.docx", OUTPUT / "2026.10.03v60.docx"
    original, root, members, infos, source_hash = read_source(source, target, 4)
    body = root.find("w:body", NS)
    changes = []
    settings = find(body, "所有模型使用相同的数据划分、输入和预测长度、")
    replace(settings, "所有模型使用相同的数据划分、输入和预测长度、评价指标及批量大小16，均采用Adam优化器，未分别搜索最优超参数。DLinear及各多尺度模型的学习率为0.001，最多训练30轮，验证集MSE连续6轮无改善时提前停止；LightTS的学习率为0.0001，最多训练50轮，早停耐心值为10轮。可训练融合参数与尺度专家共同优化，各模型均按验证集MSE选择参数，测试集仅用于最终统计。", changes, "核对86份实际运行记录，补学习率、优化器和早停条件，保留原训练上限和模型选择规则。")
    lightts = paragraph(settings, "LightTS采用THUML的公开实现，分块长度为24、模型维度参数为512；DLinear及各尺度专家的移动平均窗口均为25，路由隐藏层维度为16。软件版本为Python 3.11.9和PyTorch 2.5.1。")
    settings.addnext(lightts)
    changes.append({"before": "LightTS的分块、模型维度参数及软件版本未集中列出。", "after": text(lightts), "reason": "实现参数来自6份LightTS记录和适配器，核心参数来自模型代码，软件版本来自项目实验说明与计时记录。Dropout配置在预测路径中未调用，不作为生效的预测配置写入正文。"})
    interval = find(body, "指标在标准化空间计算，越小越好。")
    replace(interval, text(interval) + "95%置信区间依据配对种子改进率的均值和标准误，采用自由度为7的t分布计算。", changes, "按实际分析与作图代码补充8种子置信区间计算方法，不改区间数值。")
    timing = find(body, "使用预测长度为24的8个随机种子检查点")
    replace(timing, "使用预测长度为24、种子42～49的8个检查点单独测量前向计算开销。模型置于评估模式并关闭梯度计算，测试张量预先加载，批量大小为16。每个检查点先预热20批，再对完整测试集重复计时10次；每次总耗时除以批次数，先对10次计时取平均，再对8个检查点取平均。本文方法在Abilene和GÉANT上的平均每批前向耗时分别为2.65 ms和2.61 ms，固定等权模型分别为2.38 ms和2.10 ms，单尺度DLinear分别为0.77 ms和0.70 ms。计时仅覆盖模型前向计算，不含数据读取与传输。", changes, "明确旧批次的预热、重复、汇总和计时范围；6项耗时与原始记录对应，不混入后续事件计时批次。")
    before_timing = next(x["before"] for x in changes if x["before"].startswith("使用预测长度为24的8个"))
    assert re.findall(r"\d+\.\d+ ms", before_timing) == re.findall(r"\d+\.\d+ ms", text(timing))
    save_verify(source, target, 4, original, root, members, infos, source_hash, changes)
    report(audit)


def report(config):
    stage3 = json.loads((QA / "step3_changes.json").read_text(encoding="utf-8"))
    stage4 = json.loads((QA / "step4_changes.json").read_text(encoding="utf-8"))
    lines = ["# v60第三步与第四步修改报告", "", "## 本次修改", "",
             "在v58基础上依次形成v59（第三步）与v60（第四步）。最终交付v60，原v58及第三步稿保留。",
             "第三步缩短5幅图的图题，统一就近图注，调整图与说明的顺序。第四步补充实际训练、基线实现、软件及计时协议，未重新训练或替换任何实验结果。", "",
             "## 第三步 修改前后", ""]
    for i, change in enumerate(stage3["changes"], 1):
        lines += [f"### 3.{i}", "", "**修改前：** " + change["before"], "", "**修改后：** " + change["after"], "", "**原因：** " + change["reason"], ""]
    lines += ["## 第四步 修改前后", ""]
    for i, change in enumerate(stage4["changes"], 1):
        lines += [f"### 4.{i}", "", "**修改前：** " + change["before"], "", "**修改后：** " + change["after"], "", "**原因：** " + change["reason"], ""]
    lines += ["## 配置与实验来源核对", "", "| 项目 | 核对结果 |", "|---|---|",
              "| 训练记录 | 86份H=24记录；5类核心模型各16份，LightTS 6份 |",
              "| 核心模型 | Adam，学习率0.001，批量16，最多30轮，早停耐心值6 |",
              "| LightTS | Adam，学习率0.0001，批量16，最多50轮，早停耐心值10 |",
              "| LightTS实现 | THUML Time-Series-Library，提交4e938a1767106324dd753b2a44832bf870a0252e；分块24、模型维度参数512 |",
              "| 核心实现 | 各专家移动平均窗口25；路由4→16→3 |",
              "| 软件版本 | 项目实验记录为PyTorch 2.5.1；计时元数据记录Python 3.11.9、PyTorch 2.5.1，文稿未写设备型号 |",
              "| 原前向计时 | 48个检查点记录，预热20批，完整测试集重复10次，批量16 |",
              "| 耗时复算 | 用逐次总秒数÷批次数×1000重建每批耗时，再按检查点汇总，与原6项耗时一致 |",
              "| 95%区间 | 对8个配对种子改进率，用自由度7的t分布及均值标准误计算 |", "",
              "### LightTS配置的生效范围", "",
              "实际记录与适配器中的dropout字段为0.1，但官方实现只在分类分支构造Dropout；本项目的预测分支没有调用它。因此正文只列分块长度与模型维度参数，不把0.1写成预测时生效的正则化比率。512为d_model配置值，不能误写成所有内部线性层的实际隐藏维度均为512。此核对未改变实现或训练结果。", "",
              "### 计时来源说明", "",
              "文稿中的2.65/2.61、2.38/2.10、0.77/0.70 ms对应`abilene_forecasting/results/inference_benchmark/`。本步沿用该批记录，未替换其数值。另一个`inference_benchmark_cuda_events`批次采用预热50次、重复30次，数值与原批次不同，本步未混用。",
              "原批次元数据没有保存计时后端名称。当前计时脚本已使用事件计时，现有Git中保存的版本也相同，不能据此确定旧批次逐次同步的具体实现。因此正文补充原记录能够确认的预热、重复、平均口径和边界，没有猜写旧批次采用事件计时或某种同步方式。", "",
              "### 保留项", "",
              "5幅图的媒体字节、尺寸与绘图内容，3张表的全部OOXML，41个原生数学对象，11条参考文献逐项保持不变。实验结果正文的百分比及区间未改。第三步只移动/拆分读图说明，全部原百分比出现次数保持一致。第二步的摘要、引言和应用文字保持不变。全文未加入机器硬件配置，未恢复H=12或其他未采纳实验。", "",
              "### 可追溯文件", "",
              "- `abilene_forecasting/train.py`：优化器、训练打乱、验证及早停实现。",
              "- `abilene_forecasting/src/models.py`、`src/lightts_adapter.py`：主干、路由和基线实现。",
              "- `results/{abilene,geant}/*/metrics.json`、全局权重与恒定输入路由目录：实际训练参数。",
              "- `results/inference_benchmark/{benchmark_metadata.json,inference_benchmark_raw.csv,inference_benchmark_summary.csv}`：原计时协议与结果。",
              "- `analyze_global_weight_ablation.py`、`plot_fig3_classic_companion.py`：配对改进率区间。",
              "- 内部核对记录：`word_output/v60_steps3_4_review/configuration_audit.json`，保存来源文件哈希及实际配置。", ""]
    (OUTPUT / "2026.10.03v60_第三四步修改对比.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", type=int, choices=(3, 4))
    args = parser.parse_args()
    step3() if args.step == 3 else step4()
