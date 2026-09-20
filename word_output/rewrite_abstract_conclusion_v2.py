from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "2026.09.19v2.docx"
NS = {"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{%s}" % NS["w"]

CN_ABSTRACT = "为提高骨干网络源—目的节点对短期流量预测对不同时间尺度变化的适应能力，构建一种样本级自适应多尺度轻量预测方法。采用尺度1、2和4的非重叠平均池化生成多分辨率序列，由独立DLinear专家预测；提取窗口均值、标准差、末时刻均值和平均绝对一阶差分，经轻量路由网络生成Softmax权重，对各尺度结果动态融合。在Abilene和GÉANT数据集上，以DLinear、LightTS及固定等权多尺度模型为对比。共同3个随机种子下，所建方法的MSE较DLinear分别降低4.06%和4.43%，较LightTS分别降低29.89%和46.83%；8个随机种子的核心消融结果显示，相较固定等权融合，两数据集MSE分别降低1.67%和4.68%，其中GÉANT跨种子波动更大。结果表明，样本级动态尺度加权能够以较小参数增量利用不同时间分辨率的互补信息，但跨数据集稳定性仍需提升。"
CN_KEYWORDS = "网络流量预测；多变量时间序列；多尺度学习；自适应加权；DLinear"
EN_ABSTRACT = ("A lightweight forecasting method based on sample-wise adaptive multiscale weighting was developed to improve the adaptability of short-term backbone origin-destination (OD) traffic forecasting to variations at different temporal scales. "
               "Non-overlapping average pooling at scales 1, 2, and 4 was used to construct multiresolution sequences, which were processed by independent DLinear experts. "
               "The window mean, standard deviation, mean at the latest time step, and mean absolute first difference were extracted and fed into a lightweight routing network to generate Softmax weights for dynamic fusion of the scale-wise forecasts. "
               "Experiments were conducted on the Abilene and GÉANT datasets, with DLinear, LightTS, and a fixed equal-weight multiscale model as baselines. "
               "Under three common random seeds, the proposed method reduced MSE by 4.06% and 4.43% relative to DLinear, and by 29.89% and 46.83% relative to LightTS on Abilene and GÉANT, respectively. "
               "In the eight-seed core ablation, MSE was reduced by 1.67% and 4.68% compared with fixed equal weighting, while GÉANT exhibited larger cross-seed variability. "
               "These results indicate that sample-wise adaptive scale weighting can exploit complementary temporal-resolution information with only a small parameter increase, although robustness across datasets remains to be improved.")
EN_KEYWORDS = "network traffic forecasting; multivariate time series; multiscale learning; adaptive weighting; DLinear"
CONCLUSION = "在Abilene和GÉANT上的实验表明，样本级自适应多尺度加权可在较小参数增量下改善固定等权融合，并降低相对DLinear和LightTS的平均预测误差；但GÉANT跨种子波动较大。后续将扩展更多网络、预测长度及拓扑约束，以进一步检验稳定性与泛化能力。"

def text(el):
    return "".join(e.text or "" for e in el.iter() if etree.QName(e).localname=="t")

def clone_info(info):
    copied=ZipInfo(info.filename, info.date_time)
    copied.compress_type=ZIP_DEFLATED
    copied.comment=info.comment
    copied.extra=info.extra
    copied.create_system=info.create_system
    copied.external_attr=info.external_attr
    copied.internal_attr=info.internal_attr
    copied.flag_bits=info.flag_bits
    return copied

def replace_labeled_para(p, label, body_text):
    ppr = p.find("w:pPr", NS)
    runs = p.findall("w:r", NS)
    label_rpr = deepcopy(runs[0].find("w:rPr", NS)) if runs and runs[0].find("w:rPr", NS) is not None else None
    body_rpr = None
    for r in runs[1:]:
        if text(r).strip():
            rp = r.find("w:rPr", NS)
            if rp is not None:
                body_rpr = deepcopy(rp)
            break
    if body_rpr is None and runs:
        rp = runs[-1].find("w:rPr", NS)
        body_rpr = deepcopy(rp) if rp is not None else None
    for child in list(p):
        if child is not ppr:
            p.remove(child)
    r1=etree.SubElement(p,W+"r")
    if label_rpr is not None: r1.append(label_rpr)
    t1=etree.SubElement(r1,W+"t")\n    if label.endswith(" "):\n        t1.set("{http://www.w3.org/XML/1998/namespace}space","preserve")\n    t1.text=label
    r2=etree.SubElement(p,W+"r")
    if body_rpr is not None: r2.append(body_rpr)
    t2=etree.SubElement(r2,W+"t"); t2.text=body_text

def replace_plain_para(p, body_text):
    ppr=p.find("w:pPr",NS)
    runs=p.findall("w:r",NS)
    rpr=deepcopy(runs[0].find("w:rPr",NS)) if runs and runs[0].find("w:rPr",NS) is not None else None
    for child in list(p):
        if child is not ppr:
            p.remove(child)
    r=etree.SubElement(p,W+"r")
    if rpr is not None: r.append(rpr)
    t=etree.SubElement(r,W+"t"); t.text=body_text

with ZipFile(DOCX,"r") as zin:
    document=etree.fromstring(zin.read("word/document.xml"))
    body=document.find("w:body",NS)
    paras=[e for e in body if e.tag==W+"p"]

    cn_abs=next(p for p in paras if text(p).strip().startswith("摘要："))
    cn_kw=next(p for p in paras if text(p).strip().startswith("关键词："))
    en_abs=next(p for p in paras if text(p).strip().startswith("Abstract:"))
    en_kw=next(p for p in paras if text(p).strip().startswith("Key words:"))
    concl_heading=next(i for i,p in enumerate(paras) if text(p).strip()=="3 结论")
    concl=paras[concl_heading+1]

    replace_labeled_para(cn_abs,"摘要：",CN_ABSTRACT)
    replace_labeled_para(cn_kw,"关键词：",CN_KEYWORDS)
    replace_labeled_para(en_abs,"Abstract: ",EN_ABSTRACT)
    replace_labeled_para(en_kw,"Key words: ",EN_KEYWORDS)
    replace_plain_para(concl,CONCLUSION)

    # Guardrails.
    if not (300 <= len(CN_ABSTRACT) <= 400):
        raise RuntimeError(f"Chinese abstract length out of range: {len(CN_ABSTRACT)}")
    if len(CONCLUSION) > 150:
        raise RuntimeError(f"Conclusion too long: {len(CONCLUSION)}")
    forbidden=["频域","频率保留","低频门控","frequency-domain","frequency-retention","low-frequency"]
    targets="\n".join([CN_ABSTRACT,CN_KEYWORDS,EN_ABSTRACT,EN_KEYWORDS,CONCLUSION])
    for token in forbidden:
        if token.lower() in targets.lower():
            raise RuntimeError("Forbidden legacy term remains: "+token)
    for token in ["Abilene","GÉANT","LightTS","8个随机种子"]:
        if token not in CN_ABSTRACT:
            raise RuntimeError("Required abstract item missing: "+token)
    for token in ["本文","我们","作者","笔者"]:
        if token in CN_ABSTRACT:
            raise RuntimeError("Third-person abstract violation: "+token)

    output=etree.tostring(document,xml_declaration=True,encoding="UTF-8",standalone=True)
    tmp=DOCX.with_suffix(".tmp.docx")
    with ZipFile(tmp,"w",ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            payload=output if info.filename=="word/document.xml" else zin.read(info.filename)
            zout.writestr(clone_info(info),payload)
    tmp.replace(DOCX)

print("Updated abstract, keywords and conclusion.")
print("Chinese abstract length:",len(CN_ABSTRACT))
print("Conclusion length:",len(CONCLUSION))
