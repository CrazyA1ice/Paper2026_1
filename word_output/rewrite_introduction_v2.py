from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "word_output" / "2026.09.19v2.docx"

NS = {"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{%s}" % NS["w"]

def text(el):
    return "".join(e.text or "" for e in el.iter() if etree.QName(e).localname == "t")

def clone_info(info):
    copied = ZipInfo(info.filename, info.date_time)
    copied.compress_type = ZIP_DEFLATED
    copied.comment = info.comment
    copied.extra = info.extra
    copied.create_system = info.create_system
    copied.external_attr = info.external_attr
    copied.internal_attr = info.internal_attr
    copied.flag_bits = info.flag_bits
    return copied

def first_run_rpr(p):
    r = p.find("w:r", NS)
    if r is None:
        return None
    rpr = r.find("w:rPr", NS)
    return deepcopy(rpr) if rpr is not None else None

def set_para_text(p, value):
    ppr = p.find("w:pPr", NS)
    rpr = first_run_rpr(p)
    for child in list(p):
        if child is not ppr:
            p.remove(child)
    r = etree.SubElement(p, W + "r")
    if rpr is not None:
        r.append(rpr)
    t = etree.SubElement(r, W + "t")
    t.text = value
    return p

with ZipFile(DOCX, "r") as zin:
    document = etree.fromstring(zin.read("word/document.xml"))
    body = document.find("w:body", NS)
    children = list(body)

    ch1_idx = next(i for i,e in enumerate(children)
                   if e.tag == W+"p" and text(e).strip()=="1 自适应多尺度网络流量预测方法")
    intro = [(i,e,text(e).strip()) for i,e in enumerate(children[:ch1_idx])
             if e.tag == W+"p" and text(e).strip().startswith("随着网络业务规模")]
    if len(intro) != 1:
        raise RuntimeError(f"Unexpected intro start count: {len(intro)}")
    p13_idx = intro[0][0]
    paras = [children[p13_idx], children[p13_idx+1], children[p13_idx+2]]
    old = [text(p).strip() for p in paras]
    if not any("频域" in s for s in old):
        raise RuntimeError("Expected legacy frequency wording not found in introduction")

    new_paras = [
        "随着云计算、视频业务和数据中心互联等网络应用持续发展，骨干网络业务需求呈现明显的时变性、突发性和多时间尺度特征。源—目的节点对（origin-destination，OD）流量能够刻画网络入口与出口之间的业务需求，其短期预测结果可为容量规划、拥塞预警、流量工程和资源调度提供依据。网络流量预测方法已由传统统计模型逐步发展到机器学习和深度学习方法[1]。针对通信网络中的时空相关性，Qin等[2]采用图神经网络建模空间依赖关系；韦烜等[9]对大型互联网协议（Internet Protocol，IP）网络流量矩阵的分析预测进行了研究。这类方法拓展了流量预测的建模能力，但对于仅利用历史OD流量、强调结构简洁和参数规模受控的应用场景，仍有必要探索更轻量的时序建模方式。",
        "网络流量在不同时间尺度上包含互补信息：细粒度序列保留局部变化，较粗粒度序列有助于突出相对平滑的趋势。Zhou等[3]利用多尺度回声状态网络提取不同时间尺度的流量特征；TimeMixer通过可分解多尺度混合实现不同分辨率信息交互[7]；CycleLLH从周期性整合角度改进网络流量预测[10]。在轻量时间序列预测方面，DLinear通过趋势项与余项分解配合线性映射实现多步预测[4]；LightTS采用连续采样和间隔采样配合多层感知机结构，以较低计算开销建模多变量时间序列[11]。这些研究说明，多尺度表征与简洁预测结构均具有应用潜力，也为在参数规模受控条件下进一步研究尺度融合提供了基础。",
        "现有研究分别从拓扑关联、多尺度表征和轻量序列建模等角度提升预测能力，但在不显式依赖网络拓扑的历史OD序列预测场景中，如何根据当前输入窗口的状态动态确定不同时间尺度的重要性，仍值得进一步研究。为此，本文构建基于DLinear尺度专家的样本级自适应多尺度预测方法：采用尺度1、2和4构造多分辨率序列，由独立尺度专家生成候选预测，再从输入窗口提取均值、标准差、末时刻均值和平均绝对一阶差分，通过轻量路由网络生成Softmax权重，实现样本级动态融合。实验在Abilene和GÉANT两个骨干网数据集上开展，并引入DLinear、LightTS和固定等权多尺度模型进行比较；同时使用8个随机种子分析核心机制的稳定性，以检验性能改善是否来自样本级自适应尺度加权。"
    ]
    for p,val in zip(paras,new_paras):
        set_para_text(p,val)

    # Append LightTS forecasting paper as reference [11] using the existing reference style.
    ref_heading_idx = next(i for i,e in enumerate(children)
                           if e.tag == W+"p" and text(e).strip()=="参考文献")
    refs = [e for e in children[ref_heading_idx+1:] if e.tag == W+"p" and text(e).strip()]
    if any("Less is more: fast multivariate time series forecasting" in text(e) for e in refs):
        raise RuntimeError("LightTS reference already exists")
    ref_template = refs[-1]
    new_ref = deepcopy(ref_template)
    set_para_text(new_ref,
        "[11] ZHANG T, ZHANG Y, CAO W, et al. Less is more: fast multivariate time series forecasting with light sampling-oriented MLP structures[EB/OL]. (2022-07-04)[2026-09-20]. https://arxiv.org/abs/2207.01186. DOI: 10.48550/arXiv.2207.01186."
    )
    last_ref_idx = max(i for i,e in enumerate(list(body))
                       if e.tag == W+"p" and text(e).strip().startswith("[10]"))
    body.insert(last_ref_idx+1, new_ref)

    # Guardrails: front matter intentionally remains untouched for the next step.
    all_children=list(body)
    ch1_idx2=next(i for i,e in enumerate(all_children)
                  if e.tag == W+"p" and text(e).strip()=="1 自适应多尺度网络流量预测方法")
    intro_text="\n".join(text(e) for e in all_children[:ch1_idx2] if e.tag==W+"p")
    intro_body="\n".join(text(e) for e in all_children[p13_idx:ch1_idx2] if e.tag==W+"p")
    for forbidden in ["FEDformer","FITS","频域门控","频率保留"]:
        if forbidden in intro_body:
            raise RuntimeError("Legacy frequency content remains in introduction: "+forbidden)
    for required in ["LightTS","Abilene","GÉANT","8个随机种子","样本级自适应多尺度"]:
        if required not in intro_body:
            raise RuntimeError("Required introduction content missing: "+required)

    output = etree.tostring(document, xml_declaration=True, encoding="UTF-8", standalone=True)
    tmp = DOCX.with_suffix(".tmp.docx")
    with ZipFile(tmp, "w", ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            payload = output if info.filename=="word/document.xml" else zin.read(info.filename)
            zout.writestr(clone_info(info), payload)
    tmp.replace(DOCX)

print("Introduction rewritten and LightTS reference appended.")
